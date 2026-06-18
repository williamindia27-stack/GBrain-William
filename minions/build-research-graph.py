"""
build-research-graph.py
Extracts authors and institutions from paper PDFs via Groq,
creates people/ and companies/ pages in the brain,
and adds ## Authors sections to paper pages.
"""
import os
import sys
import json
import re
import subprocess
import time
import datetime
from pathlib import Path

GROQ_API_KEY  = os.environ.get("GROQ_API_KEY", "")
EXTRACTED_DIR = Path(r"C:\brain\extracted")
BASE_PDF_DIR  = Path(r"C:\brain\papers")
PAPERS_PDF_DIR = Path(r"C:\brain\papers")
GBRAIN_CMD    = os.path.join(os.path.expanduser("~"), ".bun", "bin", "gbrain.cmd")
LOG           = Path(r"C:\brain\minions\build-research-graph.log")

BASE_PAPERS = {
    "agentic_world_modeling":            "Agentic World Modeling",
    "openhands":                         "OpenHands",
    "agentscope":                        "AgentScope",
    "multi_agent_trading":               "TradingAgents",
    "ai_trader_agent":                   "AI-Trader",
    "kronos_a_foundation_model":         "Kronos",
    "image_regonition_phone_avatar":     "MUA (Mobile Avatars)",
    "human_ai_oversight_video_language": "CHAI",
    "agentic":                           "BLF (Forecasting)",
    "python_cosmological":               "Smokescreen",
}

ENV = {**os.environ, "PATH": os.path.join(os.path.expanduser("~"), ".bun", "bin") + ";" + os.environ.get("PATH", ""), "GBRAIN_POOL_SIZE": "2"}


def log(msg: str):
    print(msg, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def extract_pdf_text(pdf_path: Path, max_pages: int = 3) -> str:
    """Extract text from the first N pages of a PDF."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        pages = reader.pages[:max_pages]
        return "\n".join(page.extract_text() or "" for page in pages)
    except Exception as e:
        log(f"  pypdf failed: {e}")
        return ""


def call_groq(text: str) -> dict | None:
    """Call Groq to extract author/institution JSON from PDF text."""
    import urllib.request
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
    if not GROQ_API_KEY:
        log("  No GROQ_API_KEY, skipping")
        return None

    prompt = f"""Extract the authors and their institutions from this academic paper.
Return ONLY valid JSON with this exact structure (no extra text):
{{
  "authors": [{{"name": "Full Name", "slug": "firstname-lastname", "institution": "Institution Name or empty string"}}],
  "institutions": [{{"name": "Full Institution Name", "slug": "institution-slug"}}],
  "year": 2024,
  "domain": "computer science"
}}

Rules:
- slug: lowercase, hyphens only, no special characters (e.g. "john-smith")
- institution slug: short abbreviation (e.g. "mit-csail", "stanford-cs", "google-deepmind")
- include all authors but max 12
- include all unique institutions but max 6
- if no institution is found for an author, use empty string ""
- year: integer, or null if not found
- domain: one of "computer science", "machine learning", "finance", "physics", "biology", or similar

Paper text (first pages):
{text[:3500]}"""

    payload = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 900,
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
        raw = data["choices"][0]["message"]["content"].strip()
        m = re.search(r'\{[\s\S]*\}', raw)
        if m:
            return json.loads(m.group())
    except Exception as e:
        log(f"  Groq error: {e}")
    return None


def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def write_person_page(author: dict) -> Path:
    """Write people/<slug>.md. Returns path. Skips if already exists."""
    people_dir = EXTRACTED_DIR / "people"
    people_dir.mkdir(exist_ok=True)
    slug = author.get("slug") or slugify(author["name"])
    path = people_dir / f"{slug}.md"
    if path.exists():
        return path

    institution = (author.get("institution") or "").strip()
    affil_line = ""
    if institution:
        inst_slug = slugify(institution)
        affil_line = f"\n**Affiliation:** [[companies/{inst_slug}|{institution}]]"

    today = datetime.date.today().isoformat()
    content = f"""---
title: "{author['name']}"
type: person
tags: [researcher]
---

## Overview

{author['name']} is a researcher{f' at {institution}' if institution else ''}.{affil_line}

<!-- timeline -->

## Timeline

- **{today}** — Discovered via build-research-graph.py
"""
    path.write_text(content, encoding="utf-8")
    log(f"  Created people/{slug}.md")
    return path


def write_institution_page(institution: dict) -> Path:
    """Write companies/<slug>.md. Returns path. Skips if already exists."""
    companies_dir = EXTRACTED_DIR / "companies"
    companies_dir.mkdir(exist_ok=True)
    slug = institution.get("slug") or slugify(institution["name"])
    path = companies_dir / f"{slug}.md"
    if path.exists():
        return path

    today = datetime.date.today().isoformat()
    content = f"""---
title: "{institution['name']}"
type: institution
tags: [research-institution]
---

## Overview

{institution['name']} is a research institution.

<!-- timeline -->

## Timeline

- **{today}** — Discovered via build-research-graph.py
"""
    path.write_text(content, encoding="utf-8")
    log(f"  Created companies/{slug}.md")
    return path


def update_paper_page(slug: str, info: dict):
    """Add ## Authors section above <!-- timeline --> in the paper page."""
    paper_path = EXTRACTED_DIR / f"{slug}.md"
    if not paper_path.exists():
        log(f"  Paper page not found: {slug}.md")
        return

    content = paper_path.read_text(encoding="utf-8")
    if "## Authors" in content:
        log(f"  Already has Authors section: {slug}.md")
        return

    authors = info.get("authors", [])
    if not authors:
        return

    lines = ["## Authors", ""]
    for author in authors:
        a_slug = author.get("slug") or slugify(author["name"])
        institution = (author.get("institution") or "").strip()
        if institution:
            inst_slug = slugify(institution)
            lines.append(f"- [[people/{a_slug}|{author['name']}]] — [[companies/{inst_slug}|{institution}]]")
        else:
            lines.append(f"- [[people/{a_slug}|{author['name']}]]")

    meta = []
    if info.get("year"):
        meta.append(f"**Year:** {info['year']}")
    if info.get("domain"):
        meta.append(f"**Domain:** {info['domain']}")
    if meta:
        lines += ["", " · ".join(meta)]

    authors_block = "\n".join(lines) + "\n\n"

    if "<!-- timeline -->" in content:
        content = content.replace("<!-- timeline -->", authors_block + "<!-- timeline -->")
    else:
        content = content.rstrip() + "\n\n" + authors_block

    paper_path.write_text(content, encoding="utf-8")
    log(f"  Added Authors section to {slug}.md")


def gbrain_import(path: Path):
    """Import a single markdown file into gbrain."""
    try:
        r = subprocess.run(
            ["cmd.exe", "/c", GBRAIN_CMD, "import", "--file", str(path), "--no-embed"],
            capture_output=True, env=ENV, timeout=45
        )
        if r.returncode == 0:
            log(f"  Imported: {path.name}")
        else:
            err = r.stderr.decode("utf-8", errors="replace").strip()[:200]
            log(f"  Import failed ({path.name}): {err}")
    except Exception as e:
        log(f"  Import error: {e}")


def find_pdf(slug: str, display_name: str) -> Path | None:
    """Locate a PDF by trying common filename patterns."""
    candidates = [
        display_name,
        display_name.replace(" ", "_"),
        display_name.replace(" ", "-"),
        slug,
        slug.replace("_", " "),
        slug.replace("_", "-"),
    ]
    for name in candidates:
        p = BASE_PDF_DIR / f"{name}.pdf"
        if p.exists():
            return p

    # Fuzzy match against Desktop/Papers
    if PAPERS_PDF_DIR.exists():
        clean = re.sub(r"[^a-z0-9]", "", display_name.lower())
        for fname in PAPERS_PDF_DIR.glob("*.pdf"):
            stem_clean = re.sub(r"[^a-z0-9]", "", fname.stem.lower())
            if clean in stem_clean or stem_clean in clean:
                return fname

    return None


def discover_all_papers() -> dict:
    """Return slug->display_name for all papers in the extracted dir."""
    papers = dict(BASE_PAPERS)
    for fname in EXTRACTED_DIR.glob("*.md"):
        slug = fname.stem
        if slug in papers:
            continue
        title = slug.replace("_", " ").title()
        try:
            for line in fname.read_text(encoding="utf-8", errors="replace").splitlines()[:10]:
                if line.startswith("title:"):
                    raw = line[6:].strip().strip('"').strip("'")
                    if raw:
                        title = raw
                    break
        except Exception:
            pass
        papers[slug] = title
    return papers


def process_paper(slug: str, display_name: str) -> bool:
    """Process one paper. Returns True if authors were extracted."""
    paper_path = EXTRACTED_DIR / f"{slug}.md"
    if not paper_path.exists():
        return False

    content = paper_path.read_text(encoding="utf-8", errors="replace")
    if "## Authors" in content:
        log(f"  Skipping {slug} (already has Authors section)")
        return False

    pdf_path = find_pdf(slug, display_name)
    if not pdf_path:
        log(f"  PDF not found for {slug}, skipping")
        return False

    log(f"  PDF: {pdf_path.name}")
    text = extract_pdf_text(pdf_path)
    if not text.strip():
        log(f"  No text extracted, skipping")
        return False

    info = call_groq(text)
    if not info:
        return False

    authors = info.get("authors", [])
    institutions = info.get("institutions", [])
    log(f"  Found {len(authors)} authors, {len(institutions)} institutions")

    for author in authors:
        path = write_person_page(author)
        gbrain_import(path)
        time.sleep(0.3)

    for inst in institutions:
        path = write_institution_page(inst)
        gbrain_import(path)
        time.sleep(0.3)

    update_paper_page(slug, info)
    gbrain_import(paper_path)
    return True


def main():
    log(f"\n[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] build-research-graph started")

    if not GROQ_API_KEY:
        log("ERROR: GROQ_API_KEY not set, aborting")
        sys.exit(1)

    # If a specific slug is passed, process only that one
    if len(sys.argv) > 1:
        slug = sys.argv[1]
        papers = discover_all_papers()
        display_name = papers.get(slug, slug.replace("_", " ").title())
        log(f"Single-paper mode: {slug} ({display_name})")
        ok = process_paper(slug, display_name)
        log("Done" if ok else "Nothing to do")
        return

    # Otherwise process all papers missing Authors section
    papers = discover_all_papers()
    processed = 0
    skipped   = 0

    for slug, display_name in papers.items():
        log(f"\nProcessing: {display_name} ({slug})")
        ok = process_paper(slug, display_name)
        if ok:
            processed += 1
            time.sleep(1)  # rate limit between papers
        else:
            skipped += 1

    log(f"\n[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] Done: {processed} processed, {skipped} skipped")

    # ── Auto-enrich new researcher bios with Claude ───────────────────────────
    if processed > 0:
        log("\nRunning bio-agent to enrich new researcher pages...")
        bio_script = Path(__file__).parent / "bio-agent.py"
        try:
            r = subprocess.run(
                [sys.executable, str(bio_script)],
                env={**os.environ, "PATH": os.path.join(os.path.expanduser("~"), ".bun", "bin") + ";" + os.environ.get("PATH", "")},
                timeout=600,
            )
            if r.returncode == 0:
                log("bio-agent finished OK")
            else:
                log(f"bio-agent exited with code {r.returncode}")
        except subprocess.TimeoutExpired:
            log("bio-agent timed out (600s) — will run next cycle")
        except Exception as e:
            log(f"bio-agent error: {e}")
    else:
        log("No new papers processed — skipping bio-agent")


if __name__ == "__main__":
    main()
