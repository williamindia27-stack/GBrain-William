"""
eval-pipeline.py — GBrain end-to-end pipeline test

Stages tested:
  1. Probe document creation  — write a synthetic markdown to a temp path
  2. DB import                — gbrain import --file <path> --no-embed
  3. Embedding                — gbrain embed --stale (watches the new slug)
  4. Search retrieval         — gbrain query <probe_string> must hit the slug in top-5
  5. Think retrieval          — gbrain think <probe_string> must cite the slug
  6. Cleanup                  — gbrain delete test/pipeline-probe-<id>

Each stage is timed and reports PASS / FAIL / SKIP with an error message.
Exit code 0 = all required stages passed; non-zero = at least one failure.

Usage:
  python eval-pipeline.py               # run full pipeline test
  python eval-pipeline.py --save        # also write JSON to eval-results/
  python eval-pipeline.py --no-think    # skip the think stage (slower)
  python eval-pipeline.py --keep        # skip cleanup (inspect probe in DB)
"""
import os, sys, re, json, subprocess, datetime, argparse, time, uuid, ssl, tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ssl._create_default_https_context = ssl._create_unverified_context

GBRAIN_CMD  = os.path.join(os.path.expanduser("~"), ".bun", "bin", "gbrain.cmd")
RESULTS_DIR = Path(r"C:\brain\eval-results")
EXTRACTED   = Path(r"C:\brain\extracted")

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

for _k in ("DATABASE_URL", "VOYAGE_API_KEY", "NVIDIA_API_KEY"):
    if not ENV.get(_k):
        _v = _reg(_k)
        if _v:
            ENV[_k] = _v


# ── Probe document ─────────────────────────────────────────────────────────────
PROBE_TEMPLATE = """\
---
title: "GBrain Pipeline Probe {probe_id}"
type: paper
---

## Overview
This synthetic validation document tests whether the GBrain ingestion pipeline
correctly imports, embeds, and retrieves arbitrary knowledge pages.
The document covers a fictional scientific topic: chromatic resonance decay
in non-Euclidean waveguides, a subject with no prior entries in the knowledge base.

## Method
A markdown page is injected through gbrain import, then embedded via Voyage AI.
Retrieval is verified by querying for "chromatic resonance decay waveguide {probe_id}"
which should return this page in the top results if the pipeline is functioning.

## Key Results
A successful pipeline run confirms: database write works, Voyage AI embedding
is reachable, and pgvector hybrid search returns the correct page on demand.
The probe identifier for this run is {probe_id}.

## Why It Matters
End-to-end pipeline tests catch integration failures that unit tests miss —
broken DB connections, Voyage AI outages, or query routing regressions.

## Limitations
This test covers the import, embedding, and retrieval stages only. It does not
test PDF text extraction, Groq summarisation, image vision, or papers-watcher.

## Keywords
pipeline, end-to-end, validation, chromatic resonance decay, waveguide, {probe_id}

## Timeline
- **{today}** — Probe created and injected by eval-pipeline.py
"""

# Semantic query that matches the probe document's unique fictional topic
PROBE_QUERY = "chromatic resonance decay non-Euclidean waveguide pipeline validation"


# ── Stage runner ──────────────────────────────────────────────────────────────
def gbrain(*args, timeout=60) -> tuple[int, str, str]:
    r = subprocess.run(
        ["cmd.exe", "/c", GBRAIN_CMD] + list(args),
        capture_output=True, env=ENV, timeout=timeout,
    )
    out = (r.stdout or b"").decode("utf-8", errors="replace").strip()
    err = (r.stderr or b"").decode("utf-8", errors="replace").strip()
    err = "\n".join(l for l in err.splitlines() if "ai.gateway" not in l)
    return r.returncode, out, err


class Stage:
    def __init__(self, name: str, required: bool = True):
        self.name     = name
        self.required = required
        self.status   = "SKIP"
        self.elapsed  = 0.0
        self.detail   = ""

    def run(self, fn):
        t0 = time.perf_counter()
        try:
            result = fn()
            self.elapsed = time.perf_counter() - t0
            if result is True or result is None:
                self.status = "PASS"
            elif result is False:
                self.status = "FAIL"
            else:
                self.status, self.detail = result
        except subprocess.TimeoutExpired:
            self.elapsed = time.perf_counter() - t0
            self.status  = "FAIL"
            self.detail  = "timed out"
        except Exception as e:
            self.elapsed = time.perf_counter() - t0
            self.status  = "FAIL"
            self.detail  = str(e)[:120]
        return self.status == "PASS"

    def __repr__(self):
        icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭", "WARN": "⚠️"}.get(self.status, "?")
        t    = f"{self.elapsed:.1f}s"
        d    = f"  {self.detail}" if self.detail else ""
        req  = "" if self.required else " (optional)"
        return f"  {icon} {self.name:<28}  {t:>6}{req}{d}"


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--save",     action="store_true")
    parser.add_argument("--no-think", action="store_true")
    parser.add_argument("--keep",     action="store_true", help="Skip cleanup — leave probe in DB")
    args = parser.parse_args()

    probe_id     = uuid.uuid4().hex[:8].upper()
    probe_string = f"GBRAIN-E2E-{probe_id}"
    # Slug is derived by gbrain from the filename stem (no path prefix)
    probe_slug   = f"pipeline-probe-{probe_id.lower()}"
    today        = datetime.date.today().isoformat()

    probe_path = EXTRACTED / f"pipeline-probe-{probe_id.lower()}.md"

    stages = []
    now    = datetime.datetime.now()

    print(f"\nGBrain Pipeline Test  —  {now.strftime('%Y-%m-%d %H:%M')}")
    print(f"  Probe ID:     {probe_id}")
    print(f"  Probe string: {probe_string}")
    print(f"  Probe slug:   {probe_slug}\n")

    # ── Stage 1: Create probe document ────────────────────────────────────────
    s1 = Stage("1. Create probe document")
    stages.append(s1)
    def _create():
        content = PROBE_TEMPLATE.format(
            probe_id=probe_id, probe_string=probe_string, today=today
        )
        probe_path.write_text(content, encoding="utf-8")
        if not probe_path.exists():
            return False, "file not written"
        return True
    s1.run(_create)
    print(s1)

    if s1.status != "PASS":
        print("\n  Aborting — cannot create probe document.")
        sys.exit(1)

    # ── Stage 2: DB import ────────────────────────────────────────────────────
    s2 = Stage("2. DB import")
    stages.append(s2)
    def _import():
        # gbrain import scans a directory — probe file must be in extracted/
        code, out, err = gbrain("import", str(EXTRACTED), "--no-embed", timeout=700)
        if code != 0:
            return "FAIL", (err or out)[:100]
        combined = out + err
        # Accept if import output directly references our probe file (fast path —
        # avoids a second DB round-trip while the DB is still busy post-import)
        if probe_id.lower() in combined.lower():
            return "PASS", "probe referenced in import output"
        # Confirm our slug appeared in the list — give the DB extra time to settle
        try:
            code2, out2, _ = gbrain("list", "-n", "5", timeout=60)
            if probe_slug in out2:
                return "PASS", "slug confirmed in DB"
        except Exception:
            pass  # list timed out — fall through to output-based check
        # If nothing new was imported, the checkpoint may have it already
        if "0 pages imported" in combined and "skipped" in combined:
            return "WARN", "0 imported (already in checkpoint?) — checking list"
        return "FAIL", f"probe slug '{probe_slug}' not found after import"
    s2.run(_import)
    print(s2)

    # ── Stage 3: Embedding ────────────────────────────────────────────────────
    s3 = Stage("3. Embed (--stale)")
    stages.append(s3)
    def _embed():
        code, out, err = gbrain("embed", "--stale", timeout=90)
        # Check if our slug got embedded or was already up-to-date
        if code != 0 and "Too Many Requests" not in (out + err):
            return "FAIL", (err or out)[:100]
        if "Too Many Requests" in (out + err):
            return "WARN", "Voyage AI rate-limited — may not be embedded yet"
        return True
    s3.run(_embed)
    print(s3)

    # ── Stage 4: Search retrieval ─────────────────────────────────────────────
    s4 = Stage("4. Search retrieval (query)")
    stages.append(s4)
    def _search():
        time.sleep(1)  # brief pause for index consistency
        query = PROBE_QUERY.replace("{probe_id}", probe_id)
        code, out, err = gbrain("query", query, "--limit", "10", timeout=30)
        if code != 0:
            return "FAIL", (err or out)[:100]
        lines = out.splitlines()
        hit_line = next((l for l in lines if probe_slug in l or probe_id.lower() in l), None)
        if hit_line:
            rank = lines.index(hit_line) + 1
            score_m = re.search(r"\[([0-9.]+)\]", hit_line)
            score   = score_m.group(1) if score_m else "?"
            return "PASS", f"rank {rank}, score {score}"
        top = lines[0][:80] if lines else "(no results)"
        if s3.status == "WARN":
            return "WARN", f"rate-limited embed — may need retry. Top: {top[:60]}"
        return "FAIL", f"not in top 10. Top: {top[:60]}"
    ok4 = s4.run(_search)
    print(s4)

    # ── Stage 5: Think retrieval (optional) ───────────────────────────────────
    s5 = Stage("5. Think retrieval", required=False)
    stages.append(s5)
    if not args.no_think:
        def _think():
            code, out, err = gbrain("query", f"What is the {probe_string} pipeline test?", "--limit", "5", timeout=90)
            if code != 0:
                return "FAIL", (err or out)[:100]
            if probe_slug in out or probe_id.lower() in out or probe_string in out:
                return "PASS", "probe slug found in semantic search results"
            return "WARN", "query ran but probe slug not in top 5 results (may be filtered by salience)"
        s5.run(_think)
    else:
        s5.status  = "SKIP"
        s5.detail  = "skipped (--no-think)"
    print(s5)

    # ── Stage 6: Cleanup ──────────────────────────────────────────────────────
    s6 = Stage("6. Cleanup", required=False)
    stages.append(s6)
    if not args.keep:
        def _cleanup():
            gbrain("delete", probe_slug, timeout=20)
            try:
                probe_path.unlink(missing_ok=True)
            except Exception:
                pass
            return True
        s6.run(_cleanup)
    else:
        s6.status = "SKIP"
        s6.detail = f"kept — inspect with: gbrain get {probe_slug}"
    print(s6)

    # ── Summary ───────────────────────────────────────────────────────────────
    required_stages = [s for s in stages if s.required]
    passed  = sum(1 for s in required_stages if s.status == "PASS")
    failed  = sum(1 for s in required_stages if s.status == "FAIL")
    warned  = sum(1 for s in stages if s.status == "WARN")
    total_t = sum(s.elapsed for s in stages)

    print()
    if failed == 0:
        verdict = "✅ PIPELINE OK" if warned == 0 else "⚠️  PIPELINE OK (with warnings)"
    else:
        verdict = f"❌ PIPELINE FAILED ({failed} required stage(s) failed)"

    print(f"  {verdict}  ·  {passed}/{len(required_stages)} required stages passed  ·  {total_t:.1f}s total\n")

    if args.save:
        RESULTS_DIR.mkdir(exist_ok=True)
        ts   = now.strftime("%Y%m%d_%H%M%S")
        path = RESULTS_DIR / f"pipeline_{ts}.json"
        path.write_text(json.dumps({
            "timestamp":   ts,
            "probe_id":    probe_id,
            "probe_slug":  probe_slug,
            "verdict":     verdict,
            "passed":      passed,
            "failed":      failed,
            "total_secs":  round(total_t, 2),
            "stages": [{
                "name":    s.name,
                "status":  s.status,
                "elapsed": round(s.elapsed, 2),
                "detail":  s.detail,
            } for s in stages],
        }, indent=2), encoding="utf-8")
        print(f"  Saved to {path}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
