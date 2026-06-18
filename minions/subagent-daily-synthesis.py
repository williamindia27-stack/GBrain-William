"""
subagent-daily-synthesis.py
Submits a daily gbrain subagent job that synthesizes recently imported papers,
finds cross-paper connections, and writes insight notes into the brain.
Runs via Windows Task Scheduler after the paper pipeline (around 3 PM).
"""
import os
import sys
import subprocess
import datetime
import json
from pathlib import Path

GBRAIN_CMD = os.path.join(os.path.expanduser("~"), ".bun", "bin", "gbrain.cmd")
LOG = Path(r"C:\brain\minions\subagent-daily-synthesis.log")
ENV = {
    **os.environ,
    "PATH": os.path.join(os.path.expanduser("~"), ".bun", "bin") + ";" + os.environ.get("PATH", ""),
    "GBRAIN_POOL_SIZE": "2",
}

TODAY = datetime.date.today().isoformat()

PROMPT = f"""Execute this research synthesis task immediately. Today is {TODAY}. Do not ask for clarification — start using tools right now.

Step 1: Call list_pages with type=paper and limit=10 to get the most recent papers.

Step 2: For each paper returned, call get_page to read its content. Focus on: Overview, Key Results, Why It Matters, Research Context.

Step 3: Identify across all papers:
- Cross-paper themes (ideas appearing in multiple papers)
- Novel connections between papers not explicitly stated
- Knowledge gaps (important questions none of the papers answer)
- Contradictions or tensions between papers

Step 4: Call put_page to write a synthesis note to wiki/synthesis/{TODAY} with these exact sections:
## Today's Papers
## Cross-Paper Themes
## Key Connections
## Open Questions
## Standout Finding

Keep each section concise. Write insights a researcher would find useful, not summaries they can already read on the individual paper pages. Begin now with Step 1.
"""


def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def submit_job() -> str | None:
    """Submit the subagent job and return the job ID."""
    try:
        r = subprocess.run(
            ["cmd.exe", "/c", GBRAIN_CMD, "agent", "run", PROMPT,
             "--timeout-ms", "1200000",   # 20 min wall-clock limit
             "--max-turns", "30",
             "--json"],
            capture_output=True, env=ENV, timeout=30,
        )
        stdout = (r.stdout or b"").decode("utf-8", errors="replace").strip()
        stderr = (r.stderr or b"").decode("utf-8", errors="replace").strip()

        if r.returncode != 0:
            log(f"ERROR submitting job: {stderr[:300]}")
            return None

        # Try to parse job ID from JSON output
        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    data = json.loads(line)
                    job_id = str(data.get("jobId") or data.get("job_id") or data.get("id", ""))
                    if job_id:
                        return job_id
                except Exception:
                    pass

        # Fallback: look for "Job #N" in stdout
        import re
        m = re.search(r"[Jj]ob\s*#?(\d+)", stdout)
        if m:
            return m.group(1)

        # Fallback: bare integer on its own line (gbrain outputs just the ID)
        for line in stdout.splitlines():
            line = line.strip()
            if line.isdigit():
                return line

        log(f"Could not parse job ID from output: {stdout[:200]}")
        return None

    except subprocess.TimeoutExpired:
        log("ERROR: gbrain agent run timed out after 30s")
        return None
    except Exception as e:
        log(f"ERROR: {e}")
        return None


def main():
    log(f"subagent-daily-synthesis started — {TODAY}")

    job_id = submit_job()
    if job_id:
        log(f"Submitted job #{job_id} — agent is now running autonomously")
        log(f"Result will be written to wiki/synthesis/{TODAY}")
    else:
        log("Failed to submit job — check gbrain is running")
        sys.exit(1)

    log("Done -- agent is running in background, check Streamlit > Minions > What did my subagent do?")


if __name__ == "__main__":
    main()
