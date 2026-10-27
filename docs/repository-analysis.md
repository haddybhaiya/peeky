# Peeky repository analysis

Reviewed 2026-10-27. This describes the working tree, including its untracked scaffold files; it does not certify a committed release or CI run. The active prerequisite is Phase 0. Later phases remain planned or partial.

## Purpose and current flow

Peeky is a dependency-free Python CLI for reviewing explicitly annotated onboarding commands and running approved smoke checks inside offline Docker containers. Its intended extension is model-assisted documentation repair followed by clean verification and a controlled agent onboarding comparison.

The current flow is `inspect -> policy validation -> approved audit -> JSON evidence -> candidate passport`. Only the scaffold components below exist; the architecture diagram also includes future components.

| Component | Current behavior |
|---|---|
| `src/peeky/cli.py` | argparse commands: inspect, doctor, audit and passport; approval gate before audit |
| `parser.py` | Reads a bounded, non-symlink README; extracts up to 12 annotated commands with line numbers |
| `policy.py` | Restricts executable names, arguments, shell syntax and Python image identifiers |
| `runner.py` | Invokes Docker without a host shell; offline, non-root, read-only filesystem/source and resource limits |
| `evidence.py` | Reduces step outcomes and writes uniquely named JSON records |
| `passport.py` | Produces candidate onboarding text after basic evidence and README checks |
| `tests/` | Parser, policy, verdict and passport units; CLI smoke; two Docker fixture cases |
| `.github/workflows/ci.yml` | Declares core and Docker jobs; their presence is not evidence that CI passed |

There is no immutable source capture, persistent run state machine, model provider, repair engine, clean-retest controller, agent benchmark harness or Markdown report exporter. `peeky.example.toml` and model environment variables are templates and are not consumed by the CLI.

## Findings, in priority order

### 1. Passport evidence is not authenticated or bound to the full source

`passport.py:make_passport` trusts caller-supplied `verdict` and per-result `outcome` fields. It does not bind result IDs/commands/exit codes to the proposed steps, validate the recorded commands through policy, or verify a trusted run provenance. It hashes only README, so changing a Python source file does not invalidate the passport. Its module docstring's claim of authenticated evidence is stronger than the implementation.

A bounded controller-only probe created synthetic PASS JSON and obtained a passport for an unexecuted command; modifying a sibling source file still allowed that passport. No target command was executed. This is a demonstrated gap against FS-007, T-008/T-027 and INV-08, not proof of verified onboarding.

### 2. Runner uses mutable host source and mutable image tags

`runner.py:execute` mounts the live resolved repository directory. There is no exported immutable snapshot, Git revision/dirty-tree check, source-file allowlist or credential exclusion. A read-only mount prevents container writes but does not freeze host-side changes or exclude files already present beneath that directory. Image policy allows mutable Python tags; neither the runner nor CI verifies an immutable image digest. Evidence records a path, README hash and requested image string, not a full source/image identity.

These gaps are prerequisites for credible comparisons under FS-003, INV-04/05/07 and Phases 1-2. Do not enable public repository scans on this scaffold.

### 3. Output limits and timeout cleanup need stronger enforcement

`runner.py:execute` uses `capture_output=True` and slices stdout/stderr after the process returns. Stored excerpts are bounded, but host capture memory is not. Logs are not redacted. The timeout handler records TIMEOUT but has no named-container/CID cleanup path; terminating the Docker client alone does not establish that container execution has stopped. These are code-review findings; resource exhaustion and persistent-container behavior were not exercised.

### 4. Verdict reduction loses information and trusts outcome labels

`evidence.py:verdict` checks result count before failure outcomes. Because CLI audit stops at the first non-PASS result, a failing first step in a two-step plan becomes overall INCONCLUSIVE. The explicit observed failure should remain visible alongside incomplete coverage. Matching result count also suffices to accept unrelated IDs/commands and a nonzero exit code if the supplied outcome says PASS.

Pure controller probes observed INCONCLUSIVE for a failed first step with one remaining step, and PASS for an unrelated result carrying exit code 7 and an outcome label of PASS. These probes did not run target code. FS-003/009 need mechanically consistent result validation and explicit coverage semantics.

### 5. Docker tests can skip instead of enforcing the integration gate

Both tests in `tests/integration/test_docker.py` call `pytest.skip` when the daemon is unavailable. CI runs those same tests, so a successful pytest exit does not by itself prove that the Docker gate executed. CI also pulls a mutable image tag. Required integration should distinguish a deliberately optional local skip from a failed prerequisite on the integration worker. Current coverage does not implement all T-009..T-017 scenarios.

### 6. Phase 0 validation is still incomplete

The existing 19 unit/smoke cases pass after the rename, and an offline wheel builds. Local Ruff 0.16.3 reports two import-spacing errors and 13 files requiring formatting. These findings correspond to scaffold formatting already visible before the rename; no behavior or assertions were changed to conceal them. They remain unfixed because this task is a rename and review.

There is no `uv.lock`. Local tooling differs from the pinned development group, so local results do not verify a reproducible pinned environment or Python 3.12. Exact completed commands and integration outcomes are recorded in `work_review.md`.

## Rename scope

The project display name is Peeky. The distribution, import and executable are `peeky`; package source is `src/peeky`; opted-in fences use `bash peeky`; local run storage defaults to `.peeky/runs`; example configuration is `peeky.example.toml`; proposed model variables use `PEEKY_`. Tests, fixture annotations, CI labels, documentation and manifest paths follow the new identity. No legacy aliases are provided. FS and T acceptance IDs remain stable. PyPI availability was not checked and nothing was published.

## Next work in phase order

Finish Phase 0: resolve formatting/import defects and validate the pinned development environment, retaining the passing wheel installation smoke and recording the required checks. Then implement Phase 1 immutable source identity and behavior tests for T-001..T-008. Phase 2 should address runner capture/cleanup, digest enforcement, redaction, coverage/verdict semantics and genuine Docker gates before model repair or benchmark work starts.

No security fixes, model calls, benchmark results, Git staging/commits or remote writes are part of this review.
