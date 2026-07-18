"""Train the local predictor classifier and report accuracy.

Usage:  python scripts/train_predictor.py

Deterministic (fixed seed) over data/synthetic/predictor_train.jsonl;
writes weights + vocab to data/models/. Needs the `ml` extra (torch).
"""

from __future__ import annotations

from peterpan.ml import DEFAULT_MODEL_DIR, train


def main() -> int:
    accuracy = train()
    print(f"train accuracy: {accuracy:.2%}")
    print(f"artifacts: {DEFAULT_MODEL_DIR / 'predictor.pt'}, {DEFAULT_MODEL_DIR / 'vocab.json'}")
    return 0 if accuracy >= 0.9 else 1


if __name__ == "__main__":
    raise SystemExit(main())
