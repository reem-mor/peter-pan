"""Contract tests for the versioned n8n workflow exports (n8n/workflows/).

CI has no n8n instance, so these tests ARE the gate: they parse each export
and assert it against the repo's own contracts — the n8n schema shape, the
env-templated URL convention (git is the source of truth; one definition
serves localhost, Docker, and EC2), the peterpan.schemas models the flows
speak, and the no-embedded-credentials rule. Importing a flow into the live
instance stays a manual step (see n8n/README.md).
"""

from __future__ import annotations

import importlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from peterpan.schemas import Alert, IncidentStory

WORKFLOWS_DIR = Path(__file__).resolve().parent.parent / "n8n" / "workflows"
WORKFLOW_PATHS = sorted(WORKFLOWS_DIR.glob("*.json"))
WORKFLOW_IDS = [p.stem for p in WORKFLOW_PATHS]

TRIAGE = WORKFLOWS_DIR / "peter-pan-triage.json"
MESH = WORKFLOWS_DIR / "peter-pan-mesh-exercise.json"

# The env-templated base URL convention: every HTTP node resolves its host
# through an n8n environment variable, never a literal address.
_URL_RE = re.compile(r"^=\{\{ \$env\.(PP_[A-Z]+_BASE) \}\}(/[A-Za-z0-9/_-]+)$")

# Which FastAPI app each base env var points at (module exposing `app`).
BASE_ENV_TO_MODULE = {
    "PP_PREDICTOR_BASE": "peterpan.services.predictor",
    "PP_RAG_BASE": "peterpan.services.rag",
    "PP_GUARDRAILS_BASE": "peterpan.services.guardrails",
    "PP_AGENT_BASE": "peterpan.services.agent",
    "PP_PPOS_BASE": "peterpan.services.ppos",
}

WEBHOOK_TYPE = "n8n-nodes-base.webhook"
HTTP_TYPE = "n8n-nodes-base.httpRequest"
RESPOND_TYPE = "n8n-nodes-base.respondToWebhook"
CODE_TYPE = "n8n-nodes-base.code"


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _nodes(wf: dict[str, Any], node_type: str | None = None) -> list[dict[str, Any]]:
    nodes = cast(list[dict[str, Any]], wf["nodes"])
    return [n for n in nodes if node_type is None or n["type"] == node_type]


def _node(wf: dict[str, Any], name: str) -> dict[str, Any]:
    (match,) = [n for n in _nodes(wf) if n["name"] == name]
    return match


def _routes(env_var: str) -> set[tuple[str, str]]:
    """(method, path) pairs served by the FastAPI app the env var points at."""
    module = importlib.import_module(BASE_ENV_TO_MODULE[env_var])
    app = cast(FastAPI, module.app)
    return {
        (method, route.path)
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in route.methods
    }


def _code_fields(js_code: str) -> set[str]:
    """Field names assigned in a Code node's returned object literal.

    Comments are stripped first (an apostrophe in prose desyncs string
    pairing), then string literals, so text content (e.g. "the 14:00
    rollout") can't masquerade as an object key.
    """
    no_comments = re.sub(r"//[^\n]*", "", js_code)
    no_strings = re.sub(r"'[^']*'|\"[^\"]*\"", "''", no_comments)
    return set(re.findall(r"([A-Za-z_]\w*)\s*:", no_strings)) - {"json"}


def test_expected_workflows_present() -> None:
    assert TRIAGE in WORKFLOW_PATHS, "triage flow export missing"
    assert MESH in WORKFLOW_PATHS, "mesh exercise flow export missing"


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_valid_n8n_schema_shape(path: Path) -> None:
    """(a) Structurally importable: nodes + connections, consistent names."""
    wf = _load(path)
    assert isinstance(wf.get("name"), str) and wf["name"]
    nodes = _nodes(wf)
    assert nodes, "workflow has no nodes"
    for node in nodes:
        assert isinstance(node.get("name"), str) and node["name"]
        assert isinstance(node.get("type"), str) and node["type"].startswith("n8n-nodes-base.")
        assert isinstance(node.get("typeVersion"), int)
        assert isinstance(node.get("position"), list) and len(node["position"]) == 2
        assert isinstance(node.get("parameters"), dict)

    names = [n["name"] for n in nodes]
    assert len(names) == len(set(names)), "duplicate node names"

    connections = wf["connections"]
    assert isinstance(connections, dict)
    for source, outputs in connections.items():
        assert source in names, f"connection from unknown node {source!r}"
        for branch in outputs["main"]:
            for target in branch:
                assert target["node"] in names, f"connection to unknown node {target['node']!r}"


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_http_urls_are_env_templated(path: Path) -> None:
    """(b) No hardcoded hosts: every HTTP URL resolves through $env.PP_*_BASE."""
    wf = _load(path)
    http_nodes = _nodes(wf, HTTP_TYPE)
    assert http_nodes, "workflow exercises no HTTP endpoint"
    for node in http_nodes:
        url = node["parameters"]["url"]
        match = _URL_RE.fullmatch(url)
        assert match, f"{node['name']!r} URL is not env-templated: {url!r}"
        assert match.group(1) in BASE_ENV_TO_MODULE, f"unknown base env var in {url!r}"

    raw = path.read_text(encoding="utf-8")
    assert not re.search(r"https?://", raw), "literal URL embedded in workflow export"
    assert not re.search(r"\b\d{1,3}(\.\d{1,3}){3}\b", raw), "hardcoded IP in workflow export"
    assert not re.search(r"(?i)localhost|host\.docker\.internal", raw), "hardcoded host"


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_http_urls_match_live_route_tables(path: Path) -> None:
    """(c) Every templated URL names a real route, with the right method."""
    wf = _load(path)
    for node in _nodes(wf, HTTP_TYPE):
        match = _URL_RE.fullmatch(node["parameters"]["url"])
        assert match is not None
        env_var, route_path = match.groups()
        method = node["parameters"].get("method", "GET")
        assert (method, route_path) in _routes(env_var), (
            f"{node['name']!r} targets {method} {route_path} which "
            f"{BASE_ENV_TO_MODULE[env_var]} does not serve"
        )


def test_triage_webhook_input_matches_alert_schema() -> None:
    """(c) Input contract: Normalize Alert emits Alert-schema fields only,
    including every required one — a rail-passing alert can't 422 at /story."""
    wf = _load(TRIAGE)
    emitted = _code_fields(_node(wf, "Normalize Alert")["parameters"]["jsCode"])
    alert_fields = set(Alert.model_fields)
    required = {name for name, field in Alert.model_fields.items() if field.is_required()}
    assert emitted <= alert_fields, f"non-Alert fields emitted: {emitted - alert_fields}"
    assert required <= emitted, f"required Alert fields missing: {required - emitted}"


def test_triage_output_is_incident_story_shaped() -> None:
    """(c) Output contract: the exact payload shape Normalize Alert builds
    round-trips through the /story route the flow calls into a valid
    IncidentStory — which Respond Story echoes verbatim as the webhook body."""
    wf = _load(TRIAGE)
    build_story = _node(wf, "Build Story")
    assert _URL_RE.fullmatch(build_story["parameters"]["url"]).groups() == (  # type: ignore[union-attr]
        "PP_AGENT_BASE",
        "/story",
    )
    assert "$('Build Story')" in _node(wf, "Respond Story")["parameters"]["responseBody"]

    emitted = _code_fields(_node(wf, "Normalize Alert")["parameters"]["jsCode"])
    fixture = {
        "id": "n8n-contract-test",
        "source": "n8n-webhook",
        "title": "checkout timeout after deploy",
        "description": "p99 latency breached SLO",
        "severity": "P2",
        "received_at": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
    }
    payload = {k: v for k, v in fixture.items() if k in emitted}

    agent = importlib.import_module("peterpan.services.agent")
    response = TestClient(agent.app).post("/story", json=payload)
    assert response.status_code == 200
    story = IncidentStory.model_validate(response.json())
    assert story.confidence < 1.0  # invariant survives the wire format
    assert story.evidence, "citation trail must be non-empty"


def test_mesh_exercise_covers_every_service() -> None:
    """The mesh flow hits healthz + the main route on all five services."""
    wf = _load(MESH)
    hit: set[tuple[str, str]] = set()
    for node in _nodes(wf, HTTP_TYPE):
        match = _URL_RE.fullmatch(node["parameters"]["url"])
        assert match is not None
        hit.add(match.groups())
    for env_var in BASE_ENV_TO_MODULE:
        assert (env_var, "/healthz") in hit, f"mesh flow skips {env_var} healthz"
    expected_main = {
        ("PP_PREDICTOR_BASE", "/predict"),
        ("PP_RAG_BASE", "/query"),
        ("PP_GUARDRAILS_BASE", "/check/input"),
        ("PP_AGENT_BASE", "/story"),
        ("PP_PPOS_BASE", "/os/info"),
    }
    assert expected_main <= hit, f"mesh flow skips main routes: {expected_main - hit}"


def test_mesh_seed_alert_matches_alert_schema() -> None:
    """The mesh fixture is a schema-valid Alert, same rule as triage intake."""
    wf = _load(MESH)
    emitted = _code_fields(_node(wf, "Seed Alert")["parameters"]["jsCode"])
    required = {name for name, field in Alert.model_fields.items() if field.is_required()}
    assert emitted <= set(Alert.model_fields)
    assert required <= emitted


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_no_credentials_embedded(path: Path) -> None:
    """(d) Exports carry credential *bindings* only, never values or blocks."""
    wf = _load(path)
    for node in _nodes(wf):
        assert "credentials" not in node, f"{node['name']!r} embeds a credentials block"
    raw = path.read_text(encoding="utf-8")
    secret_shapes = r"(?i)sk-[a-z0-9]{8,}|bearer\s+[a-z0-9]|password|api[_-]?key[\"']?\s*[:=]"
    assert not re.search(secret_shapes, raw), "secret-shaped string in workflow export"


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_fail_visible_and_rails_first(path: Path) -> None:
    """Repo conventions from n8n/README.md, enforced mechanically:
    header-auth webhooks, error branches on HTTP nodes, and every terminal
    node an explicit Respond — no path drops an alert silently."""
    wf = _load(path)
    webhooks = _nodes(wf, WEBHOOK_TYPE)
    assert webhooks, "flow has no webhook trigger"
    for node in webhooks:
        assert node["parameters"].get("authentication") == "headerAuth", (
            f"webhook {node['name']!r} accepts unauthenticated intake"
        )
    for node in _nodes(wf, HTTP_TYPE):
        assert node.get("onError") == "continueErrorOutput", (
            f"HTTP node {node['name']!r} has no error branch — a down service would fail silent"
        )
    sources = set(wf["connections"])
    for node in _nodes(wf):
        if node["name"] not in sources:
            assert node["type"] == RESPOND_TYPE, (
                f"terminal node {node['name']!r} is not a Respond node (silent drop)"
            )
