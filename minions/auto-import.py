"""
auto-import.py — Phase 1 of the paper ingestion pipeline.

Watches C:\\brain\\papers for new PDFs.
For each new PDF:
  1. Extract text (pypdf)
     1b. If image-heavy (<100 chars/page avg) → vision fallback via Claude API
         (renders pages with pymupdf, sends images to Claude vision)
  2. Call Groq for a structured summary
  3. Write <slug>.md to ./extracted/  (frontmatter + summary)
  4. Write a one-page alert to ./alerts/
  5. Submit a native gbrain `import` Minion job for ./extracted/

The gbrain worker picks up the import job and runs it natively.
Embedding is handled by the separate GBrain-AutoEmbed task (embed --stale).

NO blocking gbrain subprocess calls. NO PGLite retry loops.
"""

import subprocess
import os
import re
import json
import ssl
import urllib.request
from pathlib import Path
from datetime import datetime

# Corporate SSL inspection bypass — same as NODE_TLS_REJECT_UNAUTHORIZED=0 for Node
ssl._create_default_https_context = ssl._create_unverified_context

WATCH_DIR   = r"C:\brain\papers"
EXTRACT_DIR = r"C:\brain\extracted"
LOG_FILE    = r"C:\brain\minions\auto-import.log"
KNOWN_FILE  = r"C:\brain\known-import-pdfs.txt"

GBRAIN_CMD = os.path.join(os.path.expanduser("~"), ".bun", "bin", "gbrain.cmd")

# ── Helpers ───────────────────────────────────────────────────────────────────

def log(msg):
    ts = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    line = f"[{ts}] {msg}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line.encode("cp1252", errors="replace").decode("cp1252"))

def load_known():
    try:
        with open(KNOWN_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def save_known(known):
    with open(KNOWN_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(known)) + "\n")

def gbrain_env():
    return {**os.environ, "PATH": os.path.join(os.path.expanduser("~"), ".bun", "bin") + ";" + os.environ.get("PATH", "")}

# ── Thresholds ────────────────────────────────────────────────────────────────

TEXT_MIN_CHARS_PER_PAGE = 100   # below this avg → treat as image-heavy → vision fallback
VISION_MAX_PAGES        = 8     # max pages to send to Claude vision (cost guard)
VISION_DPI              = 150   # render DPI for PDF→PNG (150 = good quality, reasonable size)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# ── Step 1: Extract text ──────────────────────────────────────────────────────

def extract_pdf(pdf_path):
    """Extract text with pypdf. Returns (text, is_image_heavy, page_count)."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        n_pages = len(reader.pages)
        pages_text = [p.extract_text() or "" for p in reader.pages]
        text = "\n\n".join(t for t in pages_text if t).strip()
        text = text.replace('\x00', '')   # null bytes → Postgres rejects
        chars_per_page = len(text) / max(n_pages, 1)
        is_image_heavy = chars_per_page < TEXT_MIN_CHARS_PER_PAGE
        return text, is_image_heavy, n_pages
    except Exception as e:
        log(f"  ERROR extracting text: {e}")
        return None, False, 0

# ── Step 1b: Vision fallback (Claude multimodal) ──────────────────────────────

def extract_with_vision(pdf_path, anthropic_key):
    """Render PDF pages to PNG with pymupdf, send to Claude vision, return rich text."""
    import base64
    import fitz  # pymupdf — already installed, no poppler needed

    doc = fitz.open(pdf_path)
    n = min(len(doc), VISION_MAX_PAGES)

    images_b64 = []
    for i in range(n):
        page = doc[i]
        mat  = fitz.Matrix(VISION_DPI / 72, VISION_DPI / 72)
        pix  = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        images_b64.append(base64.standard_b64encode(pix.tobytes("png")).decode())
    doc.close()

    # Build message content: interleave page labels + images
    content = []
    for i, b64 in enumerate(images_b64):
        content.append({"type": "text", "text": f"### Page {i + 1}"})
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": b64},
        })

    content.append({
        "type": "text",
        "text": (
            "This PDF is primarily visual (flowchart, diagram, or image-heavy). "
            "Please do ALL of the following:\n\n"
            "1. **Describe every diagram or flowchart** — what it represents, the nodes/steps, "
            "and the connections/arrows between them.\n"
            "2. **Extract ALL visible text** — labels, annotations, captions, axis titles, "
            "table headers, legend entries.\n"
            "3. **Describe the flow** — for flowcharts, walk through the sequence step-by-step "
            "(start → decision points → branches → end).\n"
            "4. **Extract any tables or structured data** verbatim.\n"
            "5. **Note any metrics, percentages, or numbers** shown in charts.\n\n"
            "Be exhaustive. This output will be stored in a knowledge base and must capture "
            "everything a reader would learn from looking at the original document."
        ),
    })

    payload = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 2500,
        "messages": [{"role": "user", "content": content}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": anthropic_key,
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data["content"][0]["text"].strip()

# ── Step 2: Groq summary ──────────────────────────────────────────────────────

def generate_summary(name, text, groq_key):
    # Use more of the paper for a richer summary (intro + methods + results)
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

# ── Step 3: Write markdown file ───────────────────────────────────────────────

def write_markdown(name, slug, summary):
    """Write a clean synthesized .md — no raw text dump.
    Structure: Compiled Truth (Groq summary) above the line,
    append-only Timeline below <!-- timeline --> sentinel.
    The raw text is chunked and embedded into Neon by the import job anyway."""
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    md_path = os.path.join(EXTRACT_DIR, f"{slug}.md")
    today = datetime.now().strftime("%Y-%m-%d")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"---\ntitle: \"{name}\"\ntype: paper\n---\n\n")
        f.write(summary or "(summary unavailable)")
        f.write(f"\n\n<!-- timeline -->\n\n## Timeline\n\n- **{today}** — Imported to GBrain and summarized\n")
    return md_path

# ── Step 4: Write alert ───────────────────────────────────────────────────────

def write_alert(name, slug, summary):
    alert_dir = r"C:\brain\alerts"
    os.makedirs(alert_dir, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    alert_path = os.path.join(alert_dir, f"{today}-{slug}.md")
    with open(alert_path, "w", encoding="utf-8") as f:
        f.write(f"# New Paper Imported — {name}\n\n")
        f.write(f"*Imported: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n")
        f.write(f"## Summary\n\n{summary or '(unavailable)'}\n\n")
        f.write(f"---\n*gbrain slug: `{slug}`*\n")
    log(f"  ALERT saved: {alert_path}")

# ── Step 5: Submit native import Minion job ───────────────────────────────────

def submit_import_job():
    """Queue a native gbrain `import` job for ./extracted/. Non-blocking."""
    params = json.dumps({"dir": EXTRACT_DIR, "noEmbed": True})
    # Use cmd.exe /c so gbrain.cmd executes correctly on Windows
    r = subprocess.run(
        ["cmd.exe", "/c", GBRAIN_CMD, "jobs", "submit", "import", "--params", params, "--max-waiting", "1"],
        capture_output=True,
        timeout=30,
        env=gbrain_env(),
    )
    if r.returncode == 0:
        out = r.stdout.decode("utf-8", errors="replace").strip()
        # Extract job id from JSON output if present
        try:
            job = json.loads(out)
            log(f"  Import job queued (id={job.get('id', '?')})")
        except Exception:
            log(f"  Import job queued")
    else:
        err = r.stderr.decode("utf-8", errors="replace").strip()
        log(f"  WARNING: import job submission failed (exit {r.returncode}): {err[:200]}")

# ── Step 1c: Direct image vision (JPG/PNG/etc.) ───────────────────────────────

def extract_image_with_vision(image_path, anthropic_key):
    """Send a JPG/PNG image directly to Claude vision. Returns descriptive text."""
    import base64
    ext = Path(image_path).suffix.lower()
    media_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                 ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp"}
    media_type = media_map.get(ext, "image/jpeg")

    with open(image_path, "rb") as fh:
        b64 = base64.standard_b64encode(fh.read()).decode()

    payload = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 3000,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": b64},
                },
                {
                    "type": "text",
                    "text": (
                        "Describe this image in exhaustive detail so it can be stored in a "
                        "knowledge base and retrieved by text search.\n\n"
                        "If it is a map or diagram:\n"
                        "- List every station, stop, node, or location name you can read\n"
                        "- Describe the lines/routes and how they connect\n"
                        "- Note any zone numbers, colour coding, or interchange markers\n"
                        "- Include directions (north/south/east/west) if visible\n\n"
                        "If it is a chart or infographic:\n"
                        "- Extract all numbers, labels, and legend entries verbatim\n\n"
                        "Be exhaustive — every text label matters for search."
                    ),
                },
            ],
        }],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": anthropic_key,
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data["content"][0]["text"].strip()


def process_image(img_name, groq_key, anthropic_key):
    """Process a JPG/PNG via Claude vision → Groq summary → extracted MD."""
    img_path = os.path.join(WATCH_DIR, img_name)
    name = Path(img_name).stem.replace("_", " ").replace("-", " ").title()
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    log(f"-- Processing image: {img_name}")

    if not anthropic_key:
        log(f"  SKIP — no ANTHROPIC_API_KEY (required for image vision)")
        return False

    # Step 1c: Claude vision
    try:
        vision_text = extract_image_with_vision(img_path, anthropic_key)
        log(f"  Step 1c OK — vision extracted {len(vision_text):,} chars")
    except Exception as e:
        log(f"  Step 1c ERROR — vision failed: {e}")
        return False

    # Step 2: Groq summary (or use vision text directly)
    summary = None
    if groq_key:
        try:
            summary = generate_summary(name, vision_text, groq_key)
            log(f"  Step 2 OK — summary generated (vision→Groq)")
        except Exception as e:
            log(f"  Step 2 WARN — Groq failed: {e}. Using vision output directly.")
            summary = vision_text
    else:
        summary = vision_text
        log(f"  Step 2 SKIP — no GROQ_API_KEY, using vision output directly")

    # Prepend the raw vision description so it's fully searchable
    full_content = f"## Visual Description\n\n{vision_text}\n\n## Summary\n\n{summary}"

    # Step 3: Write markdown to extracted/
    write_markdown(name, slug, full_content)
    log(f"  Step 3 OK — wrote extracted/{slug}.md")

    # Step 4: Write alert
    write_alert(name, slug, summary)

    return True


# ── Main ──────────────────────────────────────────────────────────────────────

def process_pdf(pdf_name, groq_key, anthropic_key):
    pdf_path = os.path.join(WATCH_DIR, pdf_name)
    name = Path(pdf_name).stem.replace("_", " ").replace("-", " ").title()
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    log(f"-- Processing: {pdf_name}")

    # Step 1: Extract text
    text, is_image_heavy, n_pages = extract_pdf(pdf_path)
    if text is None:
        return False

    vision_used = False

    # Step 1b: Vision fallback for image-heavy PDFs
    if is_image_heavy:
        avg = len(text) / max(n_pages, 1)
        log(f"  Step 1 — image-heavy ({avg:.0f} chars/page avg, {n_pages} pages) → vision fallback")
        if anthropic_key:
            try:
                vision_text = extract_with_vision(pdf_path, anthropic_key)
                text = vision_text
                vision_used = True
                log(f"  Step 1b OK — Claude vision extracted {len(text):,} chars")
            except Exception as e:
                log(f"  Step 1b WARN — vision failed: {e}. Proceeding with thin text.")
        else:
            log(f"  Step 1b SKIP — no ANTHROPIC_API_KEY, using thin text")
    else:
        log(f"  Step 1 OK — extracted {len(text):,} chars ({n_pages} pages)")

    # Step 2: Groq summary
    summary = None
    if groq_key:
        try:
            summary = generate_summary(name, text, groq_key)
            method  = "vision→Groq" if vision_used else "Groq"
            log(f"  Step 2 OK — summary generated ({method})")
        except Exception as e:
            log(f"  Step 2 WARN — Groq failed: {e}")
            summary = text if vision_used else "(summary unavailable)"
    elif vision_used:
        # No Groq but we have Claude vision output — use it directly as summary
        summary = text
        log(f"  Step 2 SKIP — no GROQ_API_KEY, using vision output directly")
    else:
        log(f"  Step 2 SKIP — no GROQ_API_KEY")
        summary = "(no LLM configured)"

    # Step 3: Write markdown to extracted/
    write_markdown(name, slug, summary)
    log(f"  Step 3 OK — wrote extracted/{slug}.md")

    # Step 4: Write alert
    write_alert(name, slug, summary)

    return True


def load_registry_key(name):
    """Read a string value from HKCU\\Environment (where user env vars are persisted on Windows)."""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
        value, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return value
    except Exception:
        return ""


def main():
    groq_key      = os.environ.get("GROQ_API_KEY", "") or load_registry_key("GROQ_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "") or load_registry_key("ANTHROPIC_API_KEY")

    if anthropic_key:
        log("ANTHROPIC_API_KEY loaded — vision fallback enabled")
    else:
        log("ANTHROPIC_API_KEY not found — vision fallback disabled")

    os.makedirs(WATCH_DIR, exist_ok=True)

    known = load_known()
    all_files = os.listdir(WATCH_DIR)

    new_pdfs   = [f for f in all_files if f.lower().endswith(".pdf")        and f not in known]
    new_images = [f for f in all_files if Path(f).suffix.lower() in IMAGE_EXTENSIONS and f not in known]

    if not new_pdfs and not new_images:
        log(f"No new files ({len(all_files)} already known in watch folder)")
        return

    if new_pdfs:
        log(f"Found {len(new_pdfs)} new PDF(s)")
    if new_images:
        log(f"Found {len(new_images)} new image(s)")

    any_written = False

    for pdf_name in new_pdfs:
        ok = process_pdf(pdf_name, groq_key, anthropic_key)
        if ok:
            known.add(pdf_name)
            save_known(known)
            any_written = True

    for img_name in new_images:
        ok = process_image(img_name, groq_key, anthropic_key)
        if ok:
            known.add(img_name)
            save_known(known)
            any_written = True

    # Step 5: queue one import job to cover all newly-written .md files
    if any_written:
        log("Queuing native import Minion job for extracted/")
        submit_import_job()

    log("Auto-import run complete")


if __name__ == "__main__":
    main()
