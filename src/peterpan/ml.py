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
data/models/. See scripts/train_predictor.py.
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
DEFAULT_MODEL_DIR = _ROOT / "data" / "models"
_TRAIN_DATA = _ROOT / "data" / "synthetic" / "predictor_train.jsonl"

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
    return [t for t in "".join(c if c.isalnum() else " " for c in text.lower()).split() if t]


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


def train(
    train_data: Path = _TRAIN_DATA,
    model_dir: Path = DEFAULT_MODEL_DIR,
    epochs: int = 300,
) -> float:
    """Train the linear bag-of-words classifier. Returns final train accuracy.

    Deterministic (fixed seed), seconds-fast, and offline — the training set
    is synthetic and labeled by hand, NOT by the floor (learning the floor's
    keywords back would make the model pointless; its value is classifying
    paraphrases the keywords miss).
    """
    try:
        import torch
    except ImportError as exc:
        raise MlPredictError("torch not installed (pip install -e '.[ml]')") from exc

    rows = [
        json.loads(line)
        for line in train_data.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise MlPredictError(f"no training rows in {train_data}")

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

    with torch.no_grad():
        accuracy = float((linear(x).argmax(dim=1) == y).float().mean())

    model_dir.mkdir(parents=True, exist_ok=True)
    torch.save(linear.state_dict(), model_dir / "predictor.pt")
    (model_dir / "vocab.json").write_text(
        json.dumps({"vocab": vocab, "classes": classes}), encoding="utf-8"
    )
    return accuracy
