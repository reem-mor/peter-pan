"""The story-builder as a LangGraph graph: classify → retrieve → synthesize.

Same contract as `services.agent.build_story` (and tested equivalent), but
orchestrated by LangGraph so LLM-driven nodes can replace deterministic ones
without changing the graph shape. The planner/synthesiser prompts that slot
in here live in prompts/incident-agent/.
"""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from peterpan.config import Settings
from peterpan.schemas import (
    Alert,
    Evidence,
    IncidentStory,
    Prediction,
    ProviderReport,
    RagResult,
)
from peterpan.services.agent import _repair_options, search_query
from peterpan.services.predictor import predict_full
from peterpan.services.rag import search


class StoryState(TypedDict, total=False):
    alert: Alert
    prediction: Prediction
    rag: RagResult
    story: IncidentStory


def classify_node(state: StoryState) -> StoryState:
    """Floor (+ optional torch) — always first; severity may only be argued up."""
    return {"prediction": predict_full(state["alert"], Settings())}


def retrieve_node(state: StoryState) -> StoryState:
    alert = state["alert"]
    return {"rag": search(search_query(alert), top_k=3)}


def synthesize_node(state: StoryState) -> StoryState:
    """Fixture synthesiser. A real LLM (prompts/incident-agent/v1.md) replaces
    this body; the citation and confidence invariants stay enforced either way."""
    alert, prediction, rag = state["alert"], state["prediction"], state["rag"]
    configured = Settings()
    evidence: list[Evidence] = [
        Evidence(
            kind="metric",
            summary=f"classified as {prediction.incident_class} at {prediction.severity}",
            source="predictor:/predict",
            confidence=prediction.confidence,
        ),
        *[m for m in rag.matches if m.confidence > 0],
    ]
    story = IncidentStory(
        alert=alert,
        what_changed=f"Signal '{alert.title}' from {alert.source}",
        probable_cause=prediction.incident_class,
        confidence=min(prediction.confidence, 0.9),
        evidence=evidence,
        repair_options=_repair_options(prediction.incident_class),
        providers=ProviderReport(
            llm="off",
            configured_llm=configured.llm.value,
            llm_fallback=False,
            rag_backend=rag.backend,
            rag_fallback=rag.fallback,
            rag_fallback_reason=rag.fallback_reason,
            predictor=prediction.mode,
            predictor_model_version=prediction.model_version,
            agent_provider="local",
        ),
    )
    return {"story": story}


def build_graph() -> object:
    graph: StateGraph[StoryState] = StateGraph(StoryState)
    graph.add_node("classify", classify_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("synthesize", synthesize_node)
    graph.add_edge(START, "classify")
    graph.add_edge("classify", "retrieve")
    graph.add_edge("retrieve", "synthesize")
    graph.add_edge("synthesize", END)
    return graph.compile()


def run_story_graph(alert: Alert) -> IncidentStory:
    """Run the compiled graph end-to-end. Bounded by construction: the graph
    is a DAG with three nodes — no cycles, no unbounded loops."""
    compiled = build_graph()
    result = compiled.invoke({"alert": alert})  # type: ignore[attr-defined]
    story = result["story"]
    if not isinstance(story, IncidentStory):
        raise RuntimeError("graph invariant violated: synthesize node produced no story")
    return story
