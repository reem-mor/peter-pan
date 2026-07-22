"""Grafana dashboard JSON exporter — deterministic, catalog-bound, preview-only.

Turns a DashboardSpec + IncidentStory into an importable Grafana dashboard
model (schemaVersion 39) without any LLM call and without any network I/O:

- Panels come from _METRIC_CATALOG, keyed by the story's probable_cause —
  the deterministic floor's verdict. Queries are never model-generated, so
  a fabricated metric name or datasource cannot reach the preview.
- Datasource refs come from _datasources() only (known-uid allowlist; UIDs
  configurable via PP_GRAFANA_*_UID to match a real Grafana's provisioning —
  infra/grafana/ ships a matching file for a disposable import instance).
- The operator's problem text is DATA: it appears in the description field
  verbatim but is never interpolated into a query expression. The alert's
  `service` label is DATA too: it reaches the $service template variable
  only when it passes the identifier allowlist — otherwise the variable is
  defaulted and the preview flags itself not-validated.
- validate() re-checks the finished JSON (unique ids, grid bounds, allowed
  datasources, query-charset allowlist, template-variable allowlist, secret
  patterns) — belt and braces, so a future generator bug fails loud instead
  of shipping a bad model. Malformed input yields warnings, never raises:
  a validator that crashes is not a safety net.

Publishing is out of scope by design: preview/dry-run is the product
behavior (README invariant: mutating actions need explicit human approval).
"""

from __future__ import annotations

import re

from peterpan.config import Settings
from peterpan.schemas import DashboardSpec, GrafanaDashboardPreview, IncidentStory


def _datasources(settings: Settings) -> dict[str, dict[str, str]]:
    """Known datasources — the only uids a generated panel may reference."""
    return {
        "prometheus": {"type": "prometheus", "uid": settings.grafana_prometheus_uid},
        "loki": {"type": "loki", "uid": settings.grafana_loki_uid},
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
_SAFE_EXPR = re.compile(r'^[\w\s{}()\[\]=~!"$.,:/|<>+*-]+$', re.ASCII)
# The $service template variable is interpolated by Grafana into every
# query expression at render time, and its value originates in an
# attacker-controllable alert label — identifier charset only (dot allowed:
# harmless inside a quoted label value, common in real service names), no
# quotes, braces, spaces or regex metacharacters.
_SAFE_SERVICE = re.compile(r"^[A-Za-z0-9._-]{1,63}$")
_SECRET_HINTS = re.compile(r"AKIA[0-9A-Z]{16}|sk-(ant|proj)-|ghp_[A-Za-z0-9]{30,}|pcsk_")

_GRID_COLS = 24
_PANEL_W = 12
_PANEL_H = 8


def _panel_json(
    panel_id: int,
    title: str,
    kind: str,
    datasource: dict[str, str],
    expr: str,
    description: str,
) -> dict[str, object]:
    x = ((panel_id - 1) % 2) * _PANEL_W
    y = ((panel_id - 1) // 2) * _PANEL_H
    return {
        "id": panel_id,
        "title": title,
        "type": kind,
        "description": description,
        "datasource": dict(datasource),
        "targets": [{"refId": "A", "expr": expr}],
        "gridPos": {"x": x, "y": y, "w": _PANEL_W, "h": _PANEL_H},
    }


def _deploy_annotations(
    story: IncidentStory, datasources: dict[str, dict[str, str]]
) -> list[dict[str, object]]:
    """Deploy evidence becomes dashboard annotations — citation carried in
    the annotation name so the deploy marker stays traceable to evidence."""
    return [
        {
            "name": f"deploy: {e.summary[:60]}",
            "datasource": dict(datasources["prometheus"]),
            "enable": True,
            "iconColor": "orange",
            "expr": 'changes(deployment_revision{service="$service"}[1h]) > 0',
            "peterpan_source": e.source,
        }
        for e in story.evidence
        if e.kind == "deploy"
    ]


def _grid_ok(grid: object) -> bool:
    """True only for a well-typed gridPos inside the column grid. Non-numeric
    or missing values are simply not-ok — never an exception."""
    if not isinstance(grid, dict):
        return False
    x, w = grid.get("x", -1), grid.get("w", 0)
    if isinstance(x, bool) or isinstance(w, bool):
        return False
    if not isinstance(x, int | float) or not isinstance(w, int | float):
        return False
    return 0 <= x < _GRID_COLS and 0 < w <= _GRID_COLS and x + w <= _GRID_COLS


def validate_dashboard_json(
    dashboard: dict[str, object], settings: Settings | None = None
) -> list[str]:
    """Return every problem found; empty list means safe to import.

    Total over malformed input by design: an unhashable panel id, a
    non-numeric gridPos, or a junk templating block becomes a warning,
    never an exception — a validator that crashes is not a safety net.
    """
    settings = settings or Settings()
    warnings: list[str] = []
    panels = dashboard.get("panels")
    if not isinstance(panels, list) or not panels:
        return ["dashboard has no panels"]

    allowed_uids = {ds["uid"] for ds in _datasources(settings).values()}
    seen_ids: set[object] = set()
    for p in panels:
        if not isinstance(p, dict):
            warnings.append("panel is not an object")
            continue
        pid, title = p.get("id"), str(p.get("title", ""))
        try:
            if pid in seen_ids:
                warnings.append(f"duplicate panel id {pid}")
            seen_ids.add(pid)
        except TypeError:
            warnings.append(f"panel id {pid!r} is not hashable")
        if not title or len(title) > 120:
            warnings.append(f"panel {pid}: empty or oversized title")
        ds = p.get("datasource")
        uid = ds.get("uid") if isinstance(ds, dict) else None
        if not isinstance(uid, str) or uid not in allowed_uids:
            warnings.append(f"panel {pid}: datasource not in allowlist")
        if not _grid_ok(p.get("gridPos")):
            warnings.append(f"panel {pid}: gridPos outside the {_GRID_COLS}-column grid")
        for target in p.get("targets", []) if isinstance(p.get("targets"), list) else []:
            expr = str(target.get("expr", "")) if isinstance(target, dict) else ""
            if not expr or not _SAFE_EXPR.match(expr):
                warnings.append(f"panel {pid}: query failed the charset allowlist")
            if _SECRET_HINTS.search(expr):
                warnings.append(f"panel {pid}: query contains a secret-shaped string")

    # Template variables are interpolated into every query at render time —
    # the charset allowlist above is meaningless if $service can smuggle
    # arbitrary text, so the variable values get their own allowlist check.
    templating = dashboard.get("templating")
    if templating is not None:
        entries = templating.get("list") if isinstance(templating, dict) else None
        if not isinstance(entries, list):
            warnings.append("templating block is malformed")
        else:
            for entry in entries:
                if not isinstance(entry, dict):
                    warnings.append("templating entry is not an object")
                    continue
                name = str(entry.get("name", ""))
                if entry.get("type") != "textbox":
                    # A "query"-typed variable executes against the datasource
                    # on import — the exporter only ever emits textboxes.
                    warnings.append(f"templating variable {name!r} is not a textbox")
                current = entry.get("current")
                values = [
                    entry.get("query"),
                    *(
                        [current.get("value"), current.get("text")]
                        if isinstance(current, dict)
                        else []
                    ),
                ]
                for value in values:
                    if not isinstance(value, str) or not _SAFE_SERVICE.match(value):
                        warnings.append(
                            f"templating variable {name!r} failed the identifier allowlist"
                        )
                        break

    # Annotations are the one other render-time query surface — same rules
    # as panel targets (charset, secret shapes, datasource allowlist).
    annotations = dashboard.get("annotations")
    if annotations is not None:
        entries = annotations.get("list") if isinstance(annotations, dict) else None
        if not isinstance(entries, list):
            warnings.append("annotations block is malformed")
        else:
            for entry in entries:
                if not isinstance(entry, dict):
                    warnings.append("annotation entry is not an object")
                    continue
                a_name = str(entry.get("name", ""))
                if len(a_name) > 120:
                    warnings.append(f"annotation {a_name[:40]!r}: oversized name")
                a_ds = entry.get("datasource")
                a_uid = a_ds.get("uid") if isinstance(a_ds, dict) else None
                if not isinstance(a_uid, str) or a_uid not in allowed_uids:
                    warnings.append(f"annotation {a_name!r}: datasource not in allowlist")
                a_expr = entry.get("expr")
                if not isinstance(a_expr, str) or not _SAFE_EXPR.match(a_expr):
                    warnings.append(f"annotation {a_name!r}: expr failed the charset allowlist")
                elif _SECRET_HINTS.search(a_expr):
                    warnings.append(f"annotation {a_name!r}: expr contains a secret-shaped string")
    return warnings


def export_grafana_preview(
    spec: DashboardSpec, story: IncidentStory, settings: Settings | None = None
) -> GrafanaDashboardPreview:
    """Deterministic export: catalog panels for the floor's incident class,
    deploy annotations from cited evidence, then full re-validation."""
    settings = settings or Settings()
    datasources = _datasources(settings)

    # The service label is attacker-controllable alert data. Outside the
    # identifier allowlist it never reaches $service (Grafana would
    # interpolate it into every query at render time) — the variable is
    # defaulted and the preview is flagged below so the operator sees why.
    raw_service = str(story.alert.labels.get("service", "checkout"))
    service_rejected = not _SAFE_SERVICE.match(raw_service)
    service = "checkout" if service_rejected else raw_service
    incident_class = story.probable_cause

    defs = list(_BASE_PANELS) + _CLASS_PANELS.get(incident_class, [])
    evidence_sources = ", ".join(e.source for e in story.evidence[:3]) or "no evidence collected"

    panels = [
        _panel_json(
            i,
            title,
            kind,
            datasources[ds_key],
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
        "annotations": {"list": _deploy_annotations(story, datasources)},
        "panels": panels,
    }

    warnings = validate_dashboard_json(dashboard, settings)
    if service_rejected:
        # Fail closed on suspicious input: the query stayed safe (variable
        # was defaulted), but a label outside the allowlist means someone
        # fed hostile data — surface it and block import via validated=False.
        warnings.append(
            "alert service label failed the identifier allowlist; $service defaulted to 'checkout'"
        )
    return GrafanaDashboardPreview(
        title=str(dashboard["title"]),
        objective=spec.problem,
        generated_by=f"grafana-exporter/{spec.generated_by}",
        panel_titles=[str(t) for (t, _, _, _) in defs],
        warnings=warnings,
        validated=not warnings,
        dashboard_json=dashboard,
    )
