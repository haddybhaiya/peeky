# Phased implementation tracker — STOP AT OPENFIRE MVP

Statuses: `SCAFFOLD_DONE` means files exist and local tests may pass, **not** end-to-end product verified; `PLANNED` means implementation/tests are still required; `VERIFIED` demands the exact listed gate evidence. `LOCAL_GATE_PASSED` records completed local execution while a required remote CI confirmation remains pending.

| Phase | Purpose | Status | Required gate |
|---|---|---|---|
| 0 | Contract, repo scaffold, CLI, CI, fixtures, docs | VERIFIED (local foundation gate, Python 3.13) | Locked sync + lint/format/type + CLI help/inspect + unit tests + wheel smoke + docs check |
| 1 | Immutable source snapshot, run policy, deterministic evidence | VERIFIED (local controller/Git gate) | FS-001/002 pre-execution contracts + T-001..T-008; real Docker remains Phase 2 |
| 2 | Real Docker smoke audit across good/bad/blocked fixtures | LOCAL_GATE_PASSED (remote CI pending) | FS-003/004 + T-009..T-017; observed local Docker gate, CI workflow updated but not run |
| 3 | Open coding-model diagnosis + docs-only repair + clean retest | PLANNED | FS-005/006 + T-018..T-025 |
| 4 | Agent onboarding passport + matched cold-start benchmark | PARTIAL (passport scaffold exists) | FS-007/008 + T-026..T-032 |
| 5 | Polish, evidence bundle, README, demo, submission review | PLANNED | FS-009/010 + T-033..T-037 |

**Current position on 2026-10-27:** Phase 2 is implemented and its local deterministic gate passed: 118 tests with 0 skips, including 15 genuine Docker/infrastructure integration cases. The formerly deferred Docker work was authorized and actually run. Retained fixture evidence shows good PASS, bad FAIL and no-op INCONCLUSIVE using a reviewed cached digest. Local controller: Windows/Python 3.13.7; target: Linux Docker Engine 29.1.3 and official pinned Python image. Remote CI and a Python 3.12 controller run remain unobserved. No model or release work was implemented; do not infer CI success from the updated workflow. Exact results are in `docs/work_review.md`.

**DO NOT schedule Phase 6+ as part of the hackathon.** Remote public GitHub write automation, language expansion, marketplace, vector memory, recurring hosted agents are separately deferred.

## Phase 0 — Package and CI foundations

Build: `pyproject.toml`, `uv.lock` (Hatchling/strict-dev-group pattern), `AGENTS.md`, CLI commands, fixtures, public docs and locked CI dependency setup. Gate: `uv sync --locked`, lint/format/type, unit/smoke, doc check, wheel creation and isolated installed wheel CLI smoke. Completed locally; see the Phase 0 completion entry in work review. This foundation gate does not establish target execution, model repair or benchmark success. Docker integration remains a Phase 2 gate. No model costs.

## Phase 1 — Trustworthy plans and source identity

Build: `src/peeky/sources.py`, `domain.py`, repository fingerprint, immutable source export and input/command policy; reject symlinks, dirty inconsistent commits and out-of-tree paths. Gate: two independent snapshots of same commit hash identically, symlink/path denial tests, inspect does not execute, limits enforced.

Completed locally: `uv run --locked pytest tests/unit tests/smoke tests/integration/test_source_capture.py -q` (85 passed, 0 skipped), Ruff lint/format, mypy, docs check, offline wheel build and installed CLI smoke. The integration case uses independent real Git/CLI processes, not a mocked PASS. T-007 deliberately stubs unavailable Docker at the capability boundary; it establishes no-host-fallback behavior, not real container isolation. See `docs/source-capture.md` for exact scope, CRLF conversion, budgets and unsigned-evidence limits. Phase 2 is not promoted by these results.

## Phase 2 — Docker execution and evidence

Build: hardened `runner.py` with image digest checks, stage semantics, accurate `BLOCKED` vs `INCONCLUSIVE` vs `FAIL`; CLI `audit` supports multiple steps in controlled shared workspace or explicit one-step contract; collect signed/provenanced logs, independent verdict. Gate: passing/broken fixture, missing image/daemon, failure/timeout and proof of no host fallback. No untrusted public repo by default.

Implemented the explicit one-smoke-command contract. All T-009..T-017 local cases pass against actual Docker, with snapshot-only inputs, inspected image/isolation/environment, bounded redacted transcripts, target-vs-infrastructure classification, forced owned cleanup, per-user HMAC integrity and atomic exclusive records. `uv run --locked pytest -m 'not live' -q`: 118 passed in 148.69s, 0 skipped. `scripts/validate_phase2.py` retains authenticated good/bad/no-op records. See `docs/phase2-runner.md` and requirements mapping. Remote CI confirmation is still required before claiming the full CI gate; Phase 3 is not implemented or promoted here.

## Phase 3 — Open-model repair loop

Build: one opt-in OpenAI-compatible provider using an open-weight **coding** model (e.g. Qwen2.5-Coder); structured JSON for `reason`, `assumptions`, `candidate_diff`, `confidence`, `source_refs`; patch only README under scoped allowlist; validate patch, require human approval and clean retest. Mock offline tests; **one genuine call and trace** for demo if available. Gate: can repair deliberately outdated command; cannot change target tests, verifier, evidence, or runner policy.

## Phase 4 — AI-era differentiator

Build: `AGENTS.generated.md` from verified steps; one fixed tool-using agent task "bootstrap and execute smoke test" with matched original-vs-passport trials using the **same** coding model, budgets, source SHA, runner and task; at least one controlled pair plus ideally two replications; collect steps, tokens, time, PASS, and blocked statuses; never claim generalized superiority. Gate: matched controls documented and independent oracle identifies success/failure.

## Phase 5 — Finish and demonstrate

Build: Markdown summary report, screenshot-ready terminal output, explanations, 3 fixtures, setup docs, visible known limitations, ethical logs, correct open source model attribution, submission artifact. Gate: full command suite passes on two machines if possible; `docs/work_review.md` includes exact evidence; 90–120s silent captioned screen recording shows real observed data; deadline verified.

## Suggested one-day order

00:00–02:00 source/runner gates; 02:00–06:00 end-to-end deterministic fixture; 06:00–12:00 opt-in model repair; 12:00–16:00 passport + benchmark; 16:00–19:00 tests/CI/report; 19:00–22:00 polish/demo; remaining time for review/submission. Estimate only, no promise.

## Never silently promote a phase

The official build and submission times may conflict between Town Hall and public Luma summary. Reconfirm on Discord. Stop scope growth at tested MVP, not a platform.
