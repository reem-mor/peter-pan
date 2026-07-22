"""Python↔TypeScript contract parity — schemas.py is the source of truth.

packages/types/src/index.ts declares "regenerate, never diverge", but until
now nothing enforced it: PR #51 added GrafanaDashboardPreview and the mirror
silently missed it, and two confidence doc-comments contradicted the
`confidence < 1.0` invariant. These tests parse the mirror's fixed
conventions (export interface / export const ARRAYS as const / doc-comments)
so any future drift fails the suite instead of shipping.

Conventions asserted (matching index.ts's own header):
- every pydantic BaseModel in peterpan.schemas has a same-named TS interface
  whose field names are exactly the model's fields (computed @properties are
  mirrored as helper functions, not fields);
- every StrEnum has a frozen values array with identical values in order;
- a Python field bounded lt=1.0 must not be documented as `<= 1.0` in TS
  (and vice versa for the deliberate le=1.0 analyst_confidence exception);
- pydantic datetime fields are carried as ISO strings on the wire.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import annotated_types
import pytest
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from peterpan import schemas

_INDEX_TS = Path(__file__).parent.parent / "packages" / "types" / "src" / "index.ts"

# StrEnum class name -> the frozen values-array name the mirror uses.
_ENUM_ARRAYS = {
    "Severity": "SEVERITIES",
    "ActionRisk": "ACTION_RISKS",
    "FeedbackVerdict": "FEEDBACK_VERDICTS",
    "PanelKind": "PANEL_KINDS",
}


def _python_models() -> dict[str, type[BaseModel]]:
    """Every BaseModel defined in peterpan.schemas (not imported ones)."""
    return {
        name: obj
        for name, obj in vars(schemas).items()
        if isinstance(obj, type)
        and issubclass(obj, BaseModel)
        and obj is not BaseModel
        and obj.__module__ == schemas.__name__
    }


def _python_enums() -> dict[str, type[StrEnum]]:
    return {
        name: obj
        for name, obj in vars(schemas).items()
        if isinstance(obj, type)
        and issubclass(obj, StrEnum)
        and obj is not StrEnum
        and obj.__module__ == schemas.__name__
    }


def _ts_source() -> str:
    return _INDEX_TS.read_text(encoding="utf-8")


def _ts_interfaces(source: str) -> dict[str, str]:
    """interface name -> raw body text (between the braces)."""
    return {
        m.group(1): m.group(2)
        for m in re.finditer(r"export interface (\w+) \{(.*?)\n\}", source, re.DOTALL)
    }


def _ts_fields(body: str) -> set[str]:
    """Field names declared in an interface body (comment lines skipped)."""
    fields = set()
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith(("/*", "*", "//")) or not stripped:
            continue
        m = re.match(r"(\w+)\??:", stripped)
        if m:
            fields.add(m.group(1))
    return fields


def _ts_enum_arrays(source: str) -> dict[str, list[str]]:
    """frozen array name -> its string values, in order."""
    return {
        m.group(1): re.findall(r'"([^"]+)"', m.group(2))
        for m in re.finditer(r"export const (\w+) = \[(.*?)\] as const", source, re.DOTALL)
    }


def _has_bound(field: FieldInfo, kind: type, value: float) -> bool:
    return any(
        isinstance(m, kind) and getattr(m, kind.__name__.lower()) == value for m in field.metadata
    )


def test_every_model_has_a_ts_interface_and_vice_versa() -> None:
    models = set(_python_models())
    interfaces = set(_ts_interfaces(_ts_source()))
    missing = models - interfaces
    extra = interfaces - models
    assert not missing, f"schemas.py models missing from packages/types: {sorted(missing)}"
    assert not extra, f"TS interfaces with no schemas.py model: {sorted(extra)}"


@pytest.mark.parametrize("name", sorted(_python_models()))
def test_interface_fields_match_model_fields(name: str) -> None:
    model = _python_models()[name]
    interfaces = _ts_interfaces(_ts_source())
    if name not in interfaces:
        pytest.fail(f"{name}: interface missing (covered by the set-equality test)")
    ts = _ts_fields(interfaces[name])
    py = set(model.model_fields)
    assert ts == py, (
        f"{name}: field drift — TS-only {sorted(ts - py)}, Python-only {sorted(py - ts)}"
    )


def test_enum_values_match_frozen_arrays() -> None:
    enums = _python_enums()
    arrays = _ts_enum_arrays(_ts_source())
    assert set(_ENUM_ARRAYS) == set(enums), (
        "enum registry drifted — update _ENUM_ARRAYS alongside schemas.py: "
        f"{sorted(set(enums) ^ set(_ENUM_ARRAYS))}"
    )
    for enum_name, array_name in _ENUM_ARRAYS.items():
        assert array_name in arrays, f"{array_name} frozen array missing from index.ts"
        assert arrays[array_name] == [e.value for e in enums[enum_name]], (
            f"{enum_name}: values drifted ({arrays[array_name]})"
        )


@pytest.mark.parametrize("name", sorted(_python_models()))
def test_confidence_bound_comments_match_python(name: str) -> None:
    """A field bounded lt=1.0 must not be documented `<= 1.0` in the mirror —
    the doc-comment IS the contract a TS consumer reads, and `<= 1.0` there
    contradicts the confidence < 1.0 product invariant. (The deliberate
    le=1.0 field, Feedback.analyst_confidence, is not asserted from this
    side: its comment legitimately references the `< 1.0` invariant in
    prose, so a text check would false-positive — the field-existence and
    range tests still cover it.)"""
    model = _python_models()[name]
    body = _ts_interfaces(_ts_source()).get(name, "")
    for field_name, field in model.model_fields.items():
        if _has_bound(field, annotated_types.Lt, 1.0):
            assert "<= 1.0" not in body, (
                f"{name}.{field_name} is lt=1.0 in Python but the TS block says '<= 1.0'"
            )


@pytest.mark.parametrize("name", sorted(_python_models()))
def test_datetime_fields_are_iso_strings_in_ts(name: str) -> None:
    model = _python_models()[name]
    body = _ts_interfaces(_ts_source()).get(name, "")
    for field_name, field in model.model_fields.items():
        if field.annotation in (datetime, datetime | None):
            m = re.search(rf"^\s*{field_name}\??: ([^;]+);", body, re.MULTILINE)
            assert m and "string" in m.group(1), (
                f"{name}.{field_name}: datetime must cross the wire as an ISO string, "
                f"got TS type {m.group(1) if m else 'MISSING'!r}"
            )
