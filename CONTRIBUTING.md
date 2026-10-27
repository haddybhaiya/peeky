# Contributing

This project is in a single-developer, phase-gated MVP sprint. Read `AGENTS.md` and `docs/phase.md`. Keep PRs focused on one phase gate; include tests, docs and evidence. Run `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src tests`, `uv run pytest tests/unit tests/smoke -m 'not docker and not live'`, and `uv run python scripts/check_docs.py`. Do not run unknown repository commands on the host or embed tokens into fixtures or logs. Benchmarks must say how many attempted, passed, blocked and skipped.
