# GBrain – System Documentation

## Contents







## Two ways to query your brain
Gbrain search : return top retrieved pages, ranked by hybrid scoring (vector + keyword+ rrf + source-tier boost + reranker)
Gbrain think : runs same retrieval, then composes a synthesized answer across the results with explicit citations to the source pages and an honest note on what brain doesn’t know
### What it does
signal  →  search  →  respond  →  write  →  auto-link  →  sync
(every	(brain-first (informed	(page +	(typed edges	(cron
message) retrieval)	by context) timeline) + backlinks)	keeps fresh)

## Capabilities
Hybrid search. Vector (HNSW on pgvector) + BM25 keyword + reciprocal-rank fusion + source-tier boost + intent-aware query rewriting. Three named search modes (conservative, balanced, tokenmax) bundle the cost/quality knobs into a single config key
Self-wiring knowledge graph : Every put_page extracts entity refs from markdown/wikilinks/typed-link syntax and writes edges with zero LLM calls.
Job Queue (Minions) : Durable subagents (LLM tool loops that survive crashes via two-phase pending→done persistence),
54 curated skills : Covers signal capture, ingest (idea / media / meeting), enrichment, querying, brain ops, citation fixing, daily task management, cron scheduling, reports, voice, soul audit, skill creation, eval framework, and migrations. Skills are markdown files (tool-agnostic), packaged as a single skillpack the installer drops into your agent workspace.
### How to create skills ? :
To create a skill : "skill-creator"
A skill is just a markdown file (SKILL.md) placed in a folder under C:\Users\wprozenko\gbrain\skills\. Every skill has:

Frontmatter — name, version, description, triggers, tools, mutating
Contract — what it guarantees
Phases — step-by-step workflow
Output Format — what the result looks like
Anti-Patterns — what NOT to do

Evaluation framework. gbrain eval longmemeval runs the public LongMemEval benchmark against your hybrid retrieval. gbrain eval export + gbrain eval replay capture real queries and replay them against code changes (set GBRAIN_CONTRIBUTOR_MODE=1).
‘gbrain eval --qrels ./eval-qrels.json’


## Integrations
Data flowing into the brain. Each integration is a recipe — markdown + setup hints — that ships in recipes/ and is discoverable via gbrain integrations list.
- Voice: Phone calls create brain pages via Twilio + OpenAI Realtime (or DIY STT+LLM+TTS). Setup recipe: recipes/twilio-voice-brain.md.
- Email + calendar: webhook handlers that route to brain signals. docs/integrations/meeting-webhooks.md.
- Embedding providers: 16 recipes covering OpenAI (default fallback), OpenRouter, Voyage, ZeroEntropy (default), Google Gemini, Azure OpenAI, MiniMax, Alibaba DashScope, Zhipu, Ollama (local), llama.cpp llama-server (local), LiteLLM proxy. Pricing matrix + decision tree in docs/integrations/embedding-providers.md.
- Rerankers: ZeroEntropy zerank-2 hosted (default in tokenmax mode) plus the
v0.40.6.1 llama-server-reranker recipe for fully-local cross-encoder rerank via llama.cpp — runs Qwen3-Reranker or self-hosted ZeroEntropy weights against the
same gateway.rerank() seam. Setup walkthrough in docs/ai-providers/llama-server-reranker.md.
- Credential gateway: vault-aware secret distribution. docs/integrations/credential-gateway.md.
- MCP clients: every major MCP client is supported. docs/mcp/ per-client setup.


## Architecture
- Two engines, one contract. PGLite (Postgres 17 via WASM, zero-config, default) for personal brains up to ~50K pages. Postgres + pgvector (Supabase or self-hosted) for shared / large / multi-machine deployments. The contract-first BrainEngine interface in src/core/engine.ts defines ~47 operations both engines implement; CLI and MCP server are generated from one source.
- Brain repo is the system of record. Your knowledge lives in a regular git repo (your "brain repo") as markdown files. GBrain syncs the repo into Postgres for retrieval; deletes in git become soft-deletes in DB. You can publish public subsets, share team mounts, run thin-client setups pointing at a colleague's brain server. Topologies
in docs/architecture/topologies.md.
- Two organizational axes (brain ⊥ source). A brain is a database (your personal brain, a team mount you joined). A source is a repo inside that brain (wiki, gstack, an essay, a

knowledge base). Routing lives in .gbrain-source dotfiles and resolves via a documented 6-tier precedence chain. Full diagrams in docs/architecture/brains-and-sources.md.
- Why the graph matters. Vector search returns chunks that are semantically close. The graph returns chunks that are factually connected. Hybrid search pulls from both; auto-linking on every write keeps the graph fresh. Deep
dive: docs/architecture/RETRIEVAL.md.








## Why GBrain
Chat & Meeting Notes: Works great. This is actually its strongest use case. You can query decisions, action items, and discussions directly.


Flowchart & Image Ingestion: Functional but maybe not reliable for complex diagrams (it worked for my gbrain flowchart) . Dense flowcharts with small text can be misread by the vision model. Simple diagrams work fine. Text-based PDFs are always more accurate.


Scalability: No issues. Built on Postgres with vector indexing, scales to thousands of documents. Supports team access with per-user data isolation. (Each person on the team gets their own slice of the brain, scoped by login. When you query, you only see what you're allowed to see, never another person's notes, never another team's data.


Bottom line: Strong for text and meeting notes, use caution with image-heavy content.


Normal RAG is one-stage retrieval, no memory, no relationships, stateless. :


For searching, RAG would vector only, GBrain does vector + BM25+ RRR


Query : RAG does 1 query, GBrain does multi-query expansion

Intent : RAG None, GBrain classify query type sp adjust search


Relationships : RAG None, GBrain knowledge graph, auto-linking between documents


Memory: RAG Stateless, GBrain grows, cross-references, finds pattern


Write-back: RAG, No, GBrain saves answers back to the brain


Ranking : RAG, Cosine similarity, GBrain Source-aware re-ranking


Synthesis : RAG, No, GBrain Dream cycle extracts insight across documents.


#### So, it can replace RAG for :


- Personal knowledge base
- Team institutional memory
- Document & Q&A
- Enterprise with compliance requirement (Partially)


It is partial because :
- ✅ Security is technically solid (OAuth 2.1, scoped tokens, RLS)
- ✅ Data isolation works (Fuzz-tested, zero leaks)
- ✅ Audit logging exists (File-based JSONL, not enterprise-grade)
✅ Full data control (self-hosted)(infra/keys)
- ❌ No formal certifications (SOC2, ISO 27001)
- ❌ No official penetration test report (no third party validation)

- ❌ No SAML/SSO for enterprise identity providers (OAuth 2.1 only)
- ❌ No signed data processing agreements
- ❌ Open source — no vendor to hold accountable
#### The tech is ready. The paperwork isn't.


GBrain is RAG done properly: hybrid search, graph relationships, and continuous learning on top. For knowledge management it outperforms basic RAG significantly. For custom production systems with specific requirements, standard RAG with a custom pipeline might be still more flexible.


It uses postgres only, with pgvector extension. It handles data and vector embedding as one DB
### At 20M token scale:
- GBrain can handle it (~100K–500K chunks) but requires significant server RAM
- No LLM can process 20M tokens in one go in production today. RAG-based systems like GBrain are the only practical approach at that scale
- Long-context LLMs are 1,250x more expensive per query and 60x slower than RAG
### Is GBrain better than standard RAG?
- Yes, it adds knowledge graph, keyword search, and reranking on top of standard vector RAG
- Their benchmark shows +31 points improvement over standard RAG (P@5)
- However: self-reported on 240 synthetic pages, not independently verified on real-world data
#### Benchmark source:
- Internal benchmark (BrainBench), run by the GBrain team on their own synthetic data
- No independent evaluation on standard benchmarks (BEIR, LongMemEval)
- Third-party site scored reliability at 4/100, worth noting the risk Bottom line:
Strong architecture for large-scale knowledge retrieval, outperforms standard RAG in their own testing, but benchmark credibility needs independent validation before making a full commitment.

#### Official GBrain benchmark might be the only one relevant so far.




System Precision@5	Recall@5
GBrain (hybrid + graph)	49.1% 97.9%
Hybrid RAG (vector + BM25, no graph)	17.8% 65.1% BM25/keyword only 17.1% 62.4%
Vector only (standard RAG)	10.8% 40.7% Key takeaway:
Standard vector RAG: 10.8% P@5 GBrain with everything: 49.1% P@5
The knowledge graph alone accounts for +31 points P@5 Even hybrid RAG without the graph only gets to 17.8%. Adding graph increase graph by more than 30%
There is no clean direct comparison between GBrain and a standard RAG system on the same independent dataset. Every comparison found either:
Uses GBrain's own synthetic corpus
Uses different metrics making them incomparable (example : Hindsight) Is qualitative not metric-based
The gbrain-evals repo itself admits:

"Not directly comparable to academic benchmark scores from other systems because the corpus is different"


















### What each does that the others don't
#### GBrain uniquely:
- Markdown-first, git as system of record
- Dream cycle: enriches knowledge overnight automatically
- Gap analysis: tells you what it doesn't know
- Runs entirely on Postgres, no extra infrastructure
- Minions: built-in job queue (Postgres-native), durable subagents that survive crashes, scheduled automation (43 triggers), rate leases, child jobs with cascading timeouts. Neither Neo4j nor Ontology RAG ship anything like this: they are retrieval systems only, not autonomous execution systems and token free
#### Neo4j uniquely:
- Stronger automatic multi-hop traversal across large heterogeneous corpora
- Mature ecosystem, battle-tested at enterprise scale
- Community detection for broad thematic queries (global mode)
#### Ontology RAG uniquely:
- Logical inference: deduces new facts from rules automatically
- Consistency checking: detects contradictions formally
- Provable entailment: required in regulated domains (healthcare, legal) Here are all the sources used for the comparison:


#### GBrain:

- Official README garrytan/gbrain: Garry's Opinionated OpenClaw/Hermes Agent Brain
- BrainBench benchmark: github.com/garrytan/gbrain-evals/blob/main/docs/benchmarks/2026-04-23-brainbench-v0.20.0.md
- GBrain evals repo: github.com/garrytan/gbrain-evals
- GBrain review: vectorize.io/articles/gbrain-review




#### Neo4j / GraphRAG:
- GraphRAG accuracy benchmarks: falkordb.com/blog/graphrag-accuracy-diffbot-falkordb
- GraphRAG vs Vector RAG comparison: lettria.com/blogpost/vectorrag-vs-graphrag-a-convincing-comparison
- Long-context vs RAG production framework: tianpan.co/blog/2026-04-09-long-context-vs-rag-production-decision-framework
- Databricks long context RAG: databricks.com/blog/long-context-rag-performance-llms


#### Ontology RAG:
- OG-RAG paper (EMNLP 2025): aclanthology.org/2025.emnlp-main.1674.pdf
- Ontology learning & knowledge graph: arxiv.org/abs/2511.05991
- When to use graphs in RAG: arxiv.org/html/2506.05690v3


#### General RAG at scale:
- pgvector benchmarks: tigerdata.com/blog/pgvector-vs-qdrant
- pgvector scaling: dev.to/philip_mcclarence_2ef9475/scaling-pgvector-memory-quantization-and-index-build-strategies-8m2



## What does my GBrain do/ how does it work ?
🔍 Search
What it does: Searches all your papers using hybrid AI search (vector + keyword combined).
When you type and press Enter: It runs your query through an 8-stage pipeline — classifies intent, expands the query, searches semantically and by keyword, fuses results, boosts the

most trusted content — then shows you scored passages with the paper name, a relevance bar, and the matching excerpt.
# then parses lines matching: [score] slug -- excerpt

# filters out scores < 0.45 and junk patterns (arxiv URLs, reference sections, etc.)

# for each result, calls expand_excerpt() which fetches the full page via gbrain get <slug> # and finds a wider passage around the matched chunk



💬 Ask
What it does: Lets you ask a question and get a synthesized AI answer from your brain.
When you click "Ask": If you have an Anthropic key, it runs gbrain think — retrieves 40 pages
+ graph edges and writes a full answer with citations and a "Knowledge Gaps" section. If you only have Groq, it retrieves passages and has Groq summarize them. If neither, it shows retrieval results only.
# gbrain think does: retrieves 40 pages + graph edges, calls Claude to synthesize # output is parsed: splits on "## Gaps" and footer separators
# shows answer (green box), knowledge gaps (yellow box), stats line (monospace)




📄 Read Paper
What it does: Lets you open and read any paper stored in your brain.
When you click "Load": It fetches the full structured markdown of the selected paper and displays it. If the paper is missing Authors or a Research Context section, buttons appear —
🕸️ Extract Authors (runs Groq on the PDF to pull author names + institutions), 🔬 Research Notes (generates a Research Context section), or ✨ Enrich All (does both at once), and writes the result back into the brain.
runs: subprocess.run(["cmd.exe", "/c", gbrain.cmd, "get", slug]) # strips YAML frontmatter (splits on "---") and renders the body
# result is cached with @st.cache_data(ttl=600) — 10 minute cache



🕸️ Graph
Has 3 sub-tabs:
🔬 Research Graph
What it does: Shows the network of papers, authors, and institutions extracted from your PDFs.
When you click "View Full Graph": Builds an interactive pyvis graph with all papers (blue boxes), people (green dots), and institutions (orange diamonds) you can drag, zoom, and hover. "⚙️ Extract" on a single paper runs Groq to pull that paper's authors from the PDF and link them. "⚙️ Extract All" does this for every paper that's still missing authors.
_build_research_graph_html()
# reads every paper's .md file from C:\Users\wprozenko\minions\extracted\ # parses the "## Authors" section for wikilinks like [[people/slug|Name]]
# builds a pyvis Network graph in memory
# papers → blue box nodes, people → green dot nodes, institutions → orange diamond nodes
# edges: paper→author (blue solid), author→institution (yellow dashed)
# returns raw HTML string, rendered via st.components.v1.html()
### 👤 Personal Graph
What it does: Lets you manually add people, companies, and meetings to your knowledge graph.
When you fill out a form and submit: It writes a structured markdown page to disk (people/, companies/, or meetings/ folder) and imports it into gbrain so it becomes searchable and linkable. The "Explore" mode lets you search and then click "Graph" on any result to see its connections.
# builds a markdown string with YAML frontmatter (type: person, tags: [contact]) # writes to: C:\Users\wprozenko\minions\extracted\people\<slug>.md
# then runs: subprocess.run(["cmd.exe", "/c", gbrain.cmd, "import", "--file", path, "--no-embed"])

### □ Who Knows?
#### What it does: Finds who in your brain has expertise on a topic.
When you click "Find": Runs gbrain whoknows — searches for people/companies ranked by how much they match the topic, how recently they were updated, and their salience score. Shows top results with medals (🥇🥈🥉) and lets you click "📄 View profile" to see their brain page.
gbrain whoknows searches for person/company pages

# ranks by: log(1 + raw_match) × exp(-days/180) × (0.5 + 0.5 × salience)

# returns JSON array, parsed and displayed as expandable expanders with metric bars




🤖 Minions
What it does: Shows all your background automation jobs and their live status.
At the top — "▶ Run Dream Cycle": Manually triggers the brain maintenance cycle (extract
→ embed → backlinks → lint → orphans) and shows you a live log as it runs.
"🤖 What did my subagent do?" expander: Lists recent gbrain subagent jobs with their status (✅ completed / 💀 dead / 🔄 active). Click a job to see what it did, and "📜 Load logs" to read its full execution transcript.
Below that — grouped minion panels (📚 Paper Pipeline / □ Intelligence / 🛠️ Maintenance): Each minion shows as a collapsible row with its schedule and a live status badge (● ok / ● failed / ● running). Expand one to see its last 50 log lines, newest first.

📋 Brief
Has 3 sub-tabs:
list_files(folder)
# os.listdir() on C:\Users\wprozenko\minions\briefs\ or \digests\
# returns .md files sorted reverse-alphabetically (newest date first)


read_md_file(folder, filename)
# opens the file directly, renders via render_brief_content()

# splits on "##" section headers, renders each section as a styled left-border div
📋 Daily Brief
What it does: Shows AI-generated daily summaries of recent papers and brain activity.
When you select a date from the dropdown: Reads the saved brief markdown file from disk and renders it with nice formatting. Generated automatically every day at 9:30 AM.
### 📰 Weekly Digest
What it does: Shows weekly synthesis reports of key themes and findings.
Same as Daily Brief — picks from a dropdown of available digest files. Generated every Friday at 3:00 PM.
🔔 Alerts
What it does: Shows notifications for newly imported papers.
On load: Scans the alerts folder and renders each alert as a green card showing the paper title, import date, and a short "What it is / Key contribution / Main finding" summary.

✏️ Capture
What it does: Lets you write a thought directly into your brain without needing a PDF.
When you fill the form and click "📥 Capture to Brain": Creates a structured markdown note (with type, tags, date, and timeline) in inbox/, then imports it into gbrain immediately so it's searchable. Below the form, your 10 most recent captures are shown as expandable cards.
# generates slug: f"inbox/{today}-{md5(body)[:8]}"
# writes markdown file to: C:\Users\wprozenko\minions\extracted\inbox\<date>-<hash>.md run_gbrain("import", "--file", file_path, "--no-embed")
# gbrain import chunks the markdown and stores it in the DB without embedding # (embedding happens later via the Auto-Embedder minion)

🔬 Intel
#### Has 4 sub-tabs:
⚡ Anomalies
What it does: Detects unusual spikes in brain activity by tag or page type.

When you click "Scan": Runs gbrain anomalies with your chosen lookback window and sigma threshold, then shows which content cohorts had statistically unusual activity (e.g. "finance pages spiked 2.4σ above baseline today") with the specific pages involved.
gbrain anomalies: queries DB for daily page counts per tag/type cohort # computes mean + stddev over lookback window
# flags cohorts where today's count > mean + (sigma × stddev)

# returns JSON array of {cohort, kind, sigma_observed, count, mean, stddev, page_slugs}


🔥 Hot Pages
What it does: Ranks which pages in your brain matter most right now.
When you click "Rank": Runs gbrain salience and shows pages scored by a formula combining emotional weight, number of notes/takes, and days since last update — with heat indicators (🔴□□) and a bar for each page.
gbrain salience: queries DB for pages updated within the window

# scores each: (emotional_weight × 5) + ln(1 + take_count) + 1/(1 + days_since_update) # returns JSON array sorted by score desc
🌿 Orphans
What it does: Finds pages with no incoming links — knowledge islands disconnected from the rest of your brain.
When you click "Find Orphans": Runs gbrain orphans and groups results by domain (people, companies, papers, etc.), showing you which pages are isolated and good candidates for linking or deleting.
or run_gbrain("orphans", "--json", "--include-pseudo") if checkbox is ticked # gbrain orphans: queries links table for pages with zero inbound edges
# groups results by slug prefix (people/, companies/, papers/, etc.) # returns JSON array of {slug, title, domain}

🏥 Health
What it does: Runs a full diagnostic on your brain and scores its overall health.
When you click "Run Diagnostics": Runs gbrain doctor and shows a score out of 100, then lists every check (embed coverage, link density, sync freshness, schema version, etc.) sorted by severity — red failures first, then warnings, then passing checks — with fix hints for anything broken.
gbrain doctor runs ~15 checks: schema_version, embed_coverage, link_density,

# sync_freshness, jsonb_integrity, orphans sample, queue_health, brain_score, etc.

# returns JSON: {health_score: 0-100, ok: bool, checks: [{name, status, message, fix}]} # status values: "ok" / "warn" / "fail" / "skip"
# sorted fail → warn → ok → skip before rendering



_read_authors_from_page(slug)

# opens C:\Users\wprozenko\minions\extracted\<slug>.md directly # walks lines, finds "## Authors" section
# parses lines matching: - [[people/slug|Name]] [[companies/slug|Institution]] # then builds a mini pyvis graph filtered to just that paper

Dream cycle : Synchronise md file to data, extract links, generate embedding if needed, update backlinks, lint detection, orphans
# records current line count in dream-cycle.log
proc = subprocess.Popen(["cmd.exe", "/c", r"C:\Users\wprozenko\minions\dream-cycle.bat"]) # polls log file every 1 second while proc.poll() is None
# streams new lines to screen in real time via st.empty().code() # waits for proc to finish, shows success/error
Sub Agent steps :
- receive its mission
- runs 2 search in parallel (turn 0)

Brain_search Brain_query
- Synthetize and writes the page Read all results
Writes a full structured summary with tables, cross-cutting themes, key takeaways Calls brain_put_page – saves to wiki/agents/52/my-summary
- Confirms Page created
Returns a recap of what it did



## 🗺️ GBrain App — Full Feature List
🖥️  App  Architecture
- 7 tabs — Search · Ask · Read Paper · Graph · Minions · Brief · Capture
- Streamlit frontend talking to gbrain CLI via subprocess
- Dynamic paper discovery — auto-detects any new .md in extracted/ so newly imported papers appear without code changes
- Postgres/PGLite engine detection shown in sidebar and header caption
- Voyage AI embeddings with hybrid search (8-stage pipeline: intent classifier → multi-query expansion → vector HNSW + keyword tsvector → RRF fusion → compiled-truth boost → dedup)
#### Tab 1 — Search
- Full hybrid search via gbrain query
- Junk filter strips raw metadata lines, citation blocks, and naked URLs from results
- Score threshold (≥ 0.45) so low-confidence results don't surface
- Result cards with score badge, slug, human-readable title, and excerpt
- Paper color badges with tag-based colors (survey, finance, framework, etc.)

- Smart slug-to-name resolution: checks PAPERS dict → pulls title from gbrain get → humanises the slug as fallback

#### 💬 Tab 2 — Ask (upgraded this session)

Retrieves 40 pages + graph edges, synthesises with inline citations (gbrain think what it does)
Manual synthesis over retrieved passages (groq what it does)
- Caption tells you which mode is active
- gbrain think output parsed into:
- Stats bar (Model · Pages · Takes · Graph · Citations) in monospace
- Answer in green box
- 🕳️ Knowledge Gaps in amber box
- Warnings line
- Falls back to retrieval if think fails

#### 📄 Tab 3 — Read Paper
- Select any paper from the full discovered list
- Reads page content via gbrain get
- Run Research Notes button — triggers the research-notes.py minion on that specific paper (adds ## Research Context section)
- Build Research Graph button — triggers build-research-graph.py for that paper (extracts authors/institutions)


#### 🕸️ Tab 4 — Graph (3 sub-tabs)
🔬 Research Graph
- Interactive PyVis network graph of papers → authors → institutions
- Shows how many papers still need author extraction
- Ingestion pipeline Mermaid diagram (6-step visual)
- Extract Authors button — runs build-research-graph.py on all pending papers with live progress
- Graph renders with colored nodes (paper=blue, person=green, institution=orange) and directional edges
#### 👤 Personal Graph
- Add Person form → writes people/<slug>.md → imports to brain
- Add Company form → writes companies/<slug>.md → imports to brain
- Add Meeting form → writes meetings/<date>.md with attendee wikilinks → imports
- Explore connections — search → pick a result → gbrain graph-query <slug> --depth 2
- direction both → renders connection tree
#### □ Who Knows? (new this session)
- Topic input → gbrain whoknows <topic> --explain --json --limit 10
- Ranked cards with 🥇🥈🥉 medals for top 3
- Each card shows Expertise match · Recency · Salience as metrics + progress bars
- Score formula: log(1 + match) × recency_decay × (0.5 + 0.5 × salience)
- View profile button loads the person/company page inline

#### 🤖 Tab 5 — Minions
Dream Cycle hero
- Purple gradient banner showing last run timestamp
- ▶ Run Dream Cycle button — runs dream-cycle.bat with live log streaming (polls log file every second while running)
Minion Groups

- Color-coded group headers (blue / purple / green)
- Each minion shows schedule, description, status badge (● ok / ● failed / ● running / never run)
- Expandable log viewer — most recent lines first, color-coded (red=error, green=ok, gray=info)
- Refresh button clears cache and reruns

#### 📋 Tab 6 — Brief
- Daily Brief — reads minions/briefs/ markdown files, renders with section-aware formatting
- Weekly Digest — reads minions/digests/
- 🔔 Alerts — reads minions/alerts/ — shows paper import notifications with title, date, and summary in green cards
- File selector (most recent first)
- Refresh button

#### ✏️ Tab 7 — Capture
- Form: type selector (note/idea/observation/question/insight/hypothesis) · title · tags · content
- Auto-generates slug: inbox/YYYY-MM-DD-<md5hash8>
- Writes via gbrain put with stdin pipe (run_gbrain_input)
- Markdown output has frontmatter, body, timeline sentinel
- Recent captures list via gbrain list --slug-prefix inbox/ -n 10


📡 Minion Scripts (background automation)


🔧 Under the Hood — Helper Functions Added This Session
- run_gbrain_input() — pipes markdown via stdin to gbrain put (for Capture)
- parse_think_output() — parses gbrain think stdout: splits answer / ## Gaps / stats bar
/ warnings
- _discover_extracted_papers() — auto-discovers newly imported papers without code changes
- _slug_display_name() — cached slug → human name resolution

- gbrain_get() — cached page reader for profiles/content
- _write_and_import() — write .md + run gbrain import in one step


#### □ GBrain Research Explorer — How It All Works
The Big Picture
Your app is a personal research brain with two layers:
- GBrain (the database engine) — stores papers as Postgres pages with vector embeddings, a link graph, and a hybrid search index
- Streamlit (the UI) — a 6-tab interface that lets you interact with everything the background minions produce


#### 📥 The First 10 Papers (The Foundation)
These are hardcoded at the top of gbrain_app.py in _BASE_PAPERS: agentic_world_modeling → "Agentic World Modeling"
openhands	→ "OpenHands"
agentscope	→ "AgentScope" multi_agent_trading		→ "TradingAgents" ai_trader_agent		→ "AI-Trader"
kronos_a_foundation_model → "Kronos"
image_regonition_phone_avatar → "MUA (Mobile Avatars)" human_ai_oversight_video_language → "CHAI"
agentic	→ "BLF (Forecasting)"
python_cosmological	→ "Smokescreen"
Each one was manually put through the ingestion pipeline (the same 7 steps described below). Their .md files live in minions/extracted/. They also have hardcoded tags (survey, finance, platform, etc.) which controls the badge color shown on search results.
Any paper imported after those 10 gets auto-discovered by scanning the extracted/ folder and reading frontmatter titles — those show up with the teal auto-import tag.


#### 🔄 The 7-Step Ingestion Pipeline
When a new PDF lands in Desktop\Papers\, here's exactly what happens:

Step 1 — PDF Extraction (pypdf)
auto-import.py opens the PDF with pypdf and extracts all raw text. Null bytes get stripped (Postgres rejects them). The full text goes into memory — it's never stored directly in the brain, just used as input for the next step.
Step 2 — AI Summarisation (Groq · Llama 3.3-70B)
The first 10,000 characters of raw text get sent to Groq with a strict prompt that forces output into 6 sections:
- Overview — what problem it solves
- Method — the core approach
- Key Results — 3–5 bullets with actual numbers
- Why It Matters — practical significance
- Limitations — what authors acknowledge
- Keywords — 5–8 technical terms
This structured summary becomes the "compiled truth" — the authoritative content for the page.
Step 3 — Write Markdown (extracted/slug.md)
The structured summary gets written to disk as a .md file with YAML frontmatter:
- 
title: "Paper Name" type: paper
- 
## Overview
...
<!-- timeline --> ## Timeline
- 2026-05-29 — Imported to GBrain
The raw PDF text is not stored here — just the structured Groq summary. Step 4 — Chunk · Embed · Store (GBrain + Voyage AI + Postgres)
auto-import.py submits a native GBrain import Minion job pointing at the extracted/ folder. GBrain then:

- Parses the markdown into chunks (passage-level)
- Sends each chunk to Voyage AI to generate a vector embedding (1536 dimensions)
- Stores everything in Postgres: pages table (the page itself) + content_chunks table (each chunk with its embedding)
- Builds a BM25 keyword index (tsvector) and an HNSW vector index (pgvector) for hybrid search
The --no-embed flag means embedding runs separately via the Auto-Embedder minion (every 30 min) so import doesn't block.
Step 5 — Graph Wiring (gbrain extract)
graph-extract.py (your new minion, daily at 11:35 AM) runs:
gbrain extract links --source db gbrain extract timeline --source db
This walks every page in the database, finds all [[wikilinks]], and writes typed edges into
the links table: author_of, affiliated_with, mentions, etc. This is what makes the knowledge graph navigable — it's how GBrain knows "this paper is connected to that researcher."
Step 6 — Author Extraction (build-research-graph.py)
Runs daily at 1:45 PM. Re-reads the first 3 pages of the original PDF (not the stored markdown) specifically to extract author names and institution affiliations. It calls Groq with a JSON extraction prompt:
- Creates people/researcher-name.md stub pages
- Creates companies/institution-name.md stub pages
- Appends an ## Authors section to the paper page with wikilinks like [[people/john-doe|John Doe]] @ [[companies/mit|MIT]]
After this step, graph-extract re-runs and those new wikilinks become edges in the links table. Step 7 — Research Context (research-notes.py)
Runs daily at 2:30 PM. For each paper missing a ## Research Context section:
- Reads the paper's compiled summary from GBrain
- Runs 8 different gbrain query calls to find related pages in the brain
- Passes the paper summary + related results to Groq
- Gets back a structured section covering: what's new, related pages in your brain, knowledge gaps, what to explore next
- Appends ## Research Context to the paper's .md file and re-imports it


🖥️ The 6 Tabs
🔍 Search
Calls gbrain query → 8-stage hybrid pipeline:
- Intent classifier (entity/temporal/event/general)
- Multi-query expansion via Haiku
- Vector search (HNSW cosine similarity with Voyage embeddings)
- Keyword search (BM25 tsvector)
- RRF fusion (combines both scores)
- Compiled-truth boost (structured summaries rank higher than raw chunks)
- Backlink boost
- Dedup + top-N
Junk filtering strips reference sections, raw URLs, and metadata artifacts.
The fix_spaces() function repairs PDF extraction artifacts (hyphenated line breaks, concatenated words). Results show a relevance bar, paper badge with tag color, and an expanded passage around the matched chunk.
💬 Ask
Same hybrid search, but the top results feed a Groq call (Llama 3.3-70B) that synthesizes a direct answer citing which papers each point comes from. Falls back to retrieval-only if no GROQ_API_KEY.
📄 Read Paper
Lets you select any paper from the brain and read its full content. Detects missing sections (## Authors, ## Research Context) and shows enrichment buttons. You can trigger:
- 🕸️ Extract Authors → runs build-research-graph.py for just that paper
- 🔬 Research Notes → runs research-notes.py for just that paper
- ✨ Enrich All → both in sequence
After enrichment the cache clears and the page reloads showing the new content.
#### 🕸️ Graph (two sub-tabs)
#### Research Graph:
- Shows an ingestion pipeline diagram (Mermaid.js, loaded from CDN)
- Shows how many papers have had authors extracted (X/total done)

- Full Research Graph — pyvis interactive network: blue boxes = papers, green dots = researchers, orange diamonds = institutions. Edges: solid blue = "author of", dashed yellow = "affiliated with"
- Per-paper mini-graph when you click "Show Authors" on a specific paper
#### Personal Graph:
- Add Person — creates a people/slug.md and imports it into GBrain
- Add Company — creates a companies/slug.md and imports it
- Add Meeting — creates a meetings/YYYY-MM-DD.md with attendee wikilinks
- Explore — hybrid search + graph-query --depth 2 to show a tree of connections
🤖 Minions
The control panel for all background processes. Three groups:
#### 📚 Paper Pipeline — runs in sequence each day:

#### □ Intelligence:


🛠️ Maintenance:

Each minion has a status badge (green OK / red failed / yellow running) based on its last log line. Clicking expands the log tail, most recent lines first.
📋 Brief
Reads from three folders on disk:
- Daily Brief — markdown files in minions/briefs/ (one per day, written by daily-brief.py)
- Weekly Digest — markdown files in minions/digests/ (one per week, written by weekly-digest.py)
- Alerts — markdown files in minions/alerts/ (one per imported paper, written by auto-import.py)
You can also trigger manual brief generation by clicking a button which runs the .bat file directly.


The Daily Rhythm (What Happens Without You)

09:30 AM Daily Brief generated from brain search results
11:00 AM arXiv downloads 2 new cs.AI papers → Desktop\Papers\
11:20 AM Auto-Import picks them up → extract + Groq summary + write markdown + import to brain
11:35 AM Graph Extract wires all wikilinks into the links table
11:40 AM Fix Raw Dumps catches any papers that got raw text instead of structured summary
:30 min Auto-Embedder embeds any new chunks with Voyage AI
01:45 PM Research Graph extracts authors from PDFs → people + companies pages + wikilinks 02:15 PM Enrich fills those people/companies pages with Groq bios
02:30 PM Research Notes adds Research Context section to each paper 03:00 PM (Friday) Weekly Digest synthesises the week
Every 5 min: Papers Watcher fires immediately if you drop a PDF manually
By end of day, every new paper has: a structured summary, vector embeddings for hybrid search, author pages with institution links, graph edges connecting everything, and a Research Context section explaining how it fits into what you already know.






build-research-graph.py
├── extracts authors & institutions via Groq
├── creates people/ + companies/ stubs
├── writes ## Authors sections into paper pages
└── if new papers were processed → runs bio-agent.py
└── Claude reads full paper excerpts (4 000 chars each)
└── generates rich 5-6 sentence bios
└── skips pages already enriched (<!-- bio-agent --> tag)
#### gbrain agent run "prompt..."
└── submits job to the Postgres minion queue
└── worker picks it up → starts an LLM loop (claude-sonnet-4-6)

Turn 0: LLM reasons → calls list_pages Turn 1: LLM reasons → calls get_page
Turn 2: LLM reasons → calls put_page → writes to brain Turn 3: LLM delivers final answer
└── job marked COMPLETED

































GBrain system(Can you give me context of the application prompt)
### □ Technology Stack






### 📦 Components & Their Benefits
#### Ask Tab
What it does: You type a question in natural language, GBrain retrieves the most relevant pages from your brain, then passes them to an LLM which reads them and generates a synthesized answer.
Benefit: You don't have to remember where you stored something or what it was called. You just ask, and GBrain reads your personal notes and papers to answer you — like asking a research assistant who has read everything you've ever saved.


#### Search Tab
What it does: Pure retrieval — no LLM generation. Returns ranked pages with scores and excerpts.
Benefit: Faster and cheaper than Ask. Good when you want to find something specific rather than get an explanation. Also useful for verifying what's actually in the brain.


#### Papers Tab
What it does: Shows all your imported research papers (both manually added base papers and auto-imported ones from the extracted/ folder). You can click any paper to read a structured summary including Overview, Method, Key Results, Why It Matters, Limitations, and Keywords.
How the .md files are created: When you drop a PDF on your Desktop, auto-import.py runs automatically:
- Step 1: pypdf extracts raw text
- Step 1b: If the paper is image-heavy (avg < 100 chars/page), Claude Vision processes up to 8 rendered pages instead
- Step 2: Groq (Llama-70b) reads the extracted text and generates a structured summary with those exact sections
- Step 3: Writes a .md file to extracted/ with YAML frontmatter
- Step 4: Submits the paper to GBrain's import job queue to be embedded and indexed Benefit: Every paper you save is instantly structured, searchable, and cross-linked in your brain
— no manual work required.


#### Hot Pages Tab
What it does: Surfaces the pages in your brain that are most "salient" right now.
Salience formula: (emotional_weight × 5) + ln(1 + active_take_count) + 1/(1 + days_since_update)
This means a page ranks highly if:
- It's tagged with emotionally significant topics (AI, finance, research themes you care about)
- It has many "takes" (atomic observations/notes attached to it)
- It was recently updated
Benefit: Your brain tells you what matters most right now — not just what was added recently, but what you've engaged with deeply. It's like a smart "trending" feed for your own knowledge.


#### Personal Graph Tab
What it does: Lets you search for any person, company, or concept and then traverses the knowledge graph 2 levels deep in both directions — showing what else that entity is connected to.
Example: Search "Leuven" → finds researcher from KU Leuven → shows their papers, company affiliations, and related topics.
How it works: Uses gbrain graph-query <slug> --depth 2 --direction both which traverses entity link edges (person → company, paper → author, etc.).
Benefit: Standard RAG can retrieve relevant text — but it can't tell you "who else is connected to this person" or "what companies is this researcher affiliated with?" The graph layer adds relational intelligence on top of text search.


#### Synthesis Tab
What it does: Shows daily AI-generated synthesis pages (wiki/synthesis/YYYY-MM-DD). Every day at 3 PM, run-synthesis-direct.py automatically:
- Pulls recent papers from the brain via gbrain list
- Reads their content
- Calls the Anthropic API directly (Sonnet) to generate a 5-section synthesis:
- Today's Papers — brief summaries
- Cross-Paper Themes — patterns across papers
- Key Connections — links between ideas
- Open Questions — gaps and unknowns
- Standout Finding — the most striking result
Benefit: You don't have to manually connect ideas across papers. Each day you get a curated intelligence briefing that draws links across everything you've read, built from your papers with your notes.


#### Minions (Background Job Queue)
What it does: A Postgres-native background job system. When you drop a paper on your Desktop, auto-import.py submits an import job to the queue. A worker process picks it up and runs the full GBrain import pipeline (chunk → embed → index) without blocking anything.
Benefit: Ingestion is fully asynchronous. You can drop 20 papers and the UI stays responsive while they're all being processed in the background. No waiting.






#### ⚔️ GBrain vs Standard RAG Architecture



































#### Why use GBrain over plain RAG?
Standard RAG is a retrieval pipe. GBrain is a personal knowledge brain — it knows what you find important (salience), who is connected to whom (graph), and synthesizes across time (daily briefings). You built it to serve how you actually work: reading papers, tracking researchers, connecting ideas across finance and AI. Plain RAG would answer "what does this paper say" — GBrain answers "what does this mean given everything else you know."


#### Dependency on Claude Code or Hermes
Claude Code: No direct dependency. GBrain runs as a standalone CLI + Streamlit UI. You use Claude (via Anthropic API) for:
- Daily synthesis (Sonnet, direct HTTP call in run-synthesis-direct.py)
- Vision fallback for image-heavy PDFs (Sonnet, in auto-import.py)
- Query expansion (Haiku, called internally by gbrain query)
Hermes: No dependency. Hermes is an agent platform — GBrain is a knowledge layer
that could be used by an agent platform like Hermes or OpenClaw via the MCP server (gbrain serve), but your current setup is standalone. You call it directly from Streamlit and scheduled Python scripts.


#### 📥 Ingestion Pipeline (Step by Step)
When you drop a PDF on C:\Users\wprozenko\Desktop\Papers:
- auto-import.py detects new file (watchdog/polling)
↓
- pypdf extracts raw text
↓ (if < 100 chars/page average)
2b. pymupdf renders pages as images at 150 DPI
→ Claude Sonnet Vision reads up to 8 pages
→ Returns structured text
↓
- Groq (llama-3.3-70b) generates structured summary:
Overview | Method | Key Results | Why It Matters | Limitations | Keywords
↓
- Writes extracted/<slug>.md with YAML frontmatter
↓
- Writes alerts/<slug>.txt (notification file)
↓
- Submits native `import` Minion job to GBrain worker
↓

- GBrain worker picks up the job:
- Reads the .md file
- Parses frontmatter + body
- Chunks the content (recursive/semantic chunker)
- Embeds each chunk via Voyage AI
- Upserts page + chunks into Neon Postgres
- Runs auto-link extraction (detects entity references)
- Marks job complete
↓
- Page is now searchable in the brain


#### 🔍 Query Pipeline (Step by Step)
When you type a query in Ask or Search:
- UI calls gbrain_search(query, limit)
↓
- gbrain query "<query>" --limit N is called:


- Intent classifier runs → classifies as entity/temporal/event/general (determines how to tune retrieval depth)
↓
- Multi-query expansion (Haiku):
Your query → Haiku generates 3-5 semantic variants
e.g. "Leuven AI researcher" → ["KU Leuven machine learning", "Belgium deep learning group", "Leuven university AI lab", ...]
↓
- Hybrid retrieval for EACH variant:
- Vector search (HNSW index via pgvector) — semantic similarity
- Keyword search (tsvector BM25) — exact term matching

↓
- RRF fusion — merges all result lists into one ranked list
↓
- Source-quality boost applied:
- originals/ × 1.5, concepts/ × 1.3, people/ × 1.2
- daily/ × 0.8, chat logs × 0.5
↓
- Compiled-truth boost (pages with dense "compiled truth" rank higher)
- Backlink boost (pages referenced by many others rank higher)
↓
- Deduplication (same page from different query variants → one result)
↓
- Returns top N pages with scores + excerpts
↓
- Results filtered: score ≥ 0.45, junk filter removes raw reference sections
↓
- If 0 results returned (e.g. Haiku expansion failed due to SSL):
→ Fallback: gbrain search "<query>" --limit N (simpler keyword+vector, no LLM)
→ Score threshold lowered to 0.1
↓
- For Ask tab only:
- Retrieved page contents passed to LLM (Sonnet)
- LLM generates a natural language answer citing the pages
↓
- Results displayed in UI


That's the complete picture. The core innovation over plain RAG is the 8-stage retrieval pipeline (intent → expansion → hybrid → RRF → quality boost → compiled-truth → dedup → cite), the knowledge graph layer for relational queries, the salience scoring for surfacing what

matters, and the automated pipelines that keep everything current without you having to touch it.

step 3.
1.normal rag vs gbrain sources
2.can we create skills
3.when does chunking embedding and store in db happen
4.can we turn off graph at what step was graph made what llm
5.Are there any other things other than vector and graph
6.upload a personal document
7.For company sharing not manually
8.personal document about dog how can any other employee access it
9.difference mcp servers
10steps to dl brain

Report

1.
2. Yes we can createwith the skill "skill-creator"
- a skill is just a markdown file (SKILL.md) placed in a folder under C:\Users\wprozenko\gbrain\skills\. Every skill has:

Frontmatter — name, version, description, triggers, tools, mutating
Contract — what it guarantees
Phases — step-by-step workflow
Output Format — what the result looks like
Anti-Patterns — what NOT to do

3. It happens when you ingest content into gbrain. The pipeline is:

File/text → chunk → embed → store in DB
Specifically triggered by:

gbrain sync — scans your brain repo folder, picks up new/changed .md files
gbrain import <file> — imports a single file
gbrain embed --stale — re-embeds anything that wasn't embedded yet
(CLI Command)

4.a. The link graph (manual + auto-extracted)
When it's built: during gbrain enrich — after sync, an LLM reads your pages and extracts relationships (who knows who, what connects to what), storing typed edges between pages.

What LLM: whatever LLM you have configured — in your case the NVIDIA NIM API. It's an active LLM call, not free.

Can you turn it off? You can simply not run gbrain enrich. Sync alone (chunk + embed) works fine without it. The graph only gets built if you explicitly run the enrichment step.
b.Relational retrieval at search time
This is the graph being used during search to walk those edges and find connected pages.

Can you turn it off? Yes — it's controlled by search mode:

Mode	Relational retrieval
conservative	OFF
balanced	ON
tokenmax	ON
gbrain config set search.mode conservative
Or disable per-query:

gbrain search "your query" --relational false
Short answer: graph is built during gbrain enrich (uses your LLM), not during sync. You can skip enrichment entirely and just use sync + embed for pure vector search — no graph, no LLM cost at ingest time.

5.Why hybrid matters

Vector alone: misses exact keyword matches ("CEO", a person's name, a date)

BM25 alone: misses synonyms and conceptual matches ("money" ≠ "capital")

Together: catches both

conservative  →  vector + BM25
balanced      →  vector + BM25 + graph
tokenmax      →  vector + BM25 + graph + LLM expansion

GBrain is an MCP server




# Skills


GBrain Skills — Complete Synthesis
Synthesis Table

Detailed Explanations

ALWAYS-ON

1. signal-detector
Category: Always-On automatic — fires silently on every message as a background sub-agent.
What it does: Monitors every conversation for two types of signal: (1) original thinking — novel insights, frameworks, or takes that the user expresses, and (2) entity mentions — people, companies, concepts, projects named in passing. It captures these without interrupting the main conversation.
Key behaviors:
Runs as a silent parallel sub-agent, invisible to the user
Evaluates each message on a "capture worthiness" bar (not every message qualifies)
Creates brain pages only for genuine signal, not noise
Writes to inbox/ for raw captures, routes entities to their respective directories
Never speaks unless asked; never slows down the main response
Anti-patterns: Don't invoke it manually. Don't expect it to capture everything — it filters for original thinking, not transcription.

2. brain-ops
Category: Always-On automatic — the foundation policy layer for every session.
What it does: Establishes and enforces the brain-first protocol for the entire session. Before answering ANY question that could have a brain answer, it requires the READ→ENRICH→WRITE loop: (1) check brain first, (2) if entity is known but stale, enrich it, (3) after learning something new, write it back.
Key behaviors:
Source attribution: every fact cited must have a [Source: ...] tag
Iron Law back-linking: every entity mentioned in a page must get a back-link from their own page
Brain-first lookup sequence: search → query → get_page → external APIs (never skip to external without checking brain)
Write-back rule: new information discovered during a session must be persisted before the session ends
Anti-patterns: Don't answer personal questions from memory without searching gbrain first. Don't write facts without source citations.

USER-INVOKABLE — Information & Research

3. query
Category: User-invokable — triggered by "what do you know about X", "tell me about Y", "who is Z".
What it does: Answers questions by searching the brain using a 3-layer pipeline: keyword search → hybrid semantic search → graph traversal. Returns cited answers — every claim traces back to a specific brain page and section.
Key behaviors:
Layer 1: gbrain search (fast, keyword, works without embeddings)
Layer 2: gbrain query (hybrid, semantic + keyword, needs embeddings)
Layer 3: graph traversal for relationship questions ("how do X and Y connect?")
Never hallucinates: if the brain has no answer, it says so clearly
Cites sources inline: [Source: people/alice.md, "State" section]
Anti-patterns: Don't use it for real-time web research (use perplexity-research). Don't expect it to know things not in the brain.

4. briefing
Category: User-invokable — triggered by "morning briefing", "daily briefing", "what's on my plate today".
What it does: Read-only daily context pulse. Loads meeting attendees' brain pages, active deals, pending action items, and recent brain changes. Uses gbrain recall --since-last-run --supersessions --pending --rollup --json for hot memory.
Key behaviors:
Completely read-only — no brain modifications
Ordered by urgency: meetings today → overdue tasks → active deals → recent changes
Pre-loads attendee context so you walk into meetings briefed
Detects action items from recent meeting pages
Anti-patterns: Don't use it to write back to the brain. Don't run it more than once per morning (it's a point-in-time snapshot).

5. perplexity-research
Category: User-invokable — triggered by "research X", "find out about Y", "what's new with Z".
What it does: Brain-augmented web research via Perplexity's sonar-pro model. Sends existing brain context to Perplexity so it finds only the delta — what's new vs what the brain already knows — rather than re-explaining things you already have.
Key behaviors:
Default model: sonar-pro (~$0.04 per query)
Sends brain context as a preamble so Perplexity skips known information
Writes research results to research/<slug>.md
Called automatically by the enrich skill for external data
Returns structured findings with source citations
Anti-patterns: Don't use it for brain queries (use query skill). Expect costs to add up on heavy usage.

6. academic-verify
Category: User-invokable — triggered by "verify this claim", "is this study legit", "check the evidence for X".
What it does: Verifies academic/research claims by tracing the full chain: publication → methodology → raw data → independent replication. Routes through perplexity-research for current information.
Key behaviors:
Verdict system: Verified / Partially verified / Unverifiable / Misattributed / Retracted
Checks: sample size, methodology, replication attempts, conflicts of interest, journal reputation
Writes results to concepts/<claim-slug>.md
Documents the verification chain, not just the verdict
Anti-patterns: Don't treat "Verified" as "definitely true" — it means "evidence trail checks out." Don't use for real-time news (no publication chain yet).

7. idea-lineage
Category: User-invokable — triggered by "idea lineage for X", "how has my thinking about X changed", "where did this idea come from".
What it does: Traces one idea's evolution through the brain: first mention, best articulation, current live version, reversals, contradictions, abandoned branches, and related concepts. Read-only by default.
Key behaviors:
Read-only unless user explicitly asks to save the lineage as a brain page
Uses takes_search for attributed beliefs/bets, find_contradictions for conflicts, find_trajectory for entity timelines
Separates legitimate temporal evolution from actual contradictions
Marks evidence gaps explicitly rather than patching with narrative
Anti-patterns: Don't confuse this with concept-synthesis (that deduplicates across the whole brain). Don't invent abandoned branches to make a better story.

8. concept-synthesis
Category: User-invokable — triggered by "synthesize my concepts", "build my intellectual map", "what are my core concepts".
What it does: Deduplicates and synthesizes raw concept stubs into a tiered intellectual map. 4 phases: dedup+merge → score+tier → synthesize (T1+T2 only) → cluster+map. Produces concepts/README.md.
Key behaviors:
Tiers: T1 Canon (most developed, central) → T2 Major → T3 Minor → T4 Riff (raw takes)
Only synthesizes T1 and T2 (T3/T4 listed but not expanded, saving cost)
Merges duplicate concepts that are the same idea under different names
Produces a cluster map showing which concepts orbit each other
Anti-patterns: Don't use it for single-idea questions (use idea-lineage). This is expensive — don't run it daily.

9. strategic-reading
Category: User-invokable — triggered by "read this through the lens of", "extract a playbook from X for Y", "apply this book to my problem".
What it does: Reads a source text through the lens of a specific strategic problem. NOT a summary — a mission-driven analysis that maps the text's insights onto the user's specific situation.
Key behaviors:
Requires TWO inputs: source text + specific problem
Chapter triage: classifies each chapter HIGH/MEDIUM/LOW relevance, only deep-reads HIGH
Output: Core Parallel, Chapter Triage, Source's Playbook, Counter-Tactics, Applied Playbook (short/medium/long-term), Key Quotes
Every recommendation must cite the source with specific evidence
Files under projects/<slug>/playbook.md (problem-specific) or concepts/<slug>.md (general strategy)
Anti-patterns: Don't use it for general book summaries (use book-mirror). Don't accept recommendations without source citations.

10. book-mirror
Category: User-invokable — triggered by "mirror this book", "personalize this book for me", "analyze this book through my life".
What it does: Chapter-by-chapter personalized analysis. Two-column format: left = author's content, right = mapped to the reader's life using brain context. Subagents read the brain (read-only) to find relevant connections.
Key behaviors:
Default model: Opus (~$0.30/chapter — expensive, use deliberately)
Read-only subagents for brain lookups (allowed_tools: get_page, search only)
Output: media/books/<slug>-personalized.md
Brain page is ALWAYS source of truth; PDF is just a rendering
Anti-patterns: Don't use it for strategic problem-solving (use strategic-reading). Budget for cost before running on long books.

11. article-enrichment
Category: User-invokable — triggered by "enrich this article", pages with needs_enrichment: true frontmatter.
What it does: Transforms raw article text dumps into structured brain pages. Adds: Executive Summary, Why It Matters, Quotable Lines (verbatim — no paraphrase), Key Insights, Surprising/Counterintuitive, See Also. Preserves raw content in a <details> collapsible block.
Key behaviors:
Checks needs_enrichment frontmatter flag before processing
Quotable Lines section: VERBATIM only, never paraphrased
Preserves the full raw source inside <details> for reference
Adds brain cross-links in See Also
Anti-patterns: Don't paraphrase quotes. Don't delete the raw content — preserve it.

12. data-research
Category: User-invokable — triggered by "extract data from emails", "track investor updates", "parse expense reports".
What it does: Structured research pipeline for extracting data from email threads into structured tables/pages. Uses parameterized YAML recipes for common workflows: investor-updates, expense-tracker, company-updates.
Key behaviors:
Recipes are YAML files defining extraction fields, sources, and output format
Critical integrity rule: always re-read from saved files after batch processing to prevent hallucination bug (the model can "remember" writing data it didn't actually write)
Output: structured markdown tables + frontmatter-rich brain pages
Anti-patterns: Never trust in-memory extraction results — always re-read from the saved file. Don't hand-roll extraction logic when a recipe exists.

USER-INVOKABLE — Ingestion

13. ingest
Category: User-invokable router — triggered by "ingest this", "add this to my brain".
What it does: Single entrypoint router for all inbound content. Detects content type and delegates to the appropriate specialist skill: idea-ingest (URLs/articles/tweets), media-ingest (video/audio/PDF/books), or meeting-ingestion (transcripts). Also defines the entity detection protocol that runs on every inbound message.
Key behaviors:
Entity detection runs on EVERY message, not just explicit ingestion requests
Routes by content type: URL → idea-ingest, video/PDF → media-ingest, transcript → meeting-ingestion
Never ingests without entity detection
Anti-patterns: Don't call idea-ingest or media-ingest directly unless you know the content type. Always route through ingest first.

14. idea-ingest
Category: User-invokable — triggered by "ingest this URL", "save this article", "capture this tweet".
What it does: Ingests URLs, articles, and tweets. Fetches content, saves raw source, creates a MANDATORY author people page, and files the content by primary subject (not format).
Key behaviors:
Author people page is MANDATORY — every article must have a page for its author
Files by primary subject, not format: a business article goes in companies/, not articles/
Saves raw source alongside the processed page
Analyzes content against existing brain context to find connections
Anti-patterns: Never skip the author people page. Never file by format (no articles/ dump).

15. media-ingest
Category: User-invokable — triggered by "ingest this video/audio/PDF/book/screenshot/GitHub repo".
What it does: Same pipeline as idea-ingest but handles binary formats. Manages transcription (video/audio), OCR (images/screenshots), and structured extraction (PDFs, GitHub repos). Files by primary subject, never by format.
Key behaviors:
Transcription: whisper or equivalent for audio/video
OCR: for screenshots and scanned PDFs
GitHub repos: indexes README + key files as brain pages
Same mandatory author page rule as idea-ingest
Anti-patterns: Don't file in media/ by default — that's for media ABOUT a topic, not the topic itself.

16. meeting-ingestion
Category: User-invokable — triggered by "ingest this meeting", "add this transcript".
What it does: Ingests meeting transcripts with mandatory entity propagation. Every attendee gets a people page update, every company gets a page update, and timelines merge across ALL mentioned entities. A meeting is NOT fully ingested until all entity pages are updated.
Key behaviors:
MANDATORY: every attendee gets a people page (create or update)
MANDATORY: every company mentioned gets entity propagation
Timeline merge: the meeting event appears on every participant's timeline
Uses the COMPLETE transcript, not just the AI summary
Anti-patterns: Never consider a meeting ingested if attendee pages weren't updated. Never use just the summary — always ingest the full transcript.

17. capture
Category: User-invokable — CLI: gbrain capture "thought".
What it does: Single human-facing ingestion entrypoint for raw thoughts. Puts the page in inbox/YYYY-MM-DD-<hash8>. Content-hash deduplication prevents re-capturing the same thought. Replaces put_page for human use.
Key behaviors:
Always goes to inbox/ — never directly to a content directory
Hash-based dedup: same content = no-op
Minimal friction: no frontmatter required, just the raw thought
The inbox is processed later by eiirp or brain-taxonomist
Anti-patterns: Don't use it for structured content (use idea-ingest). Don't bypass it by writing directly to put_page.

18. voice-note-ingest
Category: User-invokable — triggered by "ingest this voice note", "capture what I just said".
What it does: Ingests voice notes with an Iron Law: EXACT PHRASING must be preserved. Never paraphrase the user's words — the exact words are the signal.
Key behaviors:
Routes to appropriate directory: originals/ (user's own ideas), concepts/, people/, companies/, ideas/ (product ideas), personal/ (reflections), voice-notes/ (catch-all)
Transcription is verbatim, not cleaned up
The raw transcript is preserved even if a structured page is also created
Tags with voice-note source metadata
Anti-patterns: NEVER paraphrase. If you're not sure of exact wording, mark it as uncertain.

19. webhook-transforms
Category: User-invokable — triggered by "set up webhook", "process this webhook event".
What it does: Generic framework for converting external events into brain-ingestible signals. Define a transform function, register a webhook URL, and incoming events get processed through the brain pipeline.
Key behaviors:
Dead-letter queue: if transform fails, raw payload is logged to _dead-letter/{timestamp}.md
Input sanitization: strips HTML/script before any brain writes (XSS prevention)
Entity extraction runs on every transformed event
Retry once on failure, then dead-letter
Built-in transforms:
SMS received → timeline entry on sender's brain page
Meeting completed → delegates to meeting-ingestion
Social mention → brain page in media/ + entity extraction
Anti-patterns: Never pass raw HTML to brain pages. Never silently drop events — use dead-letter queue.

USER-INVOKABLE — Organization & Filing

20. eiirp
Category: User-invokable — triggered by "eiirp", "organize all of this", "file all of this", "make this permanent", "DRY this up".
What it does: Everything In Its Right Place (named after the Radiohead song). The universal post-work organizer. After any significant work session, runs a 7-phase audit: inventory outputs → walk taxonomy → schema check → file pages → audit skill graph (DRY+MECE) → verify resolvability → report.
Key behaviors:
Covers TWO domains: knowledge (brain pages) AND capabilities (skills)
Phase 3 schema check: uses gbrain schema suggest — auto-applies only if confidence ≥ 0.6
Phase 5 skill graph audit: checks for DRY violations (duplicated logic), MECE violations (ambiguous routing), and patterns worth skillifying
Idempotent: running it twice on the same work produces no changes the second time
Reads active schema pack via gbrain schema show --json — never hardcodes directory tables
Anti-patterns: Don't skip Phase 5 "because it was a one-off" — if work took >10 min, audit anyway. Don't auto-apply low-confidence schema suggestions (< 0.6).

21. brain-taxonomist
Category: User-invokable (called at write time) — the filing gate for ALL brain writes.
What it does: Decides where every brain page goes. Reads the ACTIVE schema pack via gbrain schema show --json — NO hardcoded directory tables. Primary subject determines filing, not format or source.
Key behaviors:
Per-source overrides: --source <id> can change filing rules per source
Ambiguous cases → ask-user (never guess silently)
No match → signals EIIRP Phase 3 for schema extension
The single source of truth for filing decisions
Anti-patterns: Never hardcode "articles go in articles/" — always read the schema pack. Never file by format.

22. archive-crawler
Category: User-invokable — triggered by "crawl my archive", "import my old files".
What it does: Universal archivist for personal file archives. Has a SAFETY GATE: REFUSES to run without archive-crawler.scan_paths: in gbrain.yml. Gold filter: keeps personal writing, ideas, relationships; skips system files, receipts, spam.
Key behaviors:
Safety gate: must configure scan paths before use
Gold filter logic: keeps files you wrote (documents, notes, letters); skips installers, receipts, marketing
Schema-generic: reads filing rules at runtime from active schema pack
Supports: local directories, cloud storage (Backblaze/S3), email archives (PST, mbox), data exports (LinkedIn, Facebook)
Anti-patterns: Never run without configuring scan_paths. Don't import without gold filter — you'll flood the brain with noise.

23. migrate
Category: User-invokable — triggered by "migrate from Obsidian", "import from Notion", "import from Roam".
What it does: Universal migration from any notes tool (Obsidian, Notion, Logseq, plain markdown, CSV, JSON, Roam) into gbrain. Always additive — source data is never modified or deleted.
Key behaviors:
Always tests with 5-10 files before bulk import
Converts source cross-references: wikilinks → gbrain links, block refs → page links, tags → gbrain tags
Round-trip verification: writes to gbrain, reads back, spot-checks
Obsidian: native wikilink support via gbrain extract links
Anti-patterns: Never bulk import without sample test. Never modify source files. Never skip cross-reference conversion.

USER-INVOKABLE — Task Management

24. daily-task-manager
Category: User-invokable — triggered by "add task", "complete task", "defer task", "review tasks".
What it does: Full task lifecycle management. Stores tasks at ops/tasks.md. P0-P3 priority levels (P0 = critical, P3 = someday).
Key behaviors:
P0 = do today, P1 = this week, P2 = this month, P3 = someday
Operations: add / complete / defer (snooze to future date) / remove / review
Tasks stored as structured markdown in ops/tasks.md
Weekly review surfaces all P2/P3 tasks for promotion or deletion
Anti-patterns: Don't skip the priority level — everything is P2 by default if unspecified. Don't let P3 accumulate without periodic review.

25. daily-task-prep
Category: User-invokable — triggered by "morning prep", "what's on my calendar today", "prep for today".
What it does: Read-only morning preparation. Calendar lookahead + meeting attendee brain context + yesterday's open threads + active task review.
Key behaviors:
Read-only: no brain modifications
Loads attendee brain pages for every meeting today
Surfaces overdue tasks from daily-task-manager
Identifies open threads from yesterday's meetings
Anti-patterns: Don't use it to add tasks (use daily-task-manager). Keep it read-only.

26. reports
Category: User-invokable — triggered by "save report", "load morning briefing", "show email report".
What it does: Save and load timestamped reports. Keyword routing maps common queries to report types: "email" → ea-inbox-sweep, "morning" → morning-briefing. Saves to reports/{category}/{YYYY-MM-DD-HHMM}.md.
Key behaviors:
Keyword routing: common terms map to report categories automatically
Timestamped: every report save includes the datetime in the filename
Reports are appendable — can build up a history of daily briefings
Anti-patterns: Don't use it as a task manager. Reports are read artifacts, not actionable items.

USER-INVOKABLE — Entity Management

27. enrich
Category: User-invokable — triggered by "enrich [person/company]", called by ingest skills when new entities appear.
What it does: Tier-based enrichment protocol. 7-step pipeline: identify entities → check brain → extract signal → external APIs → save raw data → write to brain → cross-reference. Tiers 1/2/3 based on notability.
Key behaviors:
Tier 1 (high notability): full external research via perplexity-research
Tier 2 (moderate): partial external search
Tier 3 (low): brain-only enrichment, no external calls
Writes to people/ and companies/
Cross-reference: back-links to every place this entity is mentioned
Anti-patterns: Don't enrich every entity to Tier 1 — calibrate by notability. Don't write without checking for existing page first.

28. citation-fixer
Category: User-invokable — triggered by "fix citations", "audit citations", "repair sources".
What it does: Audits and repairs [Source: ...] citations across brain pages. Extended in v0.25.1 with tweet/post URL resolution via X API. Batch mode available.
Key behaviors:
Deterministic links only — never invents URLs
Tweet/post resolution: resolves short URLs to full canonical URLs
Batch mode: can fix citations across multiple pages in one run
Flags uncorrectable citations (broken sources) rather than inventing replacements
Anti-patterns: Never invent URLs. Flag broken sources explicitly rather than silently dropping citations.

29. frontmatter-guard
Category: User-invokable — triggered by "fix frontmatter", "repair YAML", or automatically when frontmatter parse errors occur.
What it does: Validates and repairs YAML frontmatter. Handles 8 error classes: MISSING_OPEN, MISSING_CLOSE, YAML_PARSE, SLUG_MISMATCH, NULL_BYTES, NESTED_QUOTES, NON_STRING_FIELD, EMPTY_FRONTMATTER.
Key behaviors:
Auto-fixable: MISSING_CLOSE, SLUG_MISMATCH, NULL_BYTES, NESTED_QUOTES
NOT auto-fixable: YAML_PARSE, NON_STRING_FIELD, EMPTY_FRONTMATTER (require human review)
Creates .bak backup before any mutation
Reports errors by class with file paths
Anti-patterns: Don't auto-fix YAML_PARSE without reviewing — the content may be substantively wrong, not just syntax.

USER-INVOKABLE — Output

30. publish
Category: User-invokable — triggered by "publish this page", "share this", "export for sharing".
What it does: Shares brain pages as password-protected HTML with AES-256-GCM encryption + PBKDF2 key derivation. Zero LLM calls — pure CLI operation.
Key behaviors:
Default: ALWAYS ENCRYPT — never publishes plaintext
Strips before publishing: frontmatter, citations, confirmation numbers, brain cross-links, timeline entries
CLI: gbrain publish <file> --password
The published HTML is standalone — no brain server required to view
Anti-patterns: Never publish without a password. Never include raw frontmatter in the output (it reveals brain structure).

31. brain-pdf
Category: User-invokable — triggered by "export to PDF", "make a PDF of this page".
What it does: Renders a brain page to PDF via the gstack make-pdf binary. The brain page is ALWAYS the source of truth — the PDF is just a rendering artifact.
Key behaviors:
Binary location: $HOME/.claude/skills/gstack/make-pdf/dist/pdf
Strips YAML frontmatter before rendering
CONTAINER=1 environment variable required in containerized environments
Never edits the brain page to match the PDF — always the reverse
Anti-patterns: Don't treat PDFs as authoritative. Never modify the brain page to "match the PDF" — the page is the truth, the PDF is ephemeral.

32. ask-user
Category: User-invokable (reusable pattern) — called by other skills when a decision point requires human input.
What it does: Reusable choice gate pattern. Presents 2-4 options and STOPS execution until the user responds. Platform-agnostic (numbered list or inline buttons).
Key behaviors:
CRITICAL: after presenting choices, STOP the turn — do NOT continue, do NOT default
Always include an escape hatch option (Skip / Cancel / None of the above)
2-4 options maximum — never more
Platform-agnostic: works in terminal (numbered list) and GUI (buttons)
Anti-patterns: NEVER continue after presenting choices. NEVER pick a default silently. Always include the escape hatch.

USER-INVOKABLE — Identity

33. soul-audit
Category: User-invokable — triggered by "soul audit", "configure agent identity", "set up my agent".
What it does: 6-phase interactive interview that generates SOUL.md (agent identity and vibe), USER.md (user profile), ACCESS_POLICY.md (access tiers), and HEARTBEAT.md (operational cadence). Re-runnable per phase.
Key behaviors:
6 phases, each independently re-runnable: identity → mission → vibe → user profile → access tiers → operational cadence
Generates 4 output files that configure the agent's persistent identity
ACCESS_POLICY.md defines what the agent can/cannot do autonomously
HEARTBEAT.md configures cron-based maintenance rhythms
Anti-patterns: Don't run all 6 phases in one go unless starting fresh. Run individual phases to update specific aspects.

DEVELOPER / META

34. skill-creator
Category: Developer — triggered by "create a skill", "make a new skill for X".
What it does: Creates new skills conformant with the gbrain standard. Performs a MECE check against existing skills before creating. Updates manifest.json and RESOLVER.md. Runs conformance tests to verify.
Key behaviors:
MECE check: verifies no trigger phrase overlaps with existing skills
Creates the full SKILL.md with all required sections (Contract, When to Use, Phases, Output Format, Anti-Patterns)
Updates manifest.json and RESOLVER.md
Runs bun test test/skills-conformance.test.ts to verify conformance
Anti-patterns: Never create a skill without the MECE check. Never skip the conformance test.

35. skill-optimizer
Category: Developer — triggered by "optimize this skill", "run skillopt", "make this skill better".
What it does: Self-evolving skill optimization based on SkillOpt paper (arXiv 2605.23904, Microsoft Research, May 2026). Treats SKILL.md as trainable parameters. Validation-gated, budget-capped, atomic-versioned.
Key behaviors:
Iron Law: every candidate must clear median-of-3 + epsilon=0.05 margin before SKILL.md is rewritten
FORBIDDEN: mutating frontmatter (triggers:, brain_first:) — body only
Bundled skills require --allow-mutate-bundled + --held-out (≥5 tasks) OR writes to proposed.md for review
Bootstrap: gbrain skillopt X --bootstrap-from-skill generates starter benchmark from SKILL.md itself
Decision tree:
No benchmark → --bootstrap-from-skill → review+strengthen judges → --bootstrap-reviewed --split 1:1:1
Has benchmark → gbrain skillopt foo --benchmark skills/foo/skillopt-benchmark.jsonl
Anti-patterns: Never bypass the validation gate. Never rubber-stamp bootstrap output — always strengthen the judges before optimizing against them.

36. skillify
Category: Developer — triggered by "skillify this", "turn this into a skill".
What it does: The meta-skill for turning any raw feature or workflow into a properly-skilled unit. 11-item checklist. Phase 3 is a cross-modal eval across 3 frontier models from 3 providers.
Key behaviors:
11-item checklist ensures completeness
Phase 3 cross-modal eval: OpenAI GPT-4o + Anthropic Claude Opus + Google Gemini
Pass criteria: every dimension mean ≥7, no model scored <5
Tests AFTER eval — never before (circular testing issue)
Anti-patterns: Don't write tests before the cross-modal eval passes. Don't skip the 3-provider eval.

37. skillpack-check
Category: Developer — triggered by "check skillpack health", called by eiirp Phase 6.
What it does: Runs gbrain skillpack-check, which wraps gbrain doctor + gbrain apply-migrations --list. Returns JSON: {healthy, summary, actions, doctor, migrations}.
Exit codes: 0 = healthy, 1 = action needed, 2 = could not determine.
Key behaviors:
Read-only health check — no modifications
Surfaces pending migrations without applying them
Used by EIIRP to verify resolvability after organizing
Anti-patterns: Don't auto-apply migrations based on this output — surface to user first.

38. skillpack-harvest
Category: Developer — triggered by "harvest this skill", "publish this skill to gbrain", "promote my skill".
What it does: Lifts proven skills from host repos back into the gbrain bundle. Editorial workflow: scrub real names/companies/fork references. Privacy lint via ~/.gbrain/harvest-private-patterns.txt. Copy (not move). One skill at a time.
Key behaviors:
Always dry-run first: gbrain skillpack harvest <slug> --dry-run
Privacy linter on real harvest: ~/.gbrain/harvest-private-patterns.txt + built-in patterns
One skill at a time — no batch harvest
Source files stay in host repo (it's a copy, not a move)
6-step workflow: Plan → dry-run → genericize (editorial pass) → real harvest → verify (bun test) → downstream announcement.
Anti-patterns: Never harvest without the editorial pass. Never bypass lint without documenting why.

39. functional-area-resolver
Category: Developer — triggered by "compress routing table", "optimize RESOLVER.md".
What it does: Compresses routing tables using (dispatcher for: ...) clauses that group related skills into functional areas. Proven: functional-areas pattern = 100% routing accuracy on Sonnet (vs 81.7% baseline) at 48% the size.
Key behaviors:
Minimum file size gate: 12KB before compression is worth it
Verified via gbrain routing-eval --json before committing
The (dispatcher for: ...) clause is load-bearing — stripping it collapses accuracy to 41.7%
Commit only after eval verifies no accuracy regression
Anti-patterns: Don't use on small routing tables. Never commit without running routing-eval first.

40. testing
Category: Developer — triggered by "validate skills", "run the tests", "how are the tests", "daily test run".
What it does: Two modes: (1) Skill conformance validation — every SKILL.md has valid frontmatter, all manifest/resolver coverage round-trips, no MECE violations; (2) Project test-suite health — tiered test runner with regression classification.
Test tiers:
Unit: bun test (<2s, every commit)
Evals: LLM-judge (~60s, daily)
Integration: E2E against real Postgres (~5m, pre-ship + nightly)
System health: disk/memory/CPU/service liveness (<10s, daily)
Failure classification:
🔴 REGRESSION — code changed, test broke
🟡 STALE — test expects old behavior; code is correct
⚠️ FLAKE — API timeout, non-deterministic
🟢 NEW — just added, not passing yet
🛠 INFRA — container restart wiped state
Anti-patterns: Don't auto-fix security test failures. Don't report "all clear" without running system health checks. Don't un-skip a skipped test without understanding why it was skipped.

41. cross-modal-review
Category: Developer — triggered by "review before committing", "second opinion on this", called by skillify Phase 3.
What it does: Quality gate via a second model. Reviews work against the skill's Contract section (not vibes). Refusal routing: silently switches to next model if one refuses.
Key behaviors:
Reviews against Contract (the skill's stated guarantees), not general quality
Refusal routing: model refuses → try next model automatically
For code diffs: recommends /codex review
User-sovereignty Iron Law: reviewer findings are INFORMATIONAL until user explicitly approves each one
Anti-patterns: Never auto-apply reviewer suggestions. Always present findings as informational and let user decide.

42. smoke-test
Category: Developer — triggered by "smoke test", "post-restart check", on every container/agent restart.
What it does: 8 built-in post-restart health tests. Auto-fixes known issues. Extensible via ~/.gbrain/smoke-tests.d/*.sh.
8 built-in tests:
Bun runtime
GBrain CLI
Database connection
Worker process alive
OpenClaw Codex gateway
Gateway health
Embedding API
Brain repo accessible
Key behaviors:
Auto-fix known issues (e.g., Bun path, worker not started)
User-extensible via shell scripts in ~/.gbrain/smoke-tests.d/
Reports pass/fail per test with fix instructions for failures
Anti-patterns: Don't skip on container restart. Don't add smoke tests for things that should be unit tests.

43. schema-author
Category: Developer — triggered by "add a page type", "my brain has untyped pages", "extend the schema pack".
What it does: Evolves the brain's schema pack. Add page types, propose new ones from corpus scans, backfill page.type on existing pages, audit pack health.
Key behaviors:
Never mutates bundled packs (gbrain-base, gbrain-recommended) — fork first
7-phase workflow: check active → assess coverage → propose → fork + apply → lint (with --with-db) → sync + backfill → verify
Atomic writes: .tmp + fsync + rename pattern
Pack changes picked up within 1 second by running processes
Anti-patterns: Don't add a type for a directory you imported once for triage. Don't skip lint --with-db before adding. Don't skip dry-run before sync --apply.

44. schema-unify
Category: Developer — triggered by "migrate to gbrain-base-v2", "unify my types", "clean up my page types".
What it does: One-time migration from the old gbrain-base pack (which accumulated 94+ noisy types) to gbrain-base-v2 with 15 canonical types. Runs via the unify-types PROTECTED Minion handler.
15 canonical types: person, company, media, tweet, social-digest, analysis, atom, concept, source, deal, email, slack, writing, project, note.
Key behaviors:
PROTECTED: manual-only, autopilot will never auto-fire this
Always --explain (dry-run) before applying
Preserves frontmatter.legacy_type = <original> on every retyped page for rollback
Source pages soft-deleted with 72h restore TTL
~10 minutes on a 186K-page brain
Anti-patterns: Never run under autopilot. Always dry-run first. Never hard-delete soft-deleted source pages before the 72h window.

45. maintain
Category: Developer — triggered by "maintain brain", "run dream cycle", gbrain dream.
What it does: Brain health maintenance + the 8-phase dream cycle. Uses gbrain doctor --remediate --target-score 90 --max-usd 5 for autonomous repair.
8 dream phases:
Lint (frontmatter, slug consistency)
Backlinks (Iron Law enforcement)
Sync (pull from brain repo)
Synthesize (update compiled truth)
Extract (links + timeline)
Patterns (concept synthesis)
Embed (refresh stale embeddings)
Orphans (find + reconnect isolated pages)
Health checks: stale pages, orphans, dead links, missing cross-refs, back-link violations, citation gaps, filing violations, tag inconsistencies, embedding staleness, RLS, schema health, file storage.
Anti-patterns: Don't skip dream cycle — stale brains return stale answers. Don't run remediate without a cost cap (--max-usd 5).

OPERATIONAL

46. gbrain-advisor
Category: Operational — triggered by "advisor", weekly cron, or gbrain advisor --json.
What it does: Proactive coaching. Read-only. Surfaces critical/warn/info findings from 8 brain-state collectors: version drift, pending migrations, stale jobs, low embed coverage, schema health, orphan rate, backlink violations, skill graph health.
Key behaviors:
Always asks before fixing anything — never auto-applies
Weekly cadence recommended
- json output + exit codes for CI/cron integration
MCP: exposed behind mcp.publish_advisor flag (default off, read-only when on)
Anti-patterns: Don't skip the confirmation step. Advisor is informational — the user decides what to fix.

47. cron-scheduler
Category: Operational — triggered by "schedule this", "add a cron", "automate X daily".
What it does: Schedule management with intelligent staggering (max 1 job per 5-min slot), quiet hours gating, and thin job prompts.
Key behaviors:
Multi-source brains use gbrain sync --all --parallel 4 --workers 4 --skip-failed not per-source entries
Quiet hours: configurable windows when heavy jobs won't run
Staggering: prevents multiple heavy jobs from colliding
Thin job prompts: cron-fired jobs use brief prompts to minimize token cost
Anti-patterns: Never schedule per-source sync entries for multi-source brains. Never schedule heavy jobs without quiet-hours consideration.

48. minion-orchestrator
Category: Operational — triggered by "run job", "submit minion", "background task", "run this as a job".
What it does: Unified Minions skill for all background work. Two lanes: deterministic shell jobs (gbrain jobs submit shell) + LLM subagent jobs (gbrain agent run). Full lifecycle: submit/monitor/steer/pause/resume/cancel/replay.
Key behaviors:
Shell jobs: CLI-only — MCP CANNOT submit shell jobs (they're in PROTECTED_JOB_NAMES)
LLM subagent jobs: can be submitted via MCP
Job lifecycle: submit → monitor → steer (send messages mid-run) → pause/resume/cancel/replay
Postgres-native: durable, observable, survives restarts
Anti-patterns: Never try to submit shell jobs via MCP. Use shell jobs for deterministic CLI operations; use LLM subagent jobs for reasoning tasks.

49. gbrain-upgrade
Category: Operational — triggered by UPGRADE_AVAILABLE <old> <new> marker on stderr, or "upgrade gbrain", "is gbrain up to date".
What it does: Keeps gbrain current. Handles upgrade modes: notify (prompt with 4-option question + snooze), auto (apply silently), off (do nothing). The upgrade action is ALWAYS the hardcoded gbrain self-upgrade — never a command parsed from the marker (injection protection).
Key behaviors:
Security: NEVER runs a command embedded in the marker text — only gbrain self-upgrade
Notify mode (default): summarizes changelog in 3-5 bullets, presents 4 options: Yes / Always / Not now / Never
Snooze escalation: 24h → 48h → 7d before the same version nags again
Auto mode: for headless/always-on installs only
Anti-patterns: Don't flip an interactive workstation to auto mode to silence nudges. Never apply during a multi-step task without finishing or checkpointing first.

50. repo-architecture
Category: Operational (advisory) — triggered by "where does X go?", "where should I file Y?".
What it does: Advisory skill for deciding where new brain files belong. Decision protocol: primary subject determines location, not format or source. Delegates to skills/_brain-filing-rules.md for the actual rules.
Key behaviors:
Advisory only — doesn't write files, just recommends
Primary subject rule: a video about a company goes in companies/, not media/
Delegates to _brain-filing-rules.md for complete rule set
Anti-patterns: Don't file by format. Don't file by source (where you found it). File by what it's primarily about.

ONE-TIME SETUP

51. setup
Category: One-time setup — triggered by "set up gbrain", "initialize brain", "gbrain setup".
What it does: Full gbrain setup wizard. Gets you from zero to a working brain in under 5 minutes. Covers topology selection, Supabase/PGLite provisioning, first import, autopilot install, live sync setup, and transitions directly to cold-start.
Phase A.5: Topology selection (BEFORE anything else):
Single brain (default)
Cross-machine thin client (your brain on another machine, accessed over MCP)
Per-worktree code + shared remote artifacts
9 phases:
A = Supabase setup / B = BYO Postgres / C = First import / C.5 = Autopilot + Minions / D = Brain-first protocol injection / E = Load production agent guide / F = Health check / G = Auto-update check / H = Live sync / I = Full verification / J = Cold start (automatic transition)
Key behaviors:
Never asks for Supabase anon key — only needs the database connection string
Phase J is MANDATORY: always transitions to cold-start after verification
Records schema choices in ~/.gbrain/update-state.json so future upgrades don't re-suggest declined items
Anti-patterns: Never end setup without offering cold-start. Never skip live sync setup. Never declare complete without running Phase I verification.

52. cold-start
Category: One-time setup — triggered by "fill my brain", "bootstrap brain", "day one", "now what?".
What it does: Day-one data bootstrapping. Sequences the highest-leverage data sources to go from empty brain to useful brain in one session. Uses ClawVisor for safe credential handling — the agent never holds raw OAuth tokens.
Priority stack (by information density × import ease):
Existing markdown/Obsidian (5 min, 100s-1000s pages)
Google Contacts (10 min, 50-500 people pages)
Google Calendar 90 days (15 min, 30-90 meeting pages)
Gmail recent threads (20 min, 50-200 pages)
AI conversation exports — ChatGPT/Claude (15 min, 10-100 pages)
X/Twitter archive (20 min, 30-365 pages)
File archives via archive-crawler (30+ min)
Meeting transcripts from Circleback/Otter/Fireflies (20 min)
Key behaviors:
ClawVisor is required for Google API access — agent never holds raw tokens
If ClawVisor is declined: skip Phases 2-4, use only offline file imports
Progress tracked in ~/.gbrain/cold-start-state.json — interrupted sessions resume automatically
Every phase is independently valuable — stop after any phase
Anti-patterns: Never give the agent raw OAuth tokens. Never bulk-import without gold filtering (signal vs noise). Never skip entity cross-linking.

53. install
Category: Deprecated.
Redirects to setup. Has no active functionality. The setup skill provides everything install once did, plus auto-provision, AGENTS.md injection, and full health verification.

Quick Reference by Use Case

That's all 53 skills (plus install deprecated). The two engine-level features not in this list are retrieval_reflex (zero-LLM entity detection built into the gbrain engine itself, v0.42.39.0+) and the brain-first protocol enforced by CLAUDE.md — those aren't skill files but are part of the same system.
I wanted you to remove the Claude dekstop since i didnt use the settings
ReadReadingREADME.mdrunning
