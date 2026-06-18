"""
eval-search.py — GBrain search quality evaluation

For each query in eval-queries.json, runs gbrain query and checks
whether the expected slugs appear in the top-K results.

Metrics:
  Hit@1  — at least one expected slug in position 1
  Hit@3  — at least one expected slug in top 3
  Hit@5  — at least one expected slug in top 5
  MRR    — mean reciprocal rank of the first expected slug found

Usage:
  python eval-search.py            # run all queries
  python eval-search.py --save     # also write JSON results to eval-results/
  python eval-search.py --limit 5  # override top-K (default 10)
"""
import os, sys, json, subprocess, re, datetime, argparse
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GBRAIN_CMD  = os.path.join(os.path.expanduser("~"), ".bun", "bin", "gbrain.cmd")
QUERIES_FILE = Path(__file__).parent / "eval-queries.json"
RESULTS_DIR  = Path(__file__).parent / "eval-results"

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


for _k in ("DATABASE_URL", "VOYAGE_API_KEY", "GROQ_API_KEY"):
    if not ENV.get(_k):
        _v = _reg(_k)
        if _v:
            ENV[_k] = _v


def run_query(query: str, limit: int) -> list[dict]:
    """Run gbrain query and return list of {rank, score, slug, excerpt}."""
    try:
        r = subprocess.run(
            ["cmd.exe", "/c", GBRAIN_CMD, "query", query, "--limit", str(limit)],
            capture_output=True, env=ENV, timeout=120,
        )
        raw = r.stdout.decode("utf-8", errors="replace")
        results = []
        for line in raw.splitlines():
            m = re.match(r"\[([0-9.]+)\]\s+(\S+)\s+--\s+(.*)", line)
            if m:
                results.append({
                    "rank":    len(results) + 1,
                    "score":   float(m.group(1)),
                    "slug":    m.group(2),
                    "excerpt": m.group(3).strip()[:120],
                })
        return results
    except Exception as e:
        print(f"  ERROR running query: {e}", file=sys.stderr)
        return []


def reciprocal_rank(results: list[dict], expected: list[str]) -> float:
    for r in results:
        if r["slug"] in expected:
            return 1.0 / r["rank"]
    return 0.0


def hit_at_k(results: list[dict], expected: list[str], k: int) -> bool:
    top = {r["slug"] for r in results[:k]}
    return bool(top & set(expected))


def col(text, width, right=False):
    s = str(text)
    return s.rjust(width) if right else s.ljust(width)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--save",  action="store_true", help="Save results to eval-results/")
    parser.add_argument("--limit", type=int, default=10, help="Top-K to retrieve (default 10)")
    parser.add_argument("--filter", type=str, default="", help="Only run queries containing this string")
    args = parser.parse_args()

    queries = json.loads(QUERIES_FILE.read_text(encoding="utf-8"))
    if args.filter:
        queries = [q for q in queries if args.filter.lower() in q["query"].lower()]
    if not queries:
        print("No queries matched.")
        sys.exit(0)

    K = args.limit
    print(f"\nGBrain Search Evaluation  —  top-{K}  —  {len(queries)} queries\n")
    print(f"{'#':>3}  {'Query':<48}  {'Hit@1':>5}  {'Hit@3':>5}  {'Hit@5':>5}  {'MRR':>6}  Note")
    print("─" * 100)

    rows = []
    for i, tc in enumerate(queries, 1):
        query    = tc["query"]
        expected = tc["expected"]
        note     = tc.get("note", "")

        results = run_query(query, K)

        h1  = hit_at_k(results, expected, 1)
        h3  = hit_at_k(results, expected, 3)
        h5  = hit_at_k(results, expected, 5)
        mrr = reciprocal_rank(results, expected)

        # Find first hit for annotation
        hit_slug = next((r["slug"] for r in results if r["slug"] in expected), None)
        hit_rank = next((r["rank"] for r in results if r["slug"] in expected), None)
        miss_slug = results[0]["slug"] if results and not h1 else None

        status = "✓" if h1 else ("~" if h3 else ("·" if h5 else "✗"))
        q_short = query[:46] + ".." if len(query) > 48 else query

        print(
            f"{i:>3}  {q_short:<48}  "
            f"{'✓' if h1 else ' ':>5}  "
            f"{'✓' if h3 else ' ':>5}  "
            f"{'✓' if h5 else ' ':>5}  "
            f"{mrr:>6.3f}  {note}"
        )

        if not h1 and results:
            top_slug = results[0]["slug"]
            print(f"     {'':48}  top result: {top_slug[:60]}")
        if hit_rank and hit_rank > 1:
            print(f"     {'':48}  expected at rank {hit_rank}: {hit_slug}")

        rows.append({
            "query": query, "expected": expected, "note": note,
            "hit_at_1": h1, "hit_at_3": h3, "hit_at_5": h5, "mrr": mrr,
            "top_result": results[0]["slug"] if results else None,
            "first_hit_rank": hit_rank,
            "results": [{"rank": r["rank"], "slug": r["slug"], "score": r["score"]} for r in results],
        })

    n = len(rows)
    avg_h1  = sum(r["hit_at_1"] for r in rows) / n
    avg_h3  = sum(r["hit_at_3"] for r in rows) / n
    avg_h5  = sum(r["hit_at_5"] for r in rows) / n
    avg_mrr = sum(r["mrr"]      for r in rows) / n

    print("─" * 100)
    print(
        f"{'AVERAGE':>53}  "
        f"{avg_h1:>5.1%}  "
        f"{avg_h3:>5.1%}  "
        f"{avg_h5:>5.1%}  "
        f"{avg_mrr:>6.3f}"
    )
    print(f"\n  Hit@1={avg_h1:.1%}  Hit@3={avg_h3:.1%}  Hit@5={avg_h5:.1%}  MRR={avg_mrr:.3f}\n")

    if args.save:
        RESULTS_DIR.mkdir(exist_ok=True)
        ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = RESULTS_DIR / f"eval_{ts}.json"
        summary = {
            "timestamp": ts, "top_k": K, "n_queries": n,
            "hit_at_1": avg_h1, "hit_at_3": avg_h3, "hit_at_5": avg_h5, "mrr": avg_mrr,
            "queries": rows,
        }
        path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"  Results saved to {path}")


if __name__ == "__main__":
    main()
