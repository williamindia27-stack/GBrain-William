"""
orphan-linker.py
Fixes the root cause of orphan people/ and companies/ pages:

build-research-graph.py writes [[slug|Name]] wikilinks but pages are stored
as people/slug — so gbrain extract links never resolves them and the person
page has zero inbound edges (appears as orphan).

This script:
1. Builds a lookup of every people/ and companies/ slug on disk
2. Scans all paper .md files for bare [[slug|...]] wikilinks
3. Rewrites them to [[people/slug|...]] or [[companies/slug|...]]
4. Saves + imports updated papers
5. Runs gbrain extract links --source db to rebuild edges

Idempotent: already-prefixed links are not touched.
"""

import os, sys, re, subprocess, json, time, datetime
from pathlib import Path

EXTRACTED_DIR = Path(r"C:\brain\extracted")
GBRAIN_CMD    = os.path.join(os.path.expanduser("~"), ".bun", "bin", "gbrain.cmd")
LOG           = Path(r"C:\brain\minions\orphan-linker.log")

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


def run_gbrain(*args, timeout=300):
    cmd = ["cmd.exe", "/c", GBRAIN_CMD] + list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, env=ENV, timeout=timeout)
        stdout = (r.stdout or b"").decode("utf-8", errors="replace").strip()
        stderr = (r.stderr or b"").decode("utf-8", errors="replace").strip()
        return stdout, stderr, r.returncode
    except subprocess.TimeoutExpired:
        return "", f"gbrain timed out after {timeout}s", 1


# ── build slug lookup ─────────────────────────────────────────────────────────

def build_slug_lookup() -> dict[str, str]:
    """
    Returns {bare_slug: full_slug} for every page in people/ and companies/.
    e.g. {"xingyao-wang": "people/xingyao-wang", "cmu": "companies/cmu"}
    Bare slugs that collide across domains: people/ wins.
    """
    lookup = {}

    companies_dir = EXTRACTED_DIR / "companies"
    if companies_dir.exists():
        for p in companies_dir.glob("*.md"):
            bare = p.stem
            lookup[bare] = f"companies/{bare}"

    people_dir = EXTRACTED_DIR / "people"
    if people_dir.exists():
        for p in people_dir.glob("*.md"):
            bare = p.stem
            lookup[bare] = f"people/{bare}"   # people/ wins on collision

    return lookup


# ── fix a single paper file ───────────────────────────────────────────────────

# Match [[slug]] or [[slug|Label]] where slug does NOT already contain /
_WIKILINK_RE = re.compile(r'\[\[([^/\[\]|]+)(\|[^\[\]]+)?\]\]')


def fix_paper(paper_path: Path, lookup: dict[str, str]) -> int:
    """
    Rewrite bare wikilinks in paper_path using lookup.
    Returns number of distinct slugs fixed.
    """
    try:
        content = paper_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        log(f"    Read error {paper_path.name}: {e}")
        return 0

    original = content
    fixed_slugs: set[str] = set()

    def replace(m: re.Match) -> str:
        bare  = m.group(1)
        label = m.group(2) or ""   # e.g. "|Xingyao Wang"
        full  = lookup.get(bare)
        if full:
            fixed_slugs.add(bare)
            return f"[[{full}{label}]]"
        return m.group(0)           # not in lookup — leave unchanged

    content = _WIKILINK_RE.sub(replace, content)

    if content == original:
        return 0

    try:
        paper_path.write_text(content, encoding="utf-8")
    except Exception as e:
        log(f"    Write error {paper_path.name}: {e}")
        return 0

    _, err, rc = run_gbrain("import", "--file", str(paper_path), "--no-embed", timeout=60)
    if rc != 0:
        log(f"    Import failed {paper_path.name}: {err[:150]}")
    else:
        log(f"    Fixed {paper_path.name}: {sorted(fixed_slugs)[:8]}")

    return len(fixed_slugs)


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    log("=" * 60)
    log("orphan-linker started")

    # ── Build lookup ──────────────────────────────────────────────────────────
    lookup = build_slug_lookup()
    log(f"  Slug lookup: {len([v for v in lookup.values() if v.startswith('people/')])} people, "
        f"{len([v for v in lookup.values() if v.startswith('companies/')])} companies")

    if not lookup:
        log("  No people/ or companies/ pages found — nothing to do")
        sys.exit(0)

    # ── Scan paper pages ──────────────────────────────────────────────────────
    paper_files = sorted(EXTRACTED_DIR.glob("*.md"))
    log(f"  Scanning {len(paper_files)} paper pages...")

    papers_fixed   = 0
    links_fixed    = 0

    for paper_path in paper_files:
        n = fix_paper(paper_path, lookup)
        if n > 0:
            papers_fixed += 1
            links_fixed  += n
            time.sleep(0.2)   # gentle rate limiting

    log(f"\n  Fixed {links_fixed} wikilinks across {papers_fixed} paper(s)")

    # ── Rebuild graph edges ───────────────────────────────────────────────────
    if papers_fixed > 0:
        log("  Running gbrain extract links --source db ...")
        stdout, stderr, rc = run_gbrain("extract", "links", "--source", "db", timeout=300)
        if rc == 0:
            log(f"  Extract OK: {stdout[:200]}")
        else:
            log(f"  Extract FAILED: {stderr[:200]}")
            sys.exit(1)
    else:
        log("  No papers changed — skipping extract links")

    log("orphan-linker finished OK")
    log("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    main()
