# tests/ — unit + integration (TDD, 80%+ target)

Everyone writes tests for their lane. Run from repo root:
```bash
pytest -q --cov=. --cov-report=term-missing
```
- **Unit:** connectors (payload→canonical), H3 utils, schemas, scorers, dispersion math.
- **Integration:** API endpoints (envelope shape), DB reads/writes against the schema, agent graph.
- Mirror the source tree: `tests/connectors/`, `tests/core/`, `tests/agents/`, `tests/api/`, ...

CI runs `pytest` + `ruff` on every push/PR (`.github/workflows/ci.yml`).
