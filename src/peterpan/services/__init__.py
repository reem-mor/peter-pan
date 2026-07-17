"""PETER PAN services — one FastAPI app per deployment unit.

Every service follows the same contract: `/healthz` that checks real
dependencies, typed request/response models from `peterpan.schemas`, pure
logic separated from route handlers so it's unit-testable without HTTP.
"""
