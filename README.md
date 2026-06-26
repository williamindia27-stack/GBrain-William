# GBrain - Personal Research Brain

A personal AI knowledge base that automatically ingests papers, builds a knowledge graph, and surfaces insights.
Built on [gbrain](https://github.com/garrytan/gbrain) `v0.42.51.0` · Streamlit UI · Postgres + pgvector · Voyage AI embeddings · NVIDIA NIM / Groq LLM.

> **How it works:** gbrain is designed to be used through **Claude** - connect it via MCP and Claude handles everything through skills (search, capture, enrich, ingest) directly in chat. The **Streamlit app** is a visual dashboard on top of the same brain - useful for browsing, monitoring pipelines, and exploring data visually, but **it does not have access to skills**. However, **any skill can be manually replicated** as a **minion script** or a Streamlit button - a minion is just the same gbrain CLI commands a skill would run, triggered by a schedule or a click instead of Claude. Both interfaces read and write the same brain database.

---

## How to Install

### Step 1 - Install gbrain via your AI agent (recommended)

The easiest way is to let your AI agent handle the full install. Paste this into Claude Code, Cursor, Codex, or any agent that can run shell commands:

```
Retrieve and follow the instructions at:
https://raw.githubusercontent.com/garrytan/gbrain/master/INSTALL_FOR_AGENTS.md
```

The agent will install gbrain, ask for your API keys, and verify everything works. ~30 minutes.

> Don't have an agent yet? See the [gbrain documentation](https://github.com/garrytan/gbrain) for other install options.

---

### Step 2 - Set up this brain

Once gbrain is installed, set up our specific brain (the Streamlit app, automation scripts, and folder structure).

**1. Place the brain folder at `C:\**

Copy the `brain` folder into `C:\` (the root of your C drive). When done, `C:\brain\gbrain_app.py` should exist.

> **Note:** When downloaded from GitHub, the folder may be named `brain-main` or similar. Rename it to `brain` before placing it in `C:\`.

**2. Install Python dependencies**
```bat
pip install streamlit pandas pypdf pdfplumber requests
```

**3. Set up scheduled tasks**

Run the setup script once as Administrator - it registers all tasks automatically:

1. Right-click `C:\brain\setup-scheduled-tasks.ps1`
2. Select **Run with PowerShell**
3. Verify with: `Get-ScheduledTask | Where-Object TaskName -like "GBrain*"`

This creates all the automation tasks (paper import, embeddings, briefs, backups, etc.). See the Minions section below for the full list.

**4. Run the app**
```bat
streamlit run C:\brain\gbrain_app.py
```

Streamlit will open the app automatically in your browser.

---

### Step 3 - Connect Claude Desktop to your brain (optional but recommended)

This lets Claude read and write your brain directly during conversations - skills become active and Claude can search, capture, and enrich pages without you leaving the chat.

**Run the setup script (one command):**

1. Right-click `C:\brain\setup-claude-mcp.ps1` → **Run with PowerShell**
2. Restart Claude Desktop

That's it. The script auto-detects your username, patches the Claude config file, and confirms when done.

<details>
<summary>Manual setup (if the script doesn't work)</summary>

Open `C:\Users\<you>\AppData\Roaming\Claude\claude_desktop_config.json` and add gbrain inside `"mcpServers"`:

```json
{
  "mcpServers": {
    "gbrain": {
      "command": "C:\\Users\\<you>\\.bun\\bin\\gbrain.exe",
      "args": ["serve"],
      "env": {
        "NODE_TLS_REJECT_UNAUTHORIZED": "0"
      }
    }
  }
}
```

> Replace `<you>` with your Windows username. The `NODE_TLS_REJECT_UNAUTHORIZED` flag is needed on corporate networks with self-signed certificates.

</details>

---

## Folder Structure

```
C:\brain\
├── papers\          Drop PDFs here - the watcher picks them up automatically
├── extracted\       Structured markdown for every paper, person, company, meeting
│   ├── people\      Researcher profiles (people/slug.md)
│   ├── companies\   Institution stubs (companies/slug.md)
│   └── meetings\    Meeting notes (meetings/YYYY-MM-DD-HHMM.md)
├── briefs\          Daily AI-generated brain summaries
├── digests\         Weekly synthesis reports
├── alerts\          New-paper alert files
├── backups\         Database snapshots
├── eval-results\    Evaluation run outputs (search, model, minions, gaps)
├── eval-temp\       Temporary eval working files
├── minions\         All automation scripts and their logs (see below)
│
├── gbrain_app.py    Streamlit UI - run with: streamlit run gbrain_app.py
├── known-papers.txt     Tracks which papers have been processed
├── known-arxiv-ids.txt  Tracks which arXiv IDs have been downloaded
└── known-import-pdfs.txt Tracks which PDFs have been imported
```

---

## Running the App

```bat
streamlit run C:\brain\gbrain_app.py
```

Streamlit opens the app automatically in your browser. Tabs:
- **Search** - hybrid semantic + keyword search (BM25 + vector). Reranker merges results. MMR toggle adds diversity. Use for raw retrieval across all pages.
- **Ask** - RAG chat: LLM synthesizes an answer from your brain pages. Returns citations, gap analysis, and confidence. Toggle 🔗 Relationship mode to walk typed graph edges (invested_in, works_at, founded) for "who invested in X" type questions.
- **Read Paper** - full-text reader for any imported paper. Enrich: extract authors & institutions, generate Research Context, fix missing sections.
- **Graph** - three views of your knowledge graph
  - 🔬 Research Graph - papers → authors → institutions, extracted from PDFs. Visual force-directed graph.
  - 👤 Personal Graph - your own network: add people, companies, meetings. Explore connections.
  - 🧠 Who Knows? - given a topic, finds people in your network with relevant expertise.
- **Minions** - all automation pipelines, logs, and manual controls
  - 🔄 Sync Brain - re-ingests markdown files from disk into the DB. Resumable - picks up where it left off.
  - ⚡ Embed Stale Pages - generates embeddings for pages missing them. Pace mode throttles rate to avoid API limits.
  - 🌙 Dream Cycle - full maintenance run: extract → embed → backlinks → lint → orphans.
- **Brief** - three auto-generated intelligence reports
  - 📋 Daily Brief - AI summary of recent papers + brain activity. Runs daily at 9:30 AM.
  - 📰 Weekly Digest - weekly cross-paper theme synthesis. Runs every Friday at 3 PM.
  - 🔔 Alerts - notifications when a new paper matching your interests is added.
- **Capture** - quick-save a thought, note, or idea directly into the brain.
- **Intel** - brain analytics and diagnostics
  - ⚡ Anomalies - detects tag/type cohorts with statistically unusual activity vs. historical baseline.
  - 🔥 Hot Pages - most salient pages right now, ranked by recent activity.
  - 🏥 Health - full brain diagnostic: embedding coverage, orphans, missing sections, sync staleness.
  - 🧠 Advisor - ranked action list: pending migrations, orphaned pages, stale syncs, setup gaps.
  - 🔭 Watch - push-based context. Run `gbrain watch` in a terminal to have your brain volunteer relevant pages during a conversation.
- **Synthesis** - AI-generated cross-paper insight reports. Daily synthesis finds recurring themes and writes them to wiki/synthesis/.
- **Eval** - evaluation dashboard: search quality benchmarks, LLM answer quality, pipeline health checks, and gaps audit.
- **Help** - in-app guide with one-line descriptions of every tab and sub-tab.

---

## Minions - Automation Pipelines

All scripts live in `minions\`. They run as Windows Scheduled Tasks.

### Paper Pipeline (daily, ~11 AM)
| Script | Schedule | What it does |
|--------|----------|-------------|
| `papers-watcher.ps1` | Every 5 min | Watches `papers\` for new PDFs, triggers import immediately |
| `arxiv-download.bat` | Daily 11:00 | Downloads new AI/ML papers from arXiv |
| `auto-import.bat` | Daily 11:20 | Converts PDFs → structured markdown, imports to brain |
| **`graph-extract.bat`** | **Daily 11:35** | **Resolves `[[wikilinks]]`, writes typed edges to links table** |
| `fix-raw-dumps.bat` | Daily 11:40 | Re-runs Groq on any paper missing structured sections |
| **`embed-stale.bat`** | **Every 30 min** | **Generates Voyage AI embeddings for new/updated pages** |
| **`build-research-graph.bat`** | **Daily 1:45 PM** | **Extracts authors & institutions from PDFs, builds graph** |
| `enrich-researchers.bat` | Daily 2:15 PM | Fills researcher/institution stubs with Groq-generated bios |
| `research-notes.bat` | Daily 2:30 PM | Adds Research Context to each paper (gaps, related pages) |

### Intelligence (daily)
| Script | Schedule | What it does |
|--------|----------|-------------|
| `daily-brief.bat` | Daily 9:30 AM | AI summary of recent papers and brain activity |
| `weekly-digest.bat` | Friday 3:00 PM | Weekly synthesis of key themes |
| `subagent-daily-synthesis.bat` | Daily 3:00 PM | Cross-paper theme discovery, writes to `extracted/wiki/synthesis/` |
| `bio-agent.bat` | On demand | Enriches a specific researcher bio |

### Maintenance
| Script | Schedule | What it does |
|--------|----------|-------------|
| `backup-brain.bat` | Daily 11 AM & 4 PM | Snapshots the full brain database to `backups\` |
| `clean-logs.bat` | Wednesday 11 AM | Trims old log files |
| `prune-backups.bat` | Wednesday 11 AM | Removes old backup snapshots beyond retention window |
| `streamlit-ping.bat` | Every hour | Health-checks the Streamlit app, restarts if down |
| **`dream-cycle.bat`** | **On demand** | **Full maintenance: extract → embed → backlinks → lint → orphans** |

> [!NOTE]
> The **bold** minions above collectively perform the same job as the dream cycle, running automatically on a schedule. Use `dream-cycle.bat` only for a manual on-demand run (e.g. after a bulk import).

### Evaluation
| Script | What it does |
|--------|-------------|
| `eval-search.bat` | Tests semantic search quality |
| `eval-model.bat` | Tests LLM answer quality |
| `eval-minions.bat` | Health-checks all minion pipelines |
| `eval-gaps.bat` | Audits papers missing sections or embeddings |
| `eval-pipeline.bat` | End-to-end pipeline evaluation |

---

## Adding a Paper Manually

1. Drop the PDF into `C:\brain\papers\`
2. The watcher picks it up within 5 minutes, or run `minions\auto-import.bat` manually
3. The paper appears in the app under Search and Read Paper

## Dream Cycle 24/7 - Autopilot

gbrain has a built-in autopilot daemon that runs the full dream cycle automatically every 5 minutes, as long as your machine is on. It continuously syncs, extracts wikilinks, generates embeddings, builds backlinks, lints, and finds orphans - keeping your brain sharp without any manual intervention.

**What it does:**
- `sync` - re-ingests any changed files
- `extract` - resolves wikilinks and builds typed graph edges
- `embed` - generates embeddings for new/updated pages
- `backlinks` - keeps the backlink index up to date
- `lint` - flags broken references
- `orphans` - finds pages with no connections

**How to start it** (run once in a terminal, keep it running):

```bat
set PATH=%PATH%;C:\Users\<you>\.bun\bin
gbrain autopilot --repo C:\brain
```

> Replace `<you>` with your Windows username.

Once running, you never need to press the Dream Cycle button manually - the autopilot handles it every 5 minutes.

---

### If autopilot can't run - Minions fallback

If autopilot fails to start (e.g. permission issues or PATH problems), the minion scripts cover the same job via Windows Task Scheduler:

- `embed-stale.bat` runs every 30 min
- `graph-extract.bat` runs daily
- `dream-cycle.bat` can be run manually after bulk imports

```bat
C:\brain\minions\dream-cycle.bat
```

Runs: extract → embed → backlinks → lint → orphans. Use after bulk imports.

---

## Skills (54 installed)

All skills live in `C:\Users\<you>\gbrain\skills\`. They are used by your AI agent - not the Streamlit app.

> [!NOTE]
> Skills are **agent playbooks** - tool-agnostic markdown files that tell any AI agent (Claude, Cursor, Codex, Claude Code) which gbrain commands to run and in what order. The Streamlit app never reads them. Skills activate when an agent is connected to gbrain via MCP (see Step 3 above). gbrain can also be used standalone via CLI (`gbrain search`, `gbrain think`, etc.) with no agent at all.

| Skill | What it does |
|-------|-------------|
| `signal-detector` | Always-on: captures ideas and entities from every message |
| `brain-ops` | Always-on: brain read/write/lookup |
| `query` | "What do we know about X", graph queries |
| `enrich` | Create/enrich a person or company page |
| `capture` | Quick "save this thought" |
| `idea-ingest` | Links, articles, tweets |
| `media-ingest` | Videos, PDFs, podcasts, books, screenshots |
| `meeting-ingestion` | Meeting transcripts |
| `ingest` | Generic ingest router |
| `brain-taxonomist` | Where does a brain page go / refile |
| `eiirp` | Organize/archive a research thread |
| `citation-fixer` | Fix broken citations |
| `data-research` | Research, trackers, investor updates |
| `publish` | Share a brain page as a link |
| `repo-architecture` | Filing rules |
| `frontmatter-guard` | Validate/fix frontmatter |
| `daily-task-manager` | Task add/complete/defer |
| `daily-task-prep` | Morning prep, day planning |
| `briefing` | Daily briefing |
| `cron-scheduler` | Cron scheduling, quiet hours |
| `gbrain-advisor` | Ranked brain recommendations |
| `gbrain-upgrade` | Upgrade gbrain |
| `reports` | Save/load reports |
| `skill-creator` | Create a new skill |
| `skillify` | Make something into a proper skill |
| `skill-optimizer` | Optimize/improve existing skills |
| `skillpack-check` | Brain health check |
| `skillpack-harvest` | Promote a skill upstream to gbrain |
| `smoke-test` | Post-restart health check |
| `cross-modal-review` | Second opinion via another model |
| `testing` | Skill validation |
| `webhook-transforms` | External event processing |
| `minion-orchestrator` | Background jobs and agents |
| `ask-user` | Choice gate / user decision |
| `setup` | First boot setup |
| `cold-start` | Bootstrap / fill brain |
| `migrate` | Migrate from Obsidian/Notion/Logseq |
| `maintain` | Brain health, dream cycle, extraction |
| `soul-audit` | Agent identity |
| `functional-area-resolver` | Compress large RESOLVER.md |
| `book-mirror` | Personalized book analysis |
| `article-enrichment` | Enrich brain pages |
| `strategic-reading` | Read through a lens / extract playbook |
| `concept-synthesis` | Find patterns across notes |
| `idea-lineage` | Trace how thinking on a topic evolved |
| `perplexity-research` | Web research / current state of X |
| `archive-crawler` | Find gold in old files |
| `academic-verify` | Verify academic claims |
| `brain-pdf` | Export brain page as PDF |
| `voice-note-ingest` | Voice memo transcription and filing |
| `schema-author` | Add/evolve page types |
| `schema-unify` | Consolidate page types |
| `data-research` | Structured data research |

---

## Cross-Session Memory — Why Claude Needs to Be Taught to Use the Brain

gbrain stores and retrieves knowledge. But connecting gbrain via MCP is not enough on its own — a new Claude session has no idea the brain exists or that it should search it before answering. Without explicit instructions, Claude will answer from its own training data and say "I don't know" for personal questions that are already in your brain.

There are two layers that fix this:

### Layer 1 — Retrieval Reflex (automatic, no setup needed)

The gbrain engine scans every user message for named entities (people, places, projects, pets) and automatically injects a compact pointer — `name → slug → one-line summary` — into Claude's context. Zero-LLM, deterministic, always-on.

This means if you mention "Veka" in a message, gbrain detects the name, finds `pets/veka` in the brain, and tells Claude the page exists — before Claude even responds. Claude then knows to open it.

Verify it's on:
```powershell
gbrain config get retrieval_reflex
# should return: true
```

### Layer 2 — Policy Instructions (tells Claude *how* to act on pointers)

Retrieval Reflex points Claude to a page. But without a policy, Claude may still ignore the pointer or re-search what's already in its context. The policy layer tells Claude: *"when a brain pointer appears, open that page; when asked a personal question, search the brain first; never say I don't know without checking."*

**Which policy mechanism to use depends on your agent:**

| Agent | Mechanism | Where it lives |
|---|---|---|
| **Claude Code** | `CLAUDE.md` — auto-loaded every session, no settings needed | `C:\Users\<you>\.claude\CLAUDE.md` |
| **Claude Desktop** | System prompt — must be set manually in Settings → Custom Instructions | Settings → Custom Instructions |
| OpenClaw / Hermes / custom agent | `RESOLVER.md` + retrieval-reflex policy skill | `C:\brain\skills\RESOLVER.md` |

#### For Claude Code — CLAUDE.md

Claude Code automatically loads `~\.claude\CLAUDE.md` into every session. Create it once and every future session will know about the brain, the brain-first protocol, and any facts you hardcode (like your pet's name).

Create `C:\Users\<you>\.claude\CLAUDE.md`:

```markdown
# Claude Instructions

## Brain-First Protocol

You have access to a personal knowledge base (gbrain) via MCP tools (`mcp__gbrain__*`).

Always search gbrain before answering questions about people, pets, projects,
documents, or anything personal. Use `mcp__gbrain__recall` for natural language
questions or `mcp__gbrain__search` for keywords.

Never say "I don't know" for personal questions without searching gbrain first.
```

#### For custom agents (OpenClaw, Hermes, etc.) — RESOLVER.md + policy skill

Install the retrieval-reflex policy skill into the brain repo:
```powershell
gbrain integrations install retrieval-reflex --target "C:\brain"
```

Then add a trigger row to `C:\brain\skills\RESOLVER.md`:
```
retrieval-reflex | a named person/company/project/place becomes the subject;
a brain-page pointer appears in context; "who is", "what do we know about",
"tell me about"; about to assert a non-trivial detail about a named entity
```

The policy skill lives at `C:\brain\skills\retrieval-reflex\` after install.

### How the full stack works together

```
User asks: "what color is my dog Veka?"
        ↓
Retrieval Reflex   →  detects "Veka", injects pointer: pets/veka
        ↓
CLAUDE.md policy   →  tells Claude to open brain pages when pointers appear
        ↓
Claude opens pets/veka  →  answers: "white, light-colored coat, floppy ears"
```

Without Layer 1: Claude never knows the page exists.
Without Layer 2: Claude sees the pointer but may ignore it or re-search anyway.
Both together: instant, accurate, zero re-explanation needed across sessions.

---

## Environment Variables (set in Windows registry `HKCU\Environment`)

You need 2 API keys - one LLM, one embedding. A third LLM key can be set as fallback.

| Variable | Purpose |
|----------|---------|
| `NVIDIA_API_KEY` | LLM - for synthesis, enrichment, and briefs. Get one at [build.nvidia.com](https://build.nvidia.com) |
| `GROQ_API_KEY` | LLM - for daily briefs, weekly digests, research notes |
| `VOYAGE_API_KEY` | Embeddings - any provider supported by gbrain works |
| `DATABASE_URL` | Optional - Postgres connection string (skip to use built-in PGLite) |

> **Why optional?** gbrain uses PGLite (embedded Postgres, no server needed) by default. Only set `DATABASE_URL` if you want to connect to an external Postgres database (e.g. Supabase) for large brains (1000+ pages) or multi-machine access.

---

## Company Brain

gbrain supports multi-user deployments with per-user access scoping. Each person on the team gets their own slice of the brain - you only see what you're allowed to see, never another person's notes, never another team's data.

### Architecture

| Layer | Who sees it | What goes in |
|---|---|---|
| **Company-wide** | Everyone | Methodologies, templates, case studies, public docs |
| **Per-project** | Project team only | Client docs, meeting notes, deliverables |

Each layer is a separate source in the same Postgres database. Access is scoped at login - a consultant on Project A never sees Project B's data. The dream cycle runs 24/7 keeping all layers sharp.

### What it takes to deploy
- A shared Postgres database (Supabase or internal server) - set `DATABASE_URL` for all team members
- This Streamlit app deployed on a server (accessible by the whole team via browser)
- A login layer (Streamlit authentication or a reverse proxy with SSO)

> The Streamlit app already covers Search, Ask, Graph, Brief, Intel, and all pipeline monitoring - the hard part is built. Adding multi-user support is primarily a deployment and authentication step.

### Concretely for a consulting firm

- One shared Postgres brain per team or practice
- Everyone ingests their own meeting notes, client docs, and research
- Anyone can query the whole team's knowledge, within their access scope
- Automated minion scripts run 24/7 in the background - ingesting, embedding, graphing, and briefing continuously (Windows equivalent of gbrain's built-in autopilot daemon)

---

## Troubleshooting

### 1. `pip` not recognized

**Error:** `pip : The term 'pip' is not recognized...`

**Fix:** Use `python -m pip` instead of `pip`, or add Python's Scripts folder to PATH:
```
C:\Users\<you>\AppData\Local\Python\pythoncore-3.14-64\Scripts
```

---

### 2. GBrain postinstall blocked

**Error:** `Blocked 1 postinstall` after `bun install -g github:garrytan/gbrain`

**Fix:** Run:
```
gbrain apply-migrations --yes
```

---

### 3. GBrain init fails without embedding key

**Error:** `No embedding provider configured`

**Fix:** Run without embedding to skip for now:
```
gbrain init --pglite --no-embedding
```
Or pass your Voyage key directly:
```
gbrain init --pglite --embedding-model voyage:voyage-3-large
```

---

### 4. Embedding dimension mismatch

**Error:** `embedding: declared dims=1280 but actual is vector(1024)`

**Fix:**
```
gbrain reinit-pglite --embedding-model voyage:voyage-3-large --embedding-dimensions 1024 --yes
```

---

### 5. Missing Python module

**Error:** `ModuleNotFoundError: No module named 'wordninja'`

**Fix:**
```
python -m pip install wordninja
```

Apply the same fix for any other missing module — replace `wordninja` with the module name shown in the error.

---

### 6. Scheduled tasks — Access Denied

**Error:** `Register-ScheduledTask : Access is denied`

**Fix:** Run PowerShell as Administrator — right-click the PowerShell icon → **Run as administrator**, then re-run the setup script.

---

### 7. App shows "No LLM — retrieval only"

**Symptom:** The Streamlit app loads but shows `No LLM — retrieval only` and the Ask tab is disabled.

**Fix:** Set your `NVIDIA_API_KEY` in the Windows registry (see Environment Variables section above). If you have a Groq key, set `GROQ_API_KEY` as a fallback.

---

### 8. Downloaded folder has wrong name

**Symptom:** `C:\brain\gbrain_app.py` does not exist after copying the folder.

**Fix:** When downloaded from GitHub, the folder may be named `brain-main` or similar. Rename it to `brain` before placing it in `C:\`.
