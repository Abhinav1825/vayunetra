# agents/ — LangGraph multi-agent layer

Stateful agent graph (typed shared state, spike gate, `action_traces` latency stamping).
Spec: ARCHITECTURE.md §8, PRD §8. Owner of backbone: **Abhinav** (A0). Each agent owned by its lane.

| Node | Owner | Writes |
|---|---|---|
| **A0 Orchestrator** (state, topology, gate, `/agent/query`) | **Abhinav** | `action_traces` |
| **A1 Attribution** | **Omkar** | `attribution` |
| **A2 Forecast** | **Omkar** | `forecasts` |
| **A3 Enforcement** | **Abhinav** | `enforcement_recs` |
| **A4 Advisory** | **Sejal** | `advisories` |
| **A5 Multi-City** | **Sejal** | comparison output |

`tools/` = shared agent tools (SQL, RAG retrieve, ML model service, i18n). Design rule:
ML/physics produce the numbers; the LLM only explains, cites, localises, synthesises.
