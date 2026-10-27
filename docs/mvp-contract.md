# OpenFire submission MVP contract (scope freeze)

**Deadline-driven design:** one solo builder and approximately one day. This file describes the desired submission, **not work already completed**. Implementation phase status is authoritative in `docs/phase.md`.

## Supported case

Python 3.12-compatible local Git repository; one README.md; explicitly annotated one-line, shell-free smoke commands; Linux Docker runner; isolated no-network execution; one optional open-weight coding-model provider; one controlled agent cold-start benchmark fixture. No arbitrary installation shell, Nix/conda, GPU dependencies, full project discovery or real-world hosted jobs.

## Product acceptance gates

- FS-001: `peeky inspect` proposes executable steps without executing them.
- FS-002: Docker unavailable / non-approved commands are blocked with no host fallback.
- FS-003: Run execution captures exact command, repo commit/digest, image digest, stdout/stderr, timeout, exit code, and step outcome (not only model opinion).
- FS-004: Deterministic good fixture passes, bad setup fixture fails, unsupported fixture stays INCONCLUSIVE; CI exercises Docker path.
- FS-005: Open-weight coding model analyzes failure **only when consented**, returning structured docs-only candidate; mocks pass by default; real demonstration requires actual provider trace.
- FS-006: Candidate patch is reviewed, has bounded paths, preserves executable assertions, then is retested from a clean environment under matching policy/image.
- FS-007: Only clean verified PASS may create unmerged, version-bound AGENTS.generated.md containing tested commands and limitations.
- FS-008: Fresh **tool-using** coding agent attempts a fixed onboarding task under original docs vs generated guidance, with same model, repo SHA, environment, task, time/step/token budgets, and independent mechanical success oracle. Record failures, success and cost; do not claim improvement without data.
- FS-009: Export honest JSON + readable Markdown summary with provenance and explicit unknowns, avoiding leaked secrets.
- FS-010: README, architecture, tests, setup, project limitations, license, demo/benchmark evidence published in repo; short captioned 1–2 minute video possible without voiceover.

## Explicit out-of-scope until after hackathon

Arbitrary GitHub remote execution, authenticated GitHub writes, auto-opening PRs, hosted queues, arbitrary languages, generalized package installers, dependency prefetching with uncontrolled network, automatic merge, full workflow synthesis, agent swarm, external benchmark claims. Do not quietly expand to these.

## Honest statuses

`PASS` means the exact listed offline commands passed under recorded run conditions. `FAIL` means at least one permitted check returned a nonzero error with sufficient observation. `INCONCLUSIVE` means missing setup steps, environment failure, timeout, skipped check, model uncertainty or unsuitable oracle. `BLOCKED` is a policy gate before execution. No "repository reproducible" universal claim from one smoke command.

## Submission gate

Demo 90–120 seconds: baseline failure → agent diagnosis/proposed patch → clean rerun → generated passport → cold-start side-by-side results, provided they were **actually run**. Public source repository, 1–2 minute X demo, submission form (per Town Hall). Reconfirm final official timing with event organizer; the public Luma page lists build ending Tue Oct 27 at 8 PM IST and form closing at 10 PM IST, so **do not rely on an assumed 8-hour submission window**.
