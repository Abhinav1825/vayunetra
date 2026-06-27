"""LangGraph orchestration skeleton (F7).  Owner: Abhinav (Agent 0).

Typed shared state (ARCHITECTURE.md §8.1) + graph topology (§8.2): orchestrator ->
attribution -> forecast -> {spike gate} -> enforcement/advisory -> end. Nodes are stubs;
each agent owner fills their node. Run:  python -m agents.graph
"""
from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class GraphState(TypedDict, total=False):
    city_id: str
    time_window: tuple          # (start, end)
    focus_cells: list[str]      # H3 cells of interest (e.g. spiking)
    signals: dict               # latest measurements snapshot
    attribution: dict           # Agent 1 (Omkar)
    forecast: dict              # Agent 2 (Omkar)
    enforcement: list           # Agent 3 (Abhinav)
    advisories: list            # Agent 4 (Sejal)
    comparison: dict            # Agent 5 (Sejal)
    citations: list             # RAG sources used
    trace: list                 # per-node timing + decisions
    latency_ms: int


def _stamp(state: GraphState, node: str) -> list:
    return [*(state.get("trace") or []), node]


def orchestrator(state: GraphState) -> dict:
    # TODO Abhinav: route + merge action package; stamp action_traces latency
    return {"trace": _stamp(state, "orchestrator")}


def attribution_node(state: GraphState) -> dict:   # Omkar (A1) fills this
    return {"trace": _stamp(state, "attribution")}


def forecast_node(state: GraphState) -> dict:      # Omkar (A2) fills this
    return {"trace": _stamp(state, "forecast")}


def enforcement_node(state: GraphState) -> dict:   # Abhinav (A3) fills this
    return {"trace": _stamp(state, "enforcement")}


def advisory_node(state: GraphState) -> dict:      # Sejal (A4) fills this
    return {"trace": _stamp(state, "advisory")}


def spike_gate(state: GraphState) -> str:
    """Route to enforcement only when there is a spike/hotspot; advisory always runs."""
    return "enforcement" if state.get("focus_cells") else "advisory"


def build_graph():
    g = StateGraph(GraphState)
    for name, fn in [
        ("orchestrator", orchestrator),
        ("attribution", attribution_node),
        ("forecast", forecast_node),
        ("enforcement", enforcement_node),
        ("advisory", advisory_node),
    ]:
        g.add_node(name, fn)
    g.add_edge(START, "orchestrator")
    g.add_edge("orchestrator", "attribution")
    g.add_edge("attribution", "forecast")
    g.add_conditional_edges(
        "forecast", spike_gate, {"enforcement": "enforcement", "advisory": "advisory"}
    )
    g.add_edge("enforcement", "advisory")
    g.add_edge("advisory", END)
    return g.compile()


if __name__ == "__main__":
    app = build_graph()
    print(app.invoke({"city_id": "delhi", "focus_cells": ["883da1a3a1fffff"], "trace": []}))
