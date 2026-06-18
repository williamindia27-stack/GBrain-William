"""
enrich-researchers.py
Enriches stub people/ and companies/ pages with research bios generated via Groq.
Runs after build-research-graph so new researcher stubs are ready to be filled out.
"""
import os, sys, json, re, subprocess, time, datetime
from pathlib import Path

GROQ_API_KEY  = os.environ.get("GROQ_API_KEY", "")
EXTRACTED_DIR = Path(r"C:\brain\extracted")
GBRAIN_CMD    = os.path.join(os.path.expanduser("~"), ".bun", "bin", "gbrain.cmd")
LOG           = Path(r"C:\brain\minions\enrich-researchers.log")
ENV = {**os.environ, "PATH": os.path.join(os.path.expanduser("~"), ".bun", "bin") + ";" + os.environ.get("PATH", ""), "GBRAIN_POOL_SIZE": "2"}

# A page is a stub if the Overview body has fewer than this many real content characters
STUB_THRESHOLD = 220


def log(msg: str):
    print(msg, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def extract_section(content: str, section: str) -> str:
    """Return the body of a ## Section up to the next ## or sentinel."""
    m = re.search(rf"^## {re.escape(section)}\s*\n(.*?)(?=^## |\Z)", content, re.M | re.S)
    return m.group(1).strip() if m else ""


def is_stub(content: str) -> bool:
    """True if the Overview section has very little real content."""
    overview = extract_section(content, "Overview")
    # Strip wikilinks and formatting to get plain text length
    plain = re.sub(r"\[\[.*?\]\]", "", overview)
    plain = re.sub(r"\*\*.*?\*\*", "", plain)
    plain = re.sub(r"\s+", " ", plain).strip()
    return len(plain) < STUB_THRESHOLD


def find_linked_papers(slug: str, kind: str) -> list[dict]:
    """Find all papers that link to [[kind/slug]] and return their title + topics."""
    pattern = re.compile(rf"\[\[{re.escape(kind)}/{re.escape(slug)}[|\]]")
    papers = []
    search_dirs = [EXTRACTED_DIR]

    for search_dir in search_dirs:
        for fpath in search_dir.glob("*.md"):
            try:
                text = fpath.read_text(encoding="utf-8", errors="replace")
                if pattern.search(text):
                    title = fpath.stem.replace("_", " ").title()
                    for line in text.splitlines()[:10]:
                        if line.startswith("title:"):
                            title = line[6:].strip().strip('"').strip("'")
                            break
                    overview = extract_section(text, "Overview")[:300]
                    papers.append({"title": title, "overview": overview})
            except Exception:
                pass
    return papers


def call_groq_person(name: str, institution: str, papers: list[dict]) -> str | None:
    """Generate a research bio for a person."""
    import urllib.request
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
    if not GROQ_API_KEY:
        return None

    paper_lines = "\n".join(f"- {p['title']}: {p['overview'][:150]}" for p in papers[:6]) or "- (no papers found in brain yet)"

    prompt = f"""Write a concise 3-4 sentence research bio for this academic researcher.

Name: {name}
Institution: {institution or "Unknown"}
Papers they authored in the research brain:
{paper_lines}

Rules:
- Write in third person, present tense
- Focus on their research areas and contributions
- Mention specific topics from their papers
- Do NOT make up facts not supported by the paper list
- Keep it under 200 words
- Plain text only, no markdown formatting
- End with a period"""

    return _groq_call(prompt)


def call_groq_institution(name: str, researchers: list[str], papers: list[dict]) -> str | None:
    """Generate an overview for a research institution."""
    import urllib.request
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
    if not GROQ_API_KEY:
        return None

    researcher_line = ", ".join(researchers[:8]) or "(none found)"
    paper_lines = "\n".join(f"- {p['title']}" for p in papers[:8]) or "- (none found)"

    prompt = f"""Write a concise 2-3 sentence overview for this research institution.

Institution: {name}
Researchers from this institution in the brain: {researcher_line}
Papers from this institution:
{paper_lines}

Rules:
- Write in third person, present tense
- Focus on research areas represented in the papers
- Keep it under 150 words
- Plain text only, no markdown
- End with a period"""

    return _groq_call(prompt)


def _groq_call(prompt: str) -> str | None:
    import urllib.request
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
    payload = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 300,
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


def replace_overview(content: str, new_bio: str) -> str:
    """Replace the Overview section body while preserving wikilink lines."""
    # Find the Overview section
    m = re.search(r"(^## Overview\s*\n)(.*?)(?=^## |\Z)", content, re.M | re.S)
    if not m:
        return content

    existing_body = m.group(2)
    # Keep any **Affiliation:** / **Role:** lines (wikilinks we want to preserve)
    keep_lines = [l for l in existing_body.splitlines() if l.strip().startswith("**")]
    suffix = ("\n" + "\n".join(keep_lines)) if keep_lines else ""

    new_body = f"\n{new_bio}{suffix}\n\n"
    return content[:m.start(2)] + new_body + content[m.end(2):]


def gbrain_import(path: Path):
    try:
        r = subprocess.run(
            [GBRAIN_CMD, "import", "--file", str(path), "--no-embed"],
            capture_output=True, env=ENV, timeout=45,
        )
        if r.returncode == 0:
            log(f"  Imported: {path.name}")
        else:
            log(f"  Import failed: {r.stderr.decode('utf-8', errors='replace').strip()[:150]}")
    except Exception as e:
        log(f"  Import error: {e}")


def process_person(path: Path) -> bool:
    content = path.read_text(encoding="utf-8", errors="replace")
    if not is_stub(content):
        return False

    # Extract name and institution from frontmatter / existing overview
    name = path.stem.replace("-", " ").title()
    for line in content.splitlines()[:8]:
        if line.startswith("title:"):
            name = line[6:].strip().strip('"').strip("'")
            break

    inst_m = re.search(r"\[\[companies/[^\|]+\|([^\]]+)\]\]", content)
    institution = inst_m.group(1) if inst_m else ""

    papers = find_linked_papers(path.stem, "people")
    log(f"  {name} @ {institution or '?'} — {len(papers)} paper(s) linked")

    bio = call_groq_person(name, institution, papers)
    if not bio:
        return False

    new_content = replace_overview(content, bio)

    # Add timeline entry
    today = datetime.date.today().isoformat()
    if f"Enriched by enrich-researchers" not in new_content:
        new_content = new_content.replace(
            "<!-- timeline -->",
            f"<!-- timeline -->"
        )
        new_content = re.sub(
            r"(<!-- timeline -->.*?## Timeline\s*\n)",
            rf"\1\n- **{today}** — Enriched by enrich-researchers.py\n",
            new_content, flags=re.S,
        )

    path.write_text(new_content, encoding="utf-8")
    gbrain_import(path)
    return True


def process_institution(path: Path) -> bool:
    content = path.read_text(encoding="utf-8", errors="replace")
    if not is_stub(content):
        return False

    name = path.stem.replace("-", " ").title()
    for line in content.splitlines()[:8]:
        if line.startswith("title:"):
            name = line[6:].strip().strip('"').strip("'")
            break

    papers = find_linked_papers(path.stem, "companies")

    # Find researchers affiliated here
    researchers = []
    people_dir = EXTRACTED_DIR / "people"
    if people_dir.exists():
        inst_pattern = re.compile(rf"\[\[companies/{re.escape(path.stem)}[|\]]")
        for ppath in people_dir.glob("*.md"):
            try:
                text = ppath.read_text(encoding="utf-8", errors="replace")
                if inst_pattern.search(text):
                    rname = ppath.stem.replace("-", " ").title()
                    for line in text.splitlines()[:8]:
                        if line.startswith("title:"):
                            rname = line[6:].strip().strip('"').strip("'")
                            break
                    researchers.append(rname)
            except Exception:
                pass

    log(f"  {name} — {len(researchers)} researcher(s), {len(papers)} paper(s)")

    bio = call_groq_institution(name, researchers, papers)
    if not bio:
        return False

    new_content = replace_overview(content, bio)
    path.write_text(new_content, encoding="utf-8")
    gbrain_import(path)
    return True


def main():
    log(f"\n[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] enrich-researchers started")

    if not GROQ_API_KEY:
        log("ERROR: GROQ_API_KEY not set")
        sys.exit(1)

    people_dir    = EXTRACTED_DIR / "people"
    companies_dir = EXTRACTED_DIR / "companies"
    processed = 0
    skipped   = 0

    # Enrich people pages
    if people_dir.exists():
        for path in sorted(people_dir.glob("*.md")):
            log(f"\nPerson: {path.stem}")
            ok = process_person(path)
            if ok:
                processed += 1
                time.sleep(0.8)
            else:
                skipped += 1

    # Enrich institution pages
    if companies_dir.exists():
        for path in sorted(companies_dir.glob("*.md")):
            log(f"\nInstitution: {path.stem}")
            ok = process_institution(path)
            if ok:
                processed += 1
                time.sleep(0.8)
            else:
                skipped += 1

    log(f"\n[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] Done: {processed} enriched, {skipped} already full")


if __name__ == "__main__":
    main()
