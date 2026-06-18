"""
eval-minions.py — GBrain minions health evaluation

For each scheduled minion, checks:
  - Last run timestamp (parsed from log file)
  - Last run outcome  (OK / FAILED / CRASHED / STALE / UNKNOWN)
  - Errors in the last 50 log lines
  - Task Scheduler state (enabled / disabled / next trigger)

Usage:
  python eval-minions.py            # health dashboard
  python eval-minions.py --save     # also write JSON snapshot to eval-results/
  python eval-minions.py --verbose  # show recent log tail on failures
"""
import os, sys, re, json, datetime, argparse, subprocess
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LOG_DIR     = Path(r"C:\brain")
RESULTS_DIR = Path(r"C:\brain\eval-results")

# ── Timestamp parsers ─────────────────────────────────────────────────────────
# Two formats appear in logs:
#   [DD-MM-YYYY HH:MM:SS.cc]  → bat/trigger logs
#   [YYYY-MM-DD HH:MM:SS]     → Python script logs
_TS_PATTERNS = [
    # DD-MM-YYYY HH:MM:SS (with optional .cc)
    re.compile(r"\[(\d{2})-(\d{2})-(\d{4}) (\d{2}):(\d{2}):(\d{2})"),
    # YYYY-MM-DD HH:MM:SS
    re.compile(r"\[(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})"),
]

def _parse_ts(line: str) -> datetime.datetime | None:
    m = _TS_PATTERNS[0].search(line)
    if m:
        d, mo, y, h, mi, s = m.groups()
        try:
            return datetime.datetime(int(y), int(mo), int(d), int(h), int(mi), int(s))
        except ValueError:
            pass
    m = _TS_PATTERNS[1].search(line)
    if m:
        y, mo, d, h, mi, s = m.groups()
        try:
            return datetime.datetime(int(y), int(mo), int(d), int(h), int(mi), int(s))
        except ValueError:
            pass
    return None


def last_timestamp(lines: list[str]) -> datetime.datetime | None:
    for line in reversed(lines):
        ts = _parse_ts(line)
        if ts:
            return ts
    return None


# ── Minion definitions ────────────────────────────────────────────────────────
# freq_hours: expected maximum gap between runs (used for staleness check)
# ok_pat:     regex that, when matched in last 80 lines, means the run succeeded
# fail_pat:   regex that, when matched in last 80 lines, signals a failure
# notes:      known quirks to surface in the report
MINIONS = [
    {
        "name":       "Auto Import",
        "task":       "GBrain-AutoImport",
        "log":        "auto-import.log",
        "freq_hours": 4,
        "ok_pat":     re.compile(r"Auto-import (run complete|finished OK)", re.I),
        "fail_pat":   re.compile(r"Auto-import FAILED|FAILED \(exit [^0]", re.I),
    },
    {
        "name":       "Embed Stale",
        "task":       "GBrain-AutoEmbed",
        "log":        "embed.log",
        "freq_hours": 6,
        "ok_pat":     re.compile(r"Embed complete \(exit 0", re.I),
        # "Embed FAILED (exit 0)" is a known bat bug — treat as OK if exit was 0
        "fail_pat":   re.compile(r"Embed FAILED \(exit [^0]", re.I),
        "quirk":      "\"Embed FAILED (exit 0)\" is a known false-fail in the bat file",
    },
    {
        "name":       "Worker",
        "task":       "GBrain-Worker",
        "log":        "gbrain-worker.log",
        "freq_hours": 2,  # should be running continuously; 2h gap = probably crashed
        "ok_pat":     re.compile(r"gbrain worker (starting|restarting)", re.I),
        "fail_pat":   re.compile(r"Minion worker stopped|CONNECTION_CLOSED|probe timeout", re.I),
        "quirk":      "Worker should restart automatically after crash (restart loop added 2026-06-17)",
    },
    {
        "name":       "Daily Brief",
        "task":       "GBrain-DailyBrief",
        "log":        "daily-brief.log",
        "freq_hours": 26,
        "ok_pat":     re.compile(r"daily.brief (finished OK|complete)", re.I),
        "fail_pat":   re.compile(r"FAILED|error", re.I),
    },
    {
        "name":       "Research Notes",
        "task":       "GBrain-ResearchNotes",
        "log":        "research-notes.log",
        "freq_hours": 26,
        "ok_pat":     re.compile(r"research-notes (finished OK|exit: 0)", re.I),
        "fail_pat":   re.compile(r"research-notes FAILED|exit: [^0]", re.I),
    },
    {
        "name":       "Daily Synthesis",
        "task":       "subagent-daily-synthesis",
        "log":        "subagent-daily-synthesis.log",
        "freq_hours": 26,
        "ok_pat":     re.compile(r"(synthesis finished OK|Synthesis complete|saved to wiki/synthesis)", re.I),
        "fail_pat":   re.compile(r"(synthesis FAILED|run-synthesis-direct FAILED)", re.I),
    },
    {
        "name":       "Backup",
        "task":       "GBrain Brain Backup",
        "log":        "backup.log",
        "freq_hours": 26,
        "ok_pat":     re.compile(r"backup exit: 0", re.I),
        "fail_pat":   re.compile(r"backup exit: [^0]|FAILED", re.I),
    },
    {
        "name":       "Dream Cycle",
        "task":       "GBrain-DreamCycle",
        "log":        "dream-cycle.log",
        "freq_hours": 26,
        "ok_pat":     re.compile(r"Dream Cycle (started|finished)", re.I),
        "fail_pat":   re.compile(r"Dream Cycle.*FAILED|error", re.I),
    },
    {
        "name":       "Arxiv Download",
        "task":       "ArxivDownload",
        "task_path":  r"\GBrain\\",
        "log":        "arxiv-download.log",
        "freq_hours": 26,
        "ok_pat":     re.compile(r"arXiv download (finished OK|complete)", re.I),
        "fail_pat":   re.compile(r"arXiv download FAILED|FAILED", re.I),
    },
    {
        "name":       "Graph Extract",
        "task":       "GBrain - Graph Extract",
        "task_path":  r"\GBrain\\",
        "log":        "graph-extract.log",
        "freq_hours": 26,
        "ok_pat":     re.compile(r"graph-extract finished OK", re.I),
        "fail_pat":   re.compile(r"graph-extract FAILED|FAILED", re.I),
    },
    {
        "name":       "Weekly Digest",
        "task":       "GBrain-WeeklyDigest",
        "log":        "weekly-digest.log",
        "freq_hours": 180,
        "ok_pat":     re.compile(r"(digest.*finished OK|Weekly digest complete)", re.I),
        "fail_pat":   re.compile(r"(digest FAILED|Weekly digest FAILED)", re.I),
    },
    {
        "name":       "Papers Watcher",
        "task":       "GBrain-PapersWatcher",
        "log":        "papers-watcher.log",
        "freq_hours": 26,
        "ok_pat":     re.compile(r"(watching|watcher started|Watching for)", re.I),
        "fail_pat":   re.compile(r"FAILED|error", re.I),
    },
    {
        "name":       "Build Research Graph",
        "task":       "GBrain-ResearchGraph",
        "log":        "build-research-graph.log",
        "freq_hours": 48,
        "ok_pat":     re.compile(r"(graph.build.*complete|All.*processed)", re.I),
        "fail_pat":   re.compile(r"FAILED|Traceback", re.I),
    },
    {
        "name":       "Clean Logs",
        "task":       "GBrain-CleanLogs",
        "log":        "clean-logs.log",
        "freq_hours": 180,
        "ok_pat":     re.compile(r"(clean.logs.*OK|cleaned)", re.I),
        "fail_pat":   re.compile(r"FAILED|error", re.I),
    },
    {
        "name":       "Prune Backups",
        "task":       "GBrain-PruneBackups",
        "log":        "prune-backups.log",
        "freq_hours": 180,
        "ok_pat":     re.compile(r"(prune.*OK|pruned)", re.I),
        "fail_pat":   re.compile(r"FAILED|error", re.I),
    },
]

ERROR_LINES_PAT = re.compile(
    r"(error|traceback|exception|failed|stopped|timeout|connection_closed)",
    re.I,
)


# ── Task Scheduler query ──────────────────────────────────────────────────────
def get_task_info(task_name: str) -> dict:
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f'$t = Get-ScheduledTask -TaskName "{task_name}" -ErrorAction SilentlyContinue; '
             f'if ($t) {{ $info = Get-ScheduledTaskInfo -TaskName "{task_name}" -ErrorAction SilentlyContinue; '
             f'[pscustomobject]@{{State=$t.State; LastResult=$info.LastTaskResult; '
             f'LastRun=$info.LastRunTime; NextRun=$info.NextRunTime}} | ConvertTo-Json }}'],
            capture_output=True, timeout=15,
        )
        raw = r.stdout.decode("utf-8", errors="replace").strip()
        if not raw:
            return {}
        data = json.loads(raw)
        return {
            "state":       data.get("State", ""),
            "last_result": data.get("LastResult"),
            "next_run":    data.get("NextRun", ""),
        }
    except Exception:
        return {}


# ── Per-minion check ──────────────────────────────────────────────────────────
def check_minion(m: dict, now: datetime.datetime, verbose: bool) -> dict:
    log_path = LOG_DIR / m["log"]
    result = {
        "name":       m["name"],
        "log":        m["log"],
        "freq_hours": m["freq_hours"],
        "status":     "UNKNOWN",
        "last_run":   None,
        "age_hours":  None,
        "ok":         False,
        "errors":     [],
        "quirk":      m.get("quirk", ""),
        "task_state": "",
    }

    # Read log
    if not log_path.exists():
        result["status"] = "NO LOG"
        return result

    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    tail  = lines[-80:] if len(lines) > 80 else lines

    # Last timestamp
    last_ts = last_timestamp(lines)
    if last_ts:
        result["last_run"]  = last_ts.strftime("%Y-%m-%d %H:%M")
        result["age_hours"] = round((now - last_ts).total_seconds() / 3600, 1)

    # Success / failure detection
    tail_text  = "\n".join(tail)
    is_ok      = bool(m["ok_pat"].search(tail_text))
    is_fail    = bool(m["fail_pat"].search(tail_text))

    # Staleness
    stale = result["age_hours"] is not None and result["age_hours"] > m["freq_hours"]

    if is_fail:
        result["status"] = "FAILED"
    elif stale and not is_ok:
        result["status"] = "STALE"
    elif is_ok:
        result["status"] = "OK"
        result["ok"]     = True
    else:
        result["status"] = "WARN"

    # Error lines in tail
    for line in tail:
        if ERROR_LINES_PAT.search(line) and not m["ok_pat"].search(line):
            result["errors"].append(line.strip()[:120])
    result["errors"] = result["errors"][-5:]  # keep last 5

    # Task Scheduler
    ti = get_task_info(m["name"])
    result["task_state"]  = ti.get("state", "")
    result["task_result"] = ti.get("last_result")

    return result


# ── Rendering ─────────────────────────────────────────────────────────────────
STATUS_ICON = {
    "OK":      "✅",
    "FAILED":  "❌",
    "STALE":   "⏰",
    "WARN":    "⚠️",
    "UNKNOWN": "❓",
    "NO LOG":  "📂",
}

def age_str(h) -> str:
    if h is None:
        return "never"
    if h < 1:
        return f"{int(h*60)}m ago"
    if h < 48:
        return f"{h:.0f}h ago"
    return f"{h/24:.0f}d ago"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--save",    action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    now = datetime.datetime.now()
    print(f"\nGBrain Minions Health  —  {now.strftime('%Y-%m-%d %H:%M')}\n")
    print(f"  {'Minion':<24}  {'Status':<8}  {'Last run':<17}  {'Age':<10}  {'Scheduler'}")
    print("─" * 85)

    results = []
    counts  = {"OK": 0, "FAILED": 0, "STALE": 0, "WARN": 0, "UNKNOWN": 0, "NO LOG": 0}

    for m in MINIONS:
        r = check_minion(m, now, args.verbose)
        results.append(r)
        counts[r["status"]] = counts.get(r["status"], 0) + 1

        icon      = STATUS_ICON.get(r["status"], "?")
        last_str  = r["last_run"] or "—"
        age       = age_str(r["age_hours"])
        sched     = r.get("task_state", "") or "—"

        print(f"  {r['name']:<24}  {icon} {r['status']:<6}  {last_str:<17}  {age:<10}  {sched}")

        if r["quirk"] and r["status"] in ("FAILED", "WARN"):
            print(f"  {'':24}  ↳ {r['quirk']}")

        if args.verbose and r["errors"]:
            for e in r["errors"][-2:]:
                print(f"  {'':24}    {e[:78]}")

    print("─" * 85)
    total = len(results)
    ok_n  = counts["OK"]
    print(
        f"\n  {ok_n}/{total} healthy  ·  "
        f"❌ {counts['FAILED']} failed  ·  "
        f"⏰ {counts['STALE']} stale  ·  "
        f"⚠️  {counts['WARN']} warn\n"
    )

    # Highlight actionable failures
    problems = [r for r in results if r["status"] in ("FAILED", "STALE", "WARN")]
    if problems:
        print("  Issues to investigate:")
        for r in problems:
            note = ""
            if r["errors"]:
                note = r["errors"][-1][:80]
            elif r["quirk"]:
                note = r["quirk"][:80]
            print(f"    {'⏰' if r['status']=='STALE' else '❌' if r['status']=='FAILED' else '⚠️'}  {r['name']:<24}  {note}")
        print()

    if args.save:
        RESULTS_DIR.mkdir(exist_ok=True)
        ts   = now.strftime("%Y%m%d_%H%M%S")
        path = RESULTS_DIR / f"minions_{ts}.json"
        path.write_text(json.dumps({
            "timestamp": ts,
            "summary":   counts,
            "minions":   [{k: v for k, v in r.items() if k != "errors"} for r in results],
        }, indent=2, default=str), encoding="utf-8")
        print(f"  Saved to {path}")


if __name__ == "__main__":
    main()
