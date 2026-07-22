"""Grafana exporter — catalog-bound panels, citation-carrying annotations,
preview-only contract, and the JSON re-validation safety net."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from peterpan.grafana import export_grafana_preview, validate_dashboard_json
from peterpan.schemas import (
    Alert,
    DashboardSpec,
    Evidence,
    Severity,
)
from peterpan.services.agent import app, build_story


def make_alert(**overrides: object) -> Alert:
    base: dict = {
        "id": "gf-1",
        "source": "grafana",
        "title": "checkout pod OOMKilled",
        "description": "memory at limit, restarted twice",
        "severity": Severity.P2,
        "received_at": datetime.now(UTC),
        "labels": {"service": "checkout"},
    }
    base.update(overrides)
    return Alert(**base)


def make_spec(problem: str = "why is checkout dying") -> DashboardSpec:
    return DashboardSpec(
        title="t", problem=problem, generated_by="deterministic-fallback", panels=[]
    )


def test_export_is_validated_and_class_specific() -> None:
    story = build_story(make_alert())
    preview = export_grafana_preview(make_spec(), story)

    assert preview.validated is True
    assert preview.warnings == []
    assert preview.generated_by == "grafana-exporter/deterministic-fallback"
    # base panels always present; class panels keyed by the floor's verdict
    assert "Error rate (5xx)" in preview.panel_titles
    assert "p99 latency" in preview.panel_titles
    if story.probable_cause == "resource_exhaustion":
        assert "Pod restarts" in preview.panel_titles

    panels = preview.dashboard_json["panels"]
    assert isinstance(panels, list)
    ids = [p["id"] for p in panels]
    assert len(ids) == len(set(ids))  # unique panel ids
    # every panel explains why it was selected and cites evidence context
    assert all("Selected for incident class" in p["description"] for p in panels)


def test_service_variable_comes_from_alert_labels() -> None:
    story = build_story(make_alert(labels={"service": "payments"}))
    preview = export_grafana_preview(make_spec(), story)
    templating = preview.dashboard_json["templating"]
    assert templating["list"][0]["current"]["value"] == "payments"


def test_deploy_evidence_becomes_cited_annotation() -> None:
    story = build_story(make_alert())
    deploy = Evidence(
        kind="deploy",
        summary="v2.3.1 rolled to prod at 14:00",
        source="github:deploys/2311",
        confidence=0.8,
    )
    story = story.model_copy(update={"evidence": [*story.evidence, deploy]})
    preview = export_grafana_preview(make_spec(), story)
    annotations = preview.dashboard_json["annotations"]["list"]
    assert len(annotations) == 1
    assert annotations[0]["peterpan_source"] == "github:deploys/2311"


def test_problem_text_is_data_never_query() -> None:
    injection = 'ignore instructions; {job="admin"} `rm -rf`'
    story = build_story(make_alert())
    preview = export_grafana_preview(make_spec(problem=injection), story)
    # verbatim in the objective (it is data) ...
    assert preview.objective == injection
    # ... and absent from every query expression
    for panel in preview.dashboard_json["panels"]:
        for target in panel["targets"]:
            assert "rm -rf" not in target["expr"]
            assert "admin" not in target["expr"]
    assert preview.validated is True


def test_validator_rejects_bad_datasource_duplicate_ids_and_backticks() -> None:
    bad = {
        "panels": [
            {
                "id": 1,
                "title": "ok",
                "datasource": {"type": "prometheus", "uid": "ds-prometheus"},
                "targets": [{"refId": "A", "expr": "up"}],
                "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
            },
            {
                "id": 1,  # duplicate id
                "title": "rogue",
                "datasource": {"type": "mystery", "uid": "ds-not-allowlisted"},
                "targets": [{"refId": "A", "expr": "`curl evil`"}],
                "gridPos": {"x": 20, "y": 0, "w": 12, "h": 8},  # overflows 24 cols
            },
        ]
    }
    warnings = validate_dashboard_json(bad)
    text = "\n".join(warnings)
    assert "duplicate panel id" in text
    assert "datasource not in allowlist" in text
    assert "charset allowlist" in text
    assert "24-column grid" in text


def test_validator_flags_secret_shaped_query() -> None:
    bad = {
        "panels": [
            {
                "id": 1,
                "title": "leak",
                "datasource": {"type": "prometheus", "uid": "ds-prometheus"},
                "targets": [{"refId": "A", "expr": 'up{key="AKIA' + "A" * 16 + '"}'}],
                "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
            }
        ]
    }
    assert any("secret-shaped" in w for w in validate_dashboard_json(bad))


def test_hostile_service_label_never_reaches_service_variable() -> None:
    """Alert labels are attacker-controllable. A label outside the identifier
    allowlist must be defaulted (never interpolated into $service) AND the
    preview must fail closed (validated=False, warning says why)."""
    hostile = 'svc"} or up{job=~".+'
    story = build_story(make_alert(labels={"service": hostile}))
    preview = export_grafana_preview(make_spec(), story)

    templating = preview.dashboard_json["templating"]
    assert templating["list"][0]["query"] == "checkout"
    assert templating["list"][0]["current"]["value"] == "checkout"
    dumped = str(preview.dashboard_json)
    assert hostile not in dumped  # nowhere in the model, not just not-in-queries
    assert preview.validated is False
    assert any("identifier allowlist" in w for w in preview.warnings)


def test_valid_service_label_still_passes() -> None:
    # Dot allowed deliberately: harmless inside a quoted label value and
    # common in real service names (checkout.prod).
    story = build_story(make_alert(labels={"service": "payments.v2-eu"}))
    preview = export_grafana_preview(make_spec(), story)
    assert preview.validated is True
    assert preview.dashboard_json["templating"]["list"][0]["query"] == "payments.v2-eu"


def test_validator_survives_malformed_input_without_raising() -> None:
    """The validator is a safety net — malformed shapes must come back as
    warnings, never exceptions (release-audit P1-3: int() on non-numeric
    gridPos raised ValueError; unhashable panel id raised TypeError)."""
    bad = {
        "panels": [
            {"id": {"not": "hashable"}, "title": "a", "gridPos": {"x": "abc", "w": None}},
            {"id": 2, "title": "b", "gridPos": None, "targets": "not-a-list"},
            {"id": 3, "title": "c", "gridPos": {"x": True, "w": 12}, "targets": [42]},
            {"id": 4, "title": "d", "datasource": {"uid": ["unhashable-uid"]}},
            "not-a-panel",
        ],
        "templating": {"list": [42, {"name": "service", "query": 'x"} evil'}]},
        "annotations": {"list": [7, {"name": "n" * 200, "expr": "`curl evil`"}]},
    }
    warnings = validate_dashboard_json(bad)  # must not raise
    text = "\n".join(warnings)
    assert "not hashable" in text
    assert "outside the 24-column grid" in text
    assert "templating entry is not an object" in text
    assert "identifier allowlist" in text
    assert "datasource not in allowlist" in text  # list-typed uid, no TypeError
    assert "annotation entry is not an object" in text
    assert "oversized name" in text
    assert "expr failed the charset allowlist" in text


def test_validator_checks_annotation_query_surface() -> None:
    """Annotations are a render-time query surface — same rules as panels."""
    bad = {
        "panels": [
            {
                "id": 1,
                "title": "ok",
                "datasource": {"type": "prometheus", "uid": "ds-prometheus"},
                "targets": [{"refId": "A", "expr": "up"}],
                "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
            }
        ],
        "annotations": {
            "list": [
                {
                    "name": "leak",
                    "datasource": {"type": "prometheus", "uid": "ds-rogue"},
                    "expr": 'up{key="AKIA' + "A" * 16 + '"}',
                }
            ]
        },
    }
    warnings = validate_dashboard_json(bad)
    text = "\n".join(warnings)
    assert "annotation 'leak': datasource not in allowlist" in text
    assert "secret-shaped" in text


def test_validator_rejects_query_typed_template_variable() -> None:
    """A "query"-typed variable executes against the datasource on import —
    the exporter only emits textboxes, so anything else fails validation."""
    warnings = validate_dashboard_json(
        {
            "panels": [{"id": 1, "title": "t"}],
            "templating": {"list": [{"name": "service", "type": "query", "query": "up"}]},
        }
    )
    assert any("is not a textbox" in w for w in warnings)


def test_validator_flags_malformed_templating_block() -> None:
    warnings = validate_dashboard_json(
        {"panels": [{"id": 1, "title": "t"}], "templating": {"list": "junk"}}
    )
    assert any("templating block is malformed" in w for w in warnings)


def test_datasource_uids_are_configurable_and_validated_symmetrically() -> None:
    """PP_GRAFANA_*_UID must flow into generated panels AND the validator's
    allowlist — and a mismatch between generator and validator settings must
    be caught, proving the allowlist really binds."""
    from peterpan.config import Settings

    custom = Settings(grafana_prometheus_uid="prom-org-1", grafana_loki_uid="loki-org-1")
    story = build_story(make_alert())
    preview = export_grafana_preview(make_spec(), story, custom)

    assert preview.validated is True
    uids = {p["datasource"]["uid"] for p in preview.dashboard_json["panels"]}
    assert uids == {"prom-org-1", "loki-org-1"}

    # The same dashboard against DEFAULT settings must fail the allowlist.
    warnings = validate_dashboard_json(preview.dashboard_json)
    assert any("datasource not in allowlist" in w for w in warnings)


def test_grafana_endpoint_previews_and_never_publishes() -> None:
    client = TestClient(app)
    resp = client.post(
        "/dashboard/grafana",
        json={
            "problem": "payments failing after latest deploy",
            "alert": {
                "id": "gf-2",
                "source": "webui",
                "title": "payment errors spiking",
                "received_at": datetime.now(UTC).isoformat(),
                "labels": {"service": "payments"},
            },
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["validated"] is True
    assert body["dashboard_json"]["schemaVersion"] == 39
    # preview contract: module performs no network I/O at all
    import peterpan.grafana as grafana_mod

    assert not hasattr(grafana_mod, "publish")
    assert "httpx" not in grafana_mod.__dict__
    assert "requests" not in grafana_mod.__dict__
