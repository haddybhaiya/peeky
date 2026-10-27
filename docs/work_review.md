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

## 2026-10-27 — Phase 0 local foundation gate completed

**Authorization:** the owner requested completion of Phase 0 and deferred the two Docker tests until Docker is running. Those cases remain pending Phase 2 integration; they are not failures or passes in this gate.

**Changed:** created `uv.lock` from the existing dependency declarations; both CI jobs now sync and run with `--locked`. Fixed two import-spacing errors and formatted 13 Python files. No product runtime behavior or test assertions changed: AST comparison against HEAD confirmed equality in all 16 source/test Python files. The wheel smoke script selects the matching project version, requires one wheel, installs without network/dependencies, clears Python source-path overrides, and runs the installed module and console command outside the checkout. The docs gate checks 14 public contract files instead of depending on an intentionally ignored local prompts file. Added `.peeky/` to ignores while retaining the owner's existing `.freshstart/` entry and local-prompts ignore. The refreshed public-file manifest includes `uv.lock` and excludes the ignored prompts file without deleting it.

**Environment:** Windows, Python 3.13.7, uv 0.12.23. The new `.venv` contains the declared pytest 9.1.1, Ruff 0.16.10 and mypy 2.4.0; build resolved to 1.6.1 in the lock. Base revision `a68c595`; nothing staged or committed by this task. Python 3.12/Linux and GitHub Actions were not executed here.

| Completed command/check | Result |
|---|---|
| `uv sync --python C:\Users\hp\AppData\Local\Programs\Python\Python313\python.exe` | Resolved and installed 16 packages; created lock and isolated `.venv` |
| `uv sync --locked --offline --python C:\Users\hp\AppData\Local\Programs\Python\Python313\python.exe` | Resolved/checked 16 packages successfully from cache; lock unchanged |
| `.venv\Scripts\ruff.exe check . --fix` | Fixed 2 import-formatting errors, 0 remaining |
| `.venv\Scripts\ruff.exe format .` | 13 files formatted; 5 unchanged |
| `.venv\Scripts\ruff.exe check .` | All checks passed |
| `.venv\Scripts\ruff.exe format --check .` | All 18 files already formatted |
| `.venv\Scripts\mypy.exe src tests` | Success: 16 source files |
| Initial sandbox `.venv` unit/smoke run | 18 passed, 1 setup error: permission denied reading existing pytest temp directory; not counted as gate success |
| `uv run --locked pytest tests/unit tests/smoke -m 'not docker and not live' -q` outside sandbox | 19 passed in 0.25s; 0 skipped |
| `.venv\Scripts\python.exe scripts/check_docs.py` | 14 required files checked |
| Public-checkout docs smoke | Copied current public tracked files into a temporary directory; checker passed with the ignored local prompts absent |
| `.venv\Scripts\peeky.exe --version`, `--help`, `inspect tests/fixtures/good_repo --json` | Correct identity/help and one proposed step; no target execution |
| `uv build --offline --wheel` | Built `dist/peeky-0.1.0.dev0-py3-none-any.whl` |
| `.venv\Scripts\python.exe scripts/smoke_wheel.py` | Clean venv installed wheel with `--no-index --no-deps`; isolated module version, console version and console inspect all passed |
| Source/test AST comparison | All 16 controller/test Python files match HEAD behavior/assertions |

**Docs updated:** phase tracker, assumptions A-01/A-11, ADR-009, README, contributor setup, test plan, repository analysis and this ledger. Earlier validation records remain historical.

**Known limits:** 2 Docker tests deferred by the owner and not rerun in this completion task. No target code executed on the host. CI/Python 3.12, immutable source capture, strengthened evidence/passports, runner hardening, model repair and agent benchmarks remain unverified or unimplemented as documented. The initial sandbox permission error was resolved by rerunning the trusted controller tests outside the sandbox; no assertions were relaxed.

**Phase gate:** Phase 0 VERIFIED for the local foundation checks above. This is not a target/product PASS and does not promote Phase 2. The Docker acceptance criteria are unchanged.

**Next task:** Phase 1 immutable source identities, snapshots and T-001..T-008. Once Docker is running, execute `uv run --locked pytest tests/integration -m docker` and record actual outcomes before claiming a Docker gate.

## 2026-10-27 — Phase 1 source identity and pre-execution gate completed

**Changed:** added `sources.py` for verified raw Git commit/tree/blob capture, selected-scope index/worktree consistency, path/type/credential checks, bounded read-only temporary exports and source integrity verification. Added `domain.py` for frozen source/policy identities, deterministic plan hashes and controller run transitions. CLI inspect/audit now plan from captured committed bytes; only audit can invoke Docker, and it receives the export path. Missing Docker preserves BLOCKED/INCONCLUSIVE evidence without target execution. Schema 1.1 records source/policy/plan/state provenance. Passport validation rejects legacy evidence and source/commit/command/policy/state/result mismatches. Mechanical verdict reduction now preserves an observed failure with later incomplete coverage and rejects unrelated/nonzero PASS results. Runner constants read the shared default policy without changing resource budgets. No model or release feature was added.

**Compatibility:** inspect JSON is now a structured plan object instead of a bare list; passports require schema 1.1. Sources require a clean committed selected directory within an ordinary local Git repo. UTF-8 CRLF checkout equivalence is accepted without executing filters, and exports contain original Git bytes. Dirty files outside a selected subdirectory are irrelevant to its file manifest; a new containing commit still invalidates commit-bound guidance. See `source-capture.md` for bounds and unsupported inputs.

**Environment/revision:** base HEAD `d9dbd68`; Python 3.13.7, uv 0.12.23, pinned pytest 9.1.1/Ruff 0.16.10/mypy 2.4.0. Working tree was clean before implementation. No workspace staging, commit, remote write, credential use, publishing or target host execution. Tests create/commit only synthetic temporary Git repositories with hooks disabled. Python 3.12/Linux/remote CI was not run.

| Completed command/check | Observed result |
|---|---|
| Initial focused unit/smoke run | 74 passed, 1 failed: file-count denial was wrapped as a generic Git-tree error; preserved specific SourceError and reran without relaxing the bound/assertion |
| Intermediate expanded source gates | 78 passed, then 81 passed in 56.22s; 0 skips |
| `uv run --locked pytest tests/unit tests/smoke tests/integration/test_source_capture.py -q` | Final gate after image-policy regression cases: 85 passed in 62.28s, 0 skipped; includes one real independent-process Git integration |
| `.venv\Scripts\ruff.exe check .` | All checks passed |
| `.venv\Scripts\ruff.exe format --check .` | 25 files already formatted |
| `.venv\Scripts\mypy.exe src tests` | Success: 23 source files |
| `.venv\Scripts\python.exe scripts/check_docs.py` | 15 required public files checked |
| `uv sync --locked --offline` | 16 packages resolved/checked from cache; no dependency changes |
| `uv build --offline --wheel` | Built `dist/peeky-0.1.0.dev0-py3-none-any.whl` for validation only |
| Initial sandbox wheel smoke | Installed module/console version passed; Git refused metadata access to the workspace repo from the sandbox account; no target execution or policy bypass |
| `uv run --locked python scripts/smoke_wheel.py` outside sandbox | Passed: clean network-free installation, module version, console version and inspect on the committed good fixture |

**Behavior evidence:** two independent exports match source identity and original Git bytes; changing the worktree does not alter an already captured export; export tampering is detected. Native Windows junctions, Git symlink/submodule README modes, malicious traversal trees, case collisions, dirty/staged/untracked files, tracked credential paths and source budgets are denied. Git filters/fsmonitor/environment overrides do not execute the sentinel fixture. SHA-1 and SHA-256 Git repositories are exercised. Separate Peeky processes measure identical source/policy/plan identities and different run IDs. T-001..T-008 are mapped to concrete tests in `requirements-traceability.md`. T-007 stubs only missing Docker at the availability boundary; no Docker success is inferred. Synthetic unit PASS results validate schema binding only.

**Final review correction:** the old image-prefix allowlist also admitted registry-shaped `python:5000/other`. Restricted syntax to official `python:TAG` or a full 64-hex SHA-256 reference and added four rejection cases plus a valid digest assertion. The complete test gate, lint/type checks, offline wheel build and installed CLI smoke passed again after that change. This validates identifier syntax, not a cached image's content or resolved digest. Final public-export docs, all 59 manifest hashes and all 11 packaged source-module bytes were verified; `git diff --check` passed.

**Docs updated:** README/contributor flow, source-capture contract, architecture, runner security, evidence schema, assumptions A-12/A-13, ADR-010, phase tracker, test plan, requirements mapping, repository analysis and this ledger. CI core selection includes the genuine Git integration. Public file manifest refreshed for the added source/tests/docs.

**Known limits:** both Docker tests remain owner-deferred and were not run here. Real container isolation, image digest enforcement, bounded streaming/redaction, timeout cleanup, authenticated execution evidence and durable intermediate/crash journaling remain Phase 2/later work. The low-level runner retains its Path-based fixture interface; only CLI capture/mount flow was changed. File permissions/integrity checks do not defend against a hostile concurrent host owner. Known credential filename checks are not a complete secret scan. JSON is unsigned and cannot independently prove execution. No models, repair loop, benchmark or release is claimed.

**Phase gate:** Phase 1 VERIFIED locally for FS-001/002 pre-execution contracts and T-001..T-008, plus real Git integration and package/docs gates. This is not a real Docker/product PASS and does not promote Phase 2.

**Next task:** Phase 2 runner boundary and evidence hardening, followed by genuine Docker T-009..T-017 once the daemon is available. Do not begin models/repair or release until prerequisite gates pass.
