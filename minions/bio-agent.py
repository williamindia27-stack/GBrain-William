"""
bio-agent.py
Agent-style researcher bio enrichment using Claude (Anthropic).

Unlike enrich-researchers.py (Groq + 300-char snippets), this agent:
  1. Reads the FULL content of every paper linked to the researcher
  2. Asks Claude to reason about their specialties and contributions
  3. Writes a rich, specific 5-6 sentence bio — no made-up facts
  4. Marks pages so they are not overwritten on re-run

Idempotent: pages already enriched by this script are skipped.
"""

import os, sys, re, subprocess, time, datetime
from pathlib import Path

# Force UTF-8 output on Windows (avoids cp1252 crash on accented names)
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import urllib.request, json, ssl as _ssl

NVIDIA_API_KEY    = os.environ.get("NVIDIA_API_KEY", "")
EXTRACTED_DIR     = Path(r"C:\brain\extracted")
GBRAIN_CMD        = os.path.join(os.path.expanduser("~"), ".bun", "bin", "gbrain.cmd")
LOG               = Path(r"C:\brain\minions\bio-agent.log")
MODEL             = "meta/llama-3.3-70b-instruct"

# Characters of paper body fed to Claude per paper (enough for abstract + contributions)
PAPER_EXCERPT_CHARS = 4000
# Max papers to read per researcher
MAX_PAPERS = 5
# Min chars in Overview to consider it already enriched by THIS agent
# We re-enrich Groq stubs (< 600 chars) with richer Claude bios
STUB_THRESHOLD = 600
# Tag written into the page to mark it as done
AGENT_TAG = "<!-- bio-agent -->"

ENV = {
    **os.environ,
    "PATH": os.path.join(os.path.expanduser("~"), ".bun", "bin") + ";" + os.environ.get("PATH", ""),
    "GBRAIN_POOL_SIZE": "2",
}


# ── helpers ───────────────────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def extract_section(content: str, section: str) -> str:
    m = re.search(rf"^## {re.escape(section)}\s*\n(.*?)(?=^## |\Z)", content, re.M | re.S)
    return m.group(1).strip() if m else ""


def is_stub(content: str) -> bool:
    if AGENT_TAG in content:
        return False   # already done by this agent
    overview = extract_section(content, "Overview")
    plain = re.sub(r"\[\[.*?\]\]", "", overview)
    plain = re.sub(r"\*\*.*?\*\*", "", plain)
    plain = re.sub(r"\s+", " ", plain).strip()
    return len(plain) < STUB_THRESHOLD


def gbrain_import(path: Path):
    try:
        r = subprocess.run(
            ["cmd.exe", "/c", GBRAIN_CMD, "import", "--file", str(path), "--no-embed"],
            capture_output=True, env=ENV, timeout=60,
        )
        if r.returncode != 0:
            log(f"    Import failed: {r.stderr.decode('utf-8', errors='replace').strip()[:120]}")
    except Exception as e:
        log(f"    Import error: {e}")


# ── paper reading ─────────────────────────────────────────────────────────────

def find_linked_papers(slug: str, kind: str) -> list[Path]:
    """Return paths of papers that contain [[kind/slug|...]]."""
    pattern = re.compile(rf"\[\[{re.escape(kind)}/{re.escape(slug)}[|\]]")
    found = []
    for fpath in EXTRACTED_DIR.glob("*.md"):
        try:
            if pattern.search(fpath.read_text(encoding="utf-8", errors="replace")):
                found.append(fpath)
        except Exception:
            pass
    return found[:MAX_PAPERS]


def read_paper_excerpt(path: Path) -> str:
    """Read the most informative part of a paper: title + overview + first big section."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""

    # Get title from frontmatter
    title = path.stem.replace("_", " ")
    for line in content.splitlines()[:10]:
        if line.startswith("title:"):
            title = line[6:].strip().strip('"').strip("'")
            break

    # Strip frontmatter
    body = re.sub(r"^---.*?---\s*", "", content, flags=re.S).strip()

    excerpt = f"PAPER: {title}\n\n{body[:PAPER_EXCERPT_CHARS]}"
    return excerpt


# ── Claude call ───────────────────────────────────────────────────────────────

def call_claude(name: str, institution: str, paper_excerpts: list[str]) -> str | None:
    if not NVIDIA_API_KEY:
        log("  ERROR: NVIDIA_API_KEY not set")
        return None

    papers_block = "\n\n---\n\n".join(paper_excerpts) if paper_excerpts else "(no papers found)"

    prompt = f"""You are enriching a research knowledge graph. Write a rich, specific bio for this researcher.

RESEARCHER: {name}
INSTITUTION: {institution or "Unknown"}

PAPERS THEY AUTHORED (full excerpts):
{papers_block}

INSTRUCTIONS:
- Write exactly 5-6 sentences in third person, present tense
- Sentence 1: who they are and their primary research domain
- Sentence 2-4: their specific contributions, methods, or findings — cite exact paper titles or topics
- Sentence 5: their broader impact or research vision if inferable
- Do NOT invent facts not supported by the excerpts
- Do NOT use phrases like "according to" or "in their paper"
- Plain text only — no markdown, no bullet points
- End with a period

Write only the bio, nothing else."""

    try:
        ctx = _ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = _ssl.CERT_NONE
        payload = json.dumps({
            "model": MODEL,
            "max_tokens": 400,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {NVIDIA_API_KEY}"},
        )
        with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
            data = json.loads(r.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log(f"  NVIDIA error: {e}")
        return None


# ── page update ───────────────────────────────────────────────────────────────

def replace_overview(content: str, new_bio: str) -> str:
    """Replace the Overview body, keeping **Affiliation:** lines."""
    m = re.search(r"(^## Overview\s*\n)(.*?)(?=^## |\Z)", content, re.M | re.S)
    if not m:
        return content
    existing_body = m.group(2)
    keep_lines = [l for l in existing_body.splitlines() if l.strip().startswith("**")]
    suffix = ("\n" + "\n".join(keep_lines)) if keep_lines else ""
    new_body = f"\n{AGENT_TAG}\n{new_bio}{suffix}\n\n"
    return content[:m.start(2)] + new_body + content[m.end(2):]


# ── main ─────────────────────────────────────────────────────────────────────

def process_person(path: Path) -> bool:
    content = path.read_text(encoding="utf-8", errors="replace")
    if not is_stub(content):
        return False

    # Extract name and institution
    name = path.stem.replace("-", " ").title()
    for line in content.splitlines()[:8]:
        if line.startswith("title:"):
            name = line[6:].strip().strip('"').strip("'")
            break

    inst_m = re.search(r"\[\[companies/[^\|]+\|([^\]]+)\]\]", content)
    institution = inst_m.group(1) if inst_m else ""

    paper_paths = find_linked_papers(path.stem, "people")
    log(f"  {name} @ {institution or '?'} — {len(paper_paths)} paper(s)")

    if not paper_paths:
        log(f"    No linked papers found — skipping")
        return False

    excerpts = [read_paper_excerpt(p) for p in paper_paths]
    bio = call_claude(name, institution, excerpts)
    if not bio:
        return False

    log(f"    Bio: {bio[:120]}...")

    new_content = replace_overview(content, bio)

    # Add timeline entry
    today = datetime.date.today().isoformat()
    new_content = re.sub(
        r"(## Timeline\s*\n)",
        rf"\1\n- **{today}** — Bio enriched by bio-agent (Claude {MODEL})\n",
        new_content,
    )

    path.write_text(new_content, encoding="utf-8")
    gbrain_import(path)
    return True


def main():
    log("=" * 60)
    log("bio-agent started")

    if not NVIDIA_API_KEY:
        log("ERROR: NVIDIA_API_KEY not set — exiting")
        sys.exit(1)

    people_dir = EXTRACTED_DIR / "people"
    if not people_dir.exists():
        log("No people/ directory found")
        sys.exit(0)

    pages = sorted(people_dir.glob("*.md"))
    log(f"  Found {len(pages)} people pages")

    enriched = 0
    skipped  = 0

    for path in pages:
        ok = process_person(path)
        if ok:
            enriched += 1
            time.sleep(1.0)   # rate limiting — Claude Haiku is fast but be gentle
        else:
            skipped += 1

    log(f"\n  Done: {enriched} enriched, {skipped} skipped (already full or no papers)")
    log("bio-agent finished OK")
    log("=" * 60)


if __name__ == "__main__":
    main()
