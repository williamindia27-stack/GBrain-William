"""
arxiv-download.py
Fetches the N newest cs.AI papers from the arXiv API and downloads their PDFs
into the Papers watch-folder so auto-import picks them up automatically.

Tracks downloaded arXiv IDs in known-arxiv-ids.txt to avoid re-downloading.
Run daily at 7 AM (before the 8 AM daily brief).
"""

import os
import re
import ssl
import time
import urllib.request
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

# Windows often lacks root CA bundles for Python — use unverified context locally
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

# ── Config ─────────────────────────────────────────────────────────────────────

PAPERS_DIR   = r"C:\brain\papers"
LOG_FILE     = r"C:\brain\minions\arxiv-download.log"
KNOWN_FILE   = r"C:\brain\known-arxiv-ids.txt"

PAPERS_PER_RUN  = 2          # how many new papers to download each run
MAX_CANDIDATES  = 20         # how many recent papers to consider
ARXIV_CATEGORY  = "cs.AI"
DOWNLOAD_DELAY  = 3          # seconds between downloads (be polite to arXiv)

ARXIV_API = (
    "http://export.arxiv.org/api/query"
    "?search_query=cat:{cat}"
    "&sortBy=submittedDate&sortOrder=descending"
    "&max_results={n}"
)
NS = {"atom": "http://www.w3.org/2005/Atom"}

# ── Helpers ────────────────────────────────────────────────────────────────────

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

def sanitize_filename(title):
    """Turn a paper title into a safe filename (max 80 chars)."""
    s = re.sub(r'[\\/:*?"<>|]', "", title)   # remove forbidden chars
    s = re.sub(r"\s+", " ", s).strip()
    return s[:80]

# ── arXiv API ─────────────────────────────────────────────────────────────────

def fetch_recent_papers(n=MAX_CANDIDATES):
    """Return list of dicts: {id, title, pdf_url} for the n most recent cs.AI papers."""
    url = ARXIV_API.format(cat=ARXIV_CATEGORY, n=n)
    log(f"Querying arXiv API: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "python-urllib/3.14"})
    with urllib.request.urlopen(req, timeout=30, context=_SSL_CTX) as r:
        xml_bytes = r.read()

    root = ET.fromstring(xml_bytes)
    papers = []
    for entry in root.findall("atom:entry", NS):
        raw_id  = entry.find("atom:id", NS).text.strip()          # full URL
        arxiv_id = raw_id.split("/abs/")[-1].split("v")[0]        # e.g. 2501.12345
        title   = entry.find("atom:title", NS).text.strip().replace("\n", " ")
        # PDF link: rel="related" type="application/pdf"
        pdf_url = None
        for link in entry.findall("atom:link", NS):
            if link.get("type") == "application/pdf":
                pdf_url = link.get("href")
                break
        if pdf_url is None:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        papers.append({"id": arxiv_id, "title": title, "pdf_url": pdf_url})
    return papers

# ── Download ──────────────────────────────────────────────────────────────────

def download_paper(paper):
    """Download a single paper PDF into PAPERS_DIR. Returns True on success."""
    fname = sanitize_filename(paper["title"]) + ".pdf"
    dest  = os.path.join(PAPERS_DIR, fname)

    if os.path.exists(dest):
        log(f"  File already exists, skipping: {fname}")
        return True

    log(f"  Downloading [{paper['id']}]: {paper['title'][:60]}...")
    req = urllib.request.Request(
        paper["pdf_url"],
        headers={"User-Agent": "python-urllib/3.14"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60, context=_SSL_CTX) as r:
            data = r.read()
        with open(dest, "wb") as f:
            f.write(data)
        size_kb = len(data) // 1024
        log(f"  Saved ({size_kb} KB): {fname}")
        return True
    except urllib.error.HTTPError as e:
        log(f"  HTTP error {e.code} downloading {paper['id']}: {e.reason}")
        return False
    except Exception as e:
        log(f"  ERROR downloading {paper['id']}: {e}")
        return False

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(PAPERS_DIR, exist_ok=True)
    known = load_known()

    log(f"arXiv download started ({ARXIV_CATEGORY}, {PAPERS_PER_RUN} papers/run)")

    try:
        candidates = fetch_recent_papers(MAX_CANDIDATES)
    except Exception as e:
        log(f"ERROR fetching arXiv feed: {e}")
        return

    log(f"Got {len(candidates)} candidates, {len(known)} already known")

    new_papers = [p for p in candidates if p["id"] not in known]
    log(f"New papers to consider: {len(new_papers)}")

    downloaded = 0
    for paper in new_papers:
        if downloaded >= PAPERS_PER_RUN:
            break

        ok = download_paper(paper)
        if ok:
            known.add(paper["id"])
            save_known(known)
            downloaded += 1
            if downloaded < PAPERS_PER_RUN:
                time.sleep(DOWNLOAD_DELAY)

    if downloaded == 0:
        log("No new papers downloaded (all already known or errors)")
    else:
        log(f"Done -- downloaded {downloaded} new paper(s)")

if __name__ == "__main__":
    main()
