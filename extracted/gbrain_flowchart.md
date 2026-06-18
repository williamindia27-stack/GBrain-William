---
title: "GBrain FlowChart"
type: paper
---

## Overview

A comprehensive architecture diagram of the personal GBrain AI brain system. It maps four interconnected subsystems — Setup Journey, Paper Pipeline, Automated Minions, and GBrain Architecture — plus the Signal Lifecycle that ties them together. The flowchart shows how a fully automated personal AI brain operates 24/7 from PDF ingestion to hybrid search and knowledge growth.

## Setup Journey

6 sequential steps building the system from scratch:

1. **Install GBrain** — git clone + bun link, Windows workarounds applied
2. **Started with PGLite** — local embedded Postgres
3. **Migrated to Neon Postgres** — serverless cloud database
4. **Built Streamlit Dashboard** — gbrain_app.py with Search · Ask · Read · Minions · Brief tabs
5. **Paper Ingestion Pipeline** — auto-import.py · pypdf · Groq · .md files
6. **10+ Minions via Task Scheduler** — fully automated running system

→ **Fully Automated Personal AI Brain running 24/7**

## Paper Pipeline

Sequential flow for ingesting research papers:

1. **PDF Drop** — Desktop/Papers folder
2. **auto-import.py** — watches every 30 min
3. **Text Extract** — pypdf reads PDF
4. **Groq Summarise** — LLM generates summary
5. **Write .md** — extracted/ directory
6. **Minion Queue** — import job submitted
7. **Neon Postgres** — embeddings + metadata stored
8. **Streamlit Dashboard** — searchable · readable · briefable

## Automated Minions

**Orchestration:** Windows Task Scheduler → Triggers → Worker Queue

**10 scheduled triggers:**
- auto-import — every 30 min
- arxiv-download — daily
- embed-stale — every 30 min
- brain-backup — 11 am + 4 pm
- daily-brief — 8 am
- streamlit-ping — hourly watchdog
- check-new-papers — daily
- clean-logs — weekly
- prune-backups — weekly
- weekly-digest — Fridays

## GBrain Architecture

Core components:

- **Brain Repo** — markdown knowledge base (source of truth)
- **GBrain Engine** — signal processor · embedder · minion runner · hybrid search
- **AI Agent** — Groq LLM · context builder · answer synthesiser

### Hybrid Search — 8 Stages

1. Query Parse
2. Keyword Extract
3. Embed Query
4. Vector Search
5. BM25 Full-text
6. RRF Fusion
7. Re-rank
8. Return Top-K

## Signal Lifecycle

8-step lifecycle for every signal processed by GBrain:

1. **Signal arrives**
2. **Detector identifies type**
3. **Brain-First retrieves context**
4. **Respond** — LLM answers
5. **Write Back** — saves to brain
6. **Auto-Link** — cross-references notes
7. **Sync** — propagates changes
8. **Brain Smarter** — knowledge grows

## Method

Built as a TypeScript/Bun CLI (`gbrain`) layered over Neon Postgres + pgvector. Papers are ingested via `auto-import.py` (pypdf → Groq LLM → markdown) then imported into the DB with Voyage AI embeddings. Hybrid search combines BM25 full-text with pgvector cosine similarity using Reciprocal Rank Fusion (RRF). Synthesis (`gbrain think`) pulls 40 top pages and calls Anthropic Claude to generate a cited answer. Automation runs via Windows Task Scheduler with 15+ scheduled tasks (minions). The Streamlit dashboard (`gbrain_app.py`) provides the user interface.

## Key Results

- 25+ research papers ingested, embedded, and searchable
- Hybrid search (BM25 + RRF) returning relevant results with MRR ~0.53
- 15+ automated minions running on schedule via Windows Task Scheduler
- Daily briefs and weekly digests generated from brain contents
- `gbrain think` synthesis with Claude producing coherent cited answers (avg 4.14/5 LLM-judge score)
- Graph extraction building knowledge links between pages

## Why It Matters

Transforms passive PDF reading into an active, searchable, auto-growing knowledge graph. Papers consumed today can be retrieved, cross-referenced, and synthesised months later without manual effort. The 24/7 automation means the brain keeps growing even without direct interaction — arxiv papers are downloaded, summarised, and embedded automatically.

## Limitations

- Windows-only (Task Scheduler, registry keys, Windows paths hardcoded)
- Single-user design — no multi-user or collaboration support
- Depends on external paid APIs: Voyage AI (embeddings), Anthropic (synthesis), Groq (summaries), Neon (database)
- Import pipeline scans entire extracted/ directory on each run (slow with 200+ files)
- PDF extraction quality varies — scanned or image-heavy PDFs produce thin summaries

## Authors

wprozenko (personal project)

## Keywords

personal AI brain, knowledge base, pgvector, hybrid search, BM25, RRF, Streamlit, Task Scheduler, Voyage AI, Anthropic Claude, Groq, Neon Postgres, automation, research paper ingestion

## Research Context

**What's new:** This paper contributes a comprehensive architecture diagram of the personal GBrain AI brain system, which is not currently in the brain. The key novel element is the mapping of four interconnected subsystems and the Signal Lifecycle that ties them together.

**Related in brain:** 
* None are truly related, as no related pages were found in the brain.

**Knowledge gaps:** This paper assumes a certain level of understanding of AI brain systems and their components, which may not be covered in the brain. To fully evaluate this work, one would need to learn about the specifics of personal AI brain systems and their applications.

**Explore next:** 
* The Signal Lifecycle and its role in the GBrain AI brain system
* The Automated Minions subsystem and its functionality
* Hybrid search and knowledge growth in personal AI brain systems

*Generated 2026-06-09 by research-notes.py*

<!-- timeline -->

## Timeline

- **2026-06-09** — Initial import (incorrect — previous vision extraction described wrong flowchart)
- **2026-06-09** — Re-extracted correctly from PDF direct read — GBrain architecture flowchart
