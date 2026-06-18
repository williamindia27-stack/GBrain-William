"""
eval-gaps.py — GBrain content completeness audit

For every paper in the DB, checks:
  - Required sections: Overview, Method, Key Results, Why It Matters, Limitations
  - Enrichment sections: Research Context, Authors, Keywords, Timeline
  - Word count (thin = < 400, adequate = 400–700, rich = > 700)
  - Raw-dump detection (no structured sections, just continuous text)
  - File exists in extracted/ (orphan detection)

Usage:
  python eval-gaps.py                  # full report
  python eval-gaps.py --save           # also write JSON to eval-results/
  python eval-gaps.py --missing only   # show only incomplete papers
  python eval-gaps.py --fix-brief      # list gbrain CLI commands to re-process thin papers
"""
import os, sys, re, json, subprocess, datetime, argparse
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GBRAIN_CMD   = os.path.join(os.path.expanduser("~"), ".bun", "bin", "gbrain.cmd")
EXTRACTED    = Path(r"C:\brain\extracted")
RESULTS_DIR  = Path(r"C:\brain\eval-results")

ENV = {
    **os.environ,
    "PATH": os.path.join(os.path.expanduser("~"), ".bun", "bin") + ";" + os.environ.get("PATH", ""),
    "NODE_TLS_REJECT_UNAUTHORIZED": "0",
    "GBRAIN_POOL_SIZE": "2",
}

def _reg(key):
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            return winreg.QueryValueEx(k, key)[0]
    except Exception:
        return ""

for _k in ("DATABASE_URL", "VOYAGE_API_KEY"):
    if not ENV.get(_k):
        _v = _reg(_k)
        if _v:
            ENV[_k] = _v

# ── Section definitions ───────────────────────────────────────────────────────
REQUIRED = [
    ("overview",     "## Overview"),
    ("method",       "## Method"),
    ("key_results",  "## Key Results"),
    ("why_matters",  "## Why It Matters"),
    ("limitations",  "## Limitations"),
]
ENRICHMENT = [
    ("research_ctx", "## Research Context"),
    ("authors",      "## Authors"),
    ("keywords",     "## Keywords"),
    ("timeline",     "## Timeline"),
]

ALL_SECTIONS   = REQUIRED + ENRICHMENT
MAX_SCORE      = len(REQUIRED) + len(ENRICHMENT)   # 9
REQUIRED_SCORE = len(REQUIRED)                      # 5

THIN_THRESHOLD    = 400   # words
ADEQUATE_THRESHOLD = 700  # words

# Raw-dump markers: text that appears when auto-import fell back to raw PDF text
RAW_DUMP_PATTERNS = re.compile(
    r"(References\n\[\d+\]|arXiv:\d{4}\.\d+|©\s*\d{4}|DOI:\s*10\.|"
    r"Abstract—|Keywords—|Received \d+ \w+ \d{4})",
    re.I,
)


# ── DB query ──────────────────────────────────────────────────────────────────
def list_papers() -> list[dict]:
    try:
        r = subprocess.run(
            ["cmd.exe", "/c", GBRAIN_CMD, "list", "--type", "paper", "-n", "500"],
            capture_output=True, env=ENV, timeout=30,
        )
        raw = r.stdout.decode("utf-8", errors="replace")
        papers = []
        for line in raw.splitlines():
            parts = line.split("\t")
            if len(parts) >= 4:
                papers.append({"slug": parts[0].strip(), "date": parts[2].strip(), "title": parts[3].strip()})
            elif len(parts) >= 1 and parts[0].strip():
                papers.append({"slug": parts[0].strip(), "date": "", "title": parts[0].strip()})
        return papers
    except Exception as e:
        print(f"ERROR listing papers: {e}", file=sys.stderr)
        return []


# ── Per-paper audit ───────────────────────────────────────────────────────────
def audit_paper(paper: dict) -> dict:
    slug    = paper["slug"]
    md_path = EXTRACTED / f"{slug}.md"

    result = {
        "slug":       slug,
        "title":      paper["title"],
        "date":       paper["date"],
        "file":       md_path.name,
        "exists":     md_path.exists(),
        "sections":   {},
        "word_count": 0,
        "raw_dump":   False,
        "score":      0,
        "max_score":  MAX_SCORE,
        "issues":     [],
    }

    if not md_path.exists():
        result["issues"].append("no extracted .md file")
        return result

    content    = md_path.read_text(encoding="utf-8", errors="replace")
    word_count = len(content.split())
    result["word_count"] = word_count

    # Section presence
    for key, marker in ALL_SECTIONS:
        present = marker in content
        result["sections"][key] = present
        if present:
            result["score"] += 1

    # Raw dump detection
    result["raw_dump"] = bool(RAW_DUMP_PATTERNS.search(content[:3000]))

    # Issues
    missing_required = [label for key, label in REQUIRED if not result["sections"].get(key)]
    missing_enrich   = [label for key, label in ENRICHMENT if not result["sections"].get(key)]

    if missing_required:
        result["issues"].append(f"missing required: {', '.join(missing_required)}")
    if missing_enrich:
        result["issues"].append(f"missing enrichment: {', '.join(missing_enrich)}")
    if word_count < THIN_THRESHOLD:
        result["issues"].append(f"thin content ({word_count} words)")
    if result["raw_dump"]:
        result["issues"].append("raw PDF dump detected")

    return result


# ── Rendering ─────────────────────────────────────────────────────────────────
def score_pct(r: dict) -> int:
    return round(r["score"] / r["max_score"] * 100)

def section_tick(present: bool) -> str:
    return "✓" if present else "·"

def word_label(n: int) -> str:
    if n < THIN_THRESHOLD:
        return f"⚠ {n}w"
    if n < ADEQUATE_THRESHOLD:
        return f"  {n}w"
    return f"✓ {n}w"

SECTION_COLS = [k for k, _ in ALL_SECTIONS]
SECTION_HDR  = ["Ovr","Met","Res","Why","Lim","RCtx","Auth","Kwd","TL"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--save",       action="store_true")
    parser.add_argument("--missing",    action="store_true", help="Only show incomplete papers")
    parser.add_argument("--fix-brief",  action="store_true", help="Print re-processing suggestions")
    args = parser.parse_args()

    now    = datetime.datetime.now()
    papers = list_papers()
    if not papers:
        print("No papers found — is DATABASE_URL set?")
        sys.exit(1)

    print(f"\nGBrain Content Gaps Audit  —  {now.strftime('%Y-%m-%d %H:%M')}  —  {len(papers)} papers\n")

    results = [audit_paper(p) for p in papers]
    results.sort(key=lambda r: (r["score"], r["word_count"]))

    # Header
    hdr_sections = "  ".join(f"{h:>4}" for h in SECTION_HDR)
    print(f"  {'Title':<38}  {hdr_sections}   Words    Score")
    print("─" * 110)

    perfect = incomplete = thin = raw = no_ctx = 0
    for r in results:
        pct = score_pct(r)
        if pct == 100:
            perfect += 1
        else:
            incomplete += 1
        if r["word_count"] < THIN_THRESHOLD and r["word_count"] > 0:
            thin += 1
        if r["raw_dump"]:
            raw += 1
        if not r["sections"].get("research_ctx"):
            no_ctx += 1

        if args.missing and pct == 100 and r["word_count"] >= THIN_THRESHOLD and not r["raw_dump"]:
            continue

        if not r["exists"]:
            mark = "❌ NO FILE"
        elif r["raw_dump"]:
            mark = "⚠ RAW DUMP"
        elif pct == 100 and r["word_count"] >= THIN_THRESHOLD:
            mark = "✅"
        elif pct == 100:
            mark = "⚠ THIN"
        else:
            mark = f"{'░' * (r['score'])}{'·' * (MAX_SCORE - r['score'])}"

        title   = (r["title"][:36] + "..") if len(r["title"]) > 38 else r["title"]
        ticks   = "  ".join(
            f"{section_tick(r['sections'].get(k, False)):>4}" for k in SECTION_COLS
        )
        wl      = word_label(r["word_count"]) if r["exists"] else "   —  "
        score_s = f"{r['score']}/{r['max_score']} ({pct:3d}%)"

        print(f"  {title:<38}  {ticks}   {wl:<8}  {score_s}  {mark}")

    print("─" * 110)

    # Summary
    n = len(results)
    print(f"\n  {perfect}/{n} fully complete  ·  {incomplete} with gaps  ·  {thin} thin (<{THIN_THRESHOLD}w)  ·  {no_ctx} missing Research Context\n")

    # Section coverage stats
    print("  Section coverage:")
    for key, label in ALL_SECTIONS:
        count = sum(1 for r in results if r["sections"].get(key))
        bar   = "█" * count + "░" * (n - count)
        tag   = "required  " if (key, label) in REQUIRED else "enrichment"
        print(f"    {label:<22}  {bar}  {count}/{n}  ({tag})")

    # Action list
    action_items = [r for r in results if r["issues"]]
    if action_items:
        print(f"\n  Papers needing attention ({len(action_items)}):")
        for r in action_items:
            print(f"    • {r['title'][:55]}")
            for issue in r["issues"]:
                print(f"        └ {issue}")

    # Fix suggestions
    if args.fix_brief:
        thin_papers = [r for r in results if r["word_count"] < THIN_THRESHOLD and r["exists"]]
        no_ctx_papers = [r for r in results if not r["sections"].get("research_ctx") and r["exists"]]
        if thin_papers:
            print(f"\n  Thin papers — consider re-extracting with vision fallback:")
            for r in thin_papers:
                print(f"    gbrain delete {r['slug']}  # then drop PDF in papers/ to re-import")
        if no_ctx_papers:
            print(f"\n  Papers missing Research Context — run research-notes.py:")
            print(f"    python C:\\brain\\research-notes.py")

    if args.save:
        RESULTS_DIR.mkdir(exist_ok=True)
        ts   = now.strftime("%Y%m%d_%H%M%S")
        path = RESULTS_DIR / f"gaps_{ts}.json"
        path.write_text(json.dumps({
            "timestamp":    ts,
            "n":            n,
            "perfect":      perfect,
            "incomplete":   incomplete,
            "thin":         thin,
            "no_ctx":       no_ctx,
            "papers":       results,
        }, indent=2, default=str), encoding="utf-8")
        print(f"\n  Saved to {path}")


if __name__ == "__main__":
    main()
