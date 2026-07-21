"""Grafana dashboard JSON exporter — deterministic, catalog-bound, preview-only.

Turns a DashboardSpec + IncidentStory into an importable Grafana dashboard
model (schemaVersion 39) without any LLM call and without any network I/O:

- Panels come from _METRIC_CATALOG, keyed by the story's probable_cause —
  the deterministic floor's verdict. Queries are never model-generated, so
  a fabricated metric name or datasource cannot reach the preview.
- Datasource refs come from _DATASOURCES only (known-uid allowlist).
- The operator's problem text is DATA: it appears in the description field
  verbatim but is never interpolated into a query expression.
- validate() re-checks the finished JSON (unique ids, grid bounds, allowed
  datasources, query-charset allowlist, secret patterns) — belt and braces,
  so a future generator bug fails loud instead of shipping a bad model.

Publishing is out of scope by design: preview/dry-run is the product
behavior (README invariant: mutating actions need explicit human approval).
"""

from __future__ import annotations

import re

from peterpan.schemas import DashboardSpec, GrafanaDashboardPreview, IncidentStory

# Known datasources — the only uids a generated panel may reference.
_DATASOURCES: dict[str, dict[str, str]] = {
    "prometheus": {"type": "prometheus", "uid": "ds-prometheus"},
    "loki": {"type": "loki", "uid": "ds-loki"},
}

# One panel definition: (title, panel type, datasource key, query expr).
# Exprs use only the $service template variable and metric names from the
# demo telemetry catalog — never free text from alerts or problems.
_PanelDef = tuple[str, str, str, str]

_BASE_PANELS: list[_PanelDef] = [
    (
        "Error rate (5xx)",
        "timeseries",
        "prometheus",
        'sum(rate(http_requests_total{service="$service",status=~"5.."}[5m])) '
        '/ sum(rate(http_requests_total{service="$service"}[5m]))',
    ),
    (
        "p99 latency",
        "timeseries",
        "prometheus",
        "histogram_quantile(0.99, sum(rate("
        'http_request_duration_seconds_bucket{service="$service"}[5m])) by (le))',
    ),
    (
        "Request volume",
        "timeseries",
        "prometheus",
        'sum(rate(http_requests_total{service="$service"}[5m]))',
    ),
    (
        "Recent logs (errors)",
        "logs",
        "loki",
        '{service="$service"} |= "error"',
    ),
]

_CLASS_PANELS: dict[str, list[_PanelDef]] = {
    "resource_exhaustion": [
        (
            "Container memory working set",
            "timeseries",
            "prometheus",
            'container_memory_working_set_bytes{service="$service"}',
        ),
        (
            "Pod restarts",
            "timeseries",
            "prometheus",
            'increase(kube_pod_container_status_restarts_total{service="$service"}[30m])',
        ),
    ],
    "latency": [
        (
            "DB connections in use",
            "timeseries",
            "prometheus",
            'db_connections_in_use{service="$service"}',
        ),
        (
            "Queue depth",
            "timeseries",
            "prometheus",
            'queue_depth{service="$service"}',
        ),
    ],
    "availability": [
        (
            "Pod restarts",
            "timeseries",
            "prometheus",
            'increase(kube_pod_container_status_restarts_total{service="$service"}[30m])',
        ),
        (
            "Healthy replicas",
            "timeseries",
            "prometheus",
            'kube_deployment_status_replicas_available{service="$service"}',
        ),
    ],
    "connectivity": [
        (
            "Upstream 5xx by dependency",
            "timeseries",
            "prometheus",
            'sum(rate(upstream_requests_total{service="$service",status=~"5.."}[5m]))'
            " by (upstream)",
        ),
    ],
    "security": [
        (
            "Certificate expiry (days)",
            "stat",
            "prometheus",
            '(cert_expiry_timestamp_seconds{service="$service"} - time()) / 86400',
        ),
    ],
    "change_related": [
        (
            "Deployments (annotations feed)",
            "timeseries",
            "prometheus",
            'changes(deployment_revision{service="$service"}[1h])',
        ),
    ],
}

# Conservative query charset: PromQL/LogQL syntax only. Anything outside
# (backticks, semicolons, angle brackets, control chars) fails validation.
_SAFE_EXPR = re.compile(r'^[\w\s{}()\[\]=~!"$.,:/|<>+*-]+$')
_SECRET_HINTS = re.compile(r"AKIA[0-9A-Z]{16}|sk-(ant|proj)-|ghp_[A-Za-z0-9]{30,}|pcsk_")

_GRID_COLS = 24
_PANEL_W = 12
_PANEL_H = 8


def _panel_json(
    panel_id: int, title: str, kind: str, ds_key: str, expr: str, description: str
) -> dict[str, object]:
    x = ((panel_id - 1) % 2) * _PANEL_W
    y = ((panel_id - 1) // 2) * _PANEL_H
    return {
        "id": panel_id,
        "title": title,
        "type": kind,
        "description": description,
        "datasource": dict(_DATASOURCES[ds_key]),
        "targets": [{"refId": "A", "expr": expr}],
        "gridPos": {"x": x, "y": y, "w": _PANEL_W, "h": _PANEL_H},
    }


def _deploy_annotations(story: IncidentStory) -> list[dict[str, object]]:
    """Deploy evidence becomes dashboard annotations — citation carried in
    the annotation name so the deploy marker stays traceable to evidence."""
    return [
        {
            "name": f"deploy: {e.summary[:60]}",
            "datasource": dict(_DATASOURCES["prometheus"]),
            "enable": True,
            "iconColor": "orange",
            "expr": 'changes(deployment_revision{service="$service"}[1h]) > 0',
            "peterpan_source": e.source,
        }
        for e in story.evidence
        if e.kind == "deploy"
    ]


def validate_dashboard_json(dashboard: dict[str, object]) -> list[str]:
    """Return every problem found; empty list means safe to import."""
    warnings: list[str] = []
    panels = dashboard.get("panels")
    if not isinstance(panels, list) or not panels:
        return ["dashboard has no panels"]

    allowed_uids = {ds["uid"] for ds in _DATASOURCES.values()}
    seen_ids: set[object] = set()
    for p in panels:
        if not isinstance(p, dict):
            warnings.append("panel is not an object")
            continue
        pid, title = p.get("id"), str(p.get("title", ""))
        if pid in seen_ids:
            warnings.append(f"duplicate panel id {pid}")
        seen_ids.add(pid)
        if not title or len(title) > 120:
            warnings.append(f"panel {pid}: empty or oversized title")
        ds = p.get("datasource")
        if not isinstance(ds, dict) or ds.get("uid") not in allowed_uids:
            warnings.append(f"panel {pid}: datasource not in allowlist")
        grid = p.get("gridPos")
        if not isinstance(grid, dict) or not (
            0 <= int(grid.get("x", -1)) < _GRID_COLS
            and 0 < int(grid.get("w", 0)) <= _GRID_COLS
            and int(grid.get("x", 0)) + int(grid.get("w", 0)) <= _GRID_COLS
        ):
            warnings.append(f"panel {pid}: gridPos outside the {_GRID_COLS}-column grid")
        for target in p.get("targets", []) if isinstance(p.get("targets"), list) else []:
            expr = str(target.get("expr", "")) if isinstance(target, dict) else ""
            if not expr or not _SAFE_EXPR.match(expr):
                warnings.append(f"panel {pid}: query failed the charset allowlist")
            if _SECRET_HINTS.search(expr):
                warnings.append(f"panel {pid}: query contains a secret-shaped string")
    return warnings


def export_grafana_preview(spec: DashboardSpec, story: IncidentStory) -> GrafanaDashboardPreview:
    """Deterministic export: catalog panels for the floor's incident class,
    deploy annotations from cited evidence, then full re-validation."""
    service = story.alert.labels.get("service", "checkout")
    incident_class = story.probable_cause

    defs = list(_BASE_PANELS) + _CLASS_PANELS.get(incident_class, [])
    evidence_sources = ", ".join(e.source for e in story.evidence[:3]) or "no evidence collected"

    panels = [
        _panel_json(
            i,
            title,
            kind,
            ds_key,
            expr,
            description=(
                f"Selected for incident class '{incident_class}' "
                f"(confidence {story.confidence:.2f}). Evidence: {evidence_sources}."
            ),
        )
        for i, (title, kind, ds_key, expr) in enumerate(defs, start=1)
    ]

    dashboard: dict[str, object] = {
        "schemaVersion": 39,
        "title": f"PETER PAN · {story.alert.title[:80]}",
        "tags": ["peter-pan", "generated", incident_class],
        "time": {"from": "now-6h", "to": "now"},
        "refresh": "30s",
        "templating": {
            "list": [
                {
                    "name": "service",
                    "type": "textbox",
                    "query": service,
                    "current": {"text": service, "value": service},
                }
            ]
        },
        "annotations": {"list": _deploy_annotations(story)},
        "panels": panels,
    }

    warnings = validate_dashboard_json(dashboard)
    return GrafanaDashboardPreview(
        title=str(dashboard["title"]),
        objective=spec.problem,
        generated_by=f"grafana-exporter/{spec.generated_by}",
        panel_titles=[str(t) for (t, _, _, _) in defs],
        warnings=warnings,
        validated=not warnings,
        dashboard_json=dashboard,
    )
