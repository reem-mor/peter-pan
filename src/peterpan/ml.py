"""Local PyTorch classifier behind the deterministic floor — opt-in, guarded.

The model is an upgrade *behind* the floor, never a replacement for it:
- torch is a lazy optional import (`ml` extra); the demo path never needs it
- `apply_floor_guardrails` is pure code: the floor's class is final whenever
  it matched, severity may only be raised (toward P1), confidence is capped
  below certainty, and low-confidence model output is discarded entirely
- ANY model failure (torch missing, weights missing, bad input) raises
  MlPredictError so the caller falls back to the floor — fail-safe by
  construction, mirroring llm.py's LlmSynthesisError contract.

Training is offline and deterministic (fixed seed) over the labeled
synthetic set data/synthetic/predictor_train.jsonl; weights + vocab land in
models/. See scripts/train_predictor.py. models/ lives outside data/ on
purpose: data/ is mutable runtime state (chowned to the container user),
models/ is immutable baked artifacts (root-owned in the image).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from peterpan.schemas import Alert, Prediction, Severity

if TYPE_CHECKING:  # torch types only for checking; runtime import stays lazy
    import torch

_ROOT = Path(__file__).parent.parent.parent
DEFAULT_MODEL_DIR = _ROOT / "models"
_TRAIN_DATA = _ROOT / "data" / "synthetic" / "predictor_train.jsonl"
# Stable artifact label for provider diagnostics / PETER PAN OS. Bump when
# the training recipe or feature schema changes (not on every retrain).
MODEL_VERSION = "predictor-bow-v1"

# Below this the model has no opinion worth acting on: its output is
# discarded wholesale (it may not even raise severity on a hunch).
_MIN_ACTIONABLE_CONFIDENCE = 0.5
_CONFIDENCE_CAP = 0.9  # invariant: never certainty
_SEED = 7


class MlPredictError(Exception):
    """Any ML-path failure. Callers must catch this and fall back to the floor."""


@dataclass(frozen=True)
class MlPrediction:
    """Raw model output — NOT a Prediction until the floor guardrails ran."""

    incident_class: str
    severity: Severity
    confidence: float


def apply_floor_guardrails(floor: Prediction, model: MlPrediction) -> Prediction:
    """Merge model output into the floor's verdict. The floor always wins:

    - class: model may fill it in only when the floor said 'unclassified'
    - severity: model may raise (toward P1), never lower
    - confidence: capped below certainty; low-confidence output is discarded
    """
    if model.confidence < _MIN_ACTIONABLE_CONFIDENCE:
        return floor

    if floor.incident_class == "unclassified":
        incident_class = model.incident_class
        confidence = min(model.confidence, _CONFIDENCE_CAP)
    else:
        incident_class = floor.incident_class
        confidence = floor.confidence

    severity = min(floor.severity, model.severity, key=lambda s: s.value)  # P1 < P4
    return Prediction(incident_class=incident_class, severity=severity, confidence=confidence)


# --- tokenization / features -------------------------------------------------


def _tokenize(text: str) -> list[str]:
    """Words + char 3/4-grams per word. Pure word bag-of-words scored 28.6%
    on the holdout — real alerts phrase the same failure differently, so
    features must overlap across word forms ("saturated"/"saturation",
    "memory"/"maxmemory"); character n-grams provide that overlap."""
    words = [t for t in "".join(c if c.isalnum() else " " for c in text.lower()).split() if t]
    features = list(words)
    for w in words:
        for n in (3, 4):
            features.extend(w[i : i + n] for i in range(len(w) - n + 1) if len(w) > n)
    return features


def _vectorize(text: str, vocab: dict[str, int]) -> torch.Tensor:
    import torch

    vec = torch.zeros(len(vocab))
    for token in _tokenize(text):
        idx = vocab.get(token)
        if idx is not None:
            vec[idx] += 1.0
    return vec


# Class → severity prior: what the model's class implies at minimum, kept
# deliberately conservative (P3) except availability (P2). The floor may
# still raise further; the guardrails stop the model from ever lowering.
_CLASS_SEVERITY: dict[str, Severity] = {
    "availability": Severity.P2,
    "resource_exhaustion": Severity.P3,
    "connectivity": Severity.P3,
    "latency": Severity.P3,
    "security": Severity.P3,
    "change_related": Severity.P3,
    "unclassified": Severity.P4,
}


def model_predict(alert: Alert, model_dir: Path = DEFAULT_MODEL_DIR) -> MlPrediction:
    """Run the trained classifier. Raises MlPredictError on any failure."""
    try:
        import torch
    except ImportError as exc:
        raise MlPredictError("torch not installed (pip install -e '.[ml]')") from exc

    weights_path = model_dir / "predictor.pt"
    vocab_path = model_dir / "vocab.json"
    if not weights_path.exists() or not vocab_path.exists():
        raise MlPredictError(f"model artifacts missing under {model_dir} — run train() first")

    try:
        meta = json.loads(vocab_path.read_text(encoding="utf-8"))
        vocab: dict[str, int] = meta["vocab"]
        classes: list[str] = meta["classes"]
        linear = torch.nn.Linear(len(vocab), len(classes))
        linear.load_state_dict(torch.load(weights_path, weights_only=True))
        linear.eval()
        with torch.no_grad():
            logits = linear(_vectorize(f"{alert.title} {alert.description}", vocab))
            probs = torch.softmax(logits, dim=0)
            confidence, idx = probs.max(dim=0)
        incident_class = classes[int(idx)]
    except MlPredictError:
        raise
    except Exception as exc:  # torch/IO/shape failures all collapse to fallback
        raise MlPredictError(f"model inference failed: {type(exc).__name__}") from exc

    return MlPrediction(
        incident_class=incident_class,
        severity=_CLASS_SEVERITY.get(incident_class, Severity.P4),
        confidence=min(float(confidence), _CONFIDENCE_CAP),
    )


def _load_rows(train_data: Path) -> list[dict[str, str]]:
    rows = [
        json.loads(line)
        for line in train_data.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise MlPredictError(f"no training rows in {train_data}")
    return rows


def split_rows(
    rows: list[dict[str, str]], holdout_fraction: float = 0.2
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Deterministic stratified split. Classes with <5 examples stay train-only
    (a 1-example holdout of a tiny class measures noise, not accuracy)."""
    if not 0.0 < holdout_fraction < 1.0:
        raise ValueError("holdout_fraction must be in (0, 1)")
    import random

    by_class: dict[str, list[dict[str, str]]] = {}
    for r in rows:
        by_class.setdefault(r["incident_class"], []).append(r)

    train_rows: list[dict[str, str]] = []
    holdout: list[dict[str, str]] = []
    for cls in sorted(by_class):
        members = sorted(by_class[cls], key=lambda r: r["text"])
        random.Random(_SEED).shuffle(members)
        k = max(1, round(len(members) * holdout_fraction)) if len(members) >= 5 else 0
        holdout.extend(members[:k])
        train_rows.extend(members[k:])
    return train_rows, holdout


def _fit(
    rows: list[dict[str, str]], epochs: int
) -> tuple[torch.nn.Linear, dict[str, int], list[str]]:
    """Fit the linear classifier on the given rows. Vocab is built from these
    rows only, so a holdout evaluation can never leak through the features."""
    try:
        import torch
    except ImportError as exc:
        raise MlPredictError("torch not installed (pip install -e '.[ml]')") from exc

    classes = sorted({r["incident_class"] for r in rows})
    vocab: dict[str, int] = {}
    for r in rows:
        for token in _tokenize(r["text"]):
            vocab.setdefault(token, len(vocab))

    torch.manual_seed(_SEED)
    x = torch.stack([_vectorize(r["text"], vocab) for r in rows])
    y = torch.tensor([classes.index(r["incident_class"]) for r in rows])

    linear = torch.nn.Linear(len(vocab), len(classes))
    optimizer = torch.optim.Adam(linear.parameters(), lr=0.05)
    loss_fn = torch.nn.CrossEntropyLoss()
    for _ in range(epochs):
        optimizer.zero_grad()
        loss = loss_fn(linear(x), y)
        loss.backward()
        optimizer.step()
    return linear, vocab, classes


def evaluate_holdout(
    train_data: Path = _TRAIN_DATA,
    holdout_fraction: float = 0.2,
    epochs: int = 300,
) -> float:
    """Accuracy on a stratified holdout the model never saw — the honest
    number to quote (train accuracy on a memorizing-capacity model is ~1.0
    by construction)."""
    import torch

    train_split, holdout = split_rows(_load_rows(train_data), holdout_fraction)
    if not holdout:
        raise MlPredictError("holdout is empty — not enough data to evaluate")
    linear, vocab, classes = _fit(train_split, epochs)
    hits = 0
    with torch.no_grad():
        for r in holdout:
            logits = linear(_vectorize(r["text"], vocab))
            if classes[int(logits.argmax())] == r["incident_class"]:
                hits += 1
    return hits / len(holdout)


def train(
    train_data: Path = _TRAIN_DATA,
    model_dir: Path = DEFAULT_MODEL_DIR,
    epochs: int = 300,
) -> float:
    """Train on ALL rows and save the artifacts. Returns train accuracy —
    quote evaluate_holdout() for quality claims, never this number.

    Deterministic (fixed seed), seconds-fast, and offline — the training set
    is synthetic and labeled by hand, NOT by the floor (learning the floor's
    keywords back would make the model pointless; its value is classifying
    paraphrases the keywords miss).
    """
    import torch

    rows = _load_rows(train_data)
    linear, vocab, classes = _fit(rows, epochs)

    x = torch.stack([_vectorize(r["text"], vocab) for r in rows])
    y = torch.tensor([classes.index(r["incident_class"]) for r in rows])
    with torch.no_grad():
        accuracy = float((linear(x).argmax(dim=1) == y).float().mean())

    model_dir.mkdir(parents=True, exist_ok=True)
    torch.save(linear.state_dict(), model_dir / "predictor.pt")
    (model_dir / "vocab.json").write_text(
        json.dumps({"vocab": vocab, "classes": classes}), encoding="utf-8"
    )
    return accuracy
