"""ActionPreview gate — the PRODUCTION half of the invariant.

README invariant 2/7: production blocks mutating actions until a named human
approves. Until now only the mirage/HIGH branch was tested — deleting the
`not settings.actions_allowed` clause in propose_action kept the suite green
(release-audit P1-6). These pin the environment matrix.
"""

from __future__ import annotations

import pytest

import peterpan.services.agent as agent_mod
from peterpan.config import Settings
from peterpan.schemas import ActionRisk


@pytest.fixture
def production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(agent_mod, "settings", Settings(env="production"))


@pytest.fixture
def mirage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(agent_mod, "settings", Settings(env="mirage"))


def test_production_blocks_low_risk_until_a_named_human_approves(production: None) -> None:
    preview = agent_mod.propose_action("scale deployment to 5 replicas", ActionRisk.LOW)
    assert preview.requires_approval is True
    assert preview.executable is False

    approved = agent_mod.approve(preview, "sre-alex")
    assert approved.executable is True
    assert approved.approved_by == "sre-alex"
    assert approved.approved_at is not None


def test_production_high_risk_always_requires_approval(production: None) -> None:
    preview = agent_mod.propose_action("roll back last deploy", ActionRisk.HIGH)
    assert preview.requires_approval is True
    assert preview.executable is False


def test_production_read_only_needs_no_approval(production: None) -> None:
    preview = agent_mod.propose_action("describe pods", ActionRisk.READ_ONLY)
    assert preview.requires_approval is False
    assert preview.executable is True


def test_low_risk_auto_executes_outside_production(mirage: None) -> None:
    preview = agent_mod.propose_action("scale deployment to 5 replicas", ActionRisk.LOW)
    assert preview.requires_approval is False
    assert preview.executable is True


def test_approver_must_be_identified(production: None) -> None:
    preview = agent_mod.propose_action("roll back", ActionRisk.HIGH)
    with pytest.raises(ValueError, match="approver must be identified"):
        agent_mod.approve(preview, "   ")
