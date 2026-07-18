# Graph Report - agent-aadc713942b32af51  (2026-07-18)

## Corpus Check
- 127 files · ~54,625 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1042 nodes · 1685 edges · 80 communities (47 shown, 33 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 306 edges (avg confidence: 0.71)
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
- devDependencies
- devDependencies
- devDependencies
- test_cache.py
- index.ts
- compilerOptions
- compilerOptions
- compilerOptions
- observability.py
- usage.py
- workspaces
- package.json
- test_agent_stream.py
- run
- App.tsx
- App.tsx
- PETER PAN — web surfaces

## God Nodes (most connected - your core abstractions)
1. `Settings` - 62 edges
2. `build_story()` - 21 edges
3. `synthesize()` - 19 edges
4. `Alert` - 19 edges
5. `predict()` - 18 edges
6. `LlmSynthesisError` - 17 edges
7. `Evidence` - 16 edges
8. `SseEvent` - 15 edges
9. `compilerOptions` - 15 edges
10. `compilerOptions` - 15 edges

## Surprising Connections (you probably didn't know these)
- `test_llm_off_by_default_keeps_deterministic_path()` --calls--> `Settings`  [INFERRED]
  tests/test_llm_synthesis.py → src/peterpan/config.py
- `test_negative_values_rejected()` --calls--> `make_event()`  [INFERRED]
  tests/test_ppos_usage.py → src/peterpan/usage.py
- `Verdict` --uses--> `Settings`  [INFERRED]
  evals/run_llm_judge.py → src/peterpan/config.py
- `Verdict` --uses--> `Severity`  [INFERRED]
  evals/run_llm_judge.py → src/peterpan/schemas.py
- `judge()` --calls--> `log_usage()`  [INFERRED]
  evals/run_llm_judge.py → src/peterpan/usage.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Self-Improving Skills Loop Implementation** — claude_skills_learn_skill, claude_skills_reflect_skill, claude_skills_evolve_skill, claude_learnings_learnings_md [EXTRACTED 1.00]
- **Prompt Engineering Lifecycle** — prompt_incident_agent_system_v1_txt, prompt_incident_agent_system_v2_txt, prompt_incident_agent_system_v4_txt, prompt_incident_agent_system_v5_txt, prompt_incident_agent_system_v6_txt, prompt_incident_agent_log_md [EXTRACTED 1.00]

## Communities (80 total, 33 thin omitted)

### Community 0 - "Budget Tracking"
Cohesion: 0.26
Nodes (12): log_usage(), make_event(), Path, Path, A torn write (crash mid-append) must not take down PETER PAN OS., JSON-valid rows can still be poisoned: an unparsable ts, a naive ts, or     stri, test_load_usage_skips_poisoned_but_schema_valid_rows(), test_load_usage_survives_corrupt_lines() (+4 more)

### Community 1 - "LLM Story Evaluation"
Cohesion: 0.05
Nodes (67): Linear, main(), Train the local predictor classifier and report accuracy.  Usage:  python script, apply_floor_guardrails(), evaluate_holdout(), _fit(), _load_rows(), MlPredictError (+59 more)

### Community 2 - "Knowledge Base Ingestion"
Cohesion: 0.08
Nodes (42): _kind_for(), load_corpus(), load_full_text(), Evidence, Path, Knowledge base loader — the files under knowledge/ ARE the corpus.  Both retriev, Classify by ancestor dir, not just the immediate parent — so incidents     fed u, Title + the symptom/what-happened paragraph — keyword-rich for retrieval.      H (+34 more)

### Community 3 - "Predictor Training"
Cohesion: 0.09
Nodes (27): ABC, cache_get(), cache_key(), cache_set(), cache_stats(), CacheBackend, _degrade(), dequeue() (+19 more)

### Community 4 - "LLM Story Synthesis"
Cohesion: 0.13
Nodes (27): _LlmStoryDraft, LlmSynthesisError, load_system_prompt(), Alert, BaseModel, Exception, IncidentStory, Prediction (+19 more)

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
Cohesion: 0.11
Nodes (18): HTMLResponse, agents_route(), budget_route(), dashboard_route(), info_route(), _probe(), JSONResponse, PETER PAN OS — the operations console for the AI system itself.  Monitors what t (+10 more)

### Community 13 - "Action Approval Gate"
Cohesion: 0.07
Nodes (49): _ensure_index(), main(), _print_plan(), Ingest knowledge/ into the Pinecone index (contract §3, opt-in live path).  Buil, Create the serverless index on first run (idempotent — skips if present)., _backoff_seconds(), batched(), build_metadata() (+41 more)

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
Cohesion: 0.12
Nodes (28): DashboardError, Exception, Any LLM dashboard failure. Callers fall back to the deterministic spec., ActionPreview, ActionRisk, AgentRun, DashboardSpec, Deployment (+20 more)

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
Cohesion: 0.13
Nodes (20): build_story(), dashboard_route(), Alert, DashboardSpec, IncidentStory, JSONResponse, Agent service — builds the IncidentStory and proposes gated actions.  MVP: a det, Draw me the problem': story pipeline + dashboard spec generation. (+12 more)

### Community 46 - "test_ppos_dashboard.py"
Cohesion: 0.20
Nodes (14): Bucketed cost/token series over the last N hours — the OS chart feed.      Empty, timeseries(), event_at(), datetime, MonkeyPatch, Path, PETER PAN OS dashboard feeds: time series, mesh health sweep, dashboard page., test_dashboard_endpoint_404_when_file_missing() (+6 more)

### Community 47 - "run_retrieval_eval.py"
Cohesion: 0.27
Nodes (12): _doc_id(), _lexical_retriever(), _load_cases(), main(), _pinecone_retriever(), Evidence, Path, _rank_of() (+4 more)

### Community 48 - "tips"
Cohesion: 0.24
Nodes (10): Cheap heuristics that catch the common cost regressions early., tips(), MonkeyPatch, Path, PETER PAN OS: usage logging, aggregation, and tips., test_log_and_load_roundtrip(), test_negative_values_rejected(), test_os_endpoints() (+2 more)

### Community 49 - "test_dashboard.py"
Cohesion: 0.08
Nodes (36): BaseSettings, Mutating actions may only auto-execute outside production., Settings, build_dashboard(), deterministic_spec(), _llm_spec(), DashboardSpec, IncidentStory (+28 more)

### Community 50 - "run_llm_judge.py"
Cohesion: 0.19
Nodes (13): judge(), main(), BaseModel, LLM-judge layer over the story eval cases (RAGAS-style faithfulness).  For each, Verdict, Alert, RagResult, Inbound signal from monitoring (Grafana webhook, pager, etc.). (+5 more)

### Community 57 - "devDependencies"
Cohesion: 0.05
Nodes (40): react-router-dom, dependencies, @peterpan/types, react, react-dom, react-router-dom, devDependencies, eslint (+32 more)

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

### Community 64 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, isolatedModules, jsx, lib, module, moduleResolution, noEmit, noFallthroughCasesInSwitch (+14 more)

### Community 65 - "observability.py"
Cohesion: 0.14
Nodes (19): _append_prompt_log(), _preview(), prompt_version(), Any, Path, Langfuse tracing + structured prompt/completion logging (§6.6).  Opt-in, fixture, One LLM call's tracing context. Always has a `trace_id`, tracing     backend or, Log this call: a Langfuse generation span (if configured) and         always a s (+11 more)

### Community 66 - "usage.py"
Cohesion: 0.27
Nodes (11): usage_route(), aggregate(), _is_valid_row(), load_usage(), Token/cost usage logging — the data source for PETER PAN OS.  Every LLM call in, Events from the last N hours (None = everything)., Cost and token totals grouped by agent/model/service — the OS headline table., Schema-valid JSON can still be a poisoned row: an unparsable/naive ts,     or no (+3 more)

### Community 67 - "workspaces"
Cohesion: 0.22
Nodes (8): description, name, private, workspaces, packages/types, web/agent-os, web/demo, web/landing

### Community 68 - "package.json"
Cohesion: 0.29
Nodes (6): description, exports, name, private, type, version

### Community 69 - "test_agent_stream.py"
Cohesion: 0.33
Nodes (4): _parse_sse(), Contract test for the SSE incident-story stream (CONTRACTS.md §5).  GET /agent/s, Parse `event:`/`data:` frames (separated by a blank line) into     (event, data), test_stream_event_order_and_payloads()

### Community 70 - "run"
Cohesion: 0.50
Nodes (4): _load_jsonl(), Path, Story-pipeline eval: run every eval case through build_story and score it.  Scor, run()

## Knowledge Gaps
- **241 isolated node(s):** `$schema`, `Read`, `Glob`, `Grep`, `Bash(git status)` (+236 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **33 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `test_dashboard.py` to `observability.py`, `Knowledge Base Ingestion`, `Predictor Training`, `LLM Story Synthesis`, `Environment Configuration`, `LLM Story Evaluation`, `BaseModel`, `StrEnum`, `Action Approval Gate`, `IncidentStory`, `run_llm_judge.py`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._
- **Why does `synthesize()` connect `LLM Story Synthesis` to `Budget Tracking`, `observability.py`, `Predictor Training`, `IncidentStory`, `test_dashboard.py`, `run_llm_judge.py`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Why does `build_story()` connect `IncidentStory` to `LLM Story Evaluation`, `LLM Story Synthesis`, `run`, `RAG Retrieval Service`, `Story Graph Orchestration`, `build_story`, `test_dashboard.py`, `run_llm_judge.py`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Are the 43 inferred relationships involving `Settings` (e.g. with `Verdict` and `CacheBackend`) actually correct?**
  _`Settings` has 43 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `build_story()` (e.g. with `main()` and `run()`) actually correct?**
  _`build_story()` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `synthesize()` (e.g. with `cache_get()` and `cache_key()`) actually correct?**
  _`synthesize()` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `Alert` (e.g. with `main()` and `Verdict`) actually correct?**
  _`Alert` has 16 INFERRED edges - model-reasoned connections that need verification._