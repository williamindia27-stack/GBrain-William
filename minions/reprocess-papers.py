"""
reprocess-papers.py — One-time cleanup of existing extracted/ .md files.

Old format:  frontmatter + 3-sentence summary + full raw PDF text dump
New format:  frontmatter + structured 6-section Groq summary only

Detects old-format files automatically (they have a bare --- separator inside
the body, separating the old summary from the raw text). Already-clean files
are skipped.

After rewriting the .md files, submits a native gbrain import job so Neon
picks up the new content.

Run once:
    python reprocess-papers.py

Requires GROQ_API_KEY in environment (reads from HKCU registry if not set).
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

EXTRACT_DIR = r"C:\brain\extracted"
LOG_FILE    = r"C:\brain\minions\reprocess-papers.log"
BUN_EXE     = os.path.join(os.path.expanduser("~"), ".bun", "bin", "bun.exe")
CLI_TS      = r"C:\gbrain\src\cli.ts"

# ── Helpers ───────────────────────────────────────────────────────────────────

def log(msg):
    ts = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    line = f"[{ts}] {msg}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)

def load_groq_key():
    key = os.environ.get("GROQ_API_KEY", "")
    if key:
        return key
    # Try reading from Windows registry (same as other minion scripts)
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

# ── Parse existing .md files ──────────────────────────────────────────────────

def parse_md(path):
    """
    Returns (title, raw_text) if the file is old-format (contains raw PDF text).
    Returns (title, None) if already clean or unrecognised format.

    Old format structure:
        ---
        title: "..."
        type: paper
        ---

        ## Summary

        <old 3-line summary>

        ---

        <full raw PDF text>
    """
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Extract title from YAML frontmatter
    title = None
    fm_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if fm_match:
        for line in fm_match.group(1).splitlines():
            if line.startswith("title:"):
                title = line[6:].strip().strip('"').strip("'")
                break

    # Body = everything after the closing ---
    body = content[fm_match.end():] if fm_match else content

    # Old format has a bare "---" line separating the summary block from the raw text
    sep_match = re.search(r'\n---\n\n', body)
    if sep_match:
        raw_text = body[sep_match.end():].strip()
        if len(raw_text) > 200:          # sanity check — real raw text is long
            return title, raw_text

    return title, None                   # already clean, skip

# ── Groq call (same prompt as updated auto-import.py) ────────────────────────

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

# ── Write clean .md ───────────────────────────────────────────────────────────

def write_clean_md(path, title, summary):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f'---\ntitle: "{title}"\ntype: paper\n---\n\n')
        f.write(summary or "(summary unavailable)")

# ── Submit gbrain import job ──────────────────────────────────────────────────

def submit_import_job():
    params = json.dumps({"dir": EXTRACT_DIR, "noEmbed": True})
    r = subprocess.run(
        [BUN_EXE, CLI_TS, "jobs", "submit", "import",
         "--params", params, "--max-waiting", "1"],
        capture_output=True,
        timeout=30,
        env=gbrain_env(),
    )
    if r.returncode == 0:
        log("  Import job queued — Neon will pick up rewritten content shortly")
    else:
        err = r.stderr.decode("utf-8", errors="replace").strip()
        log(f"  WARNING: import job failed (exit {r.returncode}): {err[:200]}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    groq_key = load_groq_key()
    if not groq_key:
        log("ERROR: GROQ_API_KEY not found in environment or registry.")
        sys.exit(1)

    files = sorted(f for f in os.listdir(EXTRACT_DIR) if f.endswith(".md"))
    log(f"Scanning {len(files)} .md files in extracted/")
    log("-" * 60)

    to_process = []
    for fname in files:
        path = os.path.join(EXTRACT_DIR, fname)
        title, raw_text = parse_md(path)
        if raw_text:
            to_process.append((fname, path, title, raw_text))
        else:
            log(f"  SKIP  {fname} — already clean")

    log("-" * 60)
    log(f"{len(to_process)} file(s) need reprocessing, {len(files) - len(to_process)} already clean")

    if not to_process:
        log("Nothing to do.")
        return

    ok = 0
    failed = 0

    for i, (fname, path, title, raw_text) in enumerate(to_process, 1):
        name = title or Path(fname).stem.replace("_", " ").title()
        log(f"  [{i}/{len(to_process)}] {fname}  ({len(raw_text):,} chars)")
        try:
            summary = generate_summary(name, raw_text, groq_key)
            write_clean_md(path, name, summary)
            log(f"    OK — rewritten ({len(summary)} chars)")
            ok += 1
        except Exception as e:
            log(f"    ERROR: {e}")
            failed += 1

    log("-" * 60)
    log(f"Done. {ok} rewritten, {failed} failed.")

    if ok > 0:
        log("Queuing gbrain import job to sync rewritten content to Neon...")
        submit_import_job()

if __name__ == "__main__":
    main()
