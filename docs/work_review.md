# Work review and evidence ledger

## 2026-10-26 — Phase 0 initial scaffold prepared

**Changed:** initial `pyproject.toml`, CLI inspect/doctor/audit/passport functions, restricted Docker runner, evidence JSON, sample fixtures, documentation, GitHub Actions core and Docker jobs.

**Tested:** At generation time this was a scaffold. Fill out exact `uv sync --locked`, ruff, mypy, pytest, docs, wheel, integration results from local execution below. **Do not infer CI success from the presence of a workflow.**

**Current limitation:** no real open-model adapter, auto-repair engine, immutable git snapshot, working agent A/B tool harness or full system environment support. Those are PHASES 1–5.

**Next:** Phase 1 source identities, then Phase 2 genuine Docker runner/evidence gate.

## Validation log

| Date | Revision | Command | Status | Notes |
|---|---|---|---|---|
| — | — | — | NOT RECORDED | Update once executed |

## Scaffold verification from the artifact environment

- `python -m pytest tests/unit tests/smoke -q`: 19 passed (local Python 3.13).
- `python scripts/check_docs.py`: 12 required files checked.
- `python -m compileall -q src tests scripts`: passed.
- `uv sync --offline`: blocked: required mypy wheel absent from cache.
- `uv sync`: blocked: environment could not resolve PyPI DNS.
- `ruff`, `mypy`, wheel build, and real Docker integration: **NOT RUN**; next validate on a normal online CI runner.
- No product/benchmark/live model pass is claimed.

## 2026-10-27 — Peeky rename and repository analysis

**Changed:** renamed the display name, distribution/import/CLI, `src/peeky`, README execution annotations and fixtures, `.peeky/runs`, `peeky.example.toml`, proposed `PEEKY_` environment variables, wheel lookup, test imports, CI name and documentation. Existing FS/T acceptance IDs are retained. No test cases/assertions or runtime security behavior were added or changed beyond the identity substitutions. Refreshed manifest paths/hashes after documentation updates.

**Scope and revision:** Phase 0 prerequisite review; HEAD `971be15`, with the scaffold mostly untracked before and after this work. No staging, commits or remote writes. Commands below used Python 3.13.7 on Windows; the absolute interpreter is `C:\Users\hp\AppData\Local\Programs\Python\Python313\python.exe` (`py -3.13` also worked outside the sandbox). Locally installed tools are not the pinned development environment. Earlier interrupted command sessions were not treated as completed checks; uncertain results were rerun to completion.

| Command/check | Result |
|---|---|
| `py -3.13 -m pytest tests/unit tests/smoke -q` | 19 passed, 0 skipped |
| `py -3.13 scripts/check_docs.py` | Passed: 12 required files |
| `PYTHONPATH=src python -m peeky --version`, `--help`, `inspect tests/fixtures/good_repo --json` | Correct Peeky identity and one proposed command; no target execution |
| `PYTHONPATH=src python -m peeky inspect tests/fixtures/no_optin_repo --json` | Empty plan, expected exit 2 |
| `python -m ruff check .` (Ruff 0.16.3) | Failed: 2 I001 import-formatting errors, in policy.py and CLI smoke test |
| `python -m ruff format --check .` (Ruff 0.16.3) | Failed: 13 files would be reformatted; 5 already formatted |
| `python -m mypy src tests` (mypy 2.3.1) | Passed: 16 source files |
| `uv build --offline --wheel` (uv 0.12.23) | Passed: `dist/peeky-0.1.0.dev0-py3-none-any.whl` |
| `python scripts/smoke_wheel.py` with `PIP_NO_INDEX=1`, `PIP_DISABLE_PIP_VERSION_CHECK=1` | Passed: wheel installed in a temporary clean venv; module version and inspect worked |
| `PYTHONPATH=src python -m peeky doctor --json` outside the sandbox | Docker CLI present, daemon unavailable; exit 3 |
| `python -m pytest tests/integration -m docker -q` outside the sandbox | 2 skipped because the Docker daemon was unavailable; no integration PASS claimed |
| Bounded controller-only evidence probes | Synthetic PASS JSON accepted for an unexecuted command; source-file mutation did not invalidate passport; unrelated nonzero result labelled PASS yielded PASS; failed first step of two yielded INCONCLUSIVE |
| Rename/package/manifest consistency checks | 51 file entries verified against SHA-256; no legacy identity strings or paths; distribution, import path and entry-point declaration agree |
| `git diff --check` | Passed; Git reports the existing LICENSE line-ending conversion notice |

**Docs updated:** README, architecture and runner caveats, assumptions A-09, ADR-008, phase tracker, this ledger and `docs/repository-analysis.md`. The manifest includes the new analysis document. Original artifact-environment validation above is historical and is not overwritten.

**Known limits:** no real Docker execution in this checkout; no Python 3.12 or pinned-group validation; `uv sync` not rerun, no lockfile; no provider calls, repair/retest loop or agent benchmark. Code review found mutable source/image identity, unauthenticated passports, unbounded capture before truncation, absent explicit container cleanup/redaction and incomplete verdict/coverage validation. These findings are documented, not fixed by the rename.

**Phase gate:** Phase 0 remains incomplete due to observed Ruff failures and outstanding pinned-environment validation. Phase 2 Docker checks are BLOCKED/INCONCLUSIVE, not verified. No phase has been promoted.

**Next task:** finish Phase 0 formatting/import and pinned-environment checks, then Phase 1 immutable source/evidence identity and T-001..T-008. Restore a real Docker runner before attempting the Phase 2 gate.
