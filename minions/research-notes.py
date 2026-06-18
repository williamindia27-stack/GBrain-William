"""
research-notes.py  (perplexity-research equivalent)
For each paper missing a Research Context section:
  - Reads the paper's compiled summary from the brain
  - Queries the brain for related pages
  - Calls Groq to generate: what's new, related brain pages, knowledge gaps, next steps
  - Appends a ## Research Context section to the paper page
"""
import os, sys, json, re, subprocess, time, datetime, urllib.request, ssl
from pathlib import Path

ssl._create_default_https_context = ssl._create_unverified_context

def _reg(key):
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            return winreg.QueryValueEx(k, key)[0]
    except Exception:
        return ""

GROQ_API_KEY  = os.environ.get("GROQ_API_KEY", "") or _reg("GROQ_API_KEY")
EXTRACTED_DIR = Path(r"C:\brain\extracted")
GBRAIN_CMD    = os.path.join(os.path.expanduser("~"), ".bun", "bin", "gbrain.cmd")
LOG           = Path(r"C:\brain\minions\research-notes.log")
ENV = {**os.environ, "PATH": os.path.join(os.path.expanduser("~"), ".bun", "bin") + ";" + os.environ.get("PATH", ""), "GBRAIN_POOL_SIZE": "2"}

SECTION_MARKER = "## Research Context"


def log(msg: str):
    print(msg, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def extract_section(content: str, section: str) -> str:
    m = re.search(rf"^## {re.escape(section)}\s*\n(.*?)(?=^## |\Z)", content, re.M | re.S)
    return m.group(1).strip() if m else ""


def get_paper_summary(content: str) -> str:
    """Build a compact summary from the paper's structured sections."""
    parts = []
    for section in ["Overview", "Method", "Key Results", "Why It Matters", "Limitations"]:
        body = extract_section(content, section)
        if body:
            parts.append(f"[{section}]\n{body[:400]}")
    return "\n\n".join(parts) if parts else ""


def query_brain(query: str, limit: int = 5) -> list[dict]:
    """Run gbrain query and return parsed results."""
    try:
        r = subprocess.run(
            ["cmd.exe", "/c", GBRAIN_CMD, "query", query, "--limit", str(limit)],
            capture_output=True, env=ENV, timeout=45,
        )
        raw = r.stdout.decode("utf-8", errors="replace")
        results = []
        for line in raw.splitlines():
            m = re.match(r"\[([0-9.]+)\]\s+(\S+)\s+--\s+(.*)", line)
            if m:
                results.append({
                    "score": float(m.group(1)),
                    "slug": m.group(2),
                    "excerpt": m.group(3).strip()[:200],
                })
        return results
    except Exception as e:
        log(f"  brain query error: {e}")
        return []


def call_groq_research_context(title: str, summary: str, related: list[dict]) -> str | None:
    """Generate a Research Context section via Groq."""
    if not GROQ_API_KEY:
        return None

    related_lines = "\n".join(
        f"- [{r['slug']}] {r['excerpt'][:150]}" for r in related
    ) if related else "- (no related pages found in brain)"

    prompt = f"""You are a research analyst. Analyze this paper and generate a structured Research Context section.

PAPER TITLE: {title}

PAPER SUMMARY:
{summary[:2000]}

RELATED PAGES ALREADY IN THE BRAIN:
{related_lines}

Generate a Research Context section with exactly these four subsections:

**What's new:** (1-2 sentences) What does this paper contribute that isn't already in the brain? What's the key novel element?

**Related in brain:** (bullet list) Which brain pages overlap most with this paper? Name them directly. If none are truly related, say so.

**Knowledge gaps:** (1-2 sentences) What assumptions does this paper make that aren't covered in the brain? What would need to be learned to fully evaluate this work?

**Explore next:** (bullet list, max 3) Specific topics, papers, or questions worth investigating based on this paper.

Keep each subsection concise. Use plain text. Start directly with **What's new:**"""

    payload = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 500,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "User-Agent": "python-urllib/3.14",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log(f"  Groq error: {e}")
        return None


def gbrain_import(path: Path):
    try:
        r = subprocess.run(
            ["cmd.exe", "/c", GBRAIN_CMD, "import", "--file", str(path), "--no-embed"],
            capture_output=True, env=ENV, timeout=45,
        )
        if r.returncode == 0:
            log(f"  Imported: {path.name}")
        else:
            log(f"  Import failed: {r.stderr.decode('utf-8', errors='replace').strip()[:150]}")
    except Exception as e:
        log(f"  Import error: {e}")


def process_paper(path: Path) -> bool:
    content = path.read_text(encoding="utf-8", errors="replace")

    # Skip if already has Research Context
    if SECTION_MARKER in content:
        return False

    # Skip if no Overview — raw dump or not a real paper page
    if "## Overview" not in content:
        return False

    # Get title
    title = path.stem.replace("_", " ").title()
    for line in content.splitlines()[:10]:
        if line.startswith("title:"):
            title = line[6:].strip().strip('"').strip("'")
            break

    summary = get_paper_summary(content)
    if not summary:
        log(f"  No summary sections found, skipping")
        return False

    log(f"  Querying brain for related pages…")
    # Use title + first sentence of overview as query
    overview_first = extract_section(content, "Overview")[:200]
    related = query_brain(f"{title} {overview_first}", limit=6)
    # Filter out the paper itself
    related = [r for r in related if r["slug"] != path.stem]
    log(f"  Found {len(related)} related brain pages")

    context_text = call_groq_research_context(title, summary, related)
    if not context_text:
        return False

    today = datetime.date.today().isoformat()
    context_block = f"""\n{SECTION_MARKER}\n\n{context_text}\n\n*Generated {today} by research-notes.py*\n"""

    # Insert before <!-- timeline -->
    if "<!-- timeline -->" in content:
        content = content.replace("<!-- timeline -->", context_block + "\n<!-- timeline -->")
    else:
        content = content.rstrip() + "\n" + context_block

    path.write_text(content, encoding="utf-8")
    gbrain_import(path)
    return True


def discover_papers() -> list[Path]:
    """Return all paper .md files in the root of extracted/ (not in subdirs)."""
    return [p for p in EXTRACTED_DIR.glob("*.md") if p.is_file()]


def main():
    log(f"\n[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] research-notes started")

    if not GROQ_API_KEY:
        log("ERROR: GROQ_API_KEY not set")
        sys.exit(1)

    papers = discover_papers()
    pending = [p for p in papers if SECTION_MARKER not in p.read_text(encoding="utf-8", errors="replace") and "## Overview" in p.read_text(encoding="utf-8", errors="replace")]

    log(f"Found {len(pending)}/{len(papers)} papers needing Research Context")

    processed = 0
    skipped   = 0

    for path in pending:
        log(f"\nPaper: {path.stem}")
        ok = process_paper(path)
        if ok:
            processed += 1
            time.sleep(1.2)  # rate limit
        else:
            skipped += 1

    log(f"\n[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] Done: {processed} processed, {skipped} skipped")


if __name__ == "__main__":
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        # Single-paper mode: python research-notes.py <slug>
        slug = sys.argv[1].removesuffix(".md")
        path = EXTRACTED_DIR / f"{slug}.md"
        if not path.exists():
            log(f"ERROR: {path} not found")
            sys.exit(1)
        content = path.read_text(encoding="utf-8", errors="replace")
        force = "--force" in sys.argv
        if SECTION_MARKER in content and not force:
            log(f"Paper already has Research Context. Pass --force to re-generate.")
            sys.exit(0)
        log(f"\n[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] Single-paper mode: {slug}")
        ok = process_paper(path)
        sys.exit(0 if ok else 1)
    else:
        main()
