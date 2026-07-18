"""Contract test for the SSE incident-story stream (CONTRACTS.md §5).

GET /agent/stream?alert_id=... must emit, in order: one or more `step`
events, one or more `evidence` events, exactly one `story` event, then
`done`. Every payload must be valid JSON; `story` must validate against
IncidentStory. Fixture-first: no live LLM, no network.
"""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from peterpan.schemas import IncidentStory
from peterpan.services.agent import DEMO_ALERTS, app

client = TestClient(app)


def _parse_sse(raw_text: str) -> list[tuple[str, str]]:
    """Parse `event:`/`data:` frames (separated by a blank line) into
    (event, data) pairs, in stream order."""
    events: list[tuple[str, str]] = []
    event_name: str | None = None
    data_lines: list[str] = []
    for line in raw_text.splitlines():
        if line.startswith("event:"):
            event_name = line.removeprefix("event:").strip()
        elif line.startswith("data:"):
            data_lines.append(line.removeprefix("data:").strip())
        elif line == "" and event_name is not None:
            events.append((event_name, "".join(data_lines)))
            event_name, data_lines = None, []
    if event_name is not None:  # tolerate a stream with no trailing blank line
        events.append((event_name, "".join(data_lines)))
    return events


def test_stream_event_order_and_payloads() -> None:
    with client.stream("GET", "/agent/stream", params={"alert_id": "demo-oom"}) as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        events = _parse_sse(resp.read().decode("utf-8"))

    kinds = [name for name, _ in events]

    # step+ -> evidence+ -> story -> done
    assert kinds[0] == "step"
    first_evidence = kinds.index("evidence")
    assert all(k == "step" for k in kinds[:first_evidence])
    first_story = kinds.index("story")
    assert all(k == "evidence" for k in kinds[first_evidence:first_story])
    assert kinds[first_story] == "story"
    assert kinds[first_story + 1] == "done"
    assert kinds[first_story + 1 :] == ["done"]  # story and done are each singular

    # every payload is valid JSON
    payloads = [json.loads(data) for _, data in events]

    # step payloads carry the CONTRACTS.md §5 {"name", "detail", "ts"} shape
    for name, data in events[:first_evidence]:
        assert name == "step"
        payload = json.loads(data)
        assert set(payload) == {"name", "detail", "ts"}
        assert payload["name"] and payload["detail"] and payload["ts"]

    # evidence payloads keep the citation trail (source never empty)
    for name, data in events[first_evidence:first_story]:
        assert name == "evidence"
        payload = json.loads(data)
        assert payload["source"]
        assert 0.0 <= payload["confidence"] < 1.0

    # story payload matches IncidentStory and never claims certainty
    story = IncidentStory.model_validate(payloads[first_story])
    assert story.confidence < 1.0
    assert story.evidence
    assert all(e.source for e in story.evidence)

    # done is a valid terminal marker
    assert json.loads(events[-1][1])


def test_stream_unknown_alert_id_returns_404_envelope() -> None:
    resp = client.get("/agent/stream", params={"alert_id": "does-not-exist"})
    assert resp.status_code == 404
    body = resp.json()
    assert "error" in body and body["error"]


def test_demo_alert_catalog_is_non_empty() -> None:
    assert DEMO_ALERTS
