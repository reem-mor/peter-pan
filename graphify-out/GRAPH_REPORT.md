# Graph Report - agent-a1eb4644b9546e25e  (2026-07-18)

## Corpus Check
- 100 files · ~46,983 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 627 nodes · 1186 edges · 57 communities (27 shown, 30 thin omitted)
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 256 edges (avg confidence: 0.73)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a138434d`
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

## God Nodes (most connected - your core abstractions)
1. `Settings` - 41 edges
2. `Alert` - 29 edges
3. `Evidence` - 22 edges
4. `build_story()` - 20 edges
5. `Prediction` - 19 edges
6. `predict()` - 18 edges
7. `IncidentStory` - 16 edges
8. `LlmSynthesisError` - 15 edges
9. `synthesize()` - 14 edges
10. `MemoryRecord` - 14 edges

## Surprising Connections (you probably didn't know these)
- `test_llm_off_by_default_keeps_deterministic_path()` --calls--> `Settings`  [INFERRED]
  tests/test_llm_synthesis.py → src/peterpan/config.py
- `test_negative_values_rejected()` --calls--> `make_event()`  [INFERRED]
  tests/test_ppos_usage.py → src/peterpan/usage.py
- `Verdict` --uses--> `Settings`  [INFERRED]
  evals/run_llm_judge.py → src/peterpan/config.py
- `Verdict` --uses--> `Alert`  [INFERRED]
  evals/run_llm_judge.py → src/peterpan/schemas.py
- `Verdict` --uses--> `Severity`  [INFERRED]
  evals/run_llm_judge.py → src/peterpan/schemas.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Self-Improving Skills Loop Implementation** — claude_skills_learn_skill, claude_skills_reflect_skill, claude_skills_evolve_skill, claude_learnings_learnings_md [EXTRACTED 1.00]
- **Prompt Engineering Lifecycle** — prompt_incident_agent_system_v1_txt, prompt_incident_agent_system_v2_txt, prompt_incident_agent_system_v4_txt, prompt_incident_agent_system_v5_txt, prompt_incident_agent_system_v6_txt, prompt_incident_agent_log_md [EXTRACTED 1.00]

## Communities (57 total, 30 thin omitted)

### Community 0 - "Budget Tracking"
Cohesion: 0.16
Nodes (24): Real-LLM synthesis. Raises LlmSynthesisError on any failure., synthesize(), _is_valid_row(), load_usage(), log_usage(), make_event(), model_rates(), Path (+16 more)

### Community 1 - "LLM Story Evaluation"
Cohesion: 0.09
Nodes (40): _load_jsonl(), Path, Story-pipeline eval: run every eval case through build_story and score it.  Scor, run(), apply_floor_guardrails(), MlPrediction, Raw model output — NOT a Prediction until the floor guardrails ran., Merge model output into the floor's verdict. The floor always wins:      - class (+32 more)

### Community 2 - "Knowledge Base Ingestion"
Cohesion: 0.08
Nodes (41): _kind_for(), load_corpus(), load_full_text(), Path, Knowledge base loader — the files under knowledge/ ARE the corpus.  Both retriev, Classify by ancestor dir, not just the immediate parent — so incidents     fed u, Title + the symptom/what-happened paragraph — keyword-rich for retrieval.      H, One Evidence entry per knowledge document, source = repo-relative path. (+33 more)

### Community 3 - "Predictor Training"
Cohesion: 0.12
Nodes (30): Linear, main(), Train the local predictor classifier and report accuracy.  Usage:  python script, evaluate_holdout(), _fit(), _load_rows(), MlPredictError, model_predict() (+22 more)

### Community 4 - "LLM Story Synthesis"
Cohesion: 0.20
Nodes (18): _LlmStoryDraft, LlmSynthesisError, load_system_prompt(), BaseModel, Exception, Claude-backed story synthesis — opt-in, invariant-guarded, metered.  The LLM ref, Any LLM-path failure. Callers must catch this and fall back., The exact JSON contract the prompt demands from the model. (+10 more)

### Community 5 - "Environment Configuration"
Cohesion: 0.31
Nodes (7): Env, LlmProvider, PredictorBackend, StrEnum, RagBackend, Environment-based configuration.  The three-environment model is a core product, PETER PAN WebUI — Dynamic Incident Dashboard + PETER PAN OS console.  Run:  stre

### Community 6 - "Input/Output Guardrails"
Cohesion: 0.09
Nodes (26): GuardrailVerdict, check_input(), check_input_route(), check_output(), check_output_route(), BaseModel, Guardrails service — deterministic floors with final say over any LLM.  Input ra, TextIn (+18 more)

### Community 7 - "RAG Retrieval Service"
Cohesion: 0.10
Nodes (28): Evidence, RagResult, One piece of collected context, always with a citation trail., _lexical_confidence(), _load_corpus_and_text(), memory_route(), _overlap(), BaseModel (+20 more)

### Community 8 - "Tool Permissions"
Cohesion: 0.07
Nodes (28): hooks, PreToolUse, permissions, allow, deny, $schema, Bash(aws * delete*), Bash(aws * terminate*) (+20 more)

### Community 9 - "System Documentation"
Cohesion: 0.29
Nodes (7): incident-agent/LOG.md — Prompt Engineering Log, incident-agent/system-v1.txt — Agent Prompt v1, incident-agent/system-v2.txt — Agent Prompt v2, incident-agent/system-v4.txt — Agent Prompt v4, incident-agent/system-v5.txt — Agent Prompt v5, incident-agent/system-v6.txt — Agent Prompt v6, versions.yaml — Prompt Versions

### Community 10 - "Story Graph Orchestration"
Cohesion: 0.18
Nodes (15): build_graph(), classify_node(), The story-builder as a LangGraph graph: classify → retrieve → synthesize.  Same, Deterministic floor — always first; its severity may only be argued up., Fixture synthesiser. A real LLM (prompts/incident-agent/v1.md) replaces     this, Run the compiled graph end-to-end. Bounded by construction: the graph     is a D, retrieve_node(), run_story_graph() (+7 more)

### Community 11 - "Learning & Governance"
Cohesion: 0.12
Nodes (18): Action Preview Gate, architecture-guardian — Invariant Reviewer, security-reviewer — Safety Gate, test-engineer — Coverage Guardian, LEARNINGS.md — Captured Lessons, CLAUDE.md — Working Memory, evolve — Level 4 Skill Amendment, learn — Level 2 Lesson Capture (+10 more)

### Community 12 - "Operations Console"
Cohesion: 0.11
Nodes (17): HTMLResponse, JSONResponse, agents_route(), budget_route(), dashboard_route(), info_route(), _probe(), PETER PAN OS — the operations console for the AI system itself.  Monitors what t (+9 more)

### Community 13 - "Action Approval Gate"
Cohesion: 0.07
Nodes (51): BaseSettings, _ensure_index(), main(), _print_plan(), Ingest knowledge/ into the Pinecone index (contract §3, opt-in live path).  Buil, Create the serverless index on first run (idempotent — skips if present)., Mutating actions may only auto-execute outside production., Settings (+43 more)

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
Cohesion: 0.16
Nodes (16): ActionPreview, ActionRisk, AgentRun, Deployment, Feedback, FeedbackVerdict, Panel, PanelKind (+8 more)

### Community 42 - "StrEnum"
Cohesion: 0.10
Nodes (25): _Embeddings, FakeIndex, FakeVoyage, _match(), _no_sleep(), _plan(), Any, MonkeyPatch (+17 more)

### Community 43 - "build_story"
Cohesion: 0.15
Nodes (18): approve(), build_story(), propose_action(), Agent service — builds the IncidentStory and proposes gated actions.  MVP: a det, Every mutating action goes through here. In production, HIGH risk always     req, Build the RAG query from an alert. search() rejects blank queries, and     title, Planner → tools → synthesis. Deterministic by default; PP_LLM=anthropic     upgr, _repair_options() (+10 more)

### Community 44 - "test_ppos_budget.py"
Cohesion: 0.18
Nodes (19): usage_route(), aggregate(), budget_status(), Events from the last N hours (None = everything)., Cost and token totals grouped by agent/model/service — the OS headline table., Spend over the last 24h vs the configured daily budget.      Report-only: PETER, window(), event_at() (+11 more)

### Community 45 - "IncidentStory"
Cohesion: 0.18
Nodes (18): build_dashboard(), DashboardError, deterministic_spec(), _llm_spec(), Exception, Draw me the problem' — LLM-designed dashboards as a typed, validated spec.  Same, Any LLM dashboard failure. Callers fall back to the deterministic spec., The fallback dashboard: story-first, evidence-cited, always available. (+10 more)

### Community 46 - "test_ppos_dashboard.py"
Cohesion: 0.20
Nodes (14): Bucketed cost/token series over the last N hours — the OS chart feed.      Empty, timeseries(), event_at(), datetime, MonkeyPatch, Path, PETER PAN OS dashboard feeds: time series, mesh health sweep, dashboard page., test_dashboard_endpoint_404_when_file_missing() (+6 more)

### Community 47 - "run_retrieval_eval.py"
Cohesion: 0.30
Nodes (11): _doc_id(), _lexical_retriever(), _load_cases(), main(), _pinecone_retriever(), Path, _rank_of(), Retrieval eval — does the RAG backend return the right document?  A labeled gold (+3 more)

### Community 48 - "tips"
Cohesion: 0.22
Nodes (8): tips_route(), Cheap heuristics that catch the common cost regressions early., tips(), MonkeyPatch, PETER PAN OS: usage logging, aggregation, and tips., test_negative_values_rejected(), test_os_endpoints(), test_tips_on_empty_log_prompt_wiring()

### Community 49 - "test_dashboard.py"
Cohesion: 0.36
Nodes (6): make_story(), MonkeyPatch, Dashboard generator: fallback determinism, allowlist guard, endpoint., test_deterministic_spec_is_story_first_and_cited(), test_llm_failure_falls_back(), test_llm_off_returns_deterministic()

### Community 50 - "run_llm_judge.py"
Cohesion: 0.47
Nodes (5): judge(), main(), BaseModel, LLM-judge layer over the story eval cases (RAGAS-style faithfulness).  For each, Verdict

## Knowledge Gaps
- **84 isolated node(s):** `$schema`, `Read`, `Glob`, `Grep`, `Bash(git status)` (+79 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Action Approval Gate` to `Budget Tracking`, `LLM Story Evaluation`, `Knowledge Base Ingestion`, `LLM Story Synthesis`, `Environment Configuration`, `RAG Retrieval Service`, `StrEnum`, `IncidentStory`, `test_dashboard.py`, `run_llm_judge.py`?**
  _High betweenness centrality (0.141) - this node is a cross-community bridge._
- **Why does `Evidence` connect `RAG Retrieval Service` to `Knowledge Base Ingestion`, `LLM Story Synthesis`, `BaseModel`, `Story Graph Orchestration`, `build_story`, `Action Approval Gate`, `IncidentStory`, `run_retrieval_eval.py`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `Alert` connect `LLM Story Evaluation` to `Budget Tracking`, `Predictor Training`, `LLM Story Synthesis`, `BaseModel`, `Story Graph Orchestration`, `build_story`, `IncidentStory`, `test_dashboard.py`, `run_llm_judge.py`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Are the 24 inferred relationships involving `Settings` (e.g. with `Verdict` and `DashboardError`) actually correct?**
  _`Settings` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `Alert` (e.g. with `main()` and `Verdict`) actually correct?**
  _`Alert` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `Evidence` (e.g. with `StoryState` and `synthesize_node()`) actually correct?**
  _`Evidence` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `build_story()` (e.g. with `main()` and `run()`) actually correct?**
  _`build_story()` has 12 INFERRED edges - model-reasoned connections that need verification._