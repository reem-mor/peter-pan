# Graph Report - agent-ad99b1ac27f83d79a  (2026-07-18)

## Corpus Check
- 128 files · ~55,051 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1038 nodes · 1661 edges · 80 communities (48 shown, 32 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 294 edges (avg confidence: 0.71)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e5ddab8c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Budget Tracking
- LLM Story Evaluation
- Knowledge Base Ingestion
- Predictor Training
- LLM Story Synthesis
- Environment Configuration
- Input/Output Guardrails
- RAG Retrieval Service
- Tool Permissions
- System Documentation
- Story Graph Orchestration
- Learning & Governance
- Operations Console
- Action Approval Gate
- Secrets Deployment
- Memory Leak Incident
- CI/CD Pipeline
- Cache Stampede Incident
- Queue Backlog Incident
- DNS Outage Incident
- Payment Latency Incident
- Feature Flag Incident
- 5xx Storm Incident
- Disk Full Incident
- Certificate Expiry Incident
- Agent Orchestration
- Peter Pan System
- Microservices Framework
- DNS & Hosting
- Design System
- Prompt Engineering
- Product Research
- Dependency Management
- Peter Pan Root
- Dashboard Design
- Certificate Rotation
- prompts/README.md — Prompt Versioning
- contract-reviewer — Schema Validator
- peter-pan-design — Design System
- docker-compose.yml — Service Mesh
- stack.yaml — AWS CloudFormation
- BaseModel
- StrEnum
- build_story
- test_ppos_budget.py
- IncidentStory
- test_ppos_dashboard.py
- run_retrieval_eval.py
- tips
- test_dashboard.py
- run_llm_judge.py
- INC-2401.md
- INC-2412.md
- INC-2423.md
- INC-2434.md
- INC-2445.md
- INC-2456.md
- cache.py
- devDependencies
- devDependencies
- test_cache.py
- index.ts
- compilerOptions
- compilerOptions
- App.tsx
- compilerOptions
- Evidence
- build_story
- test_ppos_leads.py
- workspaces
- package.json
- test_agent_stream.py
- App.tsx
- PETER PAN — web surfaces

## God Nodes (most connected - your core abstractions)
1. `Settings` - 50 edges
2. `build_story()` - 21 edges
3. `Alert` - 19 edges
4. `synthesize()` - 18 edges
5. `predict()` - 18 edges
6. `LlmSynthesisError` - 17 edges
7. `Evidence` - 16 edges
8. `SseEvent` - 15 edges
9. `compilerOptions` - 15 edges
10. `compilerOptions` - 15 edges

## Surprising Connections (you probably didn't know these)
- `test_llm_off_by_default_keeps_deterministic_path()` --calls--> `Settings`  [INFERRED]
  tests/test_llm_synthesis.py → src/peterpan/config.py
- `Verdict` --uses--> `Settings`  [INFERRED]
  evals/run_llm_judge.py → src/peterpan/config.py
- `Verdict` --uses--> `Severity`  [INFERRED]
  evals/run_llm_judge.py → src/peterpan/schemas.py
- `judge()` --calls--> `log_usage()`  [INFERRED]
  evals/run_llm_judge.py → src/peterpan/usage.py
- `judge()` --calls--> `make_event()`  [INFERRED]
  evals/run_llm_judge.py → src/peterpan/usage.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Self-Improving Skills Loop Implementation** — claude_skills_learn_skill, claude_skills_reflect_skill, claude_skills_evolve_skill, claude_learnings_learnings_md [EXTRACTED 1.00]
- **Prompt Engineering Lifecycle** — prompt_incident_agent_system_v1_txt, prompt_incident_agent_system_v2_txt, prompt_incident_agent_system_v4_txt, prompt_incident_agent_system_v5_txt, prompt_incident_agent_system_v6_txt, prompt_incident_agent_log_md [EXTRACTED 1.00]

## Communities (80 total, 32 thin omitted)

### Community 0 - "Budget Tracking"
Cohesion: 0.16
Nodes (19): log_usage(), make_event(), Path, Path, A torn write (crash mid-append) must not take down PETER PAN OS., JSON-valid rows can still be poisoned: an unparsable ts, a naive ts, or     stri, test_load_usage_skips_poisoned_but_schema_valid_rows(), test_load_usage_survives_corrupt_lines() (+11 more)

### Community 1 - "LLM Story Evaluation"
Cohesion: 0.10
Nodes (36): apply_floor_guardrails(), MlPrediction, Prediction, Raw model output — NOT a Prediction until the floor guardrails ran., Merge model output into the floor's verdict. The floor always wins:      - class, Prediction, predict(), predict_full() (+28 more)

### Community 2 - "Knowledge Base Ingestion"
Cohesion: 0.08
Nodes (42): _kind_for(), load_corpus(), load_full_text(), Evidence, Path, Knowledge base loader — the files under knowledge/ ARE the corpus.  Both retriev, Classify by ancestor dir, not just the immediate parent — so incidents     fed u, Title + the symptom/what-happened paragraph — keyword-rich for retrieval.      H (+34 more)

### Community 3 - "Predictor Training"
Cohesion: 0.11
Nodes (31): Linear, main(), Train the local predictor classifier and report accuracy.  Usage:  python script, evaluate_holdout(), _fit(), _load_rows(), MlPredictError, model_predict() (+23 more)

### Community 4 - "LLM Story Synthesis"
Cohesion: 0.10
Nodes (33): cache_key(), The ADR-0001 key convention: sha256 over a length-prefixed encoding.      Length, _LlmStoryDraft, LlmSynthesisError, load_system_prompt(), Alert, BaseModel, Exception (+25 more)

### Community 5 - "Environment Configuration"
Cohesion: 0.24
Nodes (9): Env, LlmProvider, PredictorBackend, StrEnum, RagBackend, Environment-based configuration.  The three-environment model is a core product, BaseModel, QueryIn (+1 more)

### Community 6 - "Input/Output Guardrails"
Cohesion: 0.08
Nodes (28): GuardrailVerdict, check_input(), check_input_route(), check_output(), check_output_route(), BaseModel, Guardrails service — deterministic floors with final say over any LLM.  Input ra, TextIn (+20 more)

### Community 7 - "RAG Retrieval Service"
Cohesion: 0.11
Nodes (25): _lexical_confidence(), _load_corpus_and_text(), memory_route(), _overlap(), Evidence, Path, RagResult, query_route() (+17 more)

### Community 8 - "Tool Permissions"
Cohesion: 0.07
Nodes (28): hooks, PreToolUse, permissions, allow, deny, $schema, Bash(aws * delete*), Bash(aws * terminate*) (+20 more)

### Community 9 - "System Documentation"
Cohesion: 0.29
Nodes (7): incident-agent/LOG.md — Prompt Engineering Log, incident-agent/system-v1.txt — Agent Prompt v1, incident-agent/system-v2.txt — Agent Prompt v2, incident-agent/system-v4.txt — Agent Prompt v4, incident-agent/system-v5.txt — Agent Prompt v5, incident-agent/system-v6.txt — Agent Prompt v6, versions.yaml — Prompt Versions

### Community 10 - "Story Graph Orchestration"
Cohesion: 0.15
Nodes (18): build_graph(), classify_node(), Alert, IncidentStory, The story-builder as a LangGraph graph: classify → retrieve → synthesize.  Same, Deterministic floor — always first; its severity may only be argued up., Fixture synthesiser. A real LLM (prompts/incident-agent/v1.md) replaces     this, Run the compiled graph end-to-end. Bounded by construction: the graph     is a D (+10 more)

### Community 11 - "Learning & Governance"
Cohesion: 0.12
Nodes (18): Action Preview Gate, architecture-guardian — Invariant Reviewer, security-reviewer — Safety Gate, test-engineer — Coverage Guardian, LEARNINGS.md — Captured Lessons, CLAUDE.md — Working Memory, evolve — Level 4 Skill Amendment, learn — Level 2 Lesson Capture (+10 more)

### Community 12 - "Operations Console"
Cohesion: 0.09
Nodes (22): HTMLResponse, agents_route(), budget_route(), create_lead(), dashboard_route(), info_route(), LeadRequest, _notify_lead_webhook() (+14 more)

### Community 13 - "Action Approval Gate"
Cohesion: 0.07
Nodes (52): BaseSettings, _ensure_index(), main(), _print_plan(), Ingest knowledge/ into the Pinecone index (contract §3, opt-in live path).  Buil, Create the serverless index on first run (idempotent — skips if present)., Mutating actions may only auto-execute outside production., Settings (+44 more)

### Community 14 - "Secrets Deployment"
Cohesion: 0.67
Nodes (3): main(), Push the deploy keys from .env into AWS Secrets Manager — values never printed., read_env_values()

### Community 15 - "Memory Leak Incident"
Cohesion: 0.67
Nodes (3): INC-2263 — Memory Leak, checkout-oom.md — Runbook, memory-leak-hunt.md — Runbook

### Community 36 - "prompts/README.md — Prompt Versioning"
Cohesion: 0.33
Nodes (6): alert-extraction/v1.md — Extraction Prompt, assistant/v1.md — Conversational Prompt, guardrails/v1.md — Safety Prompts, incident-agent/v1.md — Agent Surface v1, rag-injection/v1.md — RAG Injection Prompt, prompts/README.md — Prompt Versioning

### Community 41 - "BaseModel"
Cohesion: 0.18
Nodes (15): ActionRisk, AgentRun, Deployment, Feedback, FeedbackVerdict, GuardrailVerdict, Panel, PanelKind (+7 more)

### Community 42 - "StrEnum"
Cohesion: 0.10
Nodes (25): _Embeddings, FakeIndex, FakeVoyage, _match(), _no_sleep(), _plan(), Any, MonkeyPatch (+17 more)

### Community 43 - "build_story"
Cohesion: 0.18
Nodes (15): ActionPreview, ActionRisk, approve(), propose_action(), Every mutating action goes through here. In production, HIGH risk always     req, make_alert(), Alert, Agent: story building and the ActionPreview approval gate. (+7 more)

### Community 44 - "test_ppos_budget.py"
Cohesion: 0.27
Nodes (13): budget_status(), Spend over the last 24h vs the configured daily budget.      Report-only: PETER, event_at(), datetime, PETER PAN OS: time windows, groupings, and the deterministic budget guard., test_aggregate_by_model_and_service(), test_budget_counts_last_24h_only(), test_budget_exceeded_over_100_percent() (+5 more)

### Community 45 - "IncidentStory"
Cohesion: 0.15
Nodes (19): build_dashboard(), DashboardError, deterministic_spec(), _llm_spec(), DashboardSpec, Exception, IncidentStory, Draw me the problem' — LLM-designed dashboards as a typed, validated spec.  Same (+11 more)

### Community 46 - "test_ppos_dashboard.py"
Cohesion: 0.17
Nodes (16): Bucketed cost/token time series — feeds the OS dashboard charts., usage_series_route(), Bucketed cost/token series over the last N hours — the OS chart feed.      Empty, timeseries(), event_at(), datetime, MonkeyPatch, Path (+8 more)

### Community 47 - "run_retrieval_eval.py"
Cohesion: 0.27
Nodes (12): _doc_id(), _lexical_retriever(), _load_cases(), main(), _pinecone_retriever(), Evidence, Path, _rank_of() (+4 more)

### Community 48 - "tips"
Cohesion: 0.21
Nodes (15): tips_route(), usage_route(), aggregate(), _is_valid_row(), load_usage(), Token/cost usage logging — the data source for PETER PAN OS.  Every LLM call in, Events from the last N hours (None = everything)., Cost and token totals grouped by agent/model/service — the OS headline table. (+7 more)

### Community 49 - "test_dashboard.py"
Cohesion: 0.05
Nodes (40): react-router-dom, dependencies, @peterpan/types, react, react-dom, react-router-dom, devDependencies, eslint (+32 more)

### Community 50 - "run_llm_judge.py"
Cohesion: 0.21
Nodes (11): judge(), main(), BaseModel, LLM-judge layer over the story eval cases (RAGAS-style faithfulness).  For each, Verdict, _load_jsonl(), Path, Story-pipeline eval: run every eval case through build_story and score it.  Scor (+3 more)

### Community 57 - "cache.py"
Cohesion: 0.10
Nodes (25): ABC, cache_get(), cache_set(), cache_stats(), CacheBackend, _degrade(), dequeue(), enqueue() (+17 more)

### Community 58 - "devDependencies"
Cohesion: 0.05
Nodes (38): dependencies, @peterpan/types, react, react-dom, devDependencies, eslint, @eslint/js, tailwindcss (+30 more)

### Community 59 - "devDependencies"
Cohesion: 0.05
Nodes (38): dependencies, @peterpan/types, react, react-dom, devDependencies, eslint, @eslint/js, tailwindcss (+30 more)

### Community 60 - "test_cache.py"
Cohesion: 0.08
Nodes (15): LogCaptureFixture, MonkeyPatch, Cache/queue (ADR-0001) — in-process backend, key stability, fallback., Every test starts from a clean slate: no PP_REDIS_URL, no leaked     backend/cou, The fixture-first path: even with a bad PP_REDIS_URL, cache_get/cache_set     mu, Selection success path: PP_REDIS_URL set, construction/ping succeeds ->     the, A backend that connects fine at startup but fails on a later call     (server re, _reset_cache_state() (+7 more)

### Community 61 - "index.ts"
Cohesion: 0.08
Nodes (22): ACTION_RISKS, ActionPreview, ActionRisk, AgentRun, Alert, DashboardSpec, Deployment, Evidence (+14 more)

### Community 62 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, isolatedModules, jsx, lib, module, moduleResolution, noEmit, noFallthroughCasesInSwitch (+14 more)

### Community 63 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, isolatedModules, jsx, lib, module, moduleResolution, noEmit, noFallthroughCasesInSwitch (+14 more)

### Community 64 - "App.tsx"
Cohesion: 0.10
Nodes (14): Feature, FEATURES, PLACEHOLDER_LOGOS, EMPTY, FieldErrors, FieldName, FieldProps, LeadForm() (+6 more)

### Community 65 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, isolatedModules, jsx, lib, module, moduleResolution, noEmit, noFallthroughCasesInSwitch (+14 more)

### Community 66 - "Evidence"
Cohesion: 0.18
Nodes (16): ActionPreview, DashboardSpec, Evidence, IncidentStory, A renderable dashboard: the answer to 'draw me the problem'.      Rendered by th, One piece of collected context, always with a citation trail., The explained incident: what changed, likely cause, evidence, options.      This, A proposed action. HIGH-risk actions are never auto-executed —     they require (+8 more)

### Community 67 - "build_story"
Cohesion: 0.16
Nodes (16): build_story(), dashboard_route(), Alert, DashboardSpec, IncidentStory, JSONResponse, Agent service — builds the IncidentStory and proposes gated actions.  MVP: a det, Draw me the problem': story pipeline + dashboard spec generation. (+8 more)

### Community 68 - "test_ppos_leads.py"
Cohesion: 0.29
Nodes (12): leads_path(), MonkeyPatch, Path, Landing-page lead capture on the PPOS service (POST /leads)., test_bounds_enforced(), test_create_lead_appends_jsonl(), test_create_lead_message_optional(), test_invalid_email_rejected() (+4 more)

### Community 69 - "workspaces"
Cohesion: 0.22
Nodes (8): description, name, private, workspaces, packages/types, web/agent-os, web/demo, web/landing

### Community 70 - "package.json"
Cohesion: 0.29
Nodes (6): description, exports, name, private, type, version

### Community 71 - "test_agent_stream.py"
Cohesion: 0.33
Nodes (4): _parse_sse(), Contract test for the SSE incident-story stream (CONTRACTS.md §5).  GET /agent/s, Parse `event:`/`data:` frames (separated by a blank line) into     (event, data), test_stream_event_order_and_payloads()

## Knowledge Gaps
- **251 isolated node(s):** `$schema`, `Read`, `Glob`, `Grep`, `Bash(git status)` (+246 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **32 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Action Approval Gate` to `LLM Story Evaluation`, `Knowledge Base Ingestion`, `Evidence`, `LLM Story Synthesis`, `Environment Configuration`, `StrEnum`, `Operations Console`, `IncidentStory`, `run_llm_judge.py`, `cache.py`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._
- **Why does `synthesize()` connect `LLM Story Synthesis` to `Budget Tracking`, `build_story`, `IncidentStory`, `Action Approval Gate`, `cache.py`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Why does `search()` connect `RAG Retrieval Service` to `Story Graph Orchestration`, `build_story`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 33 inferred relationships involving `Settings` (e.g. with `Verdict` and `CacheBackend`) actually correct?**
  _`Settings` has 33 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `build_story()` (e.g. with `main()` and `run()`) actually correct?**
  _`build_story()` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `Alert` (e.g. with `main()` and `Verdict`) actually correct?**
  _`Alert` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `synthesize()` (e.g. with `cache_get()` and `cache_key()`) actually correct?**
  _`synthesize()` has 8 INFERRED edges - model-reasoned connections that need verification._