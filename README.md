# GBrain — Personal Research Brain

A personal AI knowledge base that automatically ingests papers, builds a knowledge graph, and surfaces insights.
Built on [gbrain](https://github.com/garrytan/gbrain) `v0.42.51.0` · Streamlit UI · Postgres + pgvector · Voyage AI embeddings · Anthropic / Groq LLM.

---

## How to Install

### Step 1 — Install gbrain via your AI agent (recommended)

The easiest way is to let your AI agent handle the full install. Paste this into Claude Code, Cursor, Codex, or any agent that can run shell commands:

```
Retrieve and follow the instructions at:
https://raw.githubusercontent.com/garrytan/gbrain/master/INSTALL_FOR_AGENTS.md
```

The agent will install gbrain, ask for your API keys, and verify everything works. ~30 minutes.

> Don't have an agent yet? See the [gbrain documentation](https://github.com/garrytan/gbrain) for other install options.

---

### Step 2 — Set up this brain

Once gbrain is installed, set up our specific brain (the Streamlit app, automation scripts, and folder structure).

**1. Place the brain folder at `C:\**

Copy the `brain` folder into `C:\` (the root of your C drive). When done, `C:\brain\gbrain_app.py` should exist.

**2. Install Python dependencies**
```bat
pip install streamlit pandas pypdf pdfplumber requests
```

**3. Set up scheduled tasks**

Run the setup script once as Administrator — it registers all tasks automatically:

1. Right-click `C:\brain\setup-scheduled-tasks.ps1`
2. Select **Run with PowerShell**
3. Verify with: `Get-ScheduledTask | Where-Object TaskName -like "GBrain*"`

This creates all the automation tasks (paper import, embeddings, briefs, backups, etc.). See the Minions section below for the full list.

**4. Run the app**
```bat
streamlit run C:\brain\gbrain_app.py
```

Open `http://localhost:8501` in your browser.

---

## Folder Structure

```
C:\brain\
├── papers\          Drop PDFs here — the watcher picks them up automatically
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
├── gbrain_app.py    Streamlit UI — run with: streamlit run gbrain_app.py
├── known-papers.txt     Tracks which papers have been processed
├── known-arxiv-ids.txt  Tracks which arXiv IDs have been downloaded
└── known-import-pdfs.txt Tracks which PDFs have been imported
```

---

## Running the App

```bat
streamlit run C:\brain\gbrain_app.py
```

The app runs at `http://localhost:8501` and has tabs for:
- **Search** — hybrid semantic + keyword search across all papers
- **Ask** — chat with your brain (RAG over all pages)
- **Read Paper** — read + enrich any imported paper
- **Graph** — visual knowledge graph
  - 🔬 Research Graph — papers, authors, institutions
  - 👤 Personal Graph — add/explore people, companies, meetings
  - 🧠 Who Knows? — find who in your network knows what
- **Minions** — monitor all automation pipelines and their logs
- **Brief**
  - 📋 Daily Brief
  - 📰 Weekly Digest
  - 🔔 Alerts
- **Capture** — quick capture: add a note directly to your brain
- **Intel** — brain analytics
  - ⚡ Anomalies — detects unusual activity spikes
  - 🔥 Hot Pages — most salient pages right now
  - 🏥 Health — full brain diagnostic
  - 🧠 Advisor — ranked recommendations: pending migrations, orphans, stale syncs, setup issues
- **Synthesis** — AI-generated cross-paper insights
- **Eval** — evaluation dashboard (search quality, model quality, pipeline health, gaps audit)

---

## Minions — Automation Pipelines

All scripts live in `minions\`. They run as Windows Scheduled Tasks.

### Paper Pipeline (daily, ~11 AM)
| Script | Schedule | What it does |
|--------|----------|-------------|
| `papers-watcher.ps1` | Every 5 min | Watches `papers\` for new PDFs, triggers import immediately |
| `arxiv-download.bat` | Daily 11:00 | Downloads new AI/ML papers from arXiv |
| `auto-import.bat` | Daily 11:20 | Converts PDFs → structured markdown, imports to brain |
| `graph-extract.bat` | Daily 11:35 | Resolves `[[wikilinks]]`, writes typed edges to links table |
| `fix-raw-dumps.bat` | Daily 11:40 | Re-runs Groq on any paper missing structured sections |
| `embed-stale.bat` | Every 30 min | Generates Voyage AI embeddings for new/updated pages |
| `build-research-graph.bat` | Daily 1:45 PM | Extracts authors & institutions from PDFs, builds graph |
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
| `dream-cycle.bat` | On demand | Full maintenance: extract → embed → backlinks → lint → orphans |

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

## Running a Dream Cycle (manual maintenance)

```bat
C:\brain\minions\dream-cycle.bat
```

Runs: extract → embed → backlinks → lint → orphans. Use after bulk imports.

---

## Skills (54 installed)

All skills live in `C:\Users\<you>\gbrain\skills\`. They are used by your AI agent — not the Streamlit app.

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

## Environment Variables (set in Windows registry `HKCU\Environment`)

You need 2 API keys — one LLM, one embedding. A third LLM key can be set as fallback.

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | LLM — for `gbrain think`, enrichment, and briefs |
| `GROQ_API_KEY` | LLM fallback — used if no Anthropic key is set |
| `VOYAGE_API_KEY` | Embeddings — any provider supported by gbrain works |
| `DATABASE_URL` | Optional — Postgres connection string (skip to use built-in PGLite) |
