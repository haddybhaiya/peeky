# Peeky repository analysis

Reviewed 2026-10-27; updated after Phase 1 implementation on top of `d9dbd68`. Phases 0 and 1 are locally verified within their foundation/controller/Git scope. This does not certify a release, CI run or Docker execution. Phase 2 is next; later phases remain planned or partial.

## Purpose and current flow

Peeky is a dependency-free Python CLI for reviewing explicitly annotated onboarding commands and running approved smoke checks inside offline Docker containers. Its intended extension is model-assisted documentation repair followed by clean verification and a controlled agent onboarding comparison.

The current flow is `inspect -> policy validation -> approved audit -> JSON evidence -> candidate passport`. Only the scaffold components below exist; the architecture diagram also includes future components.

| Component | Current behavior |
|---|---|
| `src/peeky/cli.py` | argparse commands: inspect, doctor, audit and passport; approval gate before audit |
| `parser.py` | Reads a bounded, non-symlink README; extracts up to 12 annotated commands with line numbers |
| `sources.py`, `domain.py` | Verify committed Git bytes, selected-scope cleanliness, safe bounded temporary exports and source/policy/plan/state identity |
| `policy.py` | Restricts executable names, arguments, shell syntax and Python image identifiers |
| `runner.py` | Invokes Docker without a host shell; offline, non-root, read-only filesystem/source and resource limits |
| `evidence.py` | Reduces step outcomes and writes uniquely named JSON records |
| `passport.py` | Produces candidate guidance after complete source/commit/policy/plan/state/result consistency checks |
| `tests/` | Parser, policy, verdict and passport units; CLI smoke; two Docker fixture cases |
| `.github/workflows/ci.yml` | Declares core and Docker jobs with locked dependency installation; their presence is not evidence that CI passed |

Immutable source capture and minimal controller transitions with terminal run history now exist. There is no durable intermediate/crash journal, model provider, repair engine, clean-retest controller, agent benchmark harness or Markdown report exporter. `peeky.example.toml` and model environment variables remain templates and are not consumed by the CLI.

## Findings, in priority order

### 1. Source binding implemented; evidence authenticity remains open

The initial scaffold trusted caller-supplied PASS fields and only hashed README. Phase 1 now requires schema 1.1, exact committed source and revision, controller policy/plan identity, legal finalized run history, matching README commands and mechanically consistent complete results. Source mutation and new commits invalidate guidance. The misleading authenticated-evidence docstring was replaced. Local JSON is still unsigned: a fully fabricated self-consistent record is not independent execution proof. Full FS-007 assurance remains gated on later provenance and clean-run validation.

The earlier synthetic-PASS/source-mutation probe is historical; the Phase 1 tests now reject its legacy schema, inconsistent commands/results and changed source. No target command executes in those tests, and their synthetic results are not claimed as real Docker outcomes.

### 2. CLI source exports implemented; image identity remains open

CLI audit now mounts a bounded temporary export of verified original Git bytes, with scope cleanliness and path/type/credential checks. Evidence includes a complete selected-source manifest, containing commit and policy/plan identities. The low-level runner still has its Path-based fixture interface; the full boundary needs Phase 2 integration validation. Image policy and CI still allow mutable Python tags and do not verify a resolved image digest. Read-only permissions and pre-use checks are not a security boundary against hostile concurrent host mutation.

Phase 1 closes the CLI source-identity prerequisite; image/runtime/provenance gaps still prevent credible matched execution comparisons under FS-003 and INV-04/05/07. Do not enable public repository scans on this scaffold.

### 3. Output limits and timeout cleanup need stronger enforcement

`runner.py:execute` uses `capture_output=True` and slices stdout/stderr after the process returns. Stored excerpts are bounded, but host capture memory is not. Logs are not redacted. The timeout handler records TIMEOUT but has no named-container/CID cleanup path; terminating the Docker client alone does not establish that container execution has stopped. These are code-review findings; resource exhaustion and persistent-container behavior were not exercised.

### 4. Mechanical result binding and incomplete-failure handling implemented

Phase 1 validates ordered result IDs/commands and exit-code/outcome consistency. A permitted observed failure remains FAIL when later commands were not run; incomplete coverage cannot become PASS. BLOCKED runs cannot carry execution results. Regression tests cover the previously accepted unrelated/nonzero PASS result and the lost failure outcome. Result validation establishes mechanical consistency, not execution authenticity.

The initial probe outcomes above are historical and now have opposite regression assertions. FS-003/009 still need image/log/time provenance and independent execution observations in later phases.

### 5. Docker tests can skip instead of enforcing the integration gate

Both tests in `tests/integration/test_docker.py` call `pytest.skip` when the daemon is unavailable. CI runs those same tests, so a successful pytest exit does not by itself prove that the Docker gate executed. CI also pulls a mutable image tag. Required integration should distinguish a deliberately optional local skip from a failed prerequisite on the integration worker. Current coverage does not implement all T-009..T-017 scenarios.

### 6. Phase 0 validation gaps resolved locally

The follow-up completion task installed the declared pinned development group and generated `uv.lock`. Ruff 0.16.10 fixed the two import-spacing errors and formatted 13 files; all 18 Python files now pass formatting. Ruff lint, mypy 2.4.0 and all 19 unit/smoke cases pass. AST comparison against HEAD confirmed no behavior/assertion changes in the 16 controller/test Python files. The offline wheel build and installed-module/console smoke pass outside the source checkout.

Phase 0's public-checkout docs gate checked 14 files without the ignored local prompts; Phase 1 adds the source-capture contract for 15 required files. CI uses locked dependency sync. Local validation used Python 3.13.7; Python 3.12 and remote CI remain unverified. Docker integration remains deferred to Phase 2. Source/result consistency portions of the original findings are resolved as described above; runtime and authenticity assurance remain open. Exact commands and integration limits are recorded in `work_review.md`.

## Rename scope

The project display name is Peeky. The distribution, import and executable are `peeky`; package source is `src/peeky`; opted-in fences use `bash peeky`; local run storage defaults to `.peeky/runs`; example configuration is `peeky.example.toml`; proposed model variables use `PEEKY_`. Tests, fixture annotations, CI labels, documentation and manifest paths follow the new identity. No legacy aliases are provided. FS and T acceptance IDs remain stable. PyPI availability was not checked and nothing was published.

## Next work in phase order

Phases 0 and 1 are complete locally. The Phase 1 combined gate passed 85 cases with 0 skips, including an independent-process real Git integration. Ruff lint/format, mypy, docs, locked sync, offline wheel build and isolated installed CLI smoke passed. See `work_review.md` for initial failures and exact results. Phase 2 should address runner capture/cleanup, digest enforcement, redaction and genuine Docker gates before model repair or benchmark work starts. Run the two deferred integration tests once Docker is available; do not promote Phase 2 on skipped checks.

No model calls, benchmark results, releases, workspace staging/commits or remote writes were made. Tests commit only synthetic temporary Git fixtures.
