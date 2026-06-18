"""
import-all-papers.py — Process all 15 papers into clean structured .md files.

For the 10 base papers (PDFs in .vscode/AI/data/):
  - Extract text with pypdf
  - Generate structured Groq summary
  - Write clean .md to extracted/

For the 5 auto-imported papers already in extracted/:
  - Already reprocessed by reprocess-papers.py — skip if clean
  - Re-run Groq if still old format

Then submit one native gbrain import job to sync everything to Neon.

Run once:
    python import-all-papers.py
"""

import os
import re
import sys
import json
import subprocess
import urllib.request
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
from pathlib import Path
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────

DATA_DIR    = r"C:\brain\papers"
EXTRACT_DIR = r"C:\brain\extracted"
LOG_FILE    = r"C:\brain\minions\import-all-papers.log"
BUN_EXE     = os.path.join(os.path.expanduser("~"), ".bun", "bin", "bun.exe")
CLI_TS      = r"C:\gbrain\src\cli.ts"

# Map slug → PDF filename in DATA_DIR (the 10 base papers)
BASE_PAPERS = {
    "agentic_world_modeling":            "Agentic World Modeling.pdf",
    "openhands":                         "OpenHands.pdf",
    "agentscope":                        "AgentScope.pdf",
    "multi_agent_trading":               "Multi agent trading.pdf",
    "ai_trader_agent":                   "AI trader agent.pdf",
    "kronos_a_foundation_model":         "Kronos A Foundation Model.pdf",
    "image_regonition_phone_avatar":     "Image regonition phone avatar.pdf",
    "human_ai_oversight_video_language": "Human ai oversight video language.pdf",
    "agentic":                           "Agentic.pdf",
    "python_cosmological":               "Python cosmological.pdf",
}

BASE_TITLES = {
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

# ── Helpers ───────────────────────────────────────────────────────────────────

def log(msg):
    ts = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    line = f"[{ts}] {msg}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line.encode("cp1252", errors="replace").decode("cp1252"))

def load_groq_key():
    key = os.environ.get("GROQ_API_KEY", "")
    if key:
        return key
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as k:
            key, _ = winreg.QueryValueEx(k, "GROQ_API_KEY")
            return key
    except Exception:
        pass
    return ""

def gbrain_env():
    return {**os.environ, "PATH": os.path.join(os.path.expanduser("~"), ".bun", "bin") + ";" + os.environ.get("PATH", "")}

# ── PDF extraction ────────────────────────────────────────────────────────────

def extract_pdf(pdf_path):
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        pages_text = [p.extract_text() for p in reader.pages if p.extract_text()]
        text = "\n\n".join(pages_text).strip().replace('\x00', '')
        return text
    except Exception as e:
        log(f"    ERROR extracting PDF: {e}")
        return None

# ── Old-format .md detection ──────────────────────────────────────────────────

def is_old_format(path):
    """Returns (is_old, raw_text). Old format has bare --- separator + large raw dump."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        fm_match = re.match(r'^---\n.*?\n---\n', content, re.DOTALL)
        body = content[fm_match.end():] if fm_match else content
        sep_match = re.search(r'\n---\n\n', body)
        if sep_match:
            raw = body[sep_match.end():].strip()
            if len(raw) > 200:
                return True, raw
    except Exception:
        pass
    return False, None

# ── Groq summary ─────────────────────────────────────────────────────────────

def generate_summary(name, text, groq_key):
    snippet = text[:10000]
    payload = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": (
                "You are a research assistant. Read the paper and write a structured summary using exactly these sections. "
                "Be specific and include numbers/metrics where the paper mentions them. No filler, no padding.\n\n"
                "## Overview\n"
                "2-3 sentences: what problem this solves and why it matters.\n\n"
                "## Method\n"
                "2-3 sentences: the core approach or technique proposed.\n\n"
                "## Key Results\n"
                "Bullet list of 3-5 concrete findings (include benchmark names and numbers if present).\n\n"
                "## Why It Matters\n"
                "1-2 sentences: practical or scientific significance.\n\n"
                "## Limitations\n"
                "1-2 sentences: what the authors acknowledge as limitations or open questions.\n\n"
                "## Keywords\n"
                "Comma-separated list of 5-8 technical keywords."
            )},
            {"role": "user", "content": f"Paper: {name}\n\n{snippet}"},
        ],
        "temperature": 0.2,
        "max_tokens": 700,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {groq_key}",
            "User-Agent": "python-urllib/3.14",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()

# ── Write .md ─────────────────────────────────────────────────────────────────

def write_clean_md(slug, title, summary):
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    path = os.path.join(EXTRACT_DIR, f"{slug}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f'---\ntitle: "{title}"\ntype: paper\n---\n\n')
        f.write(summary or "(summary unavailable)")
    return path

# ── gbrain import job ─────────────────────────────────────────────────────────

def submit_import_job():
    params = json.dumps({"dir": EXTRACT_DIR, "noEmbed": True})
    r = subprocess.run(
        [BUN_EXE, CLI_TS, "jobs", "submit", "import",
         "--params", params, "--max-waiting", "1"],
        capture_output=True, timeout=30, env=gbrain_env(),
    )
    if r.returncode == 0:
        log("  Import job queued — worker will sync all 15 papers to Neon")
    else:
        err = r.stderr.decode("utf-8", errors="replace").strip()
        log(f"  WARNING: import job failed (exit {r.returncode}): {err[:200]}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    groq_key = load_groq_key()
    if not groq_key:
        log("ERROR: GROQ_API_KEY not found.")
        sys.exit(1)

    ok = 0
    failed = 0
    skipped = 0

    # ── Part 1: 10 base papers from DATA_DIR ──────────────────────────────────
    log("=" * 60)
    log("Part 1: Base papers (extracting from PDFs)")
    log("=" * 60)

    for i, (slug, pdf_name) in enumerate(BASE_PAPERS.items(), 1):
        title = BASE_TITLES[slug]
        pdf_path = os.path.join(DATA_DIR, pdf_name)
        md_path  = os.path.join(EXTRACT_DIR, f"{slug}.md")

        log(f"  [{i}/10] {title}")

        if not os.path.exists(pdf_path):
            log(f"    SKIP — PDF not found: {pdf_path}")
            skipped += 1
            continue

        # Extract text from PDF
        text = extract_pdf(pdf_path)
        if not text:
            failed += 1
            continue
        log(f"    Extracted {len(text):,} chars from PDF")

        # Generate Groq summary
        try:
            summary = generate_summary(title, text, groq_key)
            log(f"    Groq OK ({len(summary)} chars)")
        except Exception as e:
            log(f"    Groq ERROR: {e}")
            failed += 1
            continue

        # Write clean .md
        write_clean_md(slug, title, summary)
        log(f"    Written -> extracted/{slug}.md")
        ok += 1

    # ── Part 2: 5 auto-imported papers already in extracted/ ──────────────────
    log("=" * 60)
    log("Part 2: Auto-imported papers (checking extracted/)")
    log("=" * 60)

    auto_files = [
        f for f in os.listdir(EXTRACT_DIR)
        if f.endswith(".md") and f[:-3] not in BASE_PAPERS
    ]

    for i, fname in enumerate(sorted(auto_files), 1):
        slug = fname[:-3]
        path = os.path.join(EXTRACT_DIR, fname)
        old, raw_text = is_old_format(path)

        if not old:
            log(f"  [{i}/{len(auto_files)}] {fname} — already clean, skipping")
            skipped += 1
            continue

        # Still old format — re-run Groq
        title = slug.replace("_", " ").title()
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if line.startswith("title:"):
                        title = line[6:].strip().strip('"').strip("'")
                        break
        except Exception:
            pass

        log(f"  [{i}/{len(auto_files)}] {fname} — old format, reprocessing ({len(raw_text):,} chars)")
        try:
            summary = generate_summary(title, raw_text, groq_key)
            write_clean_md(slug, title, summary)
            log(f"    OK — rewritten ({len(summary)} chars)")
            ok += 1
        except Exception as e:
            log(f"    ERROR: {e}")
            failed += 1

    # ── Submit import job ─────────────────────────────────────────────────────
    log("=" * 60)
    log(f"Results: {ok} processed, {skipped} skipped (already clean), {failed} failed")
    log("=" * 60)

    if ok > 0:
        log("Queuing gbrain import job...")
        submit_import_job()
    else:
        log("Nothing new to import.")

if __name__ == "__main__":
    main()
