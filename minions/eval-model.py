"""
eval-model.py — GBrain LLM output quality evaluation (LLM-as-judge)

For each test question:
  1. Runs `gbrain think <question>` to get a synthesized answer
  2. Sends question + answer to Claude as a judge
  3. Scores 5 dimensions on a 1–5 scale:
       Relevance    — does the answer address the question?
       Grounding    — are claims tied to specific cited sources?
       Coherence    — logical flow, clear structure, no contradictions?
       Citations    — citations are meaningful, not just slug noise?
       Gaps honesty — does the Gaps section reflect real unknowns?

Usage:
  python eval-model.py                 # run all test questions
  python eval-model.py --save          # also write JSON to eval-results/
  python eval-model.py --question 2    # run only question #2 (1-indexed)
  python eval-model.py --verbose       # print full think output for each question
"""
import os, sys, json, subprocess, re, datetime, argparse, urllib.request, ssl
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ssl._create_default_https_context = ssl._create_unverified_context

GBRAIN_CMD  = os.path.join(os.path.expanduser("~"), ".bun", "bin", "gbrain.cmd")
RESULTS_DIR = Path(r"C:\brain\eval-results")

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

for _k in ("DATABASE_URL", "VOYAGE_API_KEY", "ANTHROPIC_API_KEY"):
    if not ENV.get(_k):
        _v = _reg(_k)
        if _v:
            ENV[_k] = _v

ANTHROPIC_KEY = ENV.get("ANTHROPIC_API_KEY", "")

# ── Test questions ─────────────────────────────────────────────────────────────
TEST_QUESTIONS = [
    {
        "question": "What is vector policy optimization and how does it improve test-time search?",
        "note":     "Core paper — should have strong citations and detail",
    },
    {
        "question": "How do multi-agent systems approach financial trading and what are their advantages?",
        "note":     "Two trading papers in brain: TradingAgents + AI-Trader",
    },
    {
        "question": "What production architecture patterns exist for deploying LLM agents at scale?",
        "note":     "Two architecture papers — should cite both",
    },
    {
        "question": "What does OpenHands provide for software engineering automation?",
        "note":     "Single-paper answer — should cite openhands directly",
    },
    {
        "question": "How does target distribution design improve supervised fine-tuning of language models?",
        "note":     "SFT theory paper — technical answer expected",
    },
    {
        "question": "What is the state of vision-language models for game playing and agent evaluation?",
        "note":     "OmniGameArena paper — benchmark description expected",
    },
    {
        "question": "How do agentic AI systems model and use world knowledge?",
        "note":     "Agentic world modeling paper — should surface key concepts",
    },
]

JUDGE_PROMPT = """\
You are an expert evaluator of AI-generated research summaries. You will be given a research question and an answer produced by an AI knowledge base system. Your job is to score the answer on 5 dimensions.

## Question
{question}

## Answer
{answer}

## Scoring instructions

Score each dimension from 1 to 5:
- 5 = excellent, no issues
- 4 = good, minor issues
- 3 = acceptable, noticeable gaps
- 2 = poor, significant issues
- 1 = very poor or missing

Dimensions:
1. **relevance** — Does the answer directly address what was asked? Does it stay on topic?
2. **grounding** — Are claims tied to specific cited sources (e.g. [slug_name])? Or are claims made without support?
3. **coherence** — Is the answer well-structured, logically consistent, and free of contradictions?
4. **citations** — Are the citations meaningful and specific? Do they feel earned, not just dropped in randomly?
5. **gaps_honesty** — Does the Gaps section accurately identify real unknowns? Does it avoid false confidence?

## Output format

Respond with ONLY valid JSON in exactly this structure:
{{
  "relevance":    {{"score": <1-5>, "reason": "<one sentence>"}},
  "grounding":    {{"score": <1-5>, "reason": "<one sentence>"}},
  "coherence":    {{"score": <1-5>, "reason": "<one sentence>"}},
  "citations":    {{"score": <1-5>, "reason": "<one sentence>"}},
  "gaps_honesty": {{"score": <1-5>, "reason": "<one sentence>"}},
  "overall":      "<one sentence overall assessment>"
}}"""

# ── gbrain think ──────────────────────────────────────────────────────────────
_FOOTER_PAT = re.compile(r"\n---\nModel:.*$", re.S)

def run_think(question: str) -> tuple[str, dict]:
    """Run gbrain think and return (answer_text, metadata)."""
    try:
        r = subprocess.run(
            ["cmd.exe", "/c", GBRAIN_CMD, "think", question],
            capture_output=True, env=ENV, timeout=120,
        )
        raw = r.stdout.decode("utf-8", errors="replace").strip()

        # Extract footer metadata
        meta = {}
        footer_m = re.search(r"Model: ([^\|]+) \| Pages: (\d+) \| Takes: (\d+) \| Graph: (\d+) \| Citations: (\d+)", raw)
        if footer_m:
            meta = {
                "model":     footer_m.group(1).strip(),
                "pages":     int(footer_m.group(2)),
                "takes":     int(footer_m.group(3)),
                "graph":     int(footer_m.group(4)),
                "citations": int(footer_m.group(5)),
            }

        # Strip footer for judge
        answer = _FOOTER_PAT.sub("", raw).strip()
        return answer, meta
    except subprocess.TimeoutExpired:
        return "(gbrain think timed out after 120s)", {}
    except Exception as e:
        return f"(error running gbrain think: {e})", {}


# ── Anthropic judge ───────────────────────────────────────────────────────────
def judge(question: str, answer: str) -> dict:
    """Call Claude to score the answer. Returns parsed score dict."""
    if not ANTHROPIC_KEY:
        return {"error": "ANTHROPIC_API_KEY not set"}

    prompt = JUDGE_PROMPT.format(question=question, answer=answer[:6000])
    payload = json.dumps({
        "model":      "claude-haiku-4-5-20251001",
        "max_tokens": 800,
        "messages":   [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type":      "application/json",
                "x-api-key":         ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["content"][0]["text"].strip()

        # Strip markdown code fences if present
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return json.loads(text)
    except json.JSONDecodeError as e:
        return {"error": f"Judge returned invalid JSON: {e}"}
    except Exception as e:
        return {"error": str(e)}


# ── Rendering ─────────────────────────────────────────────────────────────────
DIMS = ["relevance", "grounding", "coherence", "citations", "gaps_honesty"]
DIM_LABELS = {
    "relevance":    "Relevance",
    "grounding":    "Grounding",
    "coherence":    "Coherence",
    "citations":    "Citations",
    "gaps_honesty": "Gaps",
}

def score_bar(score: int) -> str:
    filled = "█" * score
    empty  = "░" * (5 - score)
    return f"{filled}{empty} {score}/5"

def dim_avg(rows: list[dict], dim: str) -> float:
    vals = [r["scores"][dim]["score"] for r in rows if "scores" in r and dim in r["scores"]]
    return sum(vals) / len(vals) if vals else 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--save",     action="store_true")
    parser.add_argument("--verbose",  action="store_true")
    parser.add_argument("--question", type=int, default=0, help="Run only question N (1-indexed)")
    args = parser.parse_args()

    questions = TEST_QUESTIONS
    if args.question:
        idx = args.question - 1
        if 0 <= idx < len(questions):
            questions = [questions[idx]]
        else:
            print(f"Question {args.question} out of range (1–{len(TEST_QUESTIONS)})")
            sys.exit(1)

    now = datetime.datetime.now()
    print(f"\nGBrain Model Evaluation  —  {now.strftime('%Y-%m-%d %H:%M')}  —  {len(questions)} question(s)\n")

    rows = []
    for i, tc in enumerate(questions, 1):
        q    = tc["question"]
        note = tc.get("note", "")

        print(f"Q{i}: {q}")
        print(f"     ({note})")
        print("     Running gbrain think...", end="", flush=True)

        answer, meta = run_think(q)
        print(f" {meta.get('pages', '?')} pages, {meta.get('citations', '?')} citations")

        if args.verbose:
            print()
            for line in answer.splitlines()[:30]:
                print(f"     {line}")
            print()

        print("     Judging...", end="", flush=True)
        scores = judge(q, answer)
        print(" done\n")

        if "error" in scores:
            print(f"     ⚠ Judge error: {scores['error']}\n")
            rows.append({"question": q, "note": note, "meta": meta, "error": scores["error"]})
            continue

        overall_score = sum(scores[d]["score"] for d in DIMS if d in scores) / len(DIMS)

        print(f"     {'Dimension':<14}  Score   Reason")
        print(f"     {'─'*70}")
        for dim in DIMS:
            if dim in scores:
                s = scores[dim]
                label = DIM_LABELS[dim]
                print(f"     {label:<14}  {score_bar(s['score'])}  {s['reason'][:55]}")

        if "overall" in scores:
            print(f"\n     Overall ({overall_score:.1f}/5): {scores['overall']}")
        print()

        rows.append({
            "question": q,
            "note":     note,
            "meta":     meta,
            "scores":   {d: scores[d] for d in DIMS if d in scores},
            "overall":  scores.get("overall", ""),
            "avg":      overall_score,
        })

    # Summary table
    if len(rows) > 1:
        print("─" * 75)
        print(f"\n  {'#':<3}  {'Avg':>5}  Question")
        for i, r in enumerate(rows, 1):
            avg = f"{r['avg']:.1f}" if "avg" in r else "ERR"
            q   = r["question"][:62] + ".." if len(r["question"]) > 64 else r["question"]
            print(f"  {i:<3}  {avg:>5}  {q}")

        valid = [r for r in rows if "avg" in r]
        if valid:
            print(f"\n  {'Dimension':<14}  " + "  ".join(f"Q{i+1}" for i in range(len(valid))))
            print(f"  {'─'*60}")
            for dim in DIMS:
                scores_row = []
                for r in valid:
                    s = r.get("scores", {}).get(dim, {}).get("score")
                    scores_row.append(f"{s}/5" if s else " — ")
                avgs = dim_avg(valid, dim)
                print(f"  {DIM_LABELS[dim]:<14}  " + "   ".join(f"{s:>3}" for s in scores_row) + f"   avg {avgs:.1f}")

            grand_avg = sum(r["avg"] for r in valid) / len(valid)
            print(f"\n  Grand average: {grand_avg:.2f} / 5.00\n")

    if args.save:
        RESULTS_DIR.mkdir(exist_ok=True)
        ts   = now.strftime("%Y%m%d_%H%M%S")
        path = RESULTS_DIR / f"model_{ts}.json"
        path.write_text(json.dumps({
            "timestamp": ts,
            "n":         len(rows),
            "results":   rows,
        }, indent=2, default=str), encoding="utf-8")
        print(f"  Saved to {path}")


if __name__ == "__main__":
    main()
