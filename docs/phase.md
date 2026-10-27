# Phased implementation tracker — STOP AT OPENFIRE MVP

Statuses: `SCAFFOLD_DONE` means files exist and local tests may pass, **not** end-to-end product verified; `PLANNED` means implementation/tests are still required; `VERIFIED` demands the exact listed gate evidence.

| Phase | Purpose | Status | Required gate |
|---|---|---|---|
| 0 | Contract, repo scaffold, CLI, CI, fixtures, docs | SCAFFOLD_DONE (subject to validation) | CLI help/inspect + unit tests + wheel smoke + docs check |
| 1 | Immutable source snapshot, run policy, deterministic evidence | PLANNED | FS-001/002 + T-001..T-008 |
| 2 | Real Docker smoke audit across good/bad/blocked fixtures | PARTIAL (scaffold runner exists) | FS-003/004 + T-009..T-017 on clean runner |
| 3 | Open coding-model diagnosis + docs-only repair + clean retest | PLANNED | FS-005/006 + T-018..T-025 |
| 4 | Agent onboarding passport + matched cold-start benchmark | PARTIAL (passport scaffold exists) | FS-007/008 + T-026..T-032 |
| 5 | Polish, evidence bundle, README, demo, submission review | PLANNED | FS-009/010 + T-033..T-037 |

**Active work on 2026-10-27:** Phase 0 identity rename and repository review. The package/CLI is now `peeky`; FS acceptance IDs remain unchanged. Unit/smoke tests, type checks, documentation presence, offline wheel build and installed-wheel smoke passed locally. The Phase 0 gate remains incomplete: Ruff reports import/formatting defects, and pinned-environment validation is outstanding. Both Docker integration tests skipped because the daemon was unavailable. See `docs/work_review.md` for exact checks and `docs/repository-analysis.md` for implementation gaps. Do not advance to Phase 1 until prerequisite checks pass.

**DO NOT schedule Phase 6+ as part of the hackathon.** Remote public GitHub write automation, language expansion, marketplace, vector memory, recurring hosted agents are separately deferred.

## Phase 0 — Package and CI foundations

Build: `pyproject.toml` (same Hatchling/strict-dev-group pattern as Recheck), `AGENTS.md`, CLI commands, fixtures, docs and CI. Gate: `uv sync`, lint/type, unit/smoke, doc check, wheel creation and installed wheel CLI smoke. No model costs. Record exact validation output in work review.

## Phase 1 — Trustworthy plans and source identity

Build: `src/peeky/sources.py`, `domain.py`, repository fingerprint, immutable source export and input/command policy; reject symlinks, dirty inconsistent commits and out-of-tree paths. Gate: two independent snapshots of same commit hash identically, symlink/path denial tests, inspect does not execute, limits enforced.

## Phase 2 — Docker execution and evidence

Build: hardened `runner.py` with image digest checks, stage semantics, accurate `BLOCKED` vs `INCONCLUSIVE` vs `FAIL`; CLI `audit` supports multiple steps in controlled shared workspace or explicit one-step contract; collect signed/provenanced logs, independent verdict. Gate: passing/broken fixture, missing image/daemon, failure/timeout and proof of no host fallback. No untrusted public repo by default.

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
