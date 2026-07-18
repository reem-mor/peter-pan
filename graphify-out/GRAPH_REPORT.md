# Graph Report - .  (2026-07-18)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 521 nodes · 999 edges · 36 communities (16 shown, 20 thin omitted)
- Extraction: 75% EXTRACTED · 25% INFERRED · 0% AMBIGUOUS · INFERRED: 250 edges (avg confidence: 0.74)
- Token cost: 1,848 input · 413 output

## Graph Freshness
- Built from commit: `8bba5479`
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

## God Nodes (most connected - your core abstractions)
1. `Alert` - 29 edges
2. `Settings` - 27 edges
3. `build_story()` - 20 edges
4. `Prediction` - 19 edges
5. `predict()` - 18 edges
6. `Evidence` - 17 edges
7. `IncidentStory` - 16 edges
8. `LlmSynthesisError` - 15 edges
9. `synthesize()` - 14 edges
10. `MemoryRecord` - 14 edges

## Surprising Connections (you probably didn't know these)
- `guardrails — Safety Service` --references--> `guardrails/v1.md — Safety Prompts`  [INFERRED]
  services/guardrails.py → prompts/guardrails/v1.md
- `rag — Retrieval Service` --references--> `rag-injection/v1.md — RAG Injection Prompt`  [INFERRED]
  services/rag.py → prompts/rag-injection/v1.md
- `agent — LangGraph Agent` --references--> `incident-agent/system-v6.txt — Agent Prompt v6`  [INFERRED]
  services/agent.py → prompts/incident-agent/system-v6.txt
- `ppos — PETER PAN OS Control Plane` --references--> `os_dashboard.html — Control Plane UI`  [INFERRED]
  services/ppos.py → ui/os_dashboard.html
- `Verdict` --uses--> `Severity`  [INFERRED]
  evals/run_llm_judge.py → src/peterpan/schemas.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Service Mesh Architecture** — services_predictor_service, services_rag_service, services_guardrails_service, services_agent_service, services_ppos_service [EXTRACTED 1.00]
- **Self-Improving Skills Loop Implementation** — claude_skills_learn_skill, claude_skills_reflect_skill, claude_skills_evolve_skill, claude_learnings_learnings_md [EXTRACTED 1.00]
- **Product Safety Enforcement** — product_invariants, action_preview_gate, services_guardrails_service, claude_agents_architecture_guardian_skill [INFERRED 0.90]
- **Prompt Engineering Lifecycle** — prompt_incident_agent_system_v1_txt, prompt_incident_agent_system_v2_txt, prompt_incident_agent_system_v4_txt, prompt_incident_agent_system_v5_txt, prompt_incident_agent_system_v6_txt, prompt_incident_agent_log_md [EXTRACTED 1.00]

## Communities (36 total, 20 thin omitted)

### Community 0 - "Budget Tracking"
Cohesion: 0.06
Nodes (63): budget_route(), Last-24h spend vs the PP_DAILY_BUDGET_USD budget. Report-only guard., tips_route(), usage_route(), aggregate(), budget_status(), _is_valid_row(), load_usage() (+55 more)

### Community 1 - "LLM Story Evaluation"
Cohesion: 0.07
Nodes (46): BaseSettings, judge(), main(), BaseModel, LLM-judge layer over the story eval cases (RAGAS-style faithfulness).  For each, Verdict, _load_jsonl(), Path (+38 more)

### Community 2 - "Knowledge Base Ingestion"
Cohesion: 0.07
Nodes (43): main(), Ingest knowledge/ into the Pinecone index (idempotent — upsert by source).  Usag, _kind_for(), load_corpus(), load_full_text(), Path, Knowledge base loader — the files under knowledge/ ARE the corpus.  Both retriev, Classify by ancestor dir, not just the immediate parent — so incidents     fed u (+35 more)

### Community 3 - "Predictor Training"
Cohesion: 0.10
Nodes (40): Linear, main(), Train the local predictor classifier and report accuracy.  Usage:  python script, apply_floor_guardrails(), evaluate_holdout(), _fit(), _load_rows(), MlPredictError (+32 more)

### Community 4 - "LLM Story Synthesis"
Cohesion: 0.10
Nodes (38): _LlmStoryDraft, LlmSynthesisError, load_system_prompt(), BaseModel, Exception, Claude-backed story synthesis — opt-in, invariant-guarded, metered.  The LLM ref, Any LLM-path failure. Callers must catch this and fall back., The exact JSON contract the prompt demands from the model. (+30 more)

### Community 5 - "Environment Configuration"
Cohesion: 0.09
Nodes (30): Env, LlmProvider, PredictorBackend, StrEnum, RagBackend, Environment-based configuration.  The three-environment model is a core product, build_dashboard(), DashboardError (+22 more)

### Community 6 - "Input/Output Guardrails"
Cohesion: 0.09
Nodes (26): GuardrailVerdict, check_input(), check_input_route(), check_output(), check_output_route(), BaseModel, Guardrails service — deterministic floors with final say over any LLM.  Input ra, TextIn (+18 more)

### Community 7 - "RAG Retrieval Service"
Cohesion: 0.10
Nodes (25): _lexical_confidence(), _load_corpus_and_text(), memory_route(), _overlap(), BaseModel, Path, query_route(), QueryIn (+17 more)

### Community 8 - "Tool Permissions"
Cohesion: 0.07
Nodes (28): hooks, PreToolUse, permissions, allow, deny, $schema, Bash(aws * delete*), Bash(aws * terminate*) (+20 more)

### Community 9 - "System Documentation"
Cohesion: 0.13
Nodes (25): contract-reviewer — Schema Validator, peter-pan-design — Design System, docker-compose.yml — Service Mesh, ARCHITECTURE.md — System Design, CONTRACTS.md — Frozen Interfaces, stack.yaml — AWS CloudFormation, alert-extraction/v1.md — Extraction Prompt, assistant/v1.md — Conversational Prompt (+17 more)

### Community 10 - "Story Graph Orchestration"
Cohesion: 0.18
Nodes (15): build_graph(), classify_node(), The story-builder as a LangGraph graph: classify → retrieve → synthesize.  Same, Deterministic floor — always first; its severity may only be argued up., Fixture synthesiser. A real LLM (prompts/incident-agent/v1.md) replaces     this, Run the compiled graph end-to-end. Bounded by construction: the graph     is a D, retrieve_node(), run_story_graph() (+7 more)

### Community 11 - "Learning & Governance"
Cohesion: 0.12
Nodes (17): Action Preview Gate, architecture-guardian — Invariant Reviewer, security-reviewer — Safety Gate, test-engineer — Coverage Guardian, LEARNINGS.md — Captured Lessons, CLAUDE.md — Working Memory, evolve — Level 4 Skill Amendment, learn — Level 2 Lesson Capture (+9 more)

### Community 12 - "Operations Console"
Cohesion: 0.12
Nodes (15): HTMLResponse, JSONResponse, agents_route(), dashboard_route(), info_route(), _probe(), PETER PAN OS — the operations console for the AI system itself.  Monitors what t, Server-side health sweep of the mesh (browsers can't cross-origin poll it). (+7 more)

### Community 13 - "Action Approval Gate"
Cohesion: 0.18
Nodes (14): ActionPreview, A proposed action. HIGH-risk actions are never auto-executed —     they require, approve(), propose_action(), Every mutating action goes through here. In production, HIGH risk always     req, make_alert(), Agent: story building and the ActionPreview approval gate., test_anonymous_approval_rejected() (+6 more)

### Community 14 - "Secrets Deployment"
Cohesion: 0.67
Nodes (3): main(), Push the deploy keys from .env into AWS Secrets Manager — values never printed., read_env_values()

### Community 15 - "Memory Leak Incident"
Cohesion: 0.67
Nodes (3): INC-2263 — Memory Leak, checkout-oom.md — Runbook, memory-leak-hunt.md — Runbook

## Knowledge Gaps
- **72 isolated node(s):** `$schema`, `Read`, `Glob`, `Grep`, `Bash(git status)` (+67 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Alert` connect `LLM Story Evaluation` to `Predictor Training`, `LLM Story Synthesis`, `Environment Configuration`, `Story Graph Orchestration`, `Action Approval Gate`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `Settings` connect `LLM Story Evaluation` to `Knowledge Base Ingestion`, `LLM Story Synthesis`, `Environment Configuration`, `RAG Retrieval Service`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `synthesize()` connect `LLM Story Synthesis` to `Budget Tracking`, `LLM Story Evaluation`, `Predictor Training`, `Environment Configuration`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `Alert` (e.g. with `main()` and `Verdict`) actually correct?**
  _`Alert` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `Settings` (e.g. with `Verdict` and `main()`) actually correct?**
  _`Settings` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `build_story()` (e.g. with `main()` and `run()`) actually correct?**
  _`build_story()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `Prediction` (e.g. with `StoryState` and `_LlmStoryDraft`) actually correct?**
  _`Prediction` has 10 INFERRED edges - model-reasoned connections that need verification._