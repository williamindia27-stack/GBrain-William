"""
fix-raw-dumps.py — Fix .md files that contain raw PDF text instead of a structured Groq summary.

Detection: files that do NOT contain "## Overview" (the first section of the new format).
These were auto-imported with raw pypdf text and slipped through reprocess-papers.py
because they had no "---" separator to trigger the old-format detection.

Action:
  1. Read the raw text from the .md body (after frontmatter)
  2. Run Groq structured summary (6-section prompt)
  3. Rewrite the .md as:
       frontmatter
       <Groq summary>
       <!-- timeline -->
       ## Timeline
       - <today> — Reprocessed by fix-raw-dumps.py
  4. Submit gbrain import job to sync to Neon.

Run:
    python fix-raw-dumps.py
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
LOG_FILE    = r"C:\brain\minions\fix-raw-dumps.log"
BUN_EXE     = os.path.join(os.path.expanduser("~"), ".bun", "bin", "bun.exe")
CLI_TS      = r"C:\gbrain\src\cli.ts"

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

# ── Detection ─────────────────────────────────────────────────────────────────

def needs_reprocess(path):
    """
    Returns (needs_fix, title, raw_body).
    A file needs fixing if its body does NOT start with a structured Groq summary.
    We check for '## Overview' as the canonical marker of the new format.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # Extract title from frontmatter
        title = None
        fm_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        if fm_match:
            for line in fm_match.group(1).splitlines():
                if line.startswith("title:"):
                    title = line[6:].strip().strip('"').strip("'")
                    break
            body = content[fm_match.end():]
        else:
            body = content

        # Strip timeline section (below <!-- timeline -->)
        tl_match = re.search(r'\n*<!-- timeline -->', body)
        if tl_match:
            body_above = body[:tl_match.start()].strip()
        else:
            body_above = body.strip()

        # If body above timeline already has structured sections, it's clean
        if "## Overview" in body_above or "## Method" in body_above:
            return False, title, None

        # It's raw text — return the body for Groq processing
        if len(body_above) < 100:
            return False, title, None  # too short to be raw text, probably empty

        return True, title, body_above

    except Exception as e:
        log(f"  ERROR reading {path}: {e}")
        return False, None, None

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

# ── Write clean .md ───────────────────────────────────────────────────────────

def write_clean_md(path, title, summary):
    today = datetime.now().strftime("%Y-%m-%d")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f'---\ntitle: "{title}"\ntype: paper\n---\n\n')
        f.write(summary or "(summary unavailable)")
        f.write(f"\n\n<!-- timeline -->\n\n## Timeline\n\n- **{today}** — Reprocessed by fix-raw-dumps.py\n")

# ── gbrain import ─────────────────────────────────────────────────────────────

def run_gbrain_import():
    """Run gbrain import directly (not via job queue) so it executes immediately."""
    log("Running gbrain import on extracted/ ...")
    r = subprocess.run(
        [BUN_EXE, CLI_TS, "import", EXTRACT_DIR, "--no-embed"],
        capture_output=True,
        timeout=120,
        env=gbrain_env(),
    )
    out = r.stdout.decode("utf-8", errors="replace").strip()
    err = r.stderr.decode("utf-8", errors="replace").strip()
    if r.returncode == 0:
        lines = [l for l in (out + "\n" + err).splitlines() if l.strip()]
        for l in lines[-5:]:
            log(f"  {l}")
        log("  Import complete.")
    else:
        log(f"  WARNING: import exited {r.returncode}")
        for l in err.splitlines()[-5:]:
            log(f"  {l}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    groq_key = load_groq_key()
    if not groq_key:
        log("ERROR: GROQ_API_KEY not found.")
        sys.exit(1)

    files = sorted(f for f in os.listdir(EXTRACT_DIR) if f.endswith(".md"))
    log(f"Scanning {len(files)} .md files for raw-dump content ...")

    to_fix = []
    for fname in files:
        path = os.path.join(EXTRACT_DIR, fname)
        needs, title, raw_body = needs_reprocess(path)
        if needs:
            to_fix.append((fname, path, title, raw_body))
            log(f"  NEEDS FIX: {fname} ({len(raw_body):,} chars of raw text)")
        else:
            log(f"  OK: {fname}")

    if not to_fix:
        log("All files are already in structured format. Nothing to do.")
        return

    log(f"\n{len(to_fix)} file(s) to fix ...")
    ok = 0
    failed = 0

    for i, (fname, path, title, raw_body) in enumerate(to_fix, 1):
        name = title or Path(fname).stem.replace("_", " ").title()
        log(f"\n[{i}/{len(to_fix)}] {fname}")
        log(f"  Title: {name}")
        log(f"  Raw body: {len(raw_body):,} chars")

        # Rate-limit guard: wait between Groq calls
        if i > 1:
            import time
            log("  Waiting 10s (Groq rate limit) ...")
            time.sleep(10)

        try:
            summary = generate_summary(name, raw_body, groq_key)
            log(f"  Groq OK ({len(summary)} chars)")
        except Exception as e:
            log(f"  Groq ERROR: {e}")
            failed += 1
            continue

        try:
            write_clean_md(path, name, summary)
            log(f"  Written: {fname}")
            ok += 1
        except Exception as e:
            log(f"  Write ERROR: {e}")
            failed += 1

    log(f"\nDone. {ok} fixed, {failed} failed.")

    if ok > 0:
        run_gbrain_import()

if __name__ == "__main__":
    main()
