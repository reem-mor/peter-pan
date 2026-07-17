"""PETER PAN WebUI — Dynamic Incident Dashboard + PETER PAN OS console.

Run:  streamlit run ui/app.py
Talks to the services in-process for the MVP (same package); switches to HTTP
calls against the deployed services by setting PP_*_URL env vars later.
"""

from __future__ import annotations

from datetime import UTC, datetime

import streamlit as st

from peterpan.config import Settings
from peterpan.schemas import ActionRisk, Alert, Severity
from peterpan.services.agent import build_story, propose_action
from peterpan.services.guardrails import check_input
from peterpan.usage import aggregate, load_usage, tips

settings = Settings()

st.set_page_config(page_title="PETER PAN", layout="wide")
st.title("PETER PAN — Predictive, Agentic Navigator")
st.caption(f"env: **{settings.env.value}** · actions auto-execute: {settings.actions_allowed}")

tab_incident, tab_draw, tab_os = st.tabs(
    ["Incident Dashboard", "Draw me the problem", "PETER PAN OS"]
)

with tab_incident:
    st.subheader("Submit a signal")
    title = st.text_input("Alert title", "checkout OOMKilled")
    description = st.text_area("Description", "pod restarted twice, memory at limit")
    severity = st.selectbox("Severity", [s.value for s in Severity], index=1)
    if st.button("Build incident story"):
        verdict = check_input(f"{title} {description}")
        if not verdict.passed:
            st.error(f"Input guardrail rejected this signal: {verdict.reason}")
        else:
            alert = Alert(
                id="ui-1",
                source="webui",
                title=title,
                description=description,
                severity=Severity(severity),
                received_at=datetime.now(UTC),
            )
            story = build_story(alert)
            st.metric("Probable cause", story.probable_cause, f"confidence {story.confidence:.0%}")
            st.write(f"**What changed:** {story.what_changed}")
            st.write("**Evidence** (every row cites its source):")
            st.table(
                [
                    {"kind": e.kind, "summary": e.summary, "source": e.source, "conf": e.confidence}
                    for e in story.evidence
                ]
            )
            st.write("**Repair options** — HIGH-risk actions require human approval:")
            for option in story.repair_options:
                preview = propose_action(option, ActionRisk.HIGH)
                st.warning(f"{option} — requires approval: {preview.requires_approval}")

with tab_draw:
    st.subheader("Draw me the problem")
    st.caption("Describe the problem; PETER PAN sketches the story as a diagram.")
    problem = st.text_input("Problem", "payments latency spiked after the 14:00 deploy")
    if st.button("Draw"):
        # MVP: mermaid sketch from the story pipeline. The dynamic-dashboard
        # generator (LLM-designed panels) replaces this.
        alert = Alert(id="draw-1", source="webui", title=problem, received_at=datetime.now(UTC))
        story = build_story(alert)
        nodes = "\n".join(
            f'  E{i}["{e.kind}: {e.summary[:40]}..."] --> Cause'
            for i, e in enumerate(story.evidence)
        )
        st.code(
            f"graph TD\n{nodes}\n  Cause[{story.probable_cause}] --> Fix[repair options]",
            language="mermaid",
        )

with tab_os:
    st.subheader("PETER PAN OS — agent & token monitor")
    events = load_usage(settings.usage_log_path)
    agg = aggregate(events)
    if agg:
        st.table(
            [
                {"agent": agent, **{k: round(v, 4) for k, v in row.items()}}
                for agent, row in agg.items()
            ]
        )
    else:
        st.info("No usage logged yet — every LLM call should go through peterpan.usage.log_usage.")
    st.write("**Tips**")
    for tip in tips(events):
        st.write(f"- {tip}")
