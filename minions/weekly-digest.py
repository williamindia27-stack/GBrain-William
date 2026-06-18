import subprocess
import os
import re
import json
import urllib.request
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
from datetime import date
from collections import defaultdict

GBRAIN_CMD  = os.path.join(os.path.expanduser("~"), ".bun", "bin", "gbrain.cmd")
DIGESTS_DIR = r"C:\brain\digests"
LOG_FILE    = r"C:\brain\minions\weekly-digest.log"

PAPER_NAMES = {
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

# Broader + deeper queries for weekly coverage
SEARCH_QUERIES = [
    "autonomous agents decision making planning",
    "multi agent collaboration coordination",
    "financial trading AI performance",
    "world model environment simulation",
    "human oversight alignment safety",
    "benchmark evaluation generalization",
    "dynamic environments adaptation",
    "agent architecture design",
    "language model reasoning",
    "real world deployment challenges",
    "data driven forecasting prediction",
    "agent learning memory",
]

def log(msg):
    from datetime import datetime
    ts = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")

def run_gbrain(*args):
    env = {**os.environ, "PATH": os.path.join(os.path.expanduser("~"), ".bun", "bin") + ";" + os.environ.get("PATH", "")}
    cmd = " ".join([f'"{GBRAIN_CMD}"'] + [f'"{a}"' if " " in str(a) else str(a) for a in args])
    r = subprocess.run(cmd, capture_output=True, shell=True, timeout=30, env=env)
    return (r.stdout or b"").decode("utf-8", errors="replace").strip()

def parse_results(raw):
    results = []
    for line in raw.splitlines():
        m = re.match(r"\[([0-9.]+)\]\s+(\S+)\s+--\s+(.*)", line)
        if m:
            results.append({"score": float(m.group(1)), "slug": m.group(2), "excerpt": m.group(3).strip()})
        elif results and line.strip():
            results[-1]["excerpt"] += " " + line.strip()
    return results

def collect_chunks():
    seen = set()
    chunks = []
    for q in SEARCH_QUERIES:
        raw = run_gbrain("search", q, "--limit", "5")
        for r in parse_results(raw):
            key = r["slug"] + r["excerpt"][:40]
            if key not in seen and r["score"] >= 0.55:
                seen.add(key)
                chunks.append(r)
    return chunks

def build_context(chunks):
    by_paper = defaultdict(list)
    for c in chunks:
        by_paper[c["slug"]].append(c["excerpt"])
    parts = []
    for slug, excerpts in by_paper.items():
        name = PAPER_NAMES.get(slug, slug)
        combined = " ".join(excerpts[:5])[:900]
        parts.append(f"[{name}]: {combined}")
    return "\n\n".join(parts)

def call_groq(context, groq_key):
    system_prompt = (
        "You are a senior AI research analyst writing a weekly digest for a personal knowledge base. "
        "Write a comprehensive weekly synthesis with exactly these 5 sections:\n\n"
        "## Core Themes This Week\n"
        "## Key Findings & Insights\n"
        "## Tensions & Debates\n"
        "## Practical Implications\n"
        "## Questions Worth Exploring Next\n\n"
        "Be specific and analytical. Cite papers in brackets like [TradingAgents]. "
        "Draw connections across papers. Max 650 words total."
    )
    payload = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Knowledge base excerpts:\n\n{context}\n\nWrite this week's research digest."},
        ],
        "temperature": 0.4,
        "max_tokens": 900,
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
    with urllib.request.urlopen(req, timeout=40) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()

def main():
    log("Starting weekly digest generation...")

    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key:
        log("ERROR: GROQ_API_KEY not set")
        raise SystemExit(1)

    chunks = collect_chunks()
    log(f"Collected {len(chunks)} chunks from {len({c['slug'] for c in chunks})} papers")

    if not chunks:
        log("ERROR: No chunks retrieved")
        raise SystemExit(1)

    context = build_context(chunks)

    try:
        digest = call_groq(context, groq_key)
    except Exception as e:
        log(f"ERROR calling Groq: {e}")
        raise SystemExit(1)

    os.makedirs(DIGESTS_DIR, exist_ok=True)
    today = date.today().isoformat()
    out_path = os.path.join(DIGESTS_DIR, f"{today}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Weekly Research Digest — {today}\n\n")
        f.write(digest)
        f.write(f"\n\n---\n*{len(chunks)} chunks · {len({c['slug'] for c in chunks})} papers*\n")

    log(f"Digest saved: {out_path}")

if __name__ == "__main__":
    main()
