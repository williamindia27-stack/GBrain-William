"""
paper-watcher.py — Continuous daemon that watches C:\\brain\\papers for new files
and immediately processes them through gbrain.

Drop a PDF or image into C:\\brain\\papers -> it is extracted, summarised,
and imported into the brain within ~10 seconds.

Run once and leave running:
    python paper-watcher.py

Ctrl+C to stop.
"""

import subprocess
import os
import re
import json
import ssl
import time
import urllib.request
import winreg
from pathlib import Path
from datetime import datetime

ssl._create_default_https_context = ssl._create_unverified_context

WATCH_DIR        = r"C:\brain\papers"
EXTRACT_DIR      = r"C:\brain\extracted"
LOG_FILE         = r"C:\brain\paper-watcher.log"
KNOWN_FILE       = r"C:\brain\known-import-pdfs.txt"
POLL_INTERVAL    = 10   # seconds between scans

TEXT_MIN_CHARS_PER_PAGE = 100
VISION_MAX_PAGES        = 8
VISION_DPI              = 150
IMAGE_EXTENSIONS        = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

GBRAIN_CMD = os.path.join(os.path.expanduser("~"), ".bun", "bin", "gbrain.cmd")


# ── Helpers ────────────────────────────────────────────────────────────────────

def log(msg):
    ts   = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    line = f"[{ts}] {msg}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    try:
        print(line.encode("cp1252", errors="replace").decode("cp1252"))
    except Exception:
        print(line)

def load_registry_key(name):
    try:
        key   = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
        value, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return value
    except Exception:
        return ""

def gbrain_env():
    return {**os.environ, "PATH": os.path.join(os.path.expanduser("~"), ".bun", "bin") + ";" + os.environ.get("PATH", "")}

def load_known():
    try:
        with open(KNOWN_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def save_known(known):
    with open(KNOWN_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(known)) + "\n")


# ── Text extraction ────────────────────────────────────────────────────────────

def extract_pdf(pdf_path):
    try:
        from pypdf import PdfReader
        reader  = PdfReader(pdf_path)
        n_pages = len(reader.pages)
        pages   = [p.extract_text() or "" for p in reader.pages]
        text    = "\n\n".join(t for t in pages if t).strip().replace("\x00", "")
        chars_per_page = len(text) / max(n_pages, 1)
        return text, chars_per_page < TEXT_MIN_CHARS_PER_PAGE, n_pages
    except Exception as e:
        log(f"  ERROR extracting PDF text: {e}")
        return None, False, 0

def extract_with_vision(pdf_path, nvidia_key):
    import base64, fitz
    doc  = fitz.open(pdf_path)
    n    = min(len(doc), VISION_MAX_PAGES)
    imgs = []
    for i in range(n):
        pix = doc[i].get_pixmap(matrix=fitz.Matrix(VISION_DPI/72, VISION_DPI/72), colorspace=fitz.csRGB)
        imgs.append(base64.standard_b64encode(pix.tobytes("png")).decode())
    doc.close()
    content = []
    for i, b64 in enumerate(imgs):
        content.append({"type": "text", "text": f"### Page {i+1}"})
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})
    content.append({"type": "text", "text": (
        "Describe every diagram/flowchart, extract ALL visible text, labels, "
        "captions, tables, and metrics. Be exhaustive — this output is stored "
        "in a knowledge base and must capture everything a reader would learn."
    )})
    return _nvidia_vision_call(content, nvidia_key)

def extract_image_with_vision(image_path, nvidia_key):
    import base64
    ext      = Path(image_path).suffix.lower()
    media    = {".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png",".gif":"image/gif",".webp":"image/webp"}
    with open(image_path, "rb") as fh:
        b64  = base64.standard_b64encode(fh.read()).decode()
    content  = [
        {"type": "image_url", "image_url": {"url": f"data:{media.get(ext,'image/jpeg')};base64,{b64}"}},
        {"type": "text", "text": "Describe this image exhaustively for a knowledge base. Extract all text, labels, data."},
    ]
    return _nvidia_vision_call(content, nvidia_key)

def _nvidia_vision_call(content, nvidia_key):
    import ssl as _ssl
    ctx = _ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = _ssl.CERT_NONE
    payload = json.dumps({"model":"meta/llama-3.2-11b-vision-instruct","max_tokens":2500,"messages":[{"role":"user","content":content}]}).encode()
    req = urllib.request.Request(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        data=payload, headers={"Content-Type":"application/json","Authorization":f"Bearer {nvidia_key}"}
    )
    with urllib.request.urlopen(req, timeout=120, context=ctx) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"].strip()


# ── Groq summary ───────────────────────────────────────────────────────────────

def generate_summary(name, text, groq_key):
    payload = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": (
                "Write a structured summary with these exact sections:\n"
                "## Overview\n## Method\n## Key Results\n## Why It Matters\n## Limitations\n## Keywords\n"
                "Be specific, include numbers/metrics. No filler."
            )},
            {"role": "user", "content": f"Paper: {name}\n\n{text[:10000]}"},
        ],
        "temperature": 0.2, "max_tokens": 700,
    }).encode()
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions", data=payload,
        headers={"Content-Type":"application/json","Authorization":f"Bearer {groq_key}","User-Agent":"python-urllib/3.14"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"].strip()


# ── Write outputs ──────────────────────────────────────────────────────────────

def write_markdown(name, slug, summary):
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    path  = os.path.join(EXTRACT_DIR, f"{slug}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"---\ntitle: \"{name}\"\ntype: paper\n---\n\n")
        f.write(summary or "(summary unavailable)")
        f.write(f"\n\n<!-- timeline -->\n\n## Timeline\n\n- **{today}** — Imported to GBrain\n")

def write_alert(name, slug, summary):
    alert_dir  = r"C:\brain\alerts"
    os.makedirs(alert_dir, exist_ok=True)
    today      = datetime.now().strftime("%Y-%m-%d")
    path       = os.path.join(alert_dir, f"{today}-{slug}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# New Paper — {name}\n\n*{datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n{summary or '(unavailable)'}\n")


# ── Capture page into gbrain ───────────────────────────────────────────────────

def capture_page(md_path, slug):
    r = subprocess.run(
        ["cmd.exe", "/c", GBRAIN_CMD, "capture", "--file", md_path, "--slug", f"papers/{slug}", "--type", "paper", "--source", "default"],
        capture_output=True, timeout=60, env=gbrain_env(),
    )
    if r.returncode == 0:
        out = r.stdout.decode("utf-8", errors="replace").strip()
        log(f"  Captured -> papers/{slug}")
    else:
        err = r.stderr.decode("utf-8", errors="replace").strip()
        log(f"  WARNING: capture failed (exit {r.returncode}): {err[:200]}")


# ── Process single file ────────────────────────────────────────────────────────

def process_pdf(pdf_name, groq_key, nvidia_key):
    pdf_path = os.path.join(WATCH_DIR, pdf_name)
    name     = Path(pdf_name).stem.replace("_"," ").replace("-"," ").title()
    slug     = re.sub(r"[^a-z0-9]+","_",name.lower()).strip("_")
    log(f"-- New PDF: {pdf_name}")

    text, image_heavy, n_pages = extract_pdf(pdf_path)
    if text is None:
        return False

    vision_used = False
    if image_heavy and nvidia_key:
        try:
            text = extract_with_vision(pdf_path, nvidia_key)
            vision_used = True
            log(f"  Extracted via vision ({len(text):,} chars)")
        except Exception as e:
            log(f"  Vision failed: {e} — using thin text")
    else:
        log(f"  Extracted {len(text):,} chars, {n_pages} pages")

    summary = None
    if groq_key:
        try:
            summary = generate_summary(name, text, groq_key)
            log(f"  Summary generated")
        except Exception as e:
            log(f"  Groq failed: {e}")
            summary = text if vision_used else "(summary unavailable)"
    else:
        summary = text if vision_used else "(no LLM configured)"

    write_markdown(name, slug, summary)
    write_alert(name, slug, summary)
    log(f"  Written: extracted/{slug}.md")
    return True

def process_image(img_name, groq_key, nvidia_key):
    img_path = os.path.join(WATCH_DIR, img_name)
    name     = Path(img_name).stem.replace("_"," ").replace("-"," ").title()
    slug     = re.sub(r"[^a-z0-9]+","_",name.lower()).strip("_")
    log(f"-- New image: {img_name}")
    if not nvidia_key:
        log("  SKIP — no NVIDIA_API_KEY")
        return False
    try:
        text = extract_image_with_vision(img_path, nvidia_key)
        log(f"  Vision extracted {len(text):,} chars")
    except Exception as e:
        log(f"  Vision failed: {e}")
        return False
    summary = generate_summary(name, text, groq_key) if groq_key else text
    full    = f"## Visual Description\n\n{text}\n\n## Summary\n\n{summary}"
    write_markdown(name, slug, full)
    write_alert(name, slug, summary)
    log(f"  Written: extracted/{slug}.md")
    return True


# ── Main watch loop ────────────────────────────────────────────────────────────

def scan_once(known, groq_key, nvidia_key):
    try:
        all_files = os.listdir(WATCH_DIR)
    except Exception as e:
        log(f"ERROR listing watch dir: {e}")
        return known

    new_pdfs   = [f for f in all_files if f.lower().endswith(".pdf")               and f not in known]
    new_images = [f for f in all_files if Path(f).suffix.lower() in IMAGE_EXTENSIONS and f not in known]

    if not new_pdfs and not new_images:
        return known

    for name in new_pdfs:
        slug = re.sub(r"[^a-z0-9]+", "_", Path(name).stem.lower()).strip("_")
        md_path = os.path.join(EXTRACT_DIR, f"{slug}.md")
        if process_pdf(name, groq_key, nvidia_key):
            known.add(name)
            save_known(known)
            capture_page(md_path, slug)

    for name in new_images:
        slug = re.sub(r"[^a-z0-9]+", "_", Path(name).stem.lower()).strip("_")
        md_path = os.path.join(EXTRACT_DIR, f"{slug}.md")
        if process_image(name, groq_key, nvidia_key):
            known.add(name)
            save_known(known)
            capture_page(md_path, slug)

    return known


def main():
    groq_key   = os.environ.get("GROQ_API_KEY","")   or load_registry_key("GROQ_API_KEY")
    nvidia_key = os.environ.get("NVIDIA_API_KEY","") or load_registry_key("NVIDIA_API_KEY")

    os.makedirs(WATCH_DIR, exist_ok=True)
    log(f"Paper watcher started — watching {WATCH_DIR} every {POLL_INTERVAL}s")
    log(f"  Groq: {'OK' if groq_key else 'MISSING — summaries disabled'}")
    log(f"  NVIDIA vision: {'OK' if nvidia_key else 'MISSING — vision fallback disabled'}")

    known = load_known()
    log(f"  {len(known)} files already known")

    while True:
        try:
            known = scan_once(known, groq_key, nvidia_key)
        except Exception as e:
            log(f"ERROR in scan: {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
