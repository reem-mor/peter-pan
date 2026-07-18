"""Train the local predictor classifier and report accuracy.

Usage:  python scripts/train_predictor.py

Deterministic (fixed seed) over data/synthetic/predictor_train.jsonl;
writes weights + vocab to data/models/. Needs the `ml` extra (torch).
"""

from __future__ import annotations

from peterpan.ml import DEFAULT_MODEL_DIR, evaluate_holdout, train


def main() -> int:
    holdout = evaluate_holdout()
    train_acc = train()
    print(f"holdout accuracy: {holdout:.2%}   <- the number to quote")
    print(f"train accuracy:   {train_acc:.2%}   (memorization ceiling, not quality)")
    print(f"artifacts: {DEFAULT_MODEL_DIR / 'predictor.pt'}, {DEFAULT_MODEL_DIR / 'vocab.json'}")
    # Ship gate rides on the holdout — never on train accuracy.
    return 0 if holdout >= 0.7 else 1


if __name__ == "__main__":
    raise SystemExit(main())
