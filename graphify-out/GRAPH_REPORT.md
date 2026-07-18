# Graph Report - peter-pan  (2026-07-18)

## Corpus Check
- 91 files · ~42,360 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 517 nodes · 972 edges · 43 communities (17 shown, 26 thin omitted)
- Extraction: 75% EXTRACTED · 25% INFERRED · 0% AMBIGUOUS · INFERRED: 242 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7918c7be`
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
- `main()` --calls--> `Severity`  [INFERRED]
  evals/run_llm_judge.py → src/peterpan/schemas.py
- `Verdict` --uses--> `Severity`  [INFERRED]
  evals/run_llm_judge.py → src/peterpan/schemas.py
- `run()` --calls--> `Severity`  [INFERRED]
  evals/run_story_eval.py → src/peterpan/schemas.py
- `main()` --calls--> `Alert`  [INFERRED]
  evals/run_llm_judge.py → src/peterpan/schemas.py
- `Verdict` --uses--> `Alert`  [INFERRED]
  evals/run_llm_judge.py → src/peterpan/schemas.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Self-Improving Skills Loop Implementation** — claude_skills_learn_skill, claude_skills_reflect_skill, claude_skills_evolve_skill, claude_learnings_learnings_md [EXTRACTED 1.00]
- **Prompt Engineering Lifecycle** — prompt_incident_agent_system_v1_txt, prompt_incident_agent_system_v2_txt, prompt_incident_agent_system_v4_txt, prompt_incident_agent_system_v5_txt, prompt_incident_agent_system_v6_txt, prompt_incident_agent_log_md [EXTRACTED 1.00]

## Communities (43 total, 26 thin omitted)

### Community 0 - "Budget Tracking"
Cohesion: 0.05
Nodes (68): _llm_spec(), Draw me the problem' — LLM-designed dashboards as a typed, validated spec.  Same, budget_route(), Last-24h spend vs the PP_DAILY_BUDGET_USD budget. Report-only guard., tips_route(), usage_route(), aggregate(), budget_status() (+60 more)

### Community 1 - "LLM Story Evaluation"
Cohesion: 0.06
Nodes (45): _load_jsonl(), Path, Story-pipeline eval: run every eval case through build_story and score it.  Scor, run(), ActionPreview, Alert, Inbound signal from monitoring (Grafana webhook, pager, etc.)., A proposed action. HIGH-risk actions are never auto-executed —     they require (+37 more)

### Community 2 - "Knowledge Base Ingestion"
Cohesion: 0.07
Nodes (43): main(), Ingest knowledge/ into the Pinecone index (idempotent — upsert by source).  Usag, _kind_for(), load_corpus(), load_full_text(), Path, Knowledge base loader — the files under knowledge/ ARE the corpus.  Both retriev, Classify by ancestor dir, not just the immediate parent — so incidents     fed u (+35 more)

### Community 3 - "Predictor Training"
Cohesion: 0.12
Nodes (30): Linear, main(), Train the local predictor classifier and report accuracy.  Usage:  python script, evaluate_holdout(), _fit(), _load_rows(), MlPredictError, model_predict() (+22 more)

### Community 4 - "LLM Story Synthesis"
Cohesion: 0.08
Nodes (45): BaseModel, DashboardError, Exception, Any LLM dashboard failure. Callers fall back to the deterministic spec., _LlmStoryDraft, LlmSynthesisError, load_system_prompt(), BaseModel (+37 more)

### Community 5 - "Environment Configuration"
Cohesion: 0.10
Nodes (24): BaseSettings, judge(), main(), BaseModel, LLM-judge layer over the story eval cases (RAGAS-style faithfulness).  For each, Verdict, Env, LlmProvider (+16 more)

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
Cohesion: 0.29
Nodes (7): incident-agent/LOG.md — Prompt Engineering Log, incident-agent/system-v1.txt — Agent Prompt v1, incident-agent/system-v2.txt — Agent Prompt v2, incident-agent/system-v4.txt — Agent Prompt v4, incident-agent/system-v5.txt — Agent Prompt v5, incident-agent/system-v6.txt — Agent Prompt v6, versions.yaml — Prompt Versions

### Community 10 - "Story Graph Orchestration"
Cohesion: 0.17
Nodes (17): build_graph(), classify_node(), The story-builder as a LangGraph graph: classify → retrieve → synthesize.  Same, Deterministic floor — always first; its severity may only be argued up., Fixture synthesiser. A real LLM (prompts/incident-agent/v1.md) replaces     this, Run the compiled graph end-to-end. Bounded by construction: the graph     is a D, retrieve_node(), run_story_graph() (+9 more)

### Community 11 - "Learning & Governance"
Cohesion: 0.12
Nodes (18): Action Preview Gate, architecture-guardian — Invariant Reviewer, security-reviewer — Safety Gate, test-engineer — Coverage Guardian, LEARNINGS.md — Captured Lessons, CLAUDE.md — Working Memory, evolve — Level 4 Skill Amendment, learn — Level 2 Lesson Capture (+10 more)

### Community 12 - "Operations Console"
Cohesion: 0.12
Nodes (15): HTMLResponse, JSONResponse, agents_route(), dashboard_route(), info_route(), _probe(), PETER PAN OS — the operations console for the AI system itself.  Monitors what t, Server-side health sweep of the mesh (browsers can't cross-origin poll it). (+7 more)

### Community 13 - "Action Approval Gate"
Cohesion: 0.25
Nodes (17): apply_floor_guardrails(), MlPrediction, Raw model output — NOT a Prediction until the floor guardrails ran., Merge model output into the floor's verdict. The floor always wins:      - class, Prediction, make_alert(), MonkeyPatch, ML predictor: the model refines, the deterministic floor always wins.  Guard log (+9 more)

### Community 14 - "Secrets Deployment"
Cohesion: 0.67
Nodes (3): main(), Push the deploy keys from .env into AWS Secrets Manager — values never printed., read_env_values()

### Community 15 - "Memory Leak Incident"
Cohesion: 0.67
Nodes (3): INC-2263 — Memory Leak, checkout-oom.md — Runbook, memory-leak-hunt.md — Runbook

### Community 36 - "prompts/README.md — Prompt Versioning"
Cohesion: 0.33
Nodes (6): alert-extraction/v1.md — Extraction Prompt, assistant/v1.md — Conversational Prompt, guardrails/v1.md — Safety Prompts, incident-agent/v1.md — Agent Surface v1, rag-injection/v1.md — RAG Injection Prompt, prompts/README.md — Prompt Versioning

## Knowledge Gaps
- **78 isolated node(s):** `$schema`, `Read`, `Glob`, `Grep`, `Bash(git status)` (+73 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Alert` connect `LLM Story Evaluation` to `Predictor Training`, `LLM Story Synthesis`, `Environment Configuration`, `Story Graph Orchestration`, `Action Approval Gate`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `Settings` connect `Environment Configuration` to `Budget Tracking`, `LLM Story Evaluation`, `Knowledge Base Ingestion`, `LLM Story Synthesis`, `RAG Retrieval Service`, `Action Approval Gate`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `synthesize()` connect `LLM Story Synthesis` to `Budget Tracking`, `LLM Story Evaluation`, `Environment Configuration`, `Story Graph Orchestration`, `Action Approval Gate`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `Alert` (e.g. with `main()` and `Verdict`) actually correct?**
  _`Alert` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `Settings` (e.g. with `Verdict` and `main()`) actually correct?**
  _`Settings` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `build_story()` (e.g. with `main()` and `run()`) actually correct?**
  _`build_story()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `Prediction` (e.g. with `StoryState` and `_LlmStoryDraft`) actually correct?**
  _`Prediction` has 10 INFERRED edges - model-reasoned connections that need verification._