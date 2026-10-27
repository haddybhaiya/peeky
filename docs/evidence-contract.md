# Evidence schema and truth policy

Schema `1.0`: `repo`, `readme_sha256`, `image`, `execution`, `steps[]`, `results[]`, `verdict`, `limitations`. `results`: `id`, `command`, `exit_code`, `stdout`, `stderr`, `outcome`, `duration_ms`. Current scaffold produces this baseline schema.

**Before submission extend:** exact git SHA/dirty state, Docker image digest, runner version and policy hash, per-step start/end UTC, reason codes and independent expected outcomes, bounded log hashes and redacted excerpts, attempt count, patch path hashes and clean-retest flag, model metadata and provider opt-in, agent A/B trial manifest, final evidence-manifest SHA-256. Export JSON and Markdown. Separate files under unique run IDs, atomic writes, no mutation after FINALIZED.

No model may edit a final evidence record, decide that failing steps "probably passed", or conceal skipped checks. `BLOCKED` before run is not equivalent to `FAIL` from the target. Clearly label unknowns, environment mismatch and flaky results.

**Success claim levels:** single-command `SMOKE_PASS`, documented setup `ONBOARDING_PASS` (all declared steps in stateful fresh env and explicit test), `AGENT_COLD_START_PASS` (independent agent executes fixed task), `GENERAL_REPRODUCIBLE` never claimed in MVP.
