"""'Draw me the problem' — LLM-designed dashboards as a typed, validated spec.

Same discipline as peterpan.llm: versioned prompt, pydantic-validated output,
evidence-source allowlist, metered usage, and a deterministic fallback spec
so the feature works with zero LLM (fixture-first).
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from peterpan.config import LlmProvider, Settings
from peterpan.schemas import DashboardSpec, IncidentStory, Panel, PanelKind
from peterpan.usage import log_usage, make_event, model_rates

_PROMPT_PATH = (
    Path(__file__).parent.parent.parent / "prompts" / "dashboard-builder" / "system-v1.txt"
)


class DashboardError(Exception):
    """Any LLM dashboard failure. Callers fall back to the deterministic spec."""


def deterministic_spec(problem: str, story: IncidentStory) -> DashboardSpec:
    """The fallback dashboard: story-first, evidence-cited, always available."""
    nodes = "\n".join(
        f'  E{i}["{e.kind}: {e.summary[:38]}"] --> Cause' for i, e in enumerate(story.evidence)
    )
    return DashboardSpec(
        title=f"Incident: {story.alert.title}",
        problem=problem,
        generated_by="deterministic-fallback",
        panels=[
            Panel(
                kind=PanelKind.STAT,
                title="Probable cause",
                content=f"{story.probable_cause} (confidence {story.confidence:.0%})",
                source="predictor:/predict",
            ),
            Panel(
                kind=PanelKind.TABLE,
                title="Evidence (cited)",
                content="",
                rows=[
                    {
                        "kind": e.kind,
                        "summary": e.summary,
                        "source": e.source,
                        "confidence": f"{e.confidence:.2f}",
                    }
                    for e in story.evidence
                ],
            ),
            Panel(
                kind=PanelKind.MERMAID,
                title="Story graph",
                content=(
                    f"graph TD\n{nodes}\n  Cause[{story.probable_cause}] --> Fix[repair options]"
                ),
            ),
            Panel(
                kind=PanelKind.MARKDOWN,
                title="Repair options (previews — human approval required)",
                content="\n".join(f"- {opt}" for opt in story.repair_options),
            ),
        ],
    )


def build_dashboard(problem: str, story: IncidentStory, settings: Settings) -> DashboardSpec:
    """LLM-designed spec when opted in; deterministic fallback otherwise/on failure."""
    if settings.llm is not LlmProvider.ANTHROPIC or not settings.anthropic_api_key:
        return deterministic_spec(problem, story)
    try:
        return _llm_spec(problem, story, settings)
    except DashboardError:
        return deterministic_spec(problem, story)


def _llm_spec(problem: str, story: IncidentStory, settings: Settings) -> DashboardSpec:
    try:
        import anthropic  # lazy: optional `llm` extra
    except ImportError as exc:
        raise DashboardError("anthropic SDK not installed") from exc

    allowed = {e.source for e in story.evidence}
    payload = json.dumps(
        {
            "problem": problem,
            "story": story.model_dump(exclude={"alert"}, mode="json"),
            "alert": {"title": story.alert.title, "severity": story.alert.severity},
        },
        default=str,
    )
    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=2000,
            system=_PROMPT_PATH.read_text(encoding="utf-8"),
            messages=[{"role": "user", "content": payload}],
        )
    except Exception as exc:
        raise DashboardError(f"anthropic API failure: {type(exc).__name__}") from exc

    in_rate, out_rate = model_rates(settings.anthropic_model)
    log_usage(
        make_event(
            service="agent",
            agent="dashboard-builder",
            model=settings.anthropic_model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cost_usd=round(
                response.usage.input_tokens * in_rate + response.usage.output_tokens * out_rate, 6
            ),
        ),
        settings.usage_log_path,
    )

    raw = "".join(b.text for b in response.content if b.type == "text").strip()
    if raw.startswith("```"):
        raw = raw.strip("`").removeprefix("json").strip()
    try:
        spec = DashboardSpec.model_validate_json(raw)
    except ValidationError as exc:
        raise DashboardError(f"spec failed validation: {exc.error_count()} errors") from exc

    fabricated = [p.source for p in spec.panels if p.source and p.source not in allowed]
    if fabricated:
        raise DashboardError(f"fabricated panel sources rejected: {fabricated}")
    if not 3 <= len(spec.panels) <= 6:
        raise DashboardError(f"panel count {len(spec.panels)} outside 3-6")
    return spec
