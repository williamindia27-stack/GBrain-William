"""
graph-extract.py
Walks every page in the gbrain database, resolves [[wikilinks]], and writes
typed edges into the links table (graph wiring — step 5 of the ingestion pipeline).

Run after any batch import so newly-added pages get their edges materialised.
Idempotent: ON CONFLICT DO NOTHING means re-runs are always safe.
"""
import os
import sys
import re
import subprocess
import datetime
from pathlib import Path

GBRAIN_CMD    = os.path.join(os.path.expanduser("~"), ".bun", "bin", "gbrain.cmd")
EXTRACTED_DIR = Path(r"C:\brain\extracted")
LOG           = Path(r"C:\brain\minions\graph-extract.log")

ENV = {
    **os.environ,
    "PATH":          os.path.join(os.path.expanduser("~"), ".bun", "bin") + ";" + os.environ.get("PATH", ""),
    "GBRAIN_POOL_SIZE": "2",
}


# ── helpers ───────────────────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_gbrain(*args, timeout: int = 300) -> tuple[str, str, int]:
    """Run a gbrain sub-command. Returns (stdout, stderr, returncode)."""
    cmd = ["cmd.exe", "/c", GBRAIN_CMD] + list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, env=ENV, timeout=timeout)
        stdout = (r.stdout or b"").decode("utf-8", errors="replace").strip()
        stderr = (r.stderr or b"").decode("utf-8", errors="replace").strip()
        return stdout, stderr, r.returncode
    except subprocess.TimeoutExpired:
        return "", f"gbrain timed out after {timeout}s", 1


def parse_extract_counts(stdout: str) -> dict[str, int]:
    """
    Parse link/timeline counts out of `gbrain extract all` output.
    Typical lines look like:
        Links extracted:    103 created, 0 skipped
        Timeline entries:   161 created, 0 skipped
    """
    counts = {"links_created": 0, "links_skipped": 0,
               "timeline_created": 0, "timeline_skipped": 0}
    for line in stdout.splitlines():
        m = re.search(r"[Ll]inks.*?(\d+)\s+created.*?(\d+)\s+skipped", line)
        if m:
            counts["links_created"]  = int(m.group(1))
            counts["links_skipped"]  = int(m.group(2))
        m2 = re.search(r"[Tt]imeline.*?(\d+)\s+created.*?(\d+)\s+skipped", line)
        if m2:
            counts["timeline_created"] = int(m2.group(1))
            counts["timeline_skipped"] = int(m2.group(2))
    return counts


def count_markdown_pages() -> int:
    """Count .md files in extracted/ (excluding sub-dirs) as a quick sanity check."""
    try:
        return sum(1 for f in EXTRACTED_DIR.glob("*.md"))
    except Exception:
        return -1


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    log("=" * 60)
    log("graph-extract started")

    pages_on_disk = count_markdown_pages()
    log(f"  Pages in extracted/: {pages_on_disk}")

    # ── Step A: extract links (wikilinks → edges) ──────────────────────────
    log("  Running: gbrain extract links --source db")
    stdout_links, stderr_links, rc_links = run_gbrain(
        "extract", "links", "--source", "db", timeout=300
    )
    if rc_links == 0:
        counts = parse_extract_counts(stdout_links)
        log(f"  Links  → {counts['links_created']} created, {counts['links_skipped']} skipped")
    else:
        log(f"  gbrain extract links FAILED (exit {rc_links})")
        if stderr_links:
            log(f"  stderr: {stderr_links[:300]}")

    # ── Step B: extract timeline entries ───────────────────────────────────
    log("  Running: gbrain extract timeline --source db")
    stdout_tl, stderr_tl, rc_tl = run_gbrain(
        "extract", "timeline", "--source", "db", timeout=300
    )
    if rc_tl == 0:
        counts_tl = parse_extract_counts(stdout_tl)
        log(f"  Timeline → {counts_tl['timeline_created']} created, {counts_tl['timeline_skipped']} skipped")
    else:
        log(f"  gbrain extract timeline FAILED (exit {rc_tl})")
        if stderr_tl:
            log(f"  stderr: {stderr_tl[:300]}")

    # ── Step C: quick graph stats ───────────────────────────────────────────
    log("  Running: gbrain doctor --json (graph coverage check)")
    stdout_doc, _, rc_doc = run_gbrain("doctor", "--json", "--fast", timeout=60)
    if rc_doc == 0 and stdout_doc:
        import json
        try:
            doc = json.loads(stdout_doc)
            checks = {c["name"]: c for c in doc.get("checks", [])}
            gc = checks.get("graph_coverage", {})
            if gc:
                log(f"  Graph coverage: {gc.get('status','?')} — {gc.get('message','')}")
        except Exception:
            pass

    # ── Summary ────────────────────────────────────────────────────────────
    ok = (rc_links == 0) and (rc_tl == 0)
    log(f"graph-extract {'finished OK' if ok else 'finished WITH ERRORS'}")
    log("=" * 60)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
