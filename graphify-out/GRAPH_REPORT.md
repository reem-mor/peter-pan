# Graph Report - peter-pan-canonical-audit  (2026-07-22)

## Corpus Check
- 217 files · ~152,526 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1843 nodes · 3292 edges · 134 communities (97 shown, 37 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 574 edges (avg confidence: 0.73)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6c97e471`
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
- test_observability.py
- test_scoring.py
- test_nemo_rails.py
- observability.py
- append_feedback
- IncidentGraph.tsx
- TokenUsage.tsx
- stream.ts
- format.ts
- os.ts
- Monitoring, Evaluation, and Learning Loop
- Roadmap and Reference Baselines
- run_feedback_eval.py
- test_feedback_eval.py
- test_confidence_bounds.py
- .actions_allowed
- ui.tsx
- n8n endpoint coverage — mesh contract map
- TokenUsage.tsx
- ServiceDetailPanel.tsx
- test_memory_feed.py
- guardrails_config/
- test_config_secrets.py
- Deployment
- os.ts
- usage.py
- build_story
- test_langgraph_and_evals.py
- search
- test_edge_cases.py
- meshFetch
- test_production_gate.py
- knowledge.py
- test_retrieval_eval.py
- ApiTokenMiddleware
- App.tsx
- test_ui_smoke.py
- ADR-0002: Canonical retrieval backend
- eslint.config.mjs
- page.tsx
- layout.tsx
- README.md
- page.tsx
- README.md
- next.config.ts
- postcss.config.mjs
- format.ts
- HealthStrip.tsx
- conftest.py
- next-env.d.ts
- test_langgraph_and_evals.py
- predict_full
- P6 blocker remediation plan

## God Nodes (most connected - your core abstractions)
1. `Settings` - 136 edges
2. `build_story()` - 35 edges
3. `synthesize()` - 32 edges
4. `LlmSynthesisError` - 28 edges
5. `Alert` - 23 edges
6. `SseEvent` - 20 edges
7. `DrawRequest` - 19 edges
8. `StepEvent` - 19 edges
9. `export_grafana_preview()` - 18 edges
10. `Evidence` - 18 edges

## Surprising Connections (you probably didn't know these)
- `check_citation_action()` --calls--> `detect_fabricated_citation()`  [INFERRED]
  guardrails_config/actions.py → src/peterpan/nemo_rails.py
- `test_llm_off_by_default_keeps_deterministic_path()` --calls--> `Settings`  [INFERRED]
  tests/test_llm_synthesis.py → src/peterpan/config.py
- `test_holdout_accuracy_is_honest_and_passes_floor()` --calls--> `evaluate_holdout()`  [INFERRED]
  tests/test_ml_holdout.py → src/peterpan/ml.py
- `test_prediction_rejects_certainty()` --calls--> `Prediction`  [INFERRED]
  tests/test_confidence_bounds.py → src/peterpan/schemas.py
- `test_lexical_rag_reports_backend_not_fallback()` --calls--> `search()`  [INFERRED]
  tests/test_provider_truth.py → src/peterpan/services/rag.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Self-Improving Skills Loop Implementation** — claude_skills_learn_skill, claude_skills_reflect_skill, claude_skills_evolve_skill, claude_learnings_learnings_md [EXTRACTED 1.00]
- **Prompt Engineering Lifecycle** — prompt_incident_agent_system_v1_txt, prompt_incident_agent_system_v2_txt, prompt_incident_agent_system_v4_txt, prompt_incident_agent_system_v5_txt, prompt_incident_agent_system_v6_txt, prompt_incident_agent_log_md [EXTRACTED 1.00]

## Communities (134 total, 37 thin omitted)

### Community 0 - "Budget Tracking"
Cohesion: 0.15
Nodes (20): log_usage(), make_event(), Path, Path, A torn write (crash mid-append) must not take down PETER PAN OS., JSON-valid rows can still be poisoned: an unparsable ts, a naive ts, or     stri, test_load_usage_skips_poisoned_but_schema_valid_rows(), test_load_usage_survives_corrupt_lines() (+12 more)

### Community 1 - "LLM Story Evaluation"
Cohesion: 0.16
Nodes (22): Linear, main(), Train the local predictor classifier and report accuracy.  Usage:  python script, evaluate_holdout(), _fit(), _load_rows(), MlPredictError, model_predict() (+14 more)

### Community 2 - "Knowledge Base Ingestion"
Cohesion: 0.07
Nodes (46): _kind_for(), load_corpus(), load_full_text(), Evidence, Path, Knowledge base loader — the files under knowledge/ ARE the corpus.  Both retriev, Classify by ancestor dir, not just the immediate parent — so incidents     fed u, Title + the symptom/what-happened paragraph — keyword-rich for retrieval.      H (+38 more)

### Community 3 - "Predictor Training"
Cohesion: 0.19
Nodes (22): TestClient, _body(), client(), MonkeyPatch, Path, POST /feedback + GET /feedback/summary contract., PR #53's structured outcome fields, HTTP-level: accepted on POST and     served, The on-disk JSONL a real deployment accumulates: legacy 5-field rows     (pre-#5 (+14 more)

### Community 4 - "LLM Story Synthesis"
Cohesion: 0.14
Nodes (35): _extract_json_payload(), Alert, IncidentStory, RagResult, Real-LLM synthesis. Raises LlmSynthesisError on any failure., Strip markdown fences / leading prose so model_validate_json can parse.      Bed, synthesize(), bedrock_response() (+27 more)

### Community 5 - "Environment Configuration"
Cohesion: 0.17
Nodes (11): check_citation_action(), check_injection_action(), check_secret_action(), check_topical_llm_action(), NeMo Guardrails action bindings for this config directory.  Auto-discovered by `, detect_injection(), detect_secret_leak(), test_detect_injection_false_on_genuine_alert() (+3 more)

### Community 6 - "Input/Output Guardrails"
Cohesion: 0.11
Nodes (32): GuardrailVerdict, _apply_nemo(), check_input(), check_input_full(), check_input_route(), check_output(), check_output_full(), check_output_route() (+24 more)

### Community 7 - "RAG Retrieval Service"
Cohesion: 0.20
Nodes (14): _lexical_confidence(), _load_corpus_and_text(), memory_route(), _overlap(), Evidence, Path, RAG service — retrieves runbooks and past incidents relevant to an alert.  The c, Feed a resolved, human-approved incident into the knowledge base.      The local (+6 more)

### Community 8 - "Tool Permissions"
Cohesion: 0.07
Nodes (28): hooks, PreToolUse, permissions, allow, deny, $schema, Bash(aws * delete*), Bash(aws * terminate*) (+20 more)

### Community 9 - "System Documentation"
Cohesion: 0.29
Nodes (7): incident-agent/LOG.md — Prompt Engineering Log, incident-agent/system-v1.txt — Agent Prompt v1, incident-agent/system-v2.txt — Agent Prompt v2, incident-agent/system-v4.txt — Agent Prompt v4, incident-agent/system-v5.txt — Agent Prompt v5, incident-agent/system-v6.txt — Agent Prompt v6, versions.yaml — Prompt Versions

### Community 10 - "Story Graph Orchestration"
Cohesion: 0.18
Nodes (17): build_graph(), classify_node(), Alert, IncidentStory, The story-builder as a LangGraph graph: classify → retrieve → synthesize.  Same, Floor (+ optional torch) — always first; severity may only be argued up., Fixture synthesiser. A real LLM (prompts/incident-agent/v1.md) replaces     this, Run the compiled graph end-to-end. Bounded by construction: the graph     is a D (+9 more)

### Community 11 - "Learning & Governance"
Cohesion: 0.12
Nodes (18): Action Preview Gate, architecture-guardian — Invariant Reviewer, security-reviewer — Safety Gate, test-engineer — Coverage Guardian, LEARNINGS.md — Captured Lessons, CLAUDE.md — Working Memory, evolve — Level 4 Skill Amendment, learn — Level 2 Lesson Capture (+10 more)

### Community 12 - "Operations Console"
Cohesion: 0.08
Nodes (26): agents_route(), budget_route(), create_lead(), feedback_route(), feedback_summary_route(), info_route(), LeadRequest, _notify_lead_webhook() (+18 more)

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
Nodes (23): DashboardError, Exception, Any LLM dashboard failure. Callers fall back to the deterministic spec., ActionPreview, AgentRun, Deployment, Feedback, FeedbackVerdict (+15 more)

### Community 42 - "StrEnum"
Cohesion: 0.09
Nodes (27): _Embeddings, FakeIndex, FakeVoyage, _match(), _no_sleep(), _plan(), Any, MonkeyPatch (+19 more)

### Community 43 - "build_story"
Cohesion: 0.05
Nodes (37): eslint-config-next, @eslint/eslintrc, next, @tailwindcss/postcss, @types/node, dependencies, next, @peterpan/types (+29 more)

### Community 44 - "test_ppos_budget.py"
Cohesion: 0.27
Nodes (13): budget_status(), Spend over the last 24h vs the configured daily budget.      Report-only: PETER, event_at(), datetime, PETER PAN OS: time windows, groupings, and the deterministic budget guard., test_aggregate_by_model_and_service(), test_budget_counts_last_24h_only(), test_budget_exceeded_over_100_percent() (+5 more)

### Community 45 - "IncidentStory"
Cohesion: 0.16
Nodes (19): build_dashboard(), deterministic_spec(), _llm_spec(), DashboardSpec, IncidentStory, Draw me the problem' — LLM-designed dashboards as a typed, validated spec.  Same, The fallback dashboard: story-first, evidence-cited, always available., LLM-designed spec when opted in; deterministic fallback otherwise/on failure. (+11 more)

### Community 46 - "test_ppos_dashboard.py"
Cohesion: 0.18
Nodes (15): Bucketed cost/token series over the last N hours — the OS chart feed.      Empty, timeseries(), event_at(), datetime, MonkeyPatch, Path, PETER PAN OS dashboard feeds: time series and mesh health sweep.  (The legacy se, /os/dashboard must stay gone — the operator console is web/agent-os. (+7 more)

### Community 47 - "run_retrieval_eval.py"
Cohesion: 0.27
Nodes (12): _doc_id(), _lexical_retriever(), _load_cases(), main(), _pinecone_retriever(), Evidence, Path, _rank_of() (+4 more)

### Community 48 - "tips"
Cohesion: 0.10
Nodes (38): check_topical_action(), _build_rails(), detect_fabricated_citation(), detect_topical_drift(), NemoCheckError, Any, Exception, NeMo Guardrails layer — additive screening behind the regex floor.  `peterpan.se (+30 more)

### Community 49 - "test_dashboard.py"
Cohesion: 0.05
Nodes (40): react-router-dom, dependencies, @peterpan/types, react, react-dom, react-router-dom, devDependencies, eslint (+32 more)

### Community 50 - "run_llm_judge.py"
Cohesion: 0.22
Nodes (13): predict(), Pure classification. Falls back to 'unclassified' at the alert's own severity., test_predict_survives_100kb_title(), test_predict_survives_unicode_hebrew_emoji(), make_alert(), Alert, Severity, Predictor: deterministic floor behavior. (+5 more)

### Community 57 - "cache.py"
Cohesion: 0.09
Nodes (27): ABC, cache_get(), cache_key(), cache_set(), cache_stats(), CacheBackend, _degrade(), dequeue() (+19 more)

### Community 58 - "devDependencies"
Cohesion: 0.05
Nodes (40): dependencies, @peterpan/types, react, react-dom, @xyflow/react, devDependencies, eslint, @eslint/js (+32 more)

### Community 59 - "devDependencies"
Cohesion: 0.05
Nodes (36): dependencies, react, react-dom, devDependencies, eslint, @eslint/js, tailwindcss, @tailwindcss/vite (+28 more)

### Community 60 - "test_cache.py"
Cohesion: 0.08
Nodes (15): LogCaptureFixture, MonkeyPatch, Cache/queue (ADR-0001) — in-process backend, key stability, fallback., Every test starts from a clean slate: no PP_REDIS_URL, no leaked     backend/cou, The fixture-first path: even with a bad PP_REDIS_URL, cache_get/cache_set     mu, Selection success path: PP_REDIS_URL set, construction/ping succeeds ->     the, A backend that connects fine at startup but fails on a later call     (server re, _reset_cache_state() (+7 more)

### Community 61 - "index.ts"
Cohesion: 0.09
Nodes (21): ACTION_RISKS, ActionPreview, ActionRisk, AgentRun, Alert, DashboardSpec, Feedback, FEEDBACK_VERDICTS (+13 more)

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
Cohesion: 0.13
Nodes (30): _code_fields(), _load(), _node(), _nodes(), Any, Path, Contract tests for the versioned n8n workflow exports (n8n/workflows/).  CI has, (b) No hardcoded hosts: every HTTP URL resolves through $env.PP_*_BASE. (+22 more)

### Community 67 - "build_story"
Cohesion: 0.09
Nodes (37): ProviderReport, AgentProvider, ActionRisk, DashboardSpec, GrafanaDashboardPreview, A renderable dashboard: the answer to 'draw me the problem'.      Rendered by th, A validated Grafana dashboard JSON model — preview/dry-run ONLY.      Publishing, build_story() (+29 more)

### Community 68 - "test_ppos_leads.py"
Cohesion: 0.29
Nodes (12): leads_path(), MonkeyPatch, Path, Landing-page lead capture on the PPOS service (POST /leads)., test_bounds_enforced(), test_create_lead_appends_jsonl(), test_create_lead_message_optional(), test_invalid_email_rejected() (+4 more)

### Community 69 - "workspaces"
Cohesion: 0.20
Nodes (9): description, name, private, workspaces, packages/types, web/agent-os, web/demo, web/landing (+1 more)

### Community 70 - "package.json"
Cohesion: 0.29
Nodes (6): description, exports, name, private, type, version

### Community 71 - "test_agent_stream.py"
Cohesion: 0.33
Nodes (4): _parse_sse(), Contract test for the SSE incident-story stream (CONTRACTS.md §5).  GET /agent/s, Parse `event:`/`data:` frames (separated by a blank line) into     (event, data), test_stream_event_order_and_payloads()

### Community 72 - "App.tsx"
Cohesion: 0.05
Nodes (65): UsageAggregate, SECTIONS, AreaChart(), BarList(), Donut(), PALETTE, HealthStrip(), loadServices() (+57 more)

### Community 73 - "PETER PAN — web surfaces"
Cohesion: 0.40
Nodes (4): Canonical product UI (required), Legacy Vite shells (migration sources — not the demo path), PETER PAN — web surfaces, Streamlit

### Community 80 - "test_observability.py"
Cohesion: 0.10
Nodes (26): BaseSettings, Mutating actions may only auto-execute outside production., Settings, The model id that meters, caches, and traces this call., resolve_model(), test_resolve_model_switches_on_provider(), _clean_langfuse_env(), _install_fake_langfuse() (+18 more)

### Community 81 - "test_scoring.py"
Cohesion: 0.14
Nodes (23): accuracy(), Feedback, FeedbackVerdict, Deterministic feedback scoring — closes the learning loop measurably.  verdict -, The one place verdict -> score is decided. Every aggregate below is     built fr, Counts by verdict, zero-filled for every FeedbackVerdict member so a     summary, Mean deterministic score over items. An empty set scores 0.0 — "no     feedback, Accuracy grouped by the prompt version that produced each trace.      Feedback ( (+15 more)

### Community 82 - "test_nemo_rails.py"
Cohesion: 0.18
Nodes (23): AgentCoreError, invoke_story(), _parse_story(), _payload(), Alert, Exception, IncidentStory, Amazon Bedrock AgentCore Runtime adapter — opt-in, fail-safe.  The EC2 ``agent`` (+15 more)

### Community 83 - "observability.py"
Cohesion: 0.08
Nodes (24): _append_prompt_log(), _preview(), prompt_version(), Any, Path, Langfuse tracing + structured prompt/completion logging (§6.6).  Opt-in, fixture, One LLM call's tracing context. Always has a `trace_id`, tracing     backend or, Log this call: a Langfuse generation span (if configured) and         always a s (+16 more)

### Community 84 - "append_feedback"
Cohesion: 0.17
Nodes (23): append_feedback(), count_feedback(), load_feedback(), Feedback, Path, Feedback store — append-only JSONL log of operator verdicts on agent output, the, Append one record and return the new total record count., All valid records, in file order. A torn append (crash mid-write) or a     schem (+15 more)

### Community 85 - "IncidentGraph.tsx"
Cohesion: 0.16
Nodes (15): IncidentGraph(), NODE_TYPES, NodeRole, ROLE_STYLES, ServiceFlowNode, ServiceNodeData, blastRadius(), EdgeKind (+7 more)

### Community 86 - "TokenUsage.tsx"
Cohesion: 0.09
Nodes (21): 1. Clone the Repository, 2. Select the Safe Local Environment, 3. Start the Service Mesh, 4. Start the Streamlit Interface, 5. Open the PETER PAN OS Operator Console (Agent OS), 6. Open the n8n Orchestration Panel, 7. Verify Service Health, AgentCore / Bedrock KB (not required for Pinecone path) (+13 more)

### Community 87 - "stream.ts"
Cohesion: 0.38
Nodes (5): REPLAY_STREAMS, INITIAL_STATE, StreamFrame, StreamMode, StreamPhase

### Community 88 - "format.ts"
Cohesion: 0.07
Nodes (26): esnext, next-env.d.ts, .next/types/**/*.ts, node_modules, **/*.ts, **/*.tsx, compilerOptions, allowJs (+18 more)

### Community 89 - "os.ts"
Cohesion: 0.33
Nodes (5): Create the Virtual Environment, Evaluation Infrastructure, Install Development and UI Dependencies, Run the Test Suite, Testing and Evaluation

### Community 90 - "Monitoring, Evaluation, and Learning Loop"
Cohesion: 0.40
Nodes (4): 1. Real-Time Observability and Production Monitoring with Langfuse, 2. Automated Regression and Quality Evaluation with Ragas, 3. PyTorch Deterministic Classifier Floor, Monitoring, Evaluation, and Learning Loop

### Community 91 - "Roadmap and Reference Baselines"
Cohesion: 0.40
Nodes (4): Business Value and Efficiency Targets, Evolution Roadmap, Reference Baselines, Roadmap and Reference Baselines

### Community 92 - "run_feedback_eval.py"
Cohesion: 0.29
Nodes (10): _load_seed(), main(), Feedback, Path, Feedback eval — does the learning loop actually show the prompt improving?  Repl, One golden feedback record plus the prompt version it was recorded     against —, Real operator feedback wins over the seed's canned verdict for the     same trac, _replay() (+2 more)

### Community 93 - "test_feedback_eval.py"
Cohesion: 0.27
Nodes (9): feedback_eval(), MonkeyPatch, Path, evals/run_feedback_eval.py: replays feedback against the golden seed and gates o, Import evals/run_feedback_eval.py fresh (it's not a package module)., A real operator verdict for a seeded trace_id replaces the canned one., test_eval_fails_below_threshold(), test_eval_fails_loudly_on_missing_seed() (+1 more)

### Community 94 - "test_confidence_bounds.py"
Cohesion: 0.31
Nodes (8): make_alert(), make_evidence(), Alert, Evidence, Contract-level enforcement of the confidence < 1.0 invariant.  Every producer al, test_evidence_rejects_certainty(), test_incident_story_rejects_certainty(), test_prediction_rejects_certainty()

### Community 95 - ".actions_allowed"
Cohesion: 0.21
Nodes (11): judge(), main(), BaseModel, LLM-judge layer over the story eval cases (RAGAS-style faithfulness).  For each, Verdict, _load_jsonl(), Path, Story-pipeline eval: run every eval case through build_story and score it.  Scor (+3 more)

### Community 96 - "ui.tsx"
Cohesion: 0.23
Nodes (10): Evidence, EvidencePanel(), ReasoningPanel(), ConfidenceMeter(), EmptyState(), Panel(), SectionLabel(), SeverityBadge() (+2 more)

### Community 97 - "n8n endpoint coverage — mesh contract map"
Cohesion: 0.25
Nodes (7): agent (:8004 · `PP_AGENT_BASE`), guardrails (:8003 · `PP_GUARDRAILS_BASE`), n8n endpoint coverage — mesh contract map, ppos (:8005 · `PP_PPOS_BASE`), predictor (:8001 · `PP_PREDICTOR_BASE`), rag (:8002 · `PP_RAG_BASE`), Repo-level assertions (`tests/test_n8n_contracts.py`)

### Community 98 - "TokenUsage.tsx"
Cohesion: 0.09
Nodes (38): _datasources(), _deploy_annotations(), export_grafana_preview(), _grid_ok(), _panel_json(), DashboardSpec, GrafanaDashboardPreview, IncidentStory (+30 more)

### Community 99 - "ServiceDetailPanel.tsx"
Cohesion: 0.32
Nodes (6): Severity, IncidentSummary, ServiceDetailPanel(), SERVICE_DETAILS, DEMO_ALERTS, DemoAlertRef

### Community 100 - "test_memory_feed.py"
Cohesion: 0.16
Nodes (21): FieldInfo, _has_bound(), BaseModel, StrEnum, _python_enums(), _python_models(), Python↔TypeScript contract parity — schemas.py is the source of truth.  packages, A field bounded lt=1.0 must not be documented `<= 1.0` in the mirror —     the d (+13 more)

### Community 101 - "guardrails_config/"
Cohesion: 0.33
Nodes (5): Deterministic vs LLM-backed rails, Editing these files, Floor-always-wins semantics, guardrails_config/, Layout

### Community 102 - "test_config_secrets.py"
Cohesion: 0.53
Nodes (5): _clear_key_env(), MonkeyPatch, Credentials in Settings are SecretStr — masked everywhere they can leak.  repr/s, test_keys_are_masked_in_repr_str_and_dump(), test_no_key_state_resolves_to_none()

### Community 103 - "Deployment"
Cohesion: 0.50
Nodes (4): Deployment, DeploymentRow, FIXTURE_DEPLOYMENTS, ServiceDetail

### Community 104 - "os.ts"
Cohesion: 0.10
Nodes (34): _anthropic_complete(), _bedrock_complete(), _LlmEvidenceDraft, _LlmStoryDraft, LlmSynthesisError, load_system_prompt(), BaseModel, Exception (+26 more)

### Community 105 - "usage.py"
Cohesion: 0.23
Nodes (14): tips_route(), usage_route(), aggregate(), _is_valid_row(), load_usage(), Token/cost usage logging — the data source for PETER PAN OS.  Every LLM call in, Events from the last N hours (None = everything)., Cost and token totals grouped by agent/model/service — the OS headline table. (+6 more)

### Community 106 - "build_story"
Cohesion: 0.16
Nodes (14): BaseHTTPMiddleware, FastAPI, Response, ApiTokenMiddleware, install_api_auth(), Request, Application-level API authentication for the EC2 mesh.  Opt-in via ``PP_API_TOKE, Reject unauthenticated mutating/read API calls when a token is configured. (+6 more)

### Community 107 - "test_langgraph_and_evals.py"
Cohesion: 0.18
Nodes (16): ActionPreview, ActionRisk, approve(), propose_action(), Every mutating action goes through here. In production, HIGH risk always     req, make_alert(), Alert, Agent: story building and the ActionPreview approval gate. (+8 more)

### Community 108 - "search"
Cohesion: 0.19
Nodes (13): RagResult, query_route(), search(), RAG: retrieval with mandatory citation trail., test_body_only_term_retrieves_its_doc(), test_empty_query_rejected(), test_endpoint_rejects_empty_query_with_422(), test_every_match_carries_a_source() (+5 more)

### Community 109 - "test_edge_cases.py"
Cohesion: 0.26
Nodes (14): _awslogs_opts(), _docker_push(), _git_sha(), _load_env_keys(), main(), _put_secret(), CompletedProcess, Build, push ECR image, and roll EC2 containers via SSM — values never printed. (+6 more)

### Community 110 - "meshFetch"
Cohesion: 0.31
Nodes (7): GET(), SERVICES, Ctx, GET(), POST(), meshBase(), meshFetch()

### Community 111 - "test_production_gate.py"
Cohesion: 0.20
Nodes (11): Env, GuardrailsBackend, LlmProvider, PredictorBackend, StrEnum, RagBackend, Environment-based configuration.  The three-environment model is a core product, Grafana dashboard JSON exporter — deterministic, catalog-bound, preview-only.  T (+3 more)

### Community 112 - "knowledge.py"
Cohesion: 0.22
Nodes (12): alert_body(), Edge-case sweep across every service surface — pre-deploy hardening.  Alert text, test_dashboard_survives_blank_title_and_description(), test_ppos_endpoints_reject_garbage_params(), test_predict_endpoint_rejects_bad_severity_and_missing_fields(), test_query_rejects_empty_and_nonpositive_top_k(), test_query_unicode_and_regex_metachars(), test_query_with_absurd_top_k_returns_at_most_corpus() (+4 more)

### Community 113 - "test_retrieval_eval.py"
Cohesion: 0.22
Nodes (9): MonkeyPatch, Path, evals/run_retrieval_eval.py: the 0.900 hit-rate gate, actually executed.  Its do, Import evals/run_retrieval_eval.py fresh (it's not a package module)., Lexical backend, zero keys — the committed golden set must clear the     0.900 h, Non-zero exit is load-bearing: a renamed/deleted knowledge doc (or a     broken, retrieval_eval(), test_eval_fails_when_expected_doc_is_unretrievable() (+1 more)

### Community 114 - "ApiTokenMiddleware"
Cohesion: 0.33
Nodes (12): apply_floor_guardrails(), MlPrediction, Prediction, Raw model output — NOT a Prediction until the floor guardrails ran., Merge model output into the floor's verdict. The floor always wins:      - class, Prediction, ML predictor: the model refines, the deterministic floor always wins.  Guard log, test_low_confidence_model_output_is_discarded() (+4 more)

### Community 115 - "App.tsx"
Cohesion: 0.47
Nodes (3): App(), StoryPanel(), useAgentStream()

### Community 116 - "test_ui_smoke.py"
Cohesion: 0.47
Nodes (5): AppTest, Streamlit UI smoke — runs the real app headless via streamlit's AppTest.  Requir, _run_app(), test_app_boots_without_exceptions(), test_draw_tab_exposes_grafana_preview_and_download()

### Community 117 - "ADR-0002: Canonical retrieval backend"
Cohesion: 0.40
Nodes (4): ADR-0002: Canonical retrieval backend, Consequences, Context, Decision

### Community 118 - "eslint.config.mjs"
Cohesion: 0.40
Nodes (4): compat, __dirname, eslintConfig, __filename

### Community 119 - "page.tsx"
Cohesion: 0.36
Nodes (9): Deterministic stratified split. Classes with <5 examples stay train-only     (a, split_rows(), load_rows(), Honest predictor evaluation: stratified holdout, no train/test overlap.  The shi, test_holdout_accuracy_is_honest_and_passes_floor(), test_split_is_deterministic(), test_split_is_disjoint_and_complete(), test_split_is_stratified_every_class_in_both_halves() (+1 more)

### Community 120 - "layout.tsx"
Cohesion: 0.40
Nodes (3): metadata, mono, sans

### Community 127 - "format.ts"
Cohesion: 0.29
Nodes (10): _alert(), MonkeyPatch, Provider truthfulness — never mislabel fallback as live cloud/LLM., test_build_story_llm_failure_sets_deterministic_fallback(), test_lexical_rag_reports_backend_not_fallback(), test_pinecone_failure_labels_fallback_not_pinecone(), test_predict_full_torch_fallback_mode(), test_predictor_floor_mode_and_healthz() (+2 more)

### Community 128 - "HealthStrip.tsx"
Cohesion: 0.48
Nodes (6): _current_params(), _egress_cidr(), main(), CompletedProcess, Preview (and optionally execute) a CFN sync for the demo stack.  Aligns live sta, _run()

### Community 133 - "test_langgraph_and_evals.py"
Cohesion: 0.38
Nodes (5): make_alert(), Alert, LangGraph story graph equivalence + eval harness health., test_langgraph_story_keeps_invariants(), test_langgraph_story_matches_deterministic_pipeline()

### Community 134 - "predict_full"
Cohesion: 0.18
Nodes (16): _artifact_status(), healthz(), predict_full(), predict_route(), Alert, Prediction, Predictor service — classifies inbound alerts and assigns severity.  A determini, Floor verdict, optionally refined by the local model under its guardrails. (+8 more)

### Community 136 - "P6 blocker remediation plan"
Cohesion: 0.40
Nodes (4): Changes, Non-goals, P6 blocker remediation plan, Scope

## Knowledge Gaps
- **371 isolated node(s):** `$schema`, `Read`, `Glob`, `Grep`, `Bash(git status)` (+366 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **37 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `test_observability.py` to `Knowledge Base Ingestion`, `LLM Story Synthesis`, `Environment Configuration`, `Input/Output Guardrails`, `predict_full`, `Story Graph Orchestration`, `Operations Console`, `Action Approval Gate`, `BaseModel`, `StrEnum`, `IncidentStory`, `tips`, `cache.py`, `build_story`, `test_nemo_rails.py`, `observability.py`, `.actions_allowed`, `TokenUsage.tsx`, `test_config_secrets.py`, `os.ts`, `build_story`, `test_production_gate.py`, `format.ts`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Why does `MemoryRecord` connect `Knowledge Base Ingestion` to `test_observability.py`, `BaseModel`, `test_production_gate.py`, `RAG Retrieval Service`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Why does `test_sse_synthesize_step_does_not_claim_claude_on_fallback()` connect `format.ts` to `test_observability.py`, `Predictor Training`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Are the 99 inferred relationships involving `Settings` (e.g. with `Verdict` and `check_topical_llm_action()`) actually correct?**
  _`Settings` has 99 INFERRED edges - model-reasoned connections that need verification._
- **Are the 33 inferred relationships involving `TestClient` (e.g. with `test_story_endpoint()` and `test_auth_accepts_matching_token()`) actually correct?**
  _`TestClient` has 33 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `build_story()` (e.g. with `main()` and `run()`) actually correct?**
  _`build_story()` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `synthesize()` (e.g. with `cache_get()` and `cache_key()`) actually correct?**
  _`synthesize()` has 20 INFERRED edges - model-reasoned connections that need verification._