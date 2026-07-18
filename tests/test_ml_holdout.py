"""Honest predictor evaluation: stratified holdout, no train/test overlap.

The shipped artifact still trains on ALL rows (standard practice at this
corpus size); the holdout number exists so accuracy claims are never made
on data the model memorized.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from peterpan.ml import _TRAIN_DATA, split_rows


def load_rows() -> list[dict[str, str]]:
    return [
        json.loads(line)
        for line in Path(_TRAIN_DATA).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


# --- split: pure, no torch ---------------------------------------------------


def test_split_is_disjoint_and_complete() -> None:
    rows = load_rows()
    train, holdout = split_rows(rows, holdout_fraction=0.2)
    assert len(train) + len(holdout) == len(rows)
    train_texts = {r["text"] for r in train}
    assert not train_texts & {r["text"] for r in holdout}


def test_split_is_deterministic() -> None:
    rows = load_rows()
    assert split_rows(rows, holdout_fraction=0.2) == split_rows(rows, holdout_fraction=0.2)


def test_split_is_stratified_every_class_in_both_halves() -> None:
    rows = load_rows()
    train, holdout = split_rows(rows, holdout_fraction=0.2)
    classes = {r["incident_class"] for r in rows}
    assert {r["incident_class"] for r in train} == classes
    # Every class with enough examples must be represented in the holdout.
    for cls in classes:
        if sum(1 for r in rows if r["incident_class"] == cls) >= 5:
            assert any(r["incident_class"] == cls for r in holdout), cls


def test_split_rejects_bad_fraction() -> None:
    rows = load_rows()
    for bad in (0.0, 1.0, -0.1, 1.5):
        with pytest.raises(ValueError):
            split_rows(rows, holdout_fraction=bad)


# --- holdout evaluation: needs torch ----------------------------------------


def test_holdout_accuracy_is_honest_and_passes_floor() -> None:
    pytest.importorskip("torch")
    from peterpan.ml import evaluate_holdout

    accuracy = evaluate_holdout()
    assert 0.0 <= accuracy <= 1.0
    # Quality floor for shipping the artifact — do not weaken to pass (see
    # quality-gate skill); improve the data or the model instead.
    assert accuracy >= 0.7
