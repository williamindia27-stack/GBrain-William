import streamlit as st
import subprocess
import os
import sys
import re
from pathlib import Path
import wordninja
import urllib.request
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import json

# ── Config ────────────────────────────────────────────────────────────────────
GBRAIN_CMD = os.path.join(os.path.expanduser("~"), ".bun", "bin", "gbrain.cmd")

def _load_registry_key(name):
    """Read a string value from HKCU\\Environment (Windows user env vars persisted in registry)."""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
        value, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return value
    except Exception:
        return ""

# Load API keys — fall back to Windows registry if not in process environment
# (Streamlit may have started before setx wrote the keys)
_NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "") or _load_registry_key("NVIDIA_API_KEY")
_GROQ_API_KEY   = os.environ.get("GROQ_API_KEY", "")   or _load_registry_key("GROQ_API_KEY")

# Pass all env vars including API keys, override PATH
ENV = {
    **os.environ,
    "PATH": os.path.join(os.path.expanduser("~"), ".bun", "bin") + ";" + os.environ.get("PATH", ""),
    "NVIDIA_API_KEY": _NVIDIA_API_KEY,
    "GROQ_API_KEY":   _GROQ_API_KEY,
    # Corporate SSL inspection: tell Bun/Node.js to skip SSL verification
    "NODE_TLS_REJECT_UNAUTHORIZED": "0",
}

EXTRACTED_DIR = r"C:\brain\extracted"

# Base papers (manually imported into the brain)
_BASE_PAPERS = {
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

_BASE_TAGS = {
    "agentic_world_modeling":            "survey",
    "openhands":                         "platform",
    "agentscope":                        "framework",
    "multi_agent_trading":               "finance",
    "ai_trader_agent":                   "finance",
    "kronos_a_foundation_model":         "finance",
    "image_regonition_phone_avatar":     "mobile",
    "human_ai_oversight_video_language": "oversight",
    "agentic":                           "forecasting",
    "python_cosmological":               "science",
}

def _discover_extracted_papers():
    """Scan extracted/ folder and parse frontmatter titles for dynamically imported papers."""
    discovered = {}
    try:
        for fname in os.listdir(EXTRACTED_DIR):
            if not fname.endswith(".md"):
                continue
            slug = fname[:-3]  # strip .md
            if slug in _BASE_PAPERS:
                continue
            path = os.path.join(EXTRACTED_DIR, fname)
            title = slug.replace("_", " ").title()
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("title:"):
                            raw = line[6:].strip().strip('"').strip("'")
                            if raw:
                                title = raw
                            break
                        if line.startswith("---") and title != slug.replace("_", " ").title():
                            break  # past frontmatter
            except Exception:
                pass
            discovered[slug] = title
    except Exception:
        pass
    return discovered

def _build_papers():
    extracted = _discover_extracted_papers()
    papers = {**_BASE_PAPERS, **extracted}
    tags   = {**_BASE_TAGS}
    for slug in extracted:
        tags[slug] = "auto-import"
    return papers, tags

PAPERS, PAPER_TAGS = _build_papers()

TAG_COLORS = {
    "survey":       "#7c3aed",
    "platform":     "#0369a1",
    "framework":    "#0369a1",
    "finance":      "#065f46",
    "mobile":       "#92400e",
    "oversight":    "#9f1239",
    "forecasting":  "#1d4ed8",
    "science":      "#374151",
    "auto-import":  "#0f766e",   # teal — distinguishes auto-imported papers
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def run_gbrain(*args, timeout=90):
    # Use cmd.exe /c so .cmd files execute on Windows without shell=True.
    # shell=True can leave orphaned bun processes when the timeout fires.
    cmd = ["cmd.exe", "/c", GBRAIN_CMD] + list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, env=ENV, timeout=timeout)
        stdout = (r.stdout or b"").decode("utf-8", errors="replace").strip()
        stderr = (r.stderr or b"").decode("utf-8", errors="replace").strip()
        return stdout, stderr, r.returncode
    except subprocess.TimeoutExpired:
        return "", f"gbrain timed out after {timeout}s", 1

def parse_search_lines(raw):
    results = []
    for line in raw.splitlines():
        m = re.match(r"\[([0-9.]+)\]\s+(\S+)\s+--\s+(.*)", line)
        if m:
            results.append({
                "score":   float(m.group(1)),
                "slug":    m.group(2),
                "excerpt": m.group(3).strip(),
            })
        elif results and line.strip():
            # continuation of the previous chunk — join it
            results[-1]["excerpt"] += " " + line.strip()
    # Clean up mid-word starts caused by chunk boundaries
    for r in results:
        ex = r["excerpt"]
        if ex and ex[0].islower() and not ex.startswith("..."):
            r["excerpt"] = "…" + ex
    return results

_MIN_SCORE = 0.45   # hybrid scores are normalized differently from keyword-only

_JUNK_PATTERNS = re.compile(
    r"@connect\.|arxiv\.org/abs|\{tiany|"   # metadata artifacts
    r"URL https?://|doi\.org/10\.|"          # raw URLs/DOIs
    r"^AI-TRADER:|^OpenHands|^AgentScope",   # document-level headers
    re.I
)

def _strip_wikilinks(text):
    """[[slug|Label]] → Label,  [[slug]] → slug"""
    text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
    return text

def _is_junk(r):
    slug = r.get("slug", "")
    # Author/institution stub pages and synthesis summaries — not source documents
    if slug.startswith("people/") or slug.startswith("companies/"):
        return True
    if "summary" in slug.lower():
        return True
    ex = r["excerpt"]
    if _JUNK_PATTERNS.search(ex[:400]):
        return True
    # Excerpt dominated by wikilink author list (## Authors section leaking through)
    if ex.count("[[people/") >= 3 or ex.count("[[companies/") >= 3:
        return True
    # Pure references section: "Lastname, Firstname and Lastname2, Firstname2..." 3+ names
    if re.search(r'^[A-Z][a-z]+,\s+[A-Z][a-z]+.*and\s+[A-Z][a-z]+,\s+[A-Z]', ex):
        return True
    # Naked .pdf filename line — no real content
    if re.match(r'^\S+\.pdf\s*$', ex.strip(), re.I):
        return True
    return False

def gbrain_search(query, limit=5):
    # gbrain query = full 8-stage hybrid pipeline:
    # intent classifier → multi-query expansion (Haiku) → vector (HNSW) + keyword (tsvector)
    # → RRF fusion → compiled-truth boost + backlink boost → dedup → cited results
    raw, _, _ = run_gbrain("query", query, "--limit", str(limit))
    results = [r for r in parse_search_lines(raw) if r["score"] >= _MIN_SCORE and not _is_junk(r)]
    results.sort(key=lambda r: r["score"], reverse=True)
    results = results[:limit]
    # Fallback: if gbrain query returned nothing (e.g. Haiku expansion failed due to SSL/timeout),
    # retry with gbrain search (simpler keyword+vector path, no LLM expansion).
    if not results:
        raw2, _, _ = run_gbrain("search", query, "--limit", str(limit))
        results = [r for r in parse_search_lines(raw2) if r["score"] >= 0.1 and not _is_junk(r)]
        results.sort(key=lambda r: r["score"], reverse=True)
        results = results[:limit]
    return results

@st.cache_data(show_spinner=False, ttl=3600)
def _slug_display_name(slug: str) -> str:
    """Return a human-readable name for a slug, even if it's not in PAPERS.
    Result is cached for 1 hour so repeated renders don't spawn extra subprocesses."""
    if slug in PAPERS:
        return PAPERS[slug]
    # Try to pull the title from gbrain (frontmatter title field)
    raw, _, _ = run_gbrain("get", slug, timeout=20)
    if raw:
        for line in raw.splitlines()[:15]:
            line = line.strip()
            if line.startswith("title:"):
                title = line[6:].strip().strip('"').strip("'")
                if title:
                    return title
    # Fallback: humanise the slug (underscores → spaces, title-case)
    return slug.replace("_", " ").replace("-", " ").title()


_SUMMARY_SECTIONS = ["Overview", "Method", "Key Results", "Why It Matters", "Limitations"]

def _extract_section(content: str, section: str) -> str:
    m = re.search(rf"^## {re.escape(section)}\s*\n(.*?)(?=^## |\Z)", content, re.M | re.S)
    return m.group(1).strip() if m else ""

def _paper_summary_for_context(slug: str, max_chars: int = 1200) -> str:
    """Return a compact multi-section summary from a paper page, or "" if unavailable."""
    content = gbrain_get(slug)
    if not content:
        return ""
    parts = []
    for sec in _SUMMARY_SECTIONS:
        body = _extract_section(content, sec)
        if body:
            parts.append(f"[{sec}]\n{body[:400]}")
    return "\n\n".join(parts)[:max_chars]

def gbrain_query(question, limit=6):
    chunks = gbrain_search(question, limit)
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key or not chunks:
        return None, chunks

    # De-duplicate slugs so we only fetch each paper once
    seen_slugs: set[str] = set()
    context_parts = []
    for c in chunks:
        slug = c["slug"]
        title = _slug_display_name(slug)
        # Try to enrich with the full structured summary from the paper page
        if slug not in seen_slugs:
            seen_slugs.add(slug)
            summary = _paper_summary_for_context(slug)
            if summary:
                context_parts.append(f"### {title}\n{summary}")
                continue
        # Fallback: use the raw search excerpt if no structured content available
        context_parts.append(f"### {title}\n{fix_spaces(c['excerpt'])}")

    context = "\n\n".join(context_parts)
    try:
        payload = json.dumps({
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": (
                    "You are a research assistant. Answer the question using ONLY the provided "
                    "paper summaries. Be concise and specific — cite which paper each point comes from. "
                    "If the summaries do not contain enough information to answer properly, say so "
                    "in one sentence and list what the summaries DO cover. "
                    "Never restate the question as the answer."
                )},
                {"role": "user", "content": f"Paper summaries:\n{context}\n\nQuestion: {question}"},
            ],
            "temperature": 0.3,
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
        import ssl as _ssl
        _ctx = _ssl.create_default_context()
        _ctx.check_hostname = False
        _ctx.verify_mode = _ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=30, context=_ctx) as r:
            data = json.loads(r.read().decode("utf-8"))
        answer = data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        answer = None
        st.warning(f"Groq error: {e}")
    return answer, chunks


def run_gbrain_input(input_text: str, *args, timeout: int = 120) -> tuple:
    """Run a gbrain sub-command with stdin piped from input_text. Returns (stdout, stderr, returncode)."""
    cmd = ["cmd.exe", "/c", GBRAIN_CMD] + list(args)
    try:
        r = subprocess.run(
            cmd, input=input_text.encode("utf-8"),
            capture_output=True, env=ENV, timeout=timeout,
        )
        stdout = (r.stdout or b"").decode("utf-8", errors="replace").strip()
        stderr = (r.stderr or b"").decode("utf-8", errors="replace").strip()
        return stdout, stderr, r.returncode
    except subprocess.TimeoutExpired:
        return "", f"gbrain timed out after {timeout}s", 1


def parse_think_output(raw: str) -> dict:
    """Parse gbrain think stdout into answer, gaps, stats, warnings."""
    lines = raw.splitlines()
    # Skip leading header/separator lines
    start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if set(stripped) <= set("─-=") and len(stripped) > 3:
            start = i + 1
        elif stripped and i > 0:
            break
    # Find the final footer separator
    footer_sep = -1
    for i in range(len(lines) - 1, -1, -1):
        stripped = lines[i].strip()
        if set(stripped) <= set("─-=") and len(stripped) > 3:
            footer_sep = i
            break
    if footer_sep > start:
        body_lines = lines[start:footer_sep]
        footer_lines = lines[footer_sep + 1:]
    else:
        body_lines = lines[start:]
        footer_lines = []
    body = "\n".join(body_lines).strip()
    # Split answer from ## Gaps section
    gaps_idx = body.find("\n## Gaps")
    if gaps_idx >= 0:
        answer = body[:gaps_idx].strip()
        gaps   = body[gaps_idx:].strip()
    else:
        answer = body
        gaps   = ""
    # Parse stats / warnings from footer
    stats = ""
    warnings = ""
    for line in footer_lines:
        line = line.strip()
        if line.lower().startswith("warnings:"):
            warnings = line[len("warnings:"):].strip()
        elif "|" in line and any(k in line for k in ("Pages", "Model", "Graph", "Takes", "Citations")):
            stats = line
    return {"answer": answer, "gaps": gaps, "stats": stats, "warnings": warnings}


@st.cache_data(show_spinner=False, ttl=600)
def gbrain_get(slug):
    raw, _, _ = run_gbrain("get", slug)
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        return parts[2].strip() if len(parts) >= 3 else raw
    return raw

def fix_spaces(text):
    """Fix PDF extraction artifacts: rejoin hyphenated line-breaks, segment concatenated words."""
    text = re.sub(r"(\w+)-\s+(\w+)", r"\1\2", text)

    def fix_token(token):
        # Peel leading/trailing punctuation so isalpha() works on the real core
        m = re.match(r'^([(\["\']*)(.*?)([)\]"\'.,;:!?]*)$', token, re.S)
        if not m:
            return token
        lead, core, trail = m.group(1), m.group(2), m.group(3)
        clean = core.replace("-", "").replace("_", "")
        if len(clean) >= 16 and clean.isalpha() and not clean.isupper():
            words = wordninja.split(core.replace("-", " "))
            # Reject if wordninja produced single-char tokens — bad split
            if len(words) > 1 and all(len(w) >= 2 for w in words):
                return lead + " ".join(words) + trail
        return token

    return " ".join(fix_token(t) for t in text.split())

def expand_excerpt(slug, excerpt, window=450):
    """Return a wider passage from the full paper around the matched chunk."""
    full = gbrain_get(slug)
    if not full:
        return excerpt
    # Strip leading ellipsis and whitespace for searching
    needle = excerpt.lstrip("…").strip()
    # If the chunk starts mid-word (lowercase first char), skip that broken word
    if needle and needle[0].islower():
        parts = needle.split(" ", 1)
        needle = parts[1] if len(parts) > 1 else needle
    # Normalize whitespace for both needle and full text so PDF spacing glitches don't block matching
    full_norm = re.sub(r"\s+", " ", full)
    # Try progressively shorter prefixes until we find the location
    for length in (60, 40, 25, 15):
        fragment = re.sub(r"\s+", " ", needle[:length]).strip()
        if not fragment:
            continue
        pos = full_norm.find(fragment)
        if pos != -1:
            break
    else:
        return excerpt  # not found — return original
    full = full_norm  # work on normalised version
    start = max(0, pos - window // 2)
    end   = min(len(full), pos + len(needle) + window // 2)
    # Walk back to a sentence/word boundary
    while start > 0 and full[start] not in " \n":
        start -= 1
    while end < len(full) and full[end] not in " \n":
        end += 1
    passage = full[start:end].strip()
    # Trim to sentence boundaries so we don't start/end mid-sentence
    sent_start = re.search(r'(?<=[.!?])\s+[A-Z]|^[A-Z]', passage)
    if sent_start and sent_start.start() < 120:
        passage = passage[sent_start.start():].lstrip()
    elif passage and not passage[0].isupper():
        # No sentence start found — strip to first capital letter
        m = re.search(r'[A-Z]', passage[:80])
        if m:
            passage = passage[m.start():]
    sent_end = re.search(r'[.!?](?=[^.!?]*$)', passage)
    if sent_end and len(passage) - sent_end.start() < 120:
        passage = passage[:sent_end.start() + 1]
    return passage

# ── UI Components ─────────────────────────────────────────────────────────────
def relevance_bar(score):
    pct = int(score * 100)
    color = "#22c55e" if pct >= 80 else "#f59e0b" if pct >= 60 else "#94a3b8"
    return f"""
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
        <div style="flex:1;background:#e2e8f0;border-radius:4px;height:6px">
            <div style="width:{pct}%;background:{color};height:6px;border-radius:4px"></div>
        </div>
        <span style="font-size:12px;color:{color};font-weight:600;min-width:36px">{pct}%</span>
    </div>"""

def paper_badge(slug):
    name  = _slug_display_name(slug)
    tag   = PAPER_TAGS.get(slug, "")
    color = TAG_COLORS.get(tag, "#374151")
    return f"""<span style="display:inline-block;background:{color};color:white;
        font-size:11px;font-weight:600;padding:2px 8px;border-radius:12px;
        margin-right:6px">{name}</span>
        <span style="font-size:11px;color:#94a3b8">{tag}</span>"""

def render_result_card(r, idx):
    slug    = r["slug"]
    score   = r["score"]
    passage = fix_spaces(expand_excerpt(slug, r["excerpt"]))
    passage = _strip_wikilinks(passage)
    passage = passage.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    st.markdown(relevance_bar(score), unsafe_allow_html=True)
    st.markdown(paper_badge(slug), unsafe_allow_html=True)
    st.markdown(
        f'<div style="background:#f8fafc;border-left:3px solid #e2e8f0;'
        f'padding:10px 14px;border-radius:0 6px 6px 0;margin:6px 0 16px 0;'
        f'font-size:14px;color:#334155;line-height:1.7;word-break:break-word">'
        f'{passage}</div>',
        unsafe_allow_html=True
    )

# ── Page Setup ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="GBrain", page_icon="🧠", layout="wide")

st.markdown("""
<style>
    .main { padding-top: 1.5rem; }
    h1 { font-size: 1.6rem !important; }
    .stTabs [data-baseweb="tab"] { font-size: 14px; }
</style>""", unsafe_allow_html=True)

st.title("🧠 GBrain")
_groq_active      = bool(os.environ.get("GROQ_API_KEY", "") or _load_registry_key("GROQ_API_KEY"))
_nvidia_active = bool(_NVIDIA_API_KEY)
if _nvidia_active:
    _status = "🟢 NVIDIA NIM active"
elif _groq_active:
    _status = "🟢 Groq LLM active"
else:
    _status = "🔴 No LLM — retrieval only"
_engine = "Postgres" if (os.environ.get("DATABASE_URL") or _load_registry_key("DATABASE_URL")) else "PGLite"
_live_papers, _ = _build_papers()
st.caption(f"{len(_live_papers)} papers · {_engine} · Voyage AI embeddings · {_status}")

tab_search, tab_ask, tab_read, tab_graph, tab_logs, tab_brief, tab_capture, tab_intel, tab_synthesis, tab_eval, tab_help = st.tabs(["🔍 Search", "💬 Ask", "📄 Read Paper", "🕸️ Graph", "🤖 Minions", "📋 Brief", "✏️ Capture", "🔬 Intel", "📝 Synthesis", "📊 Eval", "❓ Help"])

# ── Tab 1: Search ─────────────────────────────────────────────────────────────
with tab_search:
    col1, col2 = st.columns([5, 1])
    with col1:
        query = st.text_input("", placeholder=f"Search across all {len(PAPERS)} papers...", label_visibility="collapsed")
    with col2:
        limit = st.selectbox("", [3, 5, 10], index=1, label_visibility="collapsed")

    st.markdown(
        '<div style="display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 10px 0">'
        '<span style="background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe;'
        'border-radius:99px;padding:2px 10px;font-size:11px;font-weight:600">⚡ Hybrid search</span>'
        '<span style="background:#f0fdf4;color:#15803d;border:1px solid #bbf7d0;'
        'border-radius:99px;padding:2px 10px;font-size:11px">🔀 RRF fusion</span>'
        '<span style="background:#fdf4ff;color:#7e22ce;border:1px solid #e9d5ff;'
        'border-radius:99px;padding:2px 10px;font-size:11px">🧠 Intent classifier</span>'
        '<span style="background:#fff7ed;color:#c2410c;border:1px solid #fed7aa;'
        'border-radius:99px;padding:2px 10px;font-size:11px">✳️ Query expansion</span>'
        '<span style="background:#f0fdf4;color:#15803d;border:1px solid #bbf7d0;'
        'border-radius:99px;padding:2px 10px;font-size:11px">🏆 Compiled-truth boost</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    if query:
        with st.spinner("Searching..."):
            results = gbrain_search(query, limit)
        if not results:
            st.warning("No results. Try a different query.")
        else:
            st.caption(f"{len(results)} result(s) for **{query}**")
            st.divider()
            for i, r in enumerate(results):
                render_result_card(r, i)

# ── Tab 2: Ask ────────────────────────────────────────────────────────────────
_NVIDIA_KEY = _NVIDIA_API_KEY  # loaded from env or Windows registry above

with tab_ask:
    question = st.text_area(
        "",
        placeholder="What are the key differences between AI-Trader and TradingAgents?",
        height=90,
        label_visibility="collapsed",
    )
    if _NVIDIA_KEY or _groq_active:
        st.caption("🧠 **gbrain think** — retrieves 40 pages + graph edges, synthesises with inline citations and gap analysis")
    else:
        st.caption("🔍 Retrieval only — set NVIDIA_API_KEY or GROQ_API_KEY for synthesis")

    col_ask1, col_ask2 = st.columns([3, 1])
    with col_ask2:
        relational_mode = st.toggle("🔗 Relationship mode", value=False, key="relational_mode",
                                    help="Walk typed graph edges (invested_in, works_at, founded…) to answer relationship questions like 'who invested in X'")

    if st.button("Ask", type="primary") and question:
        if _NVIDIA_KEY or _groq_active:
            # ── Path 1: gbrain think (native synthesis layer) ─────────────
            _think_args = ["think", question]
            if relational_mode:
                _think_args += ["--relational", "true"]
            with st.spinner("🧠 Thinking across your brain…"):
                raw_think, stderr_think, rc_think = run_gbrain(*_think_args, timeout=180)

            if rc_think == 0 and raw_think:
                parsed = parse_think_output(raw_think)
                p_answer   = parsed["answer"]
                p_gaps     = parsed["gaps"]
                p_stats    = parsed["stats"]
                p_warnings = parsed["warnings"]

                if p_stats:
                    st.markdown(
                        f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;'
                        f'padding:6px 14px;margin-bottom:12px;font-family:monospace;font-size:12px;color:#64748b">'
                        f'{p_stats}</div>',
                        unsafe_allow_html=True,
                    )
                if p_warnings:
                    st.warning(f"⚠️ {p_warnings}")

                if p_answer:
                    st.markdown(
                        f'<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;'
                        f'padding:16px 20px;margin-bottom:16px;font-size:15px;line-height:1.7;color:#14532d">'
                        f'{p_answer}</div>',
                        unsafe_allow_html=True,
                    )
                if p_gaps:
                    gaps_body = p_gaps.replace("## Gaps", "").strip()
                    st.markdown(
                        f'<div style="background:#fffbeb;border:1px solid #fcd34d;border-radius:8px;'
                        f'padding:14px 18px;margin-top:4px">'
                        f'<div style="font-weight:700;font-size:13px;color:#92400e;margin-bottom:6px">'
                        f'🕳️ Knowledge Gaps</div>'
                        f'<div style="font-size:14px;color:#78350f;line-height:1.75">{gaps_body}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                if not p_answer:
                    with st.expander("📋 Raw think output"):
                        st.code(raw_think, language=None)
                    st.warning("No synthesis produced — gbrain think returned empty. Falling back to retrieval...")
                    with st.spinner("Searching brain..."):
                        answer, chunks = gbrain_query(question)
                    if chunks:
                        with st.expander(f"📚 Most relevant passages ({len(chunks)})", expanded=True):
                            for i, r in enumerate(chunks):
                                render_result_card(r, i)
            else:
                st.error(f"gbrain think failed (exit {rc_think}). Falling back to retrieval…")
                if stderr_think:
                    with st.expander("stderr"):
                        st.code(stderr_think[:500])
                with st.spinner("Searching brain..."):
                    answer, chunks = gbrain_query(question)
                if chunks:
                    with st.expander(f"📚 Most relevant passages ({len(chunks)})", expanded=True):
                        for i, r in enumerate(chunks):
                            render_result_card(r, i)
        else:
            # ── Path 2 / 3: Groq synthesis or retrieval-only ─────────────
            with st.spinner("Searching brain..."):
                answer, chunks = gbrain_query(question)

            if answer:
                st.markdown(
                    f'<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;'
                    f'padding:16px 20px;margin-bottom:20px;font-size:15px;line-height:1.7;color:#14532d">'
                    f'{answer}</div>',
                    unsafe_allow_html=True
                )

            if chunks:
                label = "Sources used" if answer else "Most relevant passages"
                with st.expander(f"📚 {label} ({len(chunks)})", expanded=not answer):
                    for i, r in enumerate(chunks):
                        render_result_card(r, i)

            if not answer and not chunks:
                st.warning("No results returned. Try rephrasing your question.")

# ── Tab 3: Read Paper ─────────────────────────────────────────────────────────
PYTHON_EXE            = sys.executable  # always the same Python that runs Streamlit
RESEARCH_NOTES_SCRIPT = r"C:\brain\research-notes.py"
GRAPH_SCRIPT          = r"C:\brain\build-research-graph.py"

with tab_read:
    col_a, col_b, col_c = st.columns([3, 1, 1])
    with col_a:
        # Rebuild paper list on every render so newly imported papers appear
        _current_papers, _ = _build_papers()
        selected = st.selectbox(
            "",
            options=list(_current_papers.keys()),
            format_func=lambda s: _current_papers.get(s, s),
            label_visibility="collapsed",
        )
    with col_b:
        load = st.button("Load", type="primary", use_container_width=True)
    with col_c:
        if st.button("🔄", use_container_width=True, help="Refresh paper list + clear cache"):
            gbrain_get.clear()
            st.session_state.pop("read_paper_slug", None)
            st.rerun()

    # Persist the loaded paper across enrichment button clicks via session state
    if load:
        st.session_state["read_paper_slug"] = selected

    _read_slug = st.session_state.get("read_paper_slug")
    if _read_slug:
        with st.spinner(f"Loading {_current_papers.get(_read_slug, _read_slug)}..."):
            content = gbrain_get(_read_slug)
        if content:
            # ── Enrichment buttons (write-back on demand) ─────────────────────
            _missing_rc      = "## Research Context" not in content
            _missing_authors = "## Authors" not in content

            if _missing_rc or _missing_authors:
                st.markdown(
                    '<div style="background:#fefce8;border:1px solid #fde047;border-radius:8px;'
                    'padding:10px 16px;margin-bottom:12px">'
                    '<span style="font-weight:600;color:#854d0e">⚡ This paper can be enriched</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                _enrich_cols = st.columns(3)
                with _enrich_cols[0]:
                    if _missing_authors:
                        if st.button("🕸️ Extract Authors", use_container_width=True,
                                     help="Pull authors + institutions from PDF via Groq"):
                            with st.spinner("Extracting authors…"):
                                _r = subprocess.run(
                                    [PYTHON_EXE, GRAPH_SCRIPT, _read_slug],
                                    capture_output=True, env=ENV, timeout=120,
                                )
                            if _r.returncode == 0:
                                gbrain_get.clear()
                                st.success("✅ Authors extracted")
                                st.rerun()
                            else:
                                st.error(_r.stderr.decode("utf-8", errors="replace")[:300])
                with _enrich_cols[1]:
                    if _missing_rc:
                        if st.button("🔬 Research Notes", use_container_width=True,
                                     help="Generate Research Context section via Groq"):
                            with st.spinner("Generating Research Context…"):
                                _r = subprocess.run(
                                    [PYTHON_EXE, RESEARCH_NOTES_SCRIPT, _read_slug],
                                    capture_output=True, env=ENV, timeout=120,
                                )
                            if _r.returncode == 0:
                                gbrain_get.clear()
                                st.success("✅ Research Notes added")
                                st.rerun()
                            else:
                                st.error(_r.stderr.decode("utf-8", errors="replace")[:300])
                with _enrich_cols[2]:
                    if _missing_rc or _missing_authors:
                        if st.button("✨ Enrich All", type="primary", use_container_width=True,
                                     help="Extract authors + generate Research Notes in one go"):
                            with st.spinner("Enriching paper… (1–2 min)"):
                                if _missing_authors:
                                    subprocess.run(
                                        [PYTHON_EXE, GRAPH_SCRIPT, _read_slug],
                                        env=ENV, timeout=120,
                                    )
                                if _missing_rc:
                                    subprocess.run(
                                        [PYTHON_EXE, RESEARCH_NOTES_SCRIPT, _read_slug],
                                        env=ENV, timeout=120,
                                    )
                            gbrain_get.clear()
                            st.success("✅ Enrichment complete")
                            st.rerun()
                st.divider()

            # ── Paper content ─────────────────────────────────────────────────
            st.markdown(paper_badge(_read_slug), unsafe_allow_html=True)
            st.divider()
            st.markdown(
                f'<div style="max-height:70vh;overflow-y:auto;padding:4px 8px">'
                f'{content}</div>',
                unsafe_allow_html=True
            )
        else:
            st.error("Could not load paper.")

# ── Tab 4: Graph ──────────────────────────────────────────────────────────────
PEOPLE_DIR    = os.path.join(EXTRACTED_DIR, "people")
COMPANIES_DIR = os.path.join(EXTRACTED_DIR, "companies")
MEETINGS_DIR  = os.path.join(EXTRACTED_DIR, "meetings")

def _slugify_name(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")

def _write_and_import(path: str, content: str) -> tuple[bool, str]:
    """Write a markdown file and import it into gbrain. Returns (ok, message)."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        raw, err, _ = run_gbrain("import", "--file", path, "--no-embed")
        if err and "error" in err.lower():
            return False, err[:200]
        return True, "Imported"
    except Exception as e:
        return False, str(e)

def _parse_graph_tree(raw: str) -> list[dict]:
    """Parse gbrain graph-query indented tree output into a list of nodes."""
    nodes = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        depth = (len(line) - len(line.lstrip())) // 2
        # Extract slug and type from lines like: "slug (type) → target [link_type]"
        m = re.match(r"([^\s(→]+)\s*(?:\(([^)]+)\))?\s*(?:→\s*([^\[]+?)(?:\s*\[([^\]]+)\])?)?$", stripped)
        if m:
            nodes.append({
                "depth": depth,
                "slug": m.group(1).strip(),
                "type": m.group(2) or "",
                "target": (m.group(3) or "").strip(),
                "link_type": (m.group(4) or "").strip(),
                "raw": stripped,
            })
        else:
            nodes.append({"depth": depth, "raw": stripped, "slug": "", "type": "", "target": "", "link_type": ""})
    return nodes

def _render_graph_node(node: dict):
    indent = "&nbsp;" * (node["depth"] * 4)
    slug  = node.get("slug", "")
    ntype = node.get("type", "")
    target = node.get("target", "")
    link_type = node.get("link_type", "")

    type_colors = {"person": "#7c3aed", "researcher": "#7c3aed", "institution": "#0369a1",
                   "company": "#0369a1", "paper": "#065f46", "meeting": "#92400e"}
    color = type_colors.get(ntype.lower(), "#374151")

    badge = f'<span style="background:{color};color:white;font-size:10px;padding:1px 6px;border-radius:8px;margin:0 4px">{ntype}</span>' if ntype else ""
    arrow = f'<span style="color:#94a3b8"> → {target}</span>' if target else ""
    link_badge = f'<span style="background:#f1f5f9;color:#64748b;font-size:10px;padding:1px 5px;border-radius:4px;margin-left:4px">{link_type}</span>' if link_type else ""

    st.markdown(
        f'<div style="font-family:monospace;font-size:13px;padding:2px 0">'
        f'{indent}<b>{slug}</b>{badge}{arrow}{link_badge}'
        f'</div>',
        unsafe_allow_html=True,
    )

def _read_authors_from_page(slug: str) -> list[dict]:
    """Extract authors from the ## Authors section of a paper page."""
    path = os.path.join(EXTRACTED_DIR, f"{slug}.md")
    if not os.path.exists(path):
        return []
    authors = []
    in_section = False
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.rstrip()
                if line == "## Authors":
                    in_section = True
                    continue
                if in_section:
                    if line.startswith("## ") or line.startswith("<!-- timeline"):
                        break
                    m = re.match(r"^-\s+\[\[(?:[^/\]]+/)?([^\|/\]]+?)(?:\|([^\]]+))?\]\](?:[^\[]*\[\[(?:[^/\]]+/)?([^\|/\]]+?)(?:\|([^\]]+))?\]\])?", line)
                    if m:
                        authors.append({
                            "slug": m.group(1),
                            "name": m.group(2) or m.group(1),
                            "inst_slug": m.group(3) or "",
                            "inst_name": m.group(4) or m.group(3) or "",
                        })
    except Exception:
        pass
    return authors

def _render_mermaid(diagram: str, height: int = 520) -> None:
    """Render a Mermaid diagram inside Streamlit using the Mermaid.js CDN."""
    escaped = diagram.replace("`", "&#96;")
    html = f"""
    <div id="mermaid-wrap" style="background:#0f172a;padding:24px;border-radius:12px;border:1px solid #1e293b">
      <pre class="mermaid" style="background:transparent">{escaped}</pre>
    </div>
    <script type="module">
      import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
      mermaid.initialize({{
        startOnLoad: true,
        theme: 'dark',
        themeVariables: {{
          primaryColor: '#1e3a8a',
          primaryTextColor: '#e2e8f0',
          primaryBorderColor: '#3b82f6',
          lineColor: '#475569',
          secondaryColor: '#14532d',
          tertiaryColor: '#78350f',
          background: '#0f172a',
          mainBkg: '#1e293b',
          nodeBorder: '#334155',
          clusterBkg: '#1e293b',
          titleColor: '#94a3b8',
          edgeLabelBackground: '#1e293b',
          fontFamily: 'Segoe UI, system-ui, sans-serif',
        }},
        flowchart: {{ curve: 'basis', padding: 18 }},
      }});
    </script>
    """
    import streamlit.components.v1 as components
    components.html(html, height=height, scrolling=True)


INGESTION_PIPELINE_MERMAID = """
flowchart TD
    A([🗂️ PDF on Desktop/Papers/]) --> B

    subgraph S1 [" Step 1 — PDF Extraction "]
        B[pypdf\nextract raw text\nfirst 3 pages]
    end

    B --> C

    subgraph S2 [" Step 2 — AI Summarisation "]
        C[Groq · Llama 3.3-70B\nraw text → structured summary\nOverview / Method / Results / Limits]
    end

    C --> D

    subgraph S3 [" Step 3 — Write Markdown "]
        D[📝 Write .md to disk\nextracted/paper_slug.md\nYAML frontmatter + sections]
    end

    D --> E

    subgraph S4 [" Step 4 — Chunk · Embed · Store "]
        E[gbrain import --no-embed\nchunk markdown into passages]
        E --> F[Voyage AI\ngenerate vector embeddings\nper chunk]
        F --> G[(Postgres + pgvector\npages table + content_chunks\nhybrid BM25 + HNSW index)]
    end

    G --> H

    subgraph S5 [" Step 5 — Graph Wiring "]
        H[gbrain extract all --source db\nwalk all pages\nresolve wikilinks]
        H --> I[(links table\ntyped edges\nauthor_of · affiliated_with · mentions)]
    end

    D --> J

    subgraph S6 [" Step 6 — Author Extraction "]
        J[build-research-graph.py\nre-read PDF first pages via pypdf\nGroq extracts author names + institutions]
        J --> K[people/slug.md\ncompanies/slug.md\nwikilink stubs]
        K --> L[## Authors section\nadded to paper page\nwikilinks re-extracted → new edges]
    end

    G --> M

    subgraph S7 [" Step 7 — Research Context "]
        M[research-notes.py\ngbrain search for related pages\npass paper + results to Groq]
        M --> N[## Research Context\nWhat's new · Related in brain\nKnowledge gaps · Explore next]
    end

    style S1 fill:#0f2744,stroke:#1e40af,color:#93c5fd
    style S2 fill:#1a1a2e,stroke:#7c3aed,color:#c4b5fd
    style S3 fill:#0d2318,stroke:#15803d,color:#86efac
    style S4 fill:#1a120b,stroke:#b45309,color:#fde68a
    style S5 fill:#130f1f,stroke:#6d28d9,color:#e9d5ff
    style S6 fill:#0f1f2e,stroke:#0369a1,color:#7dd3fc
    style S7 fill:#1a100e,stroke:#9f1239,color:#fda4af
"""


def _build_research_graph_html(filter_slug: str = "") -> str:
    """Build an interactive pyvis graph from all extracted papers."""
    try:
        from pyvis.network import Network
    except ImportError:
        return "<p style='color:red'>pyvis not installed. Run: pip install pyvis</p>"

    net = Network(height="680px", width="100%", bgcolor="#0f172a", font_color="#e2e8f0", directed=False)
    net.set_options(json.dumps({
        "nodes": {"borderWidth": 2, "shadow": True},
        "edges": {
            "color": {"color": "#334155", "highlight": "#60a5fa"},
            "width": 1.5,
            "smooth": {"type": "curvedCW", "roundness": 0.2},
        },
        "physics": {
            "solver": "barnesHut",
            "barnesHut": {
                "gravitationalConstant": -4000,
                "centralGravity": 0.3,
                "springLength": 130,
                "damping": 0.15,
            },
            "minVelocity": 0.75,
            "stabilization": {"iterations": 150},
        },
        "interaction": {"hover": True, "tooltipDelay": 200, "navigationButtons": True},
    }))

    papers, _ = _build_papers()
    added_nodes: set = set()
    edge_set: set = set()

    def _safe_add_edge(a, b, **kwargs):
        key = (min(a, b), max(a, b), kwargs.get("title", ""))
        if key not in edge_set:
            edge_set.add(key)
            net.add_edge(a, b, **kwargs)

    target_slugs = {filter_slug} if filter_slug else set(papers.keys())

    for slug, title in papers.items():
        if filter_slug and slug != filter_slug:
            continue
        authors = _read_authors_from_page(slug)
        if not authors and filter_slug:
            # Still add the paper node even without authors
            pass
        if not authors and not filter_slug:
            continue

        label = title[:22] + ("…" if len(title) > 22 else "")
        if slug not in added_nodes:
            net.add_node(
                slug, label=label,
                title=f"📄 {title}",
                color={"background": "#1e3a8a", "border": "#60a5fa", "highlight": {"background": "#2563eb", "border": "#93c5fd"}},
                size=28, shape="box",
                font={"size": 13, "color": "#e2e8f0", "bold": True},
            )
            added_nodes.add(slug)

        for a in authors:
            plabel = a["name"][:20] + ("…" if len(a["name"]) > 20 else "")
            if a["slug"] not in added_nodes:
                net.add_node(
                    a["slug"], label=plabel,
                    title=f"👤 {a['name']}",
                    color={"background": "#14532d", "border": "#4ade80", "highlight": {"background": "#16a34a", "border": "#86efac"}},
                    size=20, shape="dot",
                    font={"size": 12, "color": "#e2e8f0"},
                )
                added_nodes.add(a["slug"])

            _safe_add_edge(slug, a["slug"], color="#3b82f6", title="author of", width=1.5)

            if a["inst_slug"]:
                iname = a["inst_name"] or a["inst_slug"]
                ilabel = iname[:22] + ("…" if len(iname) > 22 else "")
                if a["inst_slug"] not in added_nodes:
                    net.add_node(
                        a["inst_slug"], label=ilabel,
                        title=f"🏛️ {iname}",
                        color={"background": "#78350f", "border": "#fbbf24", "highlight": {"background": "#b45309", "border": "#fde68a"}},
                        size=22, shape="diamond",
                        font={"size": 12, "color": "#e2e8f0"},
                    )
                    added_nodes.add(a["inst_slug"])

                _safe_add_edge(a["slug"], a["inst_slug"], color="#f59e0b", title="affiliated with", dashes=True, width=1)

    if not added_nodes:
        return (
            "<div style='font-family:sans-serif;color:#94a3b8;padding:40px;text-align:center'>"
            "No graph data yet — extract authors from papers first."
            "</div>"
        )

    # Legend
    legend_html = """
    <div style="font-family:sans-serif;font-size:12px;color:#94a3b8;padding:8px 0;display:flex;gap:20px;align-items:center">
      <span>Legend:</span>
      <span style="background:#1e3a8a;color:#e2e8f0;padding:2px 8px;border-radius:4px;border:1px solid #60a5fa">📄 Paper</span>
      <span style="background:#14532d;color:#e2e8f0;padding:2px 8px;border-radius:4px;border:1px solid #4ade80">👤 Person</span>
      <span style="background:#78350f;color:#e2e8f0;padding:2px 8px;border-radius:4px;border:1px solid #fbbf24">🏛️ Institution</span>
      <span style="color:#3b82f6">── author</span>
      <span style="color:#f59e0b">-- affiliated</span>
    </div>
    """
    graph_html = net.generate_html(notebook=False)
    return legend_html + graph_html


with tab_graph:
    g_research, g_personal, g_whoknows = st.tabs(["🔬 Research Graph", "👤 Personal Graph", "🧠 Who Knows?"])

    # ── Research Graph ─────────────────────────────────────────────────────────
    with g_research:
        # ── Count how many papers still need extraction ──
        _rg_papers, _ = _build_papers()
        def _has_no_authors(slug):
            path = os.path.join(EXTRACTED_DIR, f"{slug}.md")
            if not os.path.exists(path):
                return False
            with open(path, encoding="utf-8", errors="replace") as _f:
                return "## Authors" not in _f.read()

        _missing = [s for s in _rg_papers if _has_no_authors(s)]

        col_hdr, col_all = st.columns([5, 2])
        with col_hdr:
            st.caption(
                f"Authors extracted from PDFs via Groq · "
                f"**{len(_rg_papers) - len(_missing)}/{len(_rg_papers)}** papers done"
                + (f" · {len(_missing)} pending" if _missing else " ✅ all done")
            )
        with col_all:
            rg_build_all = st.button(
                f"⚙️ Extract All ({len(_missing)} pending)" if _missing else "✅ All extracted",
                type="primary" if _missing else "secondary",
                use_container_width=True,
                disabled=not _missing,
                help="Run Groq on every paper that is still missing an Authors section",
            )

        if rg_build_all and _missing:
            log_placeholder = st.empty()
            with st.spinner(f"Extracting authors for all {len(_missing)} pending papers… (this may take a few minutes)"):
                result = subprocess.run(
                    [PYTHON_EXE, GRAPH_SCRIPT],   # no slug arg = process all
                    capture_output=True, env=ENV, timeout=600,
                )
                out = result.stdout.decode("utf-8", errors="replace").strip()
            if result.returncode == 0:
                st.success(f"✅ Extraction complete — {len(_missing)} papers processed.")
            else:
                st.error(f"Extraction failed (exit {result.returncode})")
            if out:
                with st.expander("Show log", expanded=True):
                    st.code(out[-3000:], language=None)

        st.divider()

        # ── Full interactive graph ──
        col_gv1, col_gv2 = st.columns([3, 1])
        with col_gv1:
            st.markdown("**🕸️ Full Research Graph** — all papers, authors & institutions")
        with col_gv2:
            show_full_graph = st.button("View Full Graph", use_container_width=True, type="primary", key="view_full_graph")

        if show_full_graph or st.session_state.get("_full_graph_open"):
            st.session_state["_full_graph_open"] = True
            with st.spinner("Building interactive graph…"):
                graph_html = _build_research_graph_html()
            st.components.v1.html(graph_html, height=720, scrolling=False)
            if st.button("Close Graph", key="close_full_graph"):
                st.session_state["_full_graph_open"] = False
                st.rerun()

        st.divider()

        # ── Per-paper controls ──
        col_rg1, col_rg2, col_rg3 = st.columns([3, 1, 1])
        with col_rg1:
            rg_slug = st.selectbox(
                "",
                options=list(_rg_papers.keys()),
                format_func=lambda s: ("⚠️ " if s in _missing else "✅ ") + _rg_papers.get(s, s),
                label_visibility="collapsed",
                key="rg_paper_select",
            )
        with col_rg2:
            rg_show = st.button("Show Authors", type="primary", use_container_width=True)
        with col_rg3:
            rg_build = st.button(
                "⚙️ Extract" if rg_slug in _missing else "🔄 Re-extract",
                use_container_width=True,
                help="Run Groq to extract authors from this paper's PDF",
            )

        if rg_build and rg_slug:
            with st.spinner(f"Extracting authors for {_rg_papers.get(rg_slug, rg_slug)}…"):
                result = subprocess.run(
                    [PYTHON_EXE, GRAPH_SCRIPT, rg_slug],
                    capture_output=True, env=ENV, timeout=120,
                )
                out = result.stdout.decode("utf-8", errors="replace").strip()
            if result.returncode == 0:
                st.success("Extraction complete — authors are now linked.")
            else:
                st.error(f"Extraction failed (exit {result.returncode})")
            if out:
                st.code(out[-1500:], language=None)

        if rg_show and rg_slug:
            authors = _read_authors_from_page(rg_slug)
            if not authors:
                st.warning("No authors found. Click **⚙️ Extract** to pull them from the PDF.")
            else:
                st.markdown(f"**{len(authors)} author(s) found**")
                st.divider()
                for a in authors:
                    inst_html = (
                        f' <span style="color:#94a3b8;font-size:12px">@ {a["inst_name"]}</span>'
                        if a["inst_name"] else ""
                    )
                    st.markdown(
                        f'<div style="padding:6px 10px;background:#f8fafc;border-radius:6px;margin:3px 0;font-size:14px">'
                        f'👤 <b>{a["name"]}</b>{inst_html}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            # Show interactive mini-graph for this paper
            if authors:
                st.divider()
                st.markdown("**🕸️ Paper graph**")
                with st.spinner("Building graph…"):
                    mini_html = _build_research_graph_html(filter_slug=rg_slug)
                st.components.v1.html(mini_html, height=520, scrolling=False)

    # ── Personal Graph ─────────────────────────────────────────────────────────
    with g_personal:
        pg_mode = st.radio(
            "", ["➕ Add Person", "🏢 Add Company", "📅 Add Meeting", "🔍 Explore"],
            horizontal=True, label_visibility="collapsed",
        )
        st.divider()

        if pg_mode == "➕ Add Person":
            with st.form("add_person_form"):
                st.markdown("**Add a person to your knowledge graph**")
                p_name    = st.text_input("Full Name *", placeholder="Jane Smith")
                p_company = st.text_input("Company / Affiliation", placeholder="Acme Corp")
                p_role    = st.text_input("Role / Title", placeholder="CEO")
                p_notes   = st.text_area("Notes", placeholder="Met at conference…", height=80)
                p_submit  = st.form_submit_button("Add Person", type="primary")

            if p_submit and p_name:
                slug = _slugify_name(p_name)
                today = __import__("datetime").date.today().isoformat()
                inst_link = ""
                if p_company:
                    inst_slug = _slugify_name(p_company)
                    inst_link = f"\n**Affiliation:** [[companies/{inst_slug}|{p_company}]]"
                role_line = f"\n**Role:** {p_role}" if p_role else ""

                content = f"""---
title: "{p_name}"
type: person
tags: [contact]
---

## Overview

{p_name}{f' is {p_role}' if p_role else ''}{f' at {p_company}' if p_company else ''}.{inst_link}{role_line}

{p_notes}

<!-- timeline -->

## Timeline

- **{today}** — Added to knowledge graph
"""
                path = os.path.join(PEOPLE_DIR, f"{slug}.md")
                ok, msg = _write_and_import(path, content)
                if ok:
                    st.success(f"✅ Added **{p_name}** as `people/{slug}`")
                else:
                    st.error(f"Failed: {msg}")

        elif pg_mode == "🏢 Add Company":
            with st.form("add_company_form"):
                st.markdown("**Add a company or organization**")
                c_name   = st.text_input("Company Name *", placeholder="Acme Corp")
                c_domain = st.text_input("Domain / Sector", placeholder="AI / SaaS / Fintech")
                c_url    = st.text_input("Website", placeholder="https://acme.com")
                c_notes  = st.text_area("Notes", height=80)
                c_submit = st.form_submit_button("Add Company", type="primary")

            if c_submit and c_name:
                slug  = _slugify_name(c_name)
                today = __import__("datetime").date.today().isoformat()
                url_line = f"\n**Website:** {c_url}" if c_url else ""

                content = f"""---
title: "{c_name}"
type: company
tags: [company]
---

## Overview

{c_name}{f' operates in {c_domain}' if c_domain else ''}.{url_line}

{c_notes}

<!-- timeline -->

## Timeline

- **{today}** — Added to knowledge graph
"""
                path = os.path.join(COMPANIES_DIR, f"{slug}.md")
                ok, msg = _write_and_import(path, content)
                if ok:
                    st.success(f"✅ Added **{c_name}** as `companies/{slug}`")
                else:
                    st.error(f"Failed: {msg}")

        elif pg_mode == "📅 Add Meeting":
            with st.form("add_meeting_form"):
                st.markdown("**Log a meeting**")
                m_date      = st.date_input("Date")
                m_attendees = st.text_input("Attendees (comma-separated)", placeholder="Jane Smith, Bob Lee")
                m_topic     = st.text_input("Topic / Title", placeholder="Product review")
                m_notes     = st.text_area("Notes / Key takeaways", height=100)
                m_submit    = st.form_submit_button("Add Meeting", type="primary")

            if m_submit:
                date_str  = str(m_date)
                slug      = date_str
                attendees = [a.strip() for a in m_attendees.split(",") if a.strip()]
                att_links = "\n".join(
                    f"- [[people/{_slugify_name(a)}|{a}]]" for a in attendees
                ) if attendees else ""

                content = f"""---
title: "Meeting {date_str}{f': {m_topic}' if m_topic else ''}"
type: meeting
tags: [meeting]
date: {date_str}
---

## Overview

{m_topic or 'Meeting'} on {date_str}.

## Attendees

{att_links}

## Notes

{m_notes}

<!-- timeline -->

## Timeline

- **{date_str}** — Meeting took place
"""
                os.makedirs(MEETINGS_DIR, exist_ok=True)
                path = os.path.join(MEETINGS_DIR, f"{slug}.md")
                ok, msg = _write_and_import(path, content)
                if ok:
                    st.success(f"✅ Logged meeting on {date_str}")
                else:
                    st.error(f"Failed: {msg}")

        else:  # Explore
            st.markdown("**Explore connections**")
            col_e1, col_e2 = st.columns([4, 1])
            with col_e1:
                explore_q = st.text_input("", placeholder="Search for a person, company, or paper…",
                                          label_visibility="collapsed", key="explore_input")
            with col_e2:
                explore_go = st.button("Go", type="primary", use_container_width=True)

            if explore_go and explore_q:
                with st.spinner("Searching…"):
                    results = gbrain_search(explore_q, 5)

                if not results:
                    st.warning("No results found.")
                else:
                    # Show results and let user pick one to graph
                    for r in results:
                        cols = st.columns([6, 1])
                        with cols[0]:
                            st.markdown(paper_badge(r["slug"]), unsafe_allow_html=True)
                            st.caption(fix_spaces(r["excerpt"])[:200])
                        with cols[1]:
                            if st.button("Graph", key=f"graph_{r['slug']}"):
                                with st.spinner(f"Loading graph for {r['slug']}…"):
                                    raw_graph, _, _ = run_gbrain(
                                        "graph-query", r["slug"], "--depth", "2", "--direction", "both"
                                    )
                                st.markdown(f"**Graph: `{r['slug']}`**")
                                if raw_graph.strip():
                                    nodes = _parse_graph_tree(raw_graph)
                                    for node in nodes[:50]:
                                        _render_graph_node(node)
                                else:
                                    st.caption("No connections found in graph.")
                        st.divider()

    # ── Who Knows? ──────────────────────────────────────────────────────────
    with g_whoknows:
        st.markdown("**Who in my brain knows about a topic?**")
        st.caption("Ranked by expertise signal, recency, and salience — powered by `gbrain whoknows`")

        col_wk, col_wk_btn = st.columns([5, 1])
        with col_wk:
            wk_topic = st.text_input(
                "", placeholder="e.g. multi-agent systems, reinforcement learning, trading algorithms",
                label_visibility="collapsed", key="whoknows_input",
            )
        with col_wk_btn:
            wk_go = st.button("Find", type="primary", use_container_width=True, key="whoknows_go")

        if wk_go and wk_topic:
            with st.spinner(f"Finding experts on '{wk_topic}'…"):
                wk_raw, wk_err, wk_rc = run_gbrain("whoknows", wk_topic, "--explain", "--json", "--limit", "10")

            if wk_rc != 0 or not wk_raw:
                st.error(f"gbrain whoknows failed (exit {wk_rc})")
                if wk_err:
                    st.code(wk_err[:300])
            else:
                import json as _json
                try:
                    wk_data = _json.loads(wk_raw)
                except Exception:
                    # gbrain might return text before JSON — try extracting
                    m = re.search(r'\[[\s\S]*\]', wk_raw)
                    wk_data = _json.loads(m.group()) if m else []

                if not wk_data:
                    st.info(f"No experts found for '{wk_topic}'. Try a broader topic.")
                else:
                    st.caption(f"Top {len(wk_data)} experts ranked by `log(1 + match) × recency × salience`")
                    for rank, expert in enumerate(wk_data, 1):
                        slug    = expert.get("slug", "")
                        title   = expert.get("title", slug.split("/")[-1].replace("-", " ").title())
                        score   = expert.get("score", 0)
                        factors = expert.get("factors", {})

                        expertise = factors.get("expertise", factors.get("raw_match", 0))
                        recency   = factors.get("recency_decay", 1.0)
                        salience  = factors.get("salience_factor", 0.5)

                        medal = ["🥇", "🥈", "🥉"][rank - 1] if rank <= 3 else f"#{rank}"

                        with st.expander(f"{medal} **{title}** · score {score:.4f}", expanded=(rank <= 3)):
                            col_f1, col_f2, col_f3 = st.columns(3)
                            with col_f1:
                                st.metric("Expertise match", f"{expertise:.3f}")
                                st.progress(min(float(expertise), 1.0))
                            with col_f2:
                                st.metric("Recency", f"{recency:.2f}")
                                st.progress(min(float(recency), 1.0))
                            with col_f3:
                                st.metric("Salience", f"{salience:.2f}")
                                st.progress(min(float(salience), 1.0))

                            st.caption(f"`{slug}`")

                            if st.button("📄 View profile", key=f"wk_profile_{slug}_{rank}"):
                                with st.spinner(f"Loading {title}…"):
                                    profile_raw = gbrain_get(slug)
                                if profile_raw:
                                    st.markdown(profile_raw[:2000])
                                else:
                                    st.caption("No profile content found.")

# ── Tab 5: Minions ────────────────────────────────────────────────────────────
# Groups: name → (log_path, schedule, description)
MINION_GROUPS = {
    "📚 Paper Pipeline": [
        ("👁️ Papers Watcher",  r"C:\brain\papers-watcher.log",     "Every 5 minutes",       "Detects new PDFs in Desktop\\Papers and triggers import + graph wiring immediately"),
        ("🌐 arXiv Download",  r"C:\brain\arxiv-download.log",      "Daily 11:00 AM",        "Downloads new AI/ML papers from arXiv"),
        ("📥 Auto-Import",     r"C:\brain\auto-import.log",         "Daily 11:20 AM",        "Converts PDFs to structured markdown + imports to brain"),
        ("🕸️ Graph Extract",  r"C:\brain\graph-extract.log",        "Daily 11:35 AM",        "Walks all brain pages, resolves [[wikilinks]], writes typed edges into links table — step 5 of the ingestion pipeline"),
        ("🧹 Fix Raw Dumps",   r"C:\brain\fix-raw-dumps.log",       "Daily 11:40 AM",        "Safety net — re-runs Groq on any paper missing structured sections"),
        ("🧬 Auto-Embedder",   r"C:\brain\embed.log",               "Every 30 minutes",      "Generates Voyage AI embeddings for hybrid search"),
        ("🕸️ Research Graph",  r"C:\brain\build-research-graph.log", "Daily 1:45 PM",  "Extracts authors & institutions from PDFs, builds knowledge graph"),
        ("✨ Enrich",           r"C:\brain\enrich-researchers.log",    "Daily 2:15 PM",  "Fills researcher & institution stubs with Groq-generated bios"),
        ("🔬 Research Notes",   r"C:\brain\research-notes.log",        "Daily 2:30 PM",  "Adds Research Context to each paper: what's new, related brain pages, knowledge gaps"),
    ],
    "🧠 Intelligence": [
        ("📋 Daily Brief",     r"C:\brain\daily-brief.log",         "Daily 9:30 AM",         "AI-generated summary of recent papers and brain activity"),
        ("📰 Weekly Digest",   r"C:\brain\weekly-digest.log",       "Friday 3:00 PM",        "Weekly synthesis of key themes and findings"),
        ("📄 New Papers",      r"C:\brain\new-papers-alert.log",    "Daily 11:00 AM",        "Alerts when new papers are imported"),
        ("🔬 Daily Synthesis",  r"C:\brain\subagent-daily-synthesis.log", "Daily 3:00 PM",  "Reads recent papers, finds cross-paper themes and connections, writes synthesis to wiki/synthesis/{date}"),
    ],
    "🛠️ Maintenance": [
        ("🗄️ Brain Backup",   r"C:\brain\backups\backup.log",       "Daily 11:00 AM & 4 PM", "Snapshots the full brain database"),
        ("🧹 Log Cleaner",    r"C:\brain\clean-logs.log",           "Wednesday 11:00 AM",    "Trims old log files to prevent disk bloat"),
        ("✂️ Backup Pruner",  r"C:\brain\prune-backups.log",        "Wednesday 11:00 AM",    "Removes old backup snapshots beyond retention window"),
        ("📡 Streamlit Ping", r"C:\brain\streamlit-status.log",     "Every hour",            "Health-checks the Streamlit app and restarts if down"),
        ("🌙 Dream Cycle",    r"C:\brain\dream-cycle.log",          "On demand",             "extract → embed → backlinks → lint → orphans"),
    ],
}

DREAM_CYCLE_LOG = r"C:\brain\dream-cycle.log"
DREAM_CYCLE_BAT = r"C:\brain\dream-cycle.bat"

def read_log(path, tail=50):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return lines[-tail:] if len(lines) > tail else lines
    except FileNotFoundError:
        return None

def log_line_color(line):
    l = line.upper()
    if "FAILED" in l or "DOWN" in l or "ERROR" in l:
        return "#fee2e2", "#991b1b"
    if "RESTARTED" in l or "NEW:" in l or "OK" in l:
        return "#f0fdf4", "#166534"
    return "#f8fafc", "#334155"

def _minion_status_badge(lines):
    """Return an HTML status badge based on the last log line."""
    if lines is None:
        return '<span style="background:#f1f5f9;color:#94a3b8;font-size:10px;padding:1px 7px;border-radius:99px">never run</span>'
    if not lines:
        return '<span style="background:#f1f5f9;color:#94a3b8;font-size:10px;padding:1px 7px;border-radius:99px">empty</span>'
    last = ""
    for l in reversed(lines):
        if l.strip():
            last = l.strip().upper()
            break
    if "FAILED" in last or "ERROR" in last or "DOWN" in last:
        return '<span style="background:#fee2e2;color:#991b1b;font-size:10px;padding:1px 7px;border-radius:99px">● failed</span>'
    if "OK" in last or "FINISHED" in last or "DONE" in last or "UP" in last:
        return '<span style="background:#dcfce7;color:#166534;font-size:10px;padding:1px 7px;border-radius:99px">● ok</span>'
    return '<span style="background:#fef9c3;color:#854d0e;font-size:10px;padding:1px 7px;border-radius:99px">● running</span>'

def _render_minion_log(lines):
    if lines is None:
        st.caption("No log yet — minion hasn't run.")
        return
    if not lines:
        st.caption("Log is empty.")
        return
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        bg, fg = log_line_color(line)
        st.markdown(
            f'<div style="background:{bg};color:{fg};font-family:monospace;'
            f'font-size:12px;padding:3px 8px;border-radius:4px;margin:1px 0">'
            f'{line}</div>',
            unsafe_allow_html=True,
        )

GROUP_COLORS = {
    "📚 Paper Pipeline": ("#eff6ff", "#1d4ed8", "#bfdbfe"),
    "🧠 Intelligence":   ("#fdf4ff", "#7e22ce", "#e9d5ff"),
    "🛠️ Maintenance":    ("#f0fdf4", "#15803d", "#bbf7d0"),
}

def _last_dream_run() -> str:
    """Return a short string describing when the dream cycle last ran."""
    try:
        lines = [l.strip() for l in open(DREAM_CYCLE_LOG, encoding="utf-8", errors="replace").readlines() if l.strip()]
        for line in reversed(lines):
            if "Dream Cycle finished" in line or "Dream Cycle started" in line:
                # Extract timestamp from [YYYY-MM-DD HH:MM:SS]
                m = re.search(r"\[(\d{2}-\d{2}-\d{4} \d{2}:\d{2})", line)
                if m:
                    status = "✅ finished" if "finished" in line else "🔄 started"
                    return f"{status} · {m.group(1)}"
        return "never run"
    except FileNotFoundError:
        return "never run"

with tab_logs:
    # ── Dream Cycle hero ───────────────────────────────────────────────────────
    last_run = _last_dream_run()
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#1e1b4b 0%,#312e81 100%);'
        f'border-radius:12px;padding:18px 24px;margin-bottom:18px;'
        f'display:flex;justify-content:space-between;align-items:center">'
        f'<div>'
        f'<div style="color:white;font-size:16px;font-weight:700">🌙 Dream Cycle</div>'
        f'<div style="color:#a5b4fc;font-size:12px;margin-top:2px">'
        f'extract → embed → backlinks → lint → orphans</div>'
        f'<div style="color:#6366f1;font-size:11px;margin-top:4px">Last run: {last_run}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Sync + Embed controls ─────────────────────────────────────────────────
    st.divider()
    col_maint1, col_maint2 = st.columns(2)

    with col_maint1:
        st.markdown("**🔄 Sync Brain**")
        st.caption("Resumable — picks up where it left off if interrupted")
        sync_source = st.text_input("Source ID (leave blank for all)", value="", key="sync_source",
                                    placeholder="e.g. wiki")
        if st.button("Run Sync", key="sync_go", use_container_width=True):
            with st.spinner("Syncing brain…"):
                sync_args = ["sync"]
                if sync_source.strip():
                    sync_args += ["--source", sync_source.strip()]
                s_raw, s_err, s_rc = run_gbrain(*sync_args, timeout=300)
            if s_rc == 0:
                st.success("✅ Sync complete")
                if s_raw:
                    st.code(s_raw[-1000:], language=None)
            else:
                st.error(f"Sync failed (exit {s_rc})")
                if s_err:
                    st.code(s_err[:400])

    with col_maint2:
        st.markdown("**⚡ Embed Stale Pages**")
        st.caption("Pacing throttles DB load during large backfills")
        pace_mode = st.selectbox("Pace mode", ["off", "gentle", "balanced", "aggressive"],
                                  index=0, key="pace_mode")
        if st.button("Run Embed", key="embed_go", use_container_width=True):
            with st.spinner("Embedding stale pages…"):
                embed_args = ["embed", "--stale"]
                if pace_mode != "off":
                    embed_args += [f"--pace={pace_mode}"]
                e_raw, e_err, e_rc = run_gbrain(*embed_args, timeout=300)
            if e_rc == 0:
                st.success("✅ Embed complete")
                if e_raw:
                    st.code(e_raw[-500:], language=None)
            else:
                st.error(f"Embed failed (exit {e_rc})")
                if e_err:
                    st.code(e_err[:400])

    st.divider()

    if st.button("▶ Run Dream Cycle", type="primary", use_container_width=False):
        log_area   = st.empty()
        status_box = st.empty()

        status_box.info("🌙 Dream Cycle running… this takes 2–5 minutes")

        # The bat writes all output to the log file (not stdout).
        # We run it detached and then tail the log file for live updates.
        import time as _time

        # Record how many lines the log already had before we started
        _pre_lines = 0
        if os.path.exists(DREAM_CYCLE_LOG):
            with open(DREAM_CYCLE_LOG, encoding="utf-8", errors="replace") as _lf:
                _pre_lines = sum(1 for _ in _lf)

        proc = subprocess.Popen(
            ["cmd.exe", "/c", DREAM_CYCLE_BAT],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=ENV,
        )

        # Poll the log file for new lines while the process is running
        while proc.poll() is None:
            _time.sleep(1)
            if os.path.exists(DREAM_CYCLE_LOG):
                with open(DREAM_CYCLE_LOG, encoding="utf-8", errors="replace") as _lf:
                    all_lines = _lf.readlines()
                new_lines = [l.rstrip() for l in all_lines[_pre_lines:] if l.strip()]
                if new_lines:
                    log_area.code("\n".join(new_lines[-40:]), language=None)

        proc.wait()

        # Show final log output
        if os.path.exists(DREAM_CYCLE_LOG):
            with open(DREAM_CYCLE_LOG, encoding="utf-8", errors="replace") as _lf:
                all_lines = _lf.readlines()
            new_lines = [l.rstrip() for l in all_lines[_pre_lines:] if l.strip()]
            if new_lines:
                log_area.code("\n".join(new_lines), language=None)

        if proc.returncode == 0:
            status_box.success("✅ Dream Cycle complete")
        else:
            status_box.error(f"Dream Cycle finished with warnings (exit {proc.returncode})")

    st.divider()

    # ── Subagent Jobs (gbrain job queue) ───────────────────────────────────────
    _STATUS_COLORS = {
        "completed": ("#dcfce7", "#166534"),
        "dead":      ("#fee2e2", "#991b1b"),
        "failed":    ("#fee2e2", "#991b1b"),
        "active":    ("#dbeafe", "#1d4ed8"),
        "waiting":   ("#fef9c3", "#854d0e"),
        "stalled":   ("#ffedd5", "#9a3412"),
    }

    def _job_status_badge(status: str) -> str:
        bg, fg = _STATUS_COLORS.get(status, ("#f1f5f9", "#64748b"))
        icons = {"completed": "✅", "dead": "💀", "failed": "❌", "active": "🔄", "waiting": "⏳", "stalled": "⚠️"}
        icon = icons.get(status, "•")
        return (
            f'<span style="background:{bg};color:{fg};font-size:10px;'
            f'padding:2px 8px;border-radius:99px;font-weight:600">{icon} {status}</span>'
        )

    with st.expander("🤖 What did my subagent do?", expanded=False):
        if st.button("🔄 Refresh jobs", key="refresh_jobs"):
            st.rerun()

        _jobs_raw, _jobs_err, _jobs_rc = run_gbrain("jobs", "list", "--limit", "50", timeout=20)
        _today_str = __import__("datetime").date.today().isoformat()

        if _jobs_rc != 0 or not _jobs_raw.strip():
            st.caption("No subagent jobs found.")
            if _jobs_err:
                st.code(_jobs_err[:300], language=None)
        else:
            _job_rows = []
            for _line in _jobs_raw.splitlines():
                _line = _line.strip()
                if not _line or _line.startswith("ID") or _line.startswith("─") or _line.startswith("-"):
                    continue
                _parts = _line.split()
                if len(_parts) >= 3 and _parts[0].isdigit() and _parts[1] == "subagent":
                    _job_rows.append({
                        "id":     _parts[0],
                        "name":   _parts[1],
                        "status": _parts[2],
                        "queue":  _parts[3] if len(_parts) > 3 else "default",
                        "extra":  " ".join(_parts[4:]) if len(_parts) > 4 else "",
                    })

            @st.cache_data(ttl=300, show_spinner=False)
            def _get_job_info(job_id: str) -> tuple:
                """Return (prompt, result_first_line, last_error) from `gbrain jobs get <id>`. Cached 5 min."""
                _raw, _, _rc = run_gbrain("jobs", "get", job_id, timeout=15)
                _prompt, _result, _last_error = "", "", ""
                if _rc != 0:
                    return _prompt, _result, _last_error
                for _ln in _raw.splitlines():
                    _ln = _ln.strip()
                    if _ln.startswith("Data:"):
                        try:
                            _d = json.loads(_ln[5:].strip())
                            _prompt = _d.get("prompt", "")
                        except Exception:
                            pass
                    if _ln.startswith("Result:"):
                        try:
                            _r = json.loads(_ln[7:].strip())
                            for _rl in _r.get("result", "").splitlines():
                                _rl = re.sub(r"[#*`\[\]→—]", "", _rl).strip()
                                if _rl and len(_rl) > 5:
                                    _result = _rl
                                    break
                        except Exception:
                            pass
                    if _ln.startswith("Last Error:") or _ln.startswith("Error:"):
                        _last_error = _ln.split(":", 1)[-1].strip()[:400]
                    # Also try to parse JSON error fields
                    if _ln.startswith("{") and not _last_error:
                        try:
                            _obj = json.loads(_ln)
                            _last_error = (_obj.get("last_error") or _obj.get("error") or "")[:400]
                        except Exception:
                            pass
                return _prompt, _result, _last_error

            if not _job_rows:
                st.caption("No jobs in the queue yet.")
            else:
                # ── Summary counts ──────────────────────────────────────────
                _cnt = {s: 0 for s in ("completed", "active", "dead", "failed", "waiting", "stalled")}
                for _j in _job_rows:
                    _cnt[_j["status"]] = _cnt.get(_j["status"], 0) + 1

                _sum_cols = st.columns(len([s for s, n in _cnt.items() if n > 0]))
                _sum_i = 0
                for _s, _n in _cnt.items():
                    if _n == 0:
                        continue
                    _bg, _fg = _STATUS_COLORS.get(_s, ("#f1f5f9", "#64748b"))
                    _ic = {"completed": "✅", "dead": "💀", "failed": "❌", "active": "🔄", "waiting": "⏳", "stalled": "⚠️"}.get(_s, "•")
                    _sum_cols[_sum_i].markdown(
                        f'<div style="background:{_bg};border-radius:8px;padding:8px 12px;text-align:center">'
                        f'<div style="font-size:20px;font-weight:700;color:{_fg}">{_n}</div>'
                        f'<div style="font-size:11px;color:{_fg}">{_ic} {_s}</div></div>',
                        unsafe_allow_html=True,
                    )
                    _sum_i += 1

                st.divider()

                for _job in _job_rows:
                    _jid    = _job["id"]
                    _jstat  = _job["status"]
                    _badge  = _job_status_badge(_jstat)

                    # Extract synthesis date from prompt ("Today is YYYY-MM-DD")
                    _prompt, _result, _last_error = _get_job_info(_jid)
                    _synth_date = ""
                    _dm = re.search(r"Today is (\d{4}-\d{2}-\d{2})", _prompt)
                    if _dm:
                        _synth_date = _dm.group(1)

                    # Detect stalled: active but synthesis date is before today
                    _is_stalled = _jstat == "active" and _synth_date and _synth_date < _today_str

                    # Build label
                    if _synth_date:
                        _label = f"#{_jid} · Synthesis {_synth_date} · {'⚠️ stalled' if _is_stalled else _jstat}"
                    else:
                        _label = f"#{_jid} · {_jstat}"

                    with st.expander(_label, expanded=False):
                        st.markdown(_badge, unsafe_allow_html=True)

                        # ── Stalled warning ──────────────────────────────
                        if _is_stalled:
                            st.warning(
                                f"⚠️ This job has been **active since {_synth_date}** but never completed. "
                                f"The gbrain worker likely crashed mid-run. "
                                f"The synthesis note for {_synth_date} was **never written** to the brain."
                            )
                            if st.button(f"🗑️ Cancel job #{_jid}", key=f"cancel_{_jid}"):
                                with st.spinner(f"Cancelling job {_jid}…"):
                                    _c_raw, _c_err, _c_rc = run_gbrain("jobs", "cancel", _jid, timeout=15)
                                if _c_rc == 0:
                                    st.success(f"Job #{_jid} cancelled.")
                                    st.rerun()
                                else:
                                    st.error(f"Cancel failed: {_c_err[:200]}")

                        # ── Completed: show synthesis page if it exists ───
                        elif _jstat == "completed" and _synth_date:
                            _synth_slug = f"wiki/synthesis/{_synth_date}"
                            _synth_content = gbrain_get(_synth_slug)
                            if _synth_content:
                                st.success(f"✅ Synthesis written → `{_synth_slug}`")
                                with st.expander("📄 View synthesis", expanded=False):
                                    st.markdown(_synth_content[:3000])
                            else:
                                st.info(f"Job completed but `{_synth_slug}` not found in brain — agent may have used a different slug.")
                                if _result:
                                    st.markdown(
                                        f'<div style="background:#f0fdf4;border-left:3px solid #22c55e;'
                                        f'padding:10px 14px;border-radius:0 6px 6px 0;margin:8px 0 12px 0">'
                                        f'<div style="color:#166534;font-size:10px;font-weight:600;margin-bottom:4px">WHAT IT DID</div>'
                                        f'<div style="color:#1e293b;font-size:13px">{_result[:400]}</div>'
                                        f'</div>',
                                        unsafe_allow_html=True,
                                    )

                        # ── Waiting: not yet picked up ────────────────────
                        elif _jstat == "waiting":
                            st.info("⏳ Job is queued — waiting for the gbrain worker to pick it up.")

                        # ── Dead: exhausted all retries ────────────────────
                        elif _jstat in ("dead", "failed"):
                            _date_str = f" for **{_synth_date}**" if _synth_date else ""
                            st.error(
                                f"💀 This job failed and was not retried successfully. "
                                f"The synthesis note{_date_str} was **never written** to the brain."
                            )
                            if _last_error:
                                st.markdown(
                                    f'<div style="background:#fef2f2;border-left:3px solid #ef4444;'
                                    f'padding:10px 14px;border-radius:0 6px 6px 0;margin:8px 0 12px 0">'
                                    f'<div style="color:#991b1b;font-size:10px;font-weight:600;margin-bottom:4px">LAST ERROR</div>'
                                    f'<div style="color:#1e293b;font-size:12px;font-family:monospace;white-space:pre-wrap">{_last_error}</div>'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.caption("No error details available — check logs below for more info.")
                            _retry_col, _del_col = st.columns(2)
                            with _retry_col:
                                if st.button(f"🔁 Retry job #{_jid}", key=f"retry_{_jid}"):
                                    with st.spinner(f"Retrying job {_jid}…"):
                                        _r_raw, _r_err, _r_rc = run_gbrain("jobs", "retry", _jid, timeout=20)
                                    if _r_rc == 0:
                                        st.success(f"Job #{_jid} re-queued — worker will pick it up shortly.")
                                        st.cache_data.clear()
                                        st.rerun()
                                    else:
                                        st.error(f"Retry failed: {(_r_err or _r_raw)[:200]}")
                            with _del_col:
                                if st.button(f"🗑️ Delete job #{_jid}", key=f"delete_dead_{_jid}"):
                                    with st.spinner(f"Deleting job {_jid}…"):
                                        _d_raw, _d_err, _d_rc = run_gbrain("jobs", "delete", _jid, timeout=15)
                                    if _d_rc == 0:
                                        st.success(f"Job #{_jid} deleted.")
                                        st.cache_data.clear()
                                        st.rerun()
                                    else:
                                        st.error(f"Delete failed: {(_d_err or _d_raw)[:200]}")

                        # ── Load logs button ──────────────────────────────
                        if st.button("📜 Load logs", key=f"job_logs_{_jid}"):
                            with st.spinner(f"Loading logs for job {_jid}…"):
                                _log_raw, _log_err, _log_rc = run_gbrain("agent", "logs", _jid, timeout=30)
                            if _log_rc != 0 or not _log_raw.strip():
                                st.warning(f"No logs available (exit {_log_rc})")
                                if _log_err:
                                    st.code(_log_err[:400], language=None)
                            else:
                                st.code(_log_raw[:6000], language="markdown")

    st.divider()

    col_hd, col_rf = st.columns([5, 1])
    with col_hd:
        st.caption("All minions grouped by function — most recent log entry first")
    with col_rf:
        if st.button("🔄 Refresh", key="refresh_logs"):
            st.cache_data.clear()
            st.rerun()

    for group_name, minions in MINION_GROUPS.items():
        bg, fg, border = GROUP_COLORS.get(group_name, ("#f8fafc", "#374151", "#e2e8f0"))
        st.markdown(
            f'<div style="background:{bg};border:1px solid {border};border-radius:8px;'
            f'padding:6px 14px;margin:16px 0 6px 0">'
            f'<span style="color:{fg};font-weight:700;font-size:14px">{group_name}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        for name, log_path, schedule, description in minions:
            lines = read_log(log_path)
            badge = _minion_status_badge(lines)
            with st.expander(f"{name}  ·  {schedule}", expanded=False):
                # Show status badge + description at top of expander body
                st.markdown(
                    f'{badge} <span style="color:#94a3b8;font-size:12px">{description}</span>',
                    unsafe_allow_html=True,
                )
                _render_minion_log(lines)

# ── Tab 5: Brief ──────────────────────────────────────────────────────────────
BRIEFS_DIR  = r"C:\brain\briefs"
DIGESTS_DIR = r"C:\brain\digests"
ALERTS_DIR  = r"C:\brain\alerts"

def list_files(folder):
    try:
        return sorted([f for f in os.listdir(folder) if f.endswith(".md")], reverse=True)
    except FileNotFoundError:
        return []

def read_md_file(folder, filename):
    try:
        with open(os.path.join(folder, filename), "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None

def render_brief_content(content, accent="#7c3aed"):
    body = re.sub(r"^#[^\n]*\n+", "", content).strip()
    sections = re.split(r"(##[^\n]+)", body)
    for part in sections:
        part = part.strip()
        if not part:
            continue
        if part.startswith("##"):
            st.markdown(f"### {part.lstrip('#').strip()}")
        elif part.startswith("---"):
            st.caption(part.lstrip("-").strip())
        else:
            st.markdown(
                f'<div style="background:#f8fafc;border-left:3px solid {accent};'
                f'padding:12px 16px;border-radius:0 6px 6px 0;margin:4px 0 16px 0;'
                f'font-size:14px;color:#1e293b;line-height:1.75">{part}</div>',
                unsafe_allow_html=True,
            )

with tab_brief:
    kind = st.radio("", ["📋 Daily Brief", "📰 Weekly Digest", "🔔 Alerts"], horizontal=True, label_visibility="collapsed")
    st.divider()

    if kind == "🔔 Alerts":
        alerts = list_files(ALERTS_DIR)
        col_r = st.columns([5, 1])
        with col_r[1]:
            if st.button("🔄 Refresh", key="refresh_alerts"):
                st.rerun()
        if not alerts:
            st.info("No alerts yet — drop a PDF into `C:\\brain\\papers\\` to trigger the pipeline.")
        else:
            st.caption(f"{len(alerts)} alert(s) · most recent first")
            for alert_file in alerts:
                content = read_md_file(ALERTS_DIR, alert_file)
                if not content:
                    continue
                # Parse title and summary from the alert markdown
                title_match = re.search(r"^# (.+)$", content, re.M)
                date_match  = re.search(r"\*Imported: (.+?)\*", content)
                summary_match = re.search(r"## Summary\s+(.+?)(?=\n---|\Z)", content, re.S)
                title   = title_match.group(1).replace("New Paper Imported — ", "") if title_match else alert_file
                date    = date_match.group(1) if date_match else ""
                summary = summary_match.group(1).strip() if summary_match else ""
                summary_html = summary.replace("**What it is:**", "<b>What it is:</b>") \
                                      .replace("**Key contribution:**", "<b>Key contribution:</b>") \
                                      .replace("**Main finding:**", "<b>Main finding:</b>") \
                                      .replace("\n", "<br>")
                st.markdown(
                    f'<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;'
                    f'padding:14px 18px;margin-bottom:12px">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">'
                    f'<span style="font-weight:700;font-size:15px;color:#14532d">📄 {title}</span>'
                    f'<span style="font-size:11px;color:#6b7280">{date}</span></div>'
                    f'<div style="font-size:13px;color:#166534;line-height:1.7">{summary_html}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
    else:
        if kind == "📋 Daily Brief":
            folder, accent, bat = BRIEFS_DIR, "#7c3aed", "daily-brief.bat"
            schedule_hint = "Daily at 9:30 AM"
        else:
            folder, accent, bat = DIGESTS_DIR, "#0369a1", "weekly-digest.bat"
            schedule_hint = "Every Friday at 3:00 PM"

        files = list_files(folder)

        if not files:
            st.info(f"No {kind.split()[1].lower()}s yet — runs {schedule_hint}.")
            st.caption(f"Run `C:\\brain\\{bat}` manually to generate one now.")
        else:
            col_sel, col_ref = st.columns([4, 1])
            with col_sel:
                chosen = st.selectbox("", options=files, format_func=lambda f: f.replace(".md", ""), label_visibility="collapsed")
            with col_ref:
                if st.button("🔄 Refresh", key="refresh_brief"):
                    st.rerun()

            content = read_md_file(folder, chosen)
            if content:
                render_brief_content(content, accent=accent)

# ── Tab 7: Capture ────────────────────────────────────────────────────────────
import hashlib as _hashlib
import datetime as _datetime

with tab_capture:
    st.markdown("**Quick Capture** — get a thought into your brain without a PDF")
    st.caption("Writes to `inbox/` then `gbrain import` · auto-generates a slug from the date + content hash")

    with st.form("capture_form"):
        cap_type = st.selectbox(
            "Type",
            ["note", "idea", "observation", "question", "insight", "hypothesis"],
            index=0,
        )
        cap_title = st.text_input("Title (optional)", placeholder="Leave blank to auto-generate from content")
        cap_tags  = st.text_input("Tags (comma-separated)", placeholder="ai, agents, ideas")
        cap_body  = st.text_area(
            "Content *",
            placeholder="Write your thought here…\n\nYou can use [[wikilinks]] to reference brain pages.",
            height=180,
        )
        cap_submit = st.form_submit_button("📥 Capture to Brain", type="primary")

    if cap_submit:
        if not cap_body.strip():
            st.error("Content is required.")
        else:
            today       = _datetime.date.today().isoformat()
            body_hash   = _hashlib.md5(cap_body.encode()).hexdigest()[:8]
            slug        = f"inbox/{today}-{body_hash}"
            title_str   = cap_title.strip() if cap_title.strip() else f"{cap_type.title()} — {today}"
            tags_list   = [t.strip() for t in cap_tags.split(",") if t.strip()]
            tags_yaml   = "[" + ", ".join(tags_list) + "]" if tags_list else f"[{cap_type}]"

            md_content = f"""---
title: "{title_str}"
type: {cap_type}
tags: {tags_yaml}
date: {today}
---

{cap_body.strip()}

<!-- timeline -->

## Timeline

- **{today}** — Captured via Quick Capture
"""
            # Write file to disk then import (gbrain put reads /dev/stdin which
            # doesn't exist on Windows — use the same write+import pattern as
            # the personal graph forms)
            inbox_dir  = os.path.join(EXTRACTED_DIR, "inbox")
            os.makedirs(inbox_dir, exist_ok=True)
            file_name  = f"{today}-{body_hash}.md"
            file_path  = os.path.join(inbox_dir, file_name)

            with st.spinner("Writing to brain…"):
                with open(file_path, "w", encoding="utf-8") as _cf:
                    _cf.write(md_content)
                _, err, rc = run_gbrain("import", "--file", file_path, "--no-embed")

            if rc == 0:
                st.success(f"✅ Captured as `{slug}`")
                st.code(f"gbrain get {slug}", language=None)
            else:
                st.error(f"Failed to capture (exit {rc})")
                if err:
                    st.code(err[:400])

    st.divider()
    st.markdown("**Recent captures**")

    _inbox_dir   = os.path.join(EXTRACTED_DIR, "inbox")
    _inbox_files = []
    if os.path.isdir(_inbox_dir):
        _inbox_files = sorted(
            [f for f in os.listdir(_inbox_dir) if f.endswith(".md")],
            reverse=True,
        )[:10]

    if not _inbox_files:
        st.caption("No inbox captures yet — write something above!")
    else:
        for _ifile in _inbox_files:
            _ipath  = os.path.join(_inbox_dir, _ifile)
            _ititle = _ifile[:-3]
            _idate  = ""
            _ibody  = ""
            _ifull  = ""
            _itype  = "note"
            _itags  = ""
            try:
                with open(_ipath, encoding="utf-8", errors="replace") as _if:
                    _ifull  = _if.read()
                    _lines  = _ifull.splitlines()
                for _l in _lines:
                    _ls = _l.strip()
                    if _ls.startswith("title:"):
                        _ititle = _ls[6:].strip().strip('"').strip("'")
                    elif _ls.startswith("date:"):
                        _idate  = _ls[5:].strip()
                    elif _ls.startswith("type:"):
                        _itype  = _ls[5:].strip()
                    elif _ls.startswith("tags:"):
                        _itags  = _ls[5:].strip().strip("[]")
                # first non-frontmatter content line as preview
                _in_fm = False
                for _l in _lines:
                    _ls = _l.strip()
                    if _ls == "---":
                        _in_fm = not _in_fm
                        continue
                    if not _in_fm and _ls and not _ls.startswith("#") and not _ls.startswith("<!--"):
                        _ibody = _ls[:120]
                        break
            except Exception:
                pass

            _slug_short = f"inbox/{_ifile[:-3]}"
            with st.expander(f"✏️ **{_ititle}** · {_idate}", expanded=False):
                # metadata row
                col_m1, col_m2, col_m3 = st.columns([2, 2, 3])
                col_m1.caption(f"**Type:** {_itype}")
                col_m2.caption(f"**Date:** {_idate}")
                col_m3.caption(f"**Tags:** {_itags}" if _itags else "")

                # full body (strip frontmatter)
                _body_only = re.sub(r"^---[\s\S]*?---\s*", "", _ifull).strip()
                # remove timeline boilerplate
                _body_only = re.sub(r"<!--\s*timeline\s*-->[\s\S]*", "", _body_only).strip()

                if _body_only:
                    st.markdown(
                        f'<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;'
                        f'padding:14px 18px;font-size:14px;line-height:1.75;color:#14532d;'
                        f'white-space:pre-wrap">{_body_only}</div>',
                        unsafe_allow_html=True,
                    )

                st.caption(f"`{_slug_short}` · {_ipath}")

# ── Tab 8: Brain Intel ────────────────────────────────────────────────────────
with tab_intel:
    intel_anomalies, intel_salience, intel_health, intel_advisor, intel_watch = st.tabs([
        "⚡ Anomalies", "🔥 Hot Pages", "🏥 Health", "🧠 Advisor", "🔭 Watch"
    ])

    # ── Anomalies ─────────────────────────────────────────────────────────────
    with intel_anomalies:
        st.markdown("**Activity anomalies** — cohorts with statistically unusual page activity")
        st.caption("Uses `gbrain anomalies` · flags tag/type cohorts where today's count exceeds the baseline by N sigma")

        col_an1, col_an2, col_an3 = st.columns([2, 2, 1])
        with col_an1:
            an_days = st.slider("Lookback days", 7, 90, 30, key="an_days")
        with col_an2:
            an_sigma = st.slider("Min sigma threshold", 1.0, 4.0, 1.5, step=0.5, key="an_sigma")
        with col_an3:
            an_go = st.button("Scan", type="primary", use_container_width=True, key="an_go")

        if an_go:
            with st.spinner("Scanning for anomalies…"):
                an_raw, an_err, an_rc = run_gbrain(
                    "anomalies",
                    "--lookback-days", str(an_days),
                    "--sigma", str(an_sigma),
                    "--json",
                    timeout=60,
                )
            if an_rc != 0 or not an_raw:
                st.error(f"gbrain anomalies failed (exit {an_rc})")
                if an_err:
                    st.code(an_err[:400])
            else:
                try:
                    an_data = json.loads(an_raw)
                except Exception:
                    m = re.search(r'\[[\s\S]*\]', an_raw)
                    an_data = json.loads(m.group()) if m else []

                if not an_data:
                    st.success(f"✅ No anomalies detected above {an_sigma}σ in the last {an_days} days — brain activity is normal.")
                else:
                    st.warning(f"⚡ {len(an_data)} anomalous cohort(s) detected")
                    for a in an_data:
                        cohort  = a.get("cohort", "?")
                        kind    = a.get("kind", "")
                        sigma   = a.get("sigma_observed", 0)
                        count   = a.get("count", 0)
                        mean    = a.get("mean", 0)
                        stddev  = a.get("stddev", 0)
                        slugs   = a.get("page_slugs", [])

                        sigma_color = "#dc2626" if sigma >= 3 else "#d97706" if sigma >= 2 else "#ca8a04"
                        with st.expander(
                            f"**{cohort}** · σ={sigma:.2f} · count={count} (baseline {mean:.1f}±{stddev:.1f})",
                            expanded=True,
                        ):
                            st.markdown(
                                f'<span style="background:{sigma_color};color:white;font-size:11px;'
                                f'padding:2px 8px;border-radius:99px;font-weight:700">'
                                f'{kind} · {sigma:.2f}σ above baseline</span>',
                                unsafe_allow_html=True,
                            )
                            if slugs:
                                st.markdown("**Pages in this cohort:**")
                                for s in slugs[:20]:
                                    st.markdown(
                                        f'<code style="font-size:12px;background:#f8fafc;'
                                        f'padding:1px 6px;border-radius:4px">{s}</code>',
                                        unsafe_allow_html=True,
                                    )

    # ── Salience / Hot Pages ──────────────────────────────────────────────────
    with intel_salience:
        st.markdown("**Hot Pages** — what matters most in your brain right now")
        st.caption(
            "Ranked by `gbrain salience` · score = `(emotional_weight × 5) + ln(1 + takes) + 1/(1 + days_since_update)`"
        )

        col_sl1, col_sl2, col_sl3 = st.columns([2, 2, 1])
        with col_sl1:
            sl_days  = st.slider("Recency window (days)", 7, 90, 30, key="sl_days")
        with col_sl2:
            sl_limit = st.slider("Top N pages", 5, 50, 20, key="sl_limit")
        with col_sl3:
            sl_go = st.button("Rank", type="primary", use_container_width=True, key="sl_go")

        if sl_go:
            with st.spinner("Computing salience scores…"):
                sl_raw, sl_err, sl_rc = run_gbrain(
                    "salience",
                    "--days",  str(sl_days),
                    "--limit", str(sl_limit),
                    "--json",
                    timeout=60,
                )
            if sl_rc != 0 or not sl_raw:
                st.error(f"gbrain salience failed (exit {sl_rc})")
                if sl_err:
                    st.code(sl_err[:400])
            else:
                try:
                    sl_data = json.loads(sl_raw)
                except Exception:
                    m = re.search(r'\[[\s\S]*\]', sl_raw)
                    sl_data = json.loads(m.group()) if m else []

                if not sl_data:
                    st.info("No pages returned — try widening the recency window.")
                else:
                    st.caption(f"Top {len(sl_data)} pages by salience over the last {sl_days} days")
                    max_score = max((p.get("score", 0) for p in sl_data), default=1) or 1
                    for rank, page in enumerate(sl_data, 1):
                        slug         = page.get("slug", "")
                        title        = page.get("title") or slug.split("/")[-1].replace("-", " ").title()
                        score        = page.get("score", 0)
                        emo          = page.get("emotional_weight", 0)
                        takes        = page.get("active_take_count", page.get("take_count", 0))
                        days_ago     = page.get("days_since_update", 0)
                        bar_pct      = int(score / max_score * 100)

                        heat = "🔴" if rank <= 3 else "🟠" if rank <= 7 else "🟡" if rank <= 12 else "⚪"
                        st.markdown(
                            f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;'
                            f'padding:10px 14px;margin:4px 0">'
                            f'<div style="display:flex;justify-content:space-between;align-items:center">'
                            f'<span style="font-weight:600;font-size:14px">{heat} #{rank} {title}</span>'
                            f'<span style="font-size:11px;color:#64748b;font-family:monospace">'
                            f'score {score:.3f}</span></div>'
                            f'<div style="background:#e2e8f0;border-radius:4px;height:4px;margin:6px 0">'
                            f'<div style="background:#f59e0b;height:4px;border-radius:4px;width:{bar_pct}%"></div>'
                            f'</div>'
                            f'<div style="font-size:11px;color:#64748b">'
                            f'<code>{slug}</code> · '
                            f'emo {emo:.2f} · takes {takes} · updated {days_ago}d ago'
                            f'</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

    # ── Brain Health ──────────────────────────────────────────────────────────
    with intel_health:
        st.markdown("**Brain Health** — full diagnostic report")
        st.caption("Uses `gbrain doctor --json --fast` · checks embed coverage, link density, sync freshness, graph coverage, and more")

        col_h1, col_h2 = st.columns([3, 1])
        with col_h2:
            h_go = st.button("Run Diagnostics", type="primary", use_container_width=True, key="h_go")

        if h_go:
            with st.spinner("Running gbrain doctor…"):
                h_raw, h_err, h_rc = run_gbrain("doctor", "--json", "--fast", timeout=120)

            if h_rc not in (0, 1) or not h_raw:
                st.error(f"gbrain doctor failed (exit {h_rc})")
                if h_err:
                    st.code(h_err[:400])
            else:
                try:
                    h_data = json.loads(h_raw)
                except Exception:
                    m = re.search(r'\{[\s\S]*\}', h_raw)
                    h_data = json.loads(m.group()) if m else {}

                health_score = h_data.get("health_score", h_data.get("score", None))
                checks       = h_data.get("checks", [])
                overall_ok   = h_data.get("ok", None)

                # ── Score hero ────────────────────────────────────────────
                if health_score is not None:
                    score_int = int(health_score)
                    score_color = "#16a34a" if score_int >= 90 else "#d97706" if score_int >= 70 else "#dc2626"
                    score_label = "Excellent" if score_int >= 90 else "Good" if score_int >= 70 else "Needs attention"
                    st.markdown(
                        f'<div style="background:linear-gradient(135deg,#0f172a,#1e293b);'
                        f'border-radius:12px;padding:20px 28px;margin-bottom:20px;'
                        f'display:flex;align-items:center;gap:24px">'
                        f'<div style="font-size:52px;font-weight:900;color:{score_color};'
                        f'font-family:monospace;line-height:1">{score_int}</div>'
                        f'<div>'
                        f'<div style="color:white;font-size:18px;font-weight:700">Brain Health Score</div>'
                        f'<div style="color:{score_color};font-size:14px;margin-top:2px">{score_label}</div>'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                # ── Check results ────────────────────────────────────────
                if checks:
                    status_order = {"fail": 0, "warn": 1, "ok": 2, "skip": 3}
                    checks_sorted = sorted(checks, key=lambda c: status_order.get(c.get("status", "ok"), 3))

                    fail_count = sum(1 for c in checks if c.get("status") == "fail")
                    warn_count = sum(1 for c in checks if c.get("status") == "warn")
                    ok_count   = sum(1 for c in checks if c.get("status") == "ok")

                    col_fa, col_wa, col_ok = st.columns(3)
                    col_fa.metric("❌ Failing", fail_count)
                    col_wa.metric("⚠️ Warnings", warn_count)
                    col_ok.metric("✅ Passing", ok_count)
                    st.divider()

                    for check in checks_sorted:
                        name    = check.get("name", "unknown").replace("_", " ").title()
                        status  = check.get("status", "ok")
                        message = check.get("message", "")
                        fix     = check.get("fix", "")

                        if status == "fail":
                            icon, bg, fg, border = "❌", "#fef2f2", "#991b1b", "#fca5a5"
                        elif status == "warn":
                            icon, bg, fg, border = "⚠️", "#fffbeb", "#92400e", "#fcd34d"
                        elif status == "skip":
                            icon, bg, fg, border = "⏭️", "#f8fafc", "#64748b", "#e2e8f0"
                        else:
                            icon, bg, fg, border = "✅", "#f0fdf4", "#166534", "#86efac"

                        st.markdown(
                            f'<div style="background:{bg};border:1px solid {border};border-radius:8px;'
                            f'padding:10px 14px;margin:4px 0">'
                            f'<div style="display:flex;justify-content:space-between;align-items:center">'
                            f'<span style="font-weight:600;font-size:13px;color:{fg}">{icon} {name}</span>'
                            f'<span style="font-size:10px;font-family:monospace;color:{fg};'
                            f'background:rgba(0,0,0,0.06);padding:1px 6px;border-radius:4px">'
                            f'{status.upper()}</span></div>'
                            + (f'<div style="font-size:12px;color:{fg};margin-top:4px">{message}</div>' if message else "")
                            + (f'<div style="font-size:11px;color:#64748b;margin-top:4px;font-family:monospace">'
                               f'Fix: {fix}</div>' if fix else "")
                            + f'</div>',
                            unsafe_allow_html=True,
                        )
                elif not health_score:
                    st.code(h_raw[:2000], language="json")

    # ── Advisor ───────────────────────────────────────────────────────────────
    with intel_advisor:
        st.markdown("**Brain Advisor** — ranked recommendations for your brain")
        st.caption("Uses `gbrain advisor` · surfaces pending migrations, orphans, stale syncs, and setup issues")

        col_adv1, col_adv2 = st.columns([3, 1])
        with col_adv2:
            adv_go = st.button("Run Advisor", type="primary", use_container_width=True, key="adv_go")

        if adv_go:
            with st.spinner("Running gbrain advisor…"):
                adv_raw, adv_err, adv_rc = run_gbrain("advisor", "--json", timeout=120)

            if adv_rc not in (0, 1) or not adv_raw:
                # fallback: run without --json and show plain text
                with st.spinner("Retrying…"):
                    adv_raw, adv_err, adv_rc = run_gbrain("advisor", timeout=120)
                if adv_raw:
                    st.code(adv_raw, language=None)
                else:
                    st.error(f"gbrain advisor failed (exit {adv_rc})")
                    if adv_err:
                        st.code(adv_err[:600])
            else:
                try:
                    adv_data = json.loads(adv_raw)
                except Exception:
                    # not JSON — show as plain text
                    st.code(adv_raw, language=None)
                    adv_data = None

                if adv_data is not None:
                    findings = adv_data.get("findings", adv_data if isinstance(adv_data, list) else [])
                    summary  = adv_data.get("summary", "")

                    if summary:
                        st.info(summary)

                    if not findings:
                        st.success("✅ Nothing critical — your brain looks healthy.")
                    else:
                        sev_order = {"critical": 0, "warn": 1, "info": 2}
                        findings_sorted = sorted(findings, key=lambda f: sev_order.get(f.get("severity", "info"), 2))

                        crit  = sum(1 for f in findings if f.get("severity") == "critical")
                        warns = sum(1 for f in findings if f.get("severity") == "warn")
                        infos = sum(1 for f in findings if f.get("severity") == "info")

                        c1, c2, c3 = st.columns(3)
                        c1.metric("🔴 Critical", crit)
                        c2.metric("⚠️ Warnings", warns)
                        c3.metric("ℹ️ Info", infos)
                        st.divider()

                        for f in findings_sorted:
                            sev     = f.get("severity", "info")
                            title   = f.get("title", f.get("message", ""))
                            detail  = f.get("detail", f.get("description", ""))
                            fix_cmd = f.get("fix", f.get("command", ""))

                            if sev == "critical":
                                icon, bg, fg, border = "🔴", "#fef2f2", "#991b1b", "#fca5a5"
                            elif sev == "warn":
                                icon, bg, fg, border = "⚠️", "#fffbeb", "#92400e", "#fcd34d"
                            else:
                                icon, bg, fg, border = "ℹ️", "#eff6ff", "#1e40af", "#bfdbfe"

                            st.markdown(
                                f'<div style="background:{bg};border:1px solid {border};border-radius:8px;'
                                f'padding:10px 14px;margin:4px 0">'
                                f'<div style="font-weight:600;font-size:13px;color:{fg}">{icon} {title}</div>'
                                + (f'<div style="font-size:12px;color:{fg};margin-top:4px">{detail}</div>' if detail else "")
                                + (f'<div style="font-size:11px;color:#64748b;margin-top:6px;font-family:monospace">'
                                   f'▶ {fix_cmd}</div>' if fix_cmd else "")
                                + '</div>',
                                unsafe_allow_html=True,
                            )

    # ── Watch (push-based context) ────────────────────────────────────────────
    with intel_watch:
        st.markdown("**Brain Watch** — push-based context: your brain volunteers relevant pages as you have a conversation")
        st.caption("Uses `gbrain watch` · runs as a live terminal session, not a one-shot query")

        st.info(
            "**Watch is a terminal command, not a one-shot query.**\n\n"
            "`gbrain watch` reads your conversation turns line by line and volunteers brain pages as context builds up. "
            "It needs to run in its own terminal session — it holds the database write lock for the duration, "
            "so it can't run alongside other gbrain processes.",
            icon="ℹ️",
        )

        st.markdown("**How to use it:**")
        st.markdown(
            "1. Open a new terminal\n"
            "2. Run the command below\n"
            "3. Type (or paste) conversation turns — brain pages will appear after each turn\n"
            "4. Press **Ctrl+C** to end the session"
        )

        col_wc1, col_wc2 = st.columns(2)
        with col_wc1:
            wc_conf = st.slider("Min confidence", 0.1, 1.0, 0.7, step=0.05, key="watch_conf_display")
        with col_wc2:
            wc_max = st.slider("Max pages per turn", 1, 5, 3, key="watch_max_display")

        watch_cmd = f"gbrain watch --min-confidence {wc_conf} --max-pages {wc_max}"
        st.code(watch_cmd, language="bash")
        st.caption("Copy this command and run it in a separate terminal window.")

# ── Tab 9: Synthesis ─────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=300)
def _list_synthesis_pages() -> list:
    """Return sorted list of synthesis dates (YYYY-MM-DD), most recent first."""
    raw, _, rc = run_gbrain("list", "--type", "note", "-n", "100", timeout=30)
    if rc != 0 or not raw:
        return []
    dates = []
    for line in raw.splitlines():
        parts = line.split("\t")
        slug = parts[0].strip() if parts else ""
        if slug.startswith("wiki/synthesis/"):
            date_part = slug[len("wiki/synthesis/"):]
            if re.match(r"^\d{4}-\d{2}-\d{2}$", date_part):
                dates.append(date_part)
    return sorted(dates, reverse=True)

def _parse_synthesis_sections(content: str) -> dict:
    """Parse the 5 synthesis sections from markdown content."""
    section_names = [
        "Today's Papers",
        "Cross-Paper Themes",
        "Key Connections",
        "Open Questions",
        "Standout Finding",
    ]
    sections = {name: "" for name in section_names}
    for sec_name in section_names:
        m = re.search(
            rf"^##\s+{re.escape(sec_name)}\s*\n(.*?)(?=^##\s|\Z)",
            content, re.M | re.S,
        )
        if m:
            sections[sec_name] = m.group(1).strip()
    return sections

_SYNTH_SECTION_STYLES = {
    "Today's Papers":     ("#eff6ff", "#1d4ed8", "#bfdbfe", "📚"),
    "Cross-Paper Themes": ("#fdf4ff", "#7e22ce", "#e9d5ff", "🔀"),
    "Key Connections":    ("#f0fdf4", "#15803d", "#bbf7d0", "🔗"),
    "Open Questions":     ("#fffbeb", "#92400e", "#fde68a", "❓"),
    "Standout Finding":   ("#fef2f2", "#991b1b", "#fca5a5", "⭐"),
}

with tab_synthesis:
    st.markdown("**Daily Research Synthesis** — AI-generated cross-paper insights")
    st.caption(
        "Written daily at 3:00 PM by `subagent-daily-synthesis` · "
        "uses claude-sonnet-4-5 · stored at `wiki/synthesis/YYYY-MM-DD`"
    )

    col_syn_hd, col_syn_rf = st.columns([5, 1])
    with col_syn_rf:
        if st.button("🔄 Refresh", key="refresh_synthesis"):
            _list_synthesis_pages.clear()
            gbrain_get.clear()
            st.rerun()

    synth_dates = _list_synthesis_pages()

    if not synth_dates:
        st.info("No synthesis pages found yet. The daily synthesis runs at 3:00 PM.")
        st.caption(
            r"Run `C:\brain\subagent-daily-synthesis.bat` manually to generate one now."
        )
    else:
        with col_syn_hd:
            chosen_date = st.selectbox(
                "",
                options=synth_dates,
                label_visibility="collapsed",
                key="synthesis_date_select",
            )

        synth_slug = f"wiki/synthesis/{chosen_date}"

        with st.spinner(f"Loading synthesis for {chosen_date}…"):
            synth_content = gbrain_get(synth_slug)

        if not synth_content:
            st.error(f"Could not load `{synth_slug}` from brain.")
        else:
            sections = _parse_synthesis_sections(synth_content)
            has_sections = any(v for v in sections.values())

            if has_sections:
                for sec_name, sec_body in sections.items():
                    if not sec_body:
                        continue
                    bg, fg, border, icon = _SYNTH_SECTION_STYLES.get(
                        sec_name, ("#f8fafc", "#374151", "#e2e8f0", "•")
                    )
                    # Convert markdown bullets to HTML-friendly newlines
                    sec_html = sec_body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    sec_html = sec_html.replace("\n", "<br>")
                    st.markdown(
                        f'<div style="background:{bg};border:1px solid {border};border-radius:8px;'
                        f'padding:14px 18px;margin:8px 0">'
                        f'<div style="font-weight:700;font-size:13px;color:{fg};margin-bottom:8px">'
                        f'{icon} {sec_name}</div>'
                        f'<div style="font-size:14px;color:#1e293b;line-height:1.75">'
                        f'{sec_html}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                # No structured sections found — show raw content
                st.markdown(
                    f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;'
                    f'padding:16px 20px;font-size:14px;line-height:1.75;color:#1e293b;'
                    f'white-space:pre-wrap">{synth_content[:4000]}</div>',
                    unsafe_allow_html=True,
                )

            st.divider()
            st.caption(
                f"`{synth_slug}` · {len(synth_dates)} synthesis page(s) in brain · "
                f"cost ~€0.02–0.04 per run"
            )

            with st.expander("📋 Run synthesis now (manual trigger)", expanded=False):
                st.caption(
                    "Runs `subagent-daily-synthesis.bat` · reads the 10 most recent papers · "
                    "writes to `wiki/synthesis/today` · skips if already written today."
                )
                if st.button("▶ Run Synthesis Now", type="primary", key="run_synthesis_now"):
                    _syn_bat = r"C:\brain\subagent-daily-synthesis.bat"
                    with st.spinner("Running synthesis… (30–60 s)"):
                        _syn_proc = subprocess.run(
                            ["cmd.exe", "/c", _syn_bat],
                            capture_output=True, env=ENV, timeout=180,
                        )
                        _syn_out = (_syn_proc.stdout or b"").decode("utf-8", errors="replace").strip()
                        _syn_err = (_syn_proc.stderr or b"").decode("utf-8", errors="replace").strip()
                    if _syn_proc.returncode == 0:
                        st.success("✅ Synthesis complete — click Refresh to see it.")
                        _list_synthesis_pages.clear()
                        gbrain_get.clear()
                    else:
                        st.error(f"Synthesis failed (exit {_syn_proc.returncode})")
                    if _syn_out or _syn_err:
                        with st.expander("Log output"):
                            st.code((_syn_out + "\n" + _syn_err).strip()[-3000:], language=None)

# ── Tab 10: Eval Dashboard ────────────────────────────────────────────────────
with tab_eval:
    _EVAL_DIR = Path(r"C:\brain\eval-results")

    def _latest_eval(prefix: str) -> dict | None:
        if not _EVAL_DIR.exists():
            return None
        files = sorted(_EVAL_DIR.glob(f"{prefix}_*.json"), reverse=True)
        if not files:
            return None
        try:
            return json.loads(files[0].read_text(encoding="utf-8"))
        except Exception:
            return None

    def _eval_age(data: dict | None) -> str:
        if not data:
            return "never run"
        ts = data.get("timestamp", "")
        try:
            dt  = datetime.datetime.strptime(ts, "%Y%m%d_%H%M%S")
            age = datetime.datetime.now() - dt
            h   = age.total_seconds() / 3600
            if h < 1:   return f"{int(age.total_seconds()/60)}m ago"
            if h < 48:  return f"{h:.0f}h ago"
            return f"{age.days}d ago"
        except Exception:
            return ts[:8] if ts else "—"

    def _run_eval_bat(bat: str):
        try:
            subprocess.Popen(
                ["cmd.exe", "/c", bat],
                env=ENV, creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            return True
        except Exception as e:
            return str(e)

    r_search   = _latest_eval("eval")
    r_minions  = _latest_eval("minions")
    r_model    = _latest_eval("model")
    r_gaps     = _latest_eval("gaps")
    r_pipeline = _latest_eval("pipeline")

    st.markdown("### 📊 Evaluation Dashboard")
    st.caption("Results from the last run of each eval — click Re-run to refresh.")

    # ── Metric summary cards ──────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        if r_search:
            mrr = r_search.get("mrr", 0)
            h3  = r_search.get("hit_at_3", 0)
            st.metric("🔍 Search", f"MRR {mrr:.2f}", f"Hit@3 {h3:.0%}")
            st.caption(_eval_age(r_search))
        else:
            st.metric("🔍 Search", "—"); st.caption("never run")
    with c2:
        if r_minions:
            summ = r_minions.get("summary", {})
            ok   = summ.get("OK", 0)
            tot  = sum(summ.values())
            bad  = summ.get("FAILED", 0) + summ.get("STALE", 0)
            st.metric("🤖 Minions", f"{ok}/{tot} OK", f"⚠ {bad} issues", delta_color="inverse" if bad else "normal")
            st.caption(_eval_age(r_minions))
        else:
            st.metric("🤖 Minions", "—"); st.caption("never run")
    with c3:
        if r_model:
            results = r_model.get("results", [])
            avgs    = [r["avg"] for r in results if "avg" in r]
            grand   = sum(avgs) / len(avgs) if avgs else 0
            st.metric("🧠 Model", f"{grand:.2f}/5", f"{len(avgs)} questions")
            st.caption(_eval_age(r_model))
        else:
            st.metric("🧠 Model", "—"); st.caption("never run")
    with c4:
        if r_gaps:
            perf = r_gaps.get("perfect", 0)
            tot  = r_gaps.get("n", 0)
            thin = r_gaps.get("thin", 0)
            st.metric("📄 Gaps", f"{perf}/{tot} complete", f"⚠ {thin} thin" if thin else "")
            st.caption(_eval_age(r_gaps))
        else:
            st.metric("📄 Gaps", "—"); st.caption("never run")
    with c5:
        if r_pipeline:
            verdict = r_pipeline.get("verdict", "")
            passed  = r_pipeline.get("passed", 0)
            failed  = r_pipeline.get("failed", 0)
            icon    = "✅" if failed == 0 else "❌"
            st.metric("🔄 Pipeline", f"{icon} {passed}/{passed+failed}", f"{r_pipeline.get('total_secs',0):.0f}s")
            st.caption(_eval_age(r_pipeline))
        else:
            st.metric("🔄 Pipeline", "—"); st.caption("never run")

    st.divider()

    # ── Detail sections ───────────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        # Search detail
        with st.expander("🔍 Search Eval detail", expanded=False):
            if r_search:
                qs = r_search.get("queries", [])
                for q in qs:
                    h1  = "✅" if q.get("hit_at_1") else ("⚠️" if q.get("hit_at_3") else "❌")
                    mrr = q.get("mrr", 0)
                    lbl = q["query"][:52] + ".." if len(q["query"]) > 54 else q["query"]
                    st.markdown(f"{h1} `{mrr:.2f}` {lbl}")
            else:
                st.info("No results yet.")
            if st.button("▶ Re-run Search Eval", key="run_search"):
                _run_eval_bat(r"C:\brain\eval-search.bat")
                st.success("Search eval started — results save to eval-results/ when done.")

        # Model detail
        with st.expander("🧠 Model Eval detail", expanded=False):
            if r_model:
                DIMS = ["relevance","grounding","coherence","citations","gaps_honesty"]
                DIM_LABELS = {"relevance":"Relevance","grounding":"Grounding",
                              "coherence":"Coherence","citations":"Citations","gaps_honesty":"Gaps"}
                results = r_model.get("results", [])
                for i, r in enumerate(results, 1):
                    avg  = r.get("avg", 0)
                    icon = "✅" if avg >= 4 else ("⚠️" if avg >= 3 else "❌")
                    q    = r["question"][:55] + ".." if len(r["question"]) > 57 else r["question"]
                    st.markdown(f"{icon} **Q{i}** ({avg:.1f}/5) {q}")
                    if r.get("overall"):
                        st.caption(r["overall"][:120])
                st.divider()
                # Dimension averages
                for dim in DIMS:
                    vals = [r.get("scores", {}).get(dim, {}).get("score", 0) for r in results if "scores" in r]
                    if vals:
                        avg = sum(vals) / len(vals)
                        bar = "█" * round(avg) + "░" * (5 - round(avg))
                        st.markdown(f"`{bar}` **{DIM_LABELS[dim]}** {avg:.1f}/5")
            else:
                st.info("No results yet.")
            if st.button("▶ Re-run Model Eval", key="run_model"):
                _run_eval_bat(r"C:\brain\eval-model.bat")
                st.success("Model eval started (takes ~3 min) — saves to eval-results/ when done.")

    with col_right:
        # Minions detail
        with st.expander("🤖 Minions Health detail", expanded=False):
            if r_minions:
                STATUS_ICON = {"OK":"✅","FAILED":"❌","STALE":"⏰","WARN":"⚠️","UNKNOWN":"❓","NO LOG":"📂"}
                for m in r_minions.get("minions", []):
                    icon = STATUS_ICON.get(m.get("status",""), "?")
                    age  = m.get("age_hours")
                    age_s = f"{age:.0f}h ago" if age is not None else "—"
                    st.markdown(f"{icon} **{m['name']}** — {age_s}")
            else:
                st.info("No results yet.")
            if st.button("▶ Re-run Minions Health", key="run_minions"):
                _run_eval_bat(r"C:\brain\eval-minions.bat")
                st.success("Minions health check started.")

        # Gaps detail
        with st.expander("📄 Content Gaps detail", expanded=False):
            if r_gaps:
                papers = r_gaps.get("papers", [])
                incomplete = [p for p in papers if p.get("score", 9) < 9]
                if incomplete:
                    st.markdown("**Papers with gaps:**")
                    for p in sorted(incomplete, key=lambda x: x.get("score", 0)):
                        pct  = round(p["score"] / p["max_score"] * 100) if p.get("max_score") else 0
                        icon = "❌" if pct < 50 else "⚠️"
                        st.markdown(f"{icon} `{pct}%` {p['title'][:50]}")
                        for issue in p.get("issues", [])[:2]:
                            st.caption(f"  └ {issue}")
                else:
                    st.success("All papers complete!")
            else:
                st.info("No results yet.")
            if st.button("▶ Re-run Gaps Audit", key="run_gaps"):
                _run_eval_bat(r"C:\brain\eval-gaps.bat")
                st.success("Gaps audit started.")

    # Pipeline detail (full width)
    with st.expander("🔄 Pipeline Test detail", expanded=bool(r_pipeline and r_pipeline.get("failed", 0))):
        if r_pipeline:
            st.markdown(f"**Probe:** `{r_pipeline.get('probe_slug','—')}` · **{r_pipeline.get('verdict','—')}**")
            for s in r_pipeline.get("stages", []):
                icon = {"PASS":"✅","FAIL":"❌","SKIP":"⏭","WARN":"⚠️"}.get(s["status"],"?")
                t    = f"{s['elapsed']:.1f}s"
                det  = f" — {s['detail']}" if s.get("detail") else ""
                st.markdown(f"{icon} **{s['name']}** `{t}`{det}")
        else:
            st.info("No results yet.")
        if st.button("▶ Run Pipeline Test", key="run_pipeline"):
            _run_eval_bat(r"C:\brain\eval-pipeline.bat")
            st.success("Pipeline test started (~40s) — saves to eval-results/ when done.")

# ── Tab 11: Help ─────────────────────────────────────────────────────────────
with tab_help:
    st.markdown("### ❓ Tab & Feature Guide")

    def _help_row(label, desc):
        st.markdown(
            f"<div style='display:flex;gap:16px;padding:5px 0;border-bottom:1px solid #f1f5f9'>"
            f"<span style='min-width:200px;font-size:15px;font-weight:600;color:#1e293b'>{label}</span>"
            f"<span style='font-size:15px;color:#374151'>{desc}</span></div>",
            unsafe_allow_html=True,
        )

    def _sub_row(label, desc):
        st.markdown(
            f"<div style='display:flex;gap:16px;padding:4px 0 4px 20px;border-bottom:1px solid #f8fafc'>"
            f"<span style='min-width:180px;font-size:15px;color:#475569'>{label}</span>"
            f"<span style='font-size:15px;color:#64748b'>{desc}</span></div>",
            unsafe_allow_html=True,
        )

    _help_row("🔍 Search", "Hybrid semantic + keyword search (BM25 + vector). Reranker merges results. MMR toggle adds diversity. Use for raw retrieval across all pages.")
    _help_row("💬 Ask", "RAG chat — LLM synthesizes an answer from your brain pages. Returns citations, gap analysis, and confidence. Use for questions, not just lookup.")
    with st.expander("&nbsp;&nbsp;&nbsp;&nbsp;→ Ask sub-features", expanded=False):
        _sub_row("🔗 Relationship mode", "Walks typed graph edges (invested_in, works_at, founded) instead of vector search. Use for 'who invested in X' type questions.")
    _help_row("📄 Read Paper", "Full-text reader for any imported paper. Enrich: extract authors & institutions, generate Research Context, fix missing sections.")
    with st.expander("🕸️ Graph — three views of your knowledge graph", expanded=False):
        _sub_row("🔬 Research Graph", "Papers → authors → institutions, extracted from PDFs. Visual force-directed graph.")
        _sub_row("👤 Personal Graph", "Your own network: add people, companies, meetings. Explore connections.")
        _sub_row("🧠 Who Knows?", "Given a topic, finds people in your network with relevant expertise based on their brain pages.")
    with st.expander("🤖 Minions — automation pipelines, logs, and manual controls", expanded=False):
        _sub_row("🔄 Sync Brain", "Re-ingests markdown files from disk into the DB. Resumable — picks up where it left off. Only needed if you edit files manually outside the app.")
        _sub_row("⚡ Embed Stale Pages", "Generates Voyage AI embeddings for pages added/updated since last embed. Without embeddings, pages won't appear in semantic search. Pace mode throttles rate.")
        _sub_row("🌙 Dream Cycle", "Full maintenance run: extract wikilinks → embed → build backlinks → lint → find orphans. Run after bulk imports.")
    with st.expander("📋 Brief — three auto-generated intelligence reports", expanded=False):
        _sub_row("📋 Daily Brief", "AI summary of recent papers + brain activity. Runs daily at 9:30 AM via scheduled task.")
        _sub_row("📰 Weekly Digest", "Weekly cross-paper theme synthesis. Runs every Friday at 3 PM.")
        _sub_row("🔔 Alerts", "Notifications when a new paper matching your interest areas is added to the brain.")
    _help_row("✏️ Capture", "Quick-save a thought, note, or idea directly into the brain without leaving the app.")
    with st.expander("🔬 Intel — brain analytics and diagnostics", expanded=False):
        _sub_row("⚡ Anomalies", "Detects tag/type cohorts with statistically unusual activity today vs. historical baseline (N sigma threshold).")
        _sub_row("🔥 Hot Pages", "Most salient pages right now — ranked by recent access and activity weight.")
        _sub_row("🏥 Health", "Full brain diagnostic: embedding coverage, orphan count, missing sections, sync staleness, schema issues.")
        _sub_row("🧠 Advisor", "Ranked action list: pending migrations, orphaned pages, stale syncs, setup gaps. Run after upgrades.")
        _sub_row("🔭 Watch", "Push-based context. Run `gbrain watch` in a terminal — brain volunteers relevant pages as your conversation builds up.")
    _help_row("📝 Synthesis", "AI-generated cross-paper insight reports. Daily synthesis finds recurring themes across recent papers and writes them to wiki/synthesis/.")
    _help_row("📊 Eval", "Evaluation dashboard: search quality benchmarks, LLM answer quality, pipeline health checks, and gaps audit (papers missing sections or embeddings).")

# ── Sidebar ───────────────────────────────────────────────────────────────────
