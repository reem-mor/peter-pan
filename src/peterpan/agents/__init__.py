"""PETER PAN agents — LangGraph orchestration.

Requires the `agents` extra (`pip install -e ".[agents]"`). Fixture-first:
the graph runs deterministically with no LLM; real model calls slot into the
nodes (see prompts/incident-agent/) without changing the graph shape.
"""
