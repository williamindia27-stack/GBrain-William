"""
run-synthesis-direct.py
Runs daily paper synthesis directly (no job queue, no worker needed).
Reads papers via gbrain CLI, synthesizes with Anthropic API, writes result back.
"""
import os
import sys
import subprocess
import datetime
import json
import ssl
from pathlib import Path

ssl._create_default_https_context = ssl._create_unverified_context

GBRAIN_CMD  = os.path.join(os.path.expanduser("~"), ".bun", "bin", "gbrain.cmd")
LOG         = Path(r"C:\brain\minions\subagent-daily-synthesis.log")
TODAY       = datetime.date.today().isoformat()
TARGET_SLUG = f"wiki/synthesis/{TODAY}"
MAX_PAPERS  = 10

ENV = {
    **os.environ,
    "PATH": os.path.join(os.path.expanduser("~"), ".bun", "bin") + ";" + os.environ.get("PATH", ""),
    "GBRAIN_POOL_SIZE": "2",
    # Corporate SSL inspection intercepts HTTPS with a self-signed cert.
    # NODE_TLS_REJECT_UNAUTHORIZED=0 tells Bun/Node.js to skip SSL verification
    # for all outbound calls (Voyage AI embeddings, Anthropic API, etc.)
    "NODE_TLS_REJECT_UNAUTHORIZED": "0",
}

# Load API key from registry if not in env
if not ENV.get("ANTHROPIC_API_KEY"):
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
        ENV["ANTHROPIC_API_KEY"] = winreg.QueryValueEx(key, "ANTHROPIC_API_KEY")[0]
        winreg.CloseKey(key)
    except Exception:
        pass

if not ENV.get("DATABASE_URL"):
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
        ENV["DATABASE_URL"] = winreg.QueryValueEx(key, "DATABASE_URL")[0]
        winreg.CloseKey(key)
    except Exception:
        pass


def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def gbrain(args: list, timeout: int = 30) -> str:
    r = subprocess.run(
        ["cmd.exe", "/c", GBRAIN_CMD] + args,
        capture_output=True, env=ENV, timeout=timeout,
    )
    out = (r.stdout or b"").decode("utf-8", errors="replace").strip()
    err = (r.stderr or b"").decode("utf-8", errors="replace").strip()
    # Filter ai.gateway noise from stderr
    err_clean = "\n".join(l for l in err.splitlines() if "ai.gateway" not in l)
    if r.returncode != 0 and err_clean:
        raise RuntimeError(f"gbrain {args[0]} failed: {err_clean[:200]}")
    return out


def list_papers() -> list[dict]:
    out = gbrain(["list", "--type", "paper", "-n", str(MAX_PAPERS)])
    papers = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 4:
            papers.append({"slug": parts[0].strip(), "title": parts[3].strip()})
        elif len(parts) >= 1 and parts[0].strip():
            papers.append({"slug": parts[0].strip(), "title": parts[0].strip()})
    # Hard cap — gbrain list may ignore -n on some versions
    return papers[:MAX_PAPERS]


def get_page(slug: str) -> str:
    try:
        return gbrain(["get", slug], timeout=15)
    except Exception as e:
        return f"(could not read: {e})"


def synthesize_with_anthropic(papers_content: list[dict]) -> str:
    api_key = ENV.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    import urllib.request

    papers_text = ""
    for p in papers_content:
        papers_text += f"\n\n---\n### {p['title']} ({p['slug']})\n{p['content'][:3000]}"

    prompt = f"""You are a research synthesis agent. Today is {TODAY}.

I will give you {len(papers_content)} recent AI/ML papers from a personal knowledge brain. Read them and write a synthesis note.

{papers_text}

---

Write a synthesis note with EXACTLY these 5 sections (use these exact headings):

## Today's Papers
List the papers covered (title and one sentence each).

## Cross-Paper Themes
Themes or ideas that appear across multiple papers.

## Key Connections
Non-obvious links between specific papers that aren't explicitly stated.

## Open Questions
Important questions that none of these papers answer.

## Standout Finding
The single most interesting or surprising insight across all papers.

Keep each section concise (3-8 bullet points or sentences). Focus on insights, not summaries."""

    payload = json.dumps({
        "model": "claude-sonnet-4-5",
        "max_tokens": 3000,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    # Corporate SSL inspection replaces certificates (Missing Authority Key Identifier).
    # Bypass verification — the proxy already sees all traffic.
    import ssl as _ssl
    _ctx = _ssl.create_default_context()
    _ctx.check_hostname = False
    _ctx.verify_mode = _ssl.CERT_NONE
    with urllib.request.urlopen(req, timeout=120, context=_ctx) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    return data["content"][0]["text"].strip()


def restore_if_soft_deleted():
    """If TARGET_SLUG is soft-deleted, restore it so gbrain put can write a visible page."""
    # gbrain put updates soft-deleted pages without clearing deleted_at, making them
    # invisible to get/list. Restore by clearing deleted_at directly via Bun+postgres.
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
        db_url = winreg.QueryValueEx(key, "DATABASE_URL")[0]
        winreg.CloseKey(key)
    except Exception:
        db_url = ENV.get("DATABASE_URL", "")

    if not db_url:
        return  # No DB access, skip

    bun_script = f"""
import postgres from 'postgres';
const sql = postgres({repr(db_url)}, {{ ssl: {{ rejectUnauthorized: false }} }});
const rows = await sql`SELECT deleted_at FROM pages WHERE slug = {repr(TARGET_SLUG)}`;
if (rows.length > 0 && rows[0].deleted_at) {{
    await sql`UPDATE pages SET deleted_at = NULL WHERE slug = {repr(TARGET_SLUG)}`;
    console.log('restored');
}}
await sql.end();
"""
    try:
        r = subprocess.run(
            ["cmd.exe", "/c", os.path.join(os.path.expanduser("~"), ".bun", "bin", "bun.exe"), "-e", bun_script],
            capture_output=True, env=ENV, timeout=15,
        )
        out = (r.stdout or b"").decode("utf-8", errors="replace").strip()
        if out == "restored":
            log(f"Soft-deleted page {TARGET_SLUG} restored before write")
    except Exception as e:
        log(f"(restore attempt failed: {e} — continuing anyway)")


def write_synthesis(content: str):
    # If the slug was previously soft-deleted, gbrain put updates the content but
    # keeps deleted_at set, making the page invisible. Restore first.
    restore_if_soft_deleted()

    frontmatter = f"""---
title: "Research Synthesis {TODAY}"
type: note
tags: [synthesis, daily]
date: {TODAY}
---

"""
    full = frontmatter + content

    # Pipe content via stdin — avoids cmd.exe < "path" quoting issues on Windows
    r = subprocess.run(
        ["cmd.exe", "/c", GBRAIN_CMD, "put", TARGET_SLUG],
        input=full.encode("utf-8"),
        capture_output=True, env=ENV, timeout=60,
    )
    err = (r.stderr or b"").decode("utf-8", errors="replace").strip()
    err_clean = "\n".join(l for l in err.splitlines() if "ai.gateway" not in l)
    out = (r.stdout or b"").decode("utf-8", errors="replace").strip()
    if r.returncode != 0:
        raise RuntimeError(f"gbrain put failed (rc={r.returncode}): {err_clean[:300]} | {out[:200]}")
    log(f"Written to {TARGET_SLUG}")


def already_written() -> bool:
    try:
        gbrain(["get", TARGET_SLUG], timeout=15)
        return True
    except Exception:
        return False


def main():
    log(f"run-synthesis-direct started -- {TODAY}")

    if already_written():
        log(f"Synthesis for {TODAY} already exists at {TARGET_SLUG} -- skipping")
        return

    if not ENV.get("ANTHROPIC_API_KEY"):
        log("ERROR: ANTHROPIC_API_KEY not found in env or registry")
        sys.exit(1)

    log("Step 1: Listing recent papers...")
    papers = list_papers()
    log(f"  Found {len(papers)} papers: {', '.join(p['title'][:30] for p in papers[:5])}...")

    log("Step 2: Reading paper content...")
    papers_content = []
    for p in papers:
        content = get_page(p["slug"])
        papers_content.append({**p, "content": content})
        log(f"  Read: {p['title'][:50]} ({len(content)} chars)")

    log(f"Step 3: Synthesizing with Anthropic API ({len(papers_content)} papers)...")
    synthesis = synthesize_with_anthropic(papers_content)
    log(f"  Synthesis complete ({len(synthesis)} chars)")

    log(f"Step 4: Writing to {TARGET_SLUG}...")
    write_synthesis(synthesis)

    log("Done -- synthesis written successfully!")
    log(f"View it: gbrain get {TARGET_SLUG}")


if __name__ == "__main__":
    main()
