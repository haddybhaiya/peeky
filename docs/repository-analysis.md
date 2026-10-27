# Peeky repository analysis

Updated 2026-10-27 after Phase 2 implementation on base `f5ac0c8`. Phases 0/1 passed their local foundation/Git gates. Phase 2 now passes its local real Docker gate; remote CI confirmation remains pending. No models, repair loop, benchmark, release or GitHub write was implemented. Historical findings and exact earlier checks remain in `work_review.md`.

## Current product flow

`inspect -> committed source capture -> policy/approval -> one offline Docker smoke command -> observed State/logs/cleanup -> authenticated JSON -> candidate passport`.

| Component | Current behavior |
|---|---|
| `cli.py`, `parser.py` | Read bounded annotated README data, propose steps without execution, require approval, reject unsupported no-op/multi-step audits with retained evidence |
| `sources.py`, `domain.py` | Verify committed Git bytes/index/scope, deny unsafe paths/types/credentials, create bounded read-only snapshots, record source/policy/plan/state identity |
| `hosttools.py` | Resolve installed Git/Docker while excluding cwd, relative paths and target-tree tools |
| `images.py`, `policy.py` | Permit only the reviewed cached official Python digest for execution; command/argument/timeout budgets remain controller-owned |
| `runner.py` | Create/inspect/start/state/cleanup lifecycle, snapshot-only inputs, effective isolation/environment checks, real exit classification and bounded streams |
| `redaction.py`, `provenance.py`, `evidence.py` | Redact before persistence, retain full bounded transcripts/hashes, authenticate under a private per-user key, atomically/exclusively finalize records |
| `passport.py` | Require authenticated schema 1.2, current clean source/commit/policy/plan, legal finalized state and matching complete runtime observations |
| `validate_phase2.py` | Run reviewed good/bad/no-op fixtures and retain authenticated redacted evidence with an index |
| CI/tests | Locked core/Git/package gate plus digest-prefetched Docker gate and validator; workflow edits are not observed CI success |

`peeky.example.toml` and model environment variables remain templates; no arbitrary target dependency installation, online target setup or stateful multi-step bootstrap is supported.

## Original findings addressed

1. **README-only passport binding:** now complete selected-source/commit/policy/plan binding, result consistency and local controller authentication. Schema 1.0/1.1 guidance must be regenerated. Local HMAC is not third-party attestation or proof against key-owner compromise.
2. **Mutable live mounts and tag-based execution:** runner now requires a controller-created snapshot, matches the exact captured step, verifies cached reviewed image identity and inspects the effective single read-only source mount before start. Mutable/unreviewed executable image inputs are denied.
3. **Unbounded capture and client-only timeout:** memory-bounded stream drainers, redaction, output budget interruption, owned forced container removal and follow-up absence checks are implemented. A still-running timeout records no target exit code. Hard controller death/daemon loss remains outside normal-return guarantees.
4. **Unrelated/nonzero PASS fields and lost failures:** ordered IDs/commands/exit consistency and complete runtime observations are checked; valid observed failure remains FAIL despite later incomplete coverage. Unsupported multi-step stages never execute. Coverage counts observed slots rather than implying success.
5. **Skipped Docker gate:** selected Docker tests now fail missing prerequisites. The real local gate ran; CI prefetches the pinned digest rather than a mutable tag. No CI execution result is claimed here.
6. **Foundation checks:** locked dependencies, lint/format/types, docs, wheel and installed CLI smoke are enforced. The final deterministic suite passed 118 cases with no skips, including 15 real Docker/infrastructure cases; exact results are in the ledger.

Final review also moved the authentication key out of scanned working directories, excluded tracked controller state/keys, prevented host-tool spoofing and cleared/verified Docker proxy/environment defaults before target start.

## Remaining limits and next work

Docker shares the host kernel; host operator/daemon/tool installations are trusted. Host-owner source races, daemon/kernel compromise and hard controller termination are not defeated by these controls. Pattern-based redaction and credential filename checks are incomplete secret discovery. Atomic records require local hard-link support; durable intermediate/crash recovery is not implemented. The private per-user HMAC key must remain outside shared evidence and target access.

The observed local environment is Windows/Python 3.13.7 controlling Linux Docker Engine 29.1.3, with a pinned official Python image. Remote CI, a Python 3.12 controller, other hosts/platforms and unknown hostile targets remain unverified. Only the reviewed bounded fixtures ran; no broad reproducibility or causal benchmark claim follows from their success.

Next confirm the updated CI gate after an authorized push, then proceed to separately authorized Phase 3 provider/docs-only repair and frozen clean recheck. Phase 4 agent trials and Phase 5 export/demo/release remain later work. No workspace staging, commit or remote write was performed by this task; Git commits created by tests are synthetic temporary fixtures only.


## Phase 3 update (2026-10-27)

Base `57201b1` includes merged PR #4; its prerequisite Python 3.12 core and real Docker sandbox CI jobs were observed successful. Phase 3 now has one opt-in BYOK Gemma adapter, strict structured output, command-only README diff, authenticated exact-artifact approval, persistent attempt claims and fresh original/candidate Docker rechecks. Deterministic validation passed 163 cases (1 live deselected, no skips), including two real repair Docker cases with explicitly mocked model output. No target code executes on the host and no target worktree/index is changed.

The genuine live gate is BLOCKED: separately authorized requests returned HTTP 500 and connection failure, preserving two authenticated INCONCLUSIVE records. No live proposal or usage/cost was returned, and no real-model human-approved repair occurred. T-023 fails accordingly. Next resolve the provider/transport failure under renewed authorization, obtain one real structured proposal and review it before a matching fresh recheck. No Phase 3 GitHub writes, commits, push, benchmarks or release were performed.


### Phase 3 blocker resolved under renewed authorization

The owner authorized a bounded retry batch and made missing free-model usage/cost nonfatal. HTTP 503 explicitly reported temporary high demand; the next call returned a genuine Gemma 4 31B completion; the last retry timed out. The returned completion used Google's flagged thought framing. The adapter now requests minimal thinking and handles only that exact provider frame before strict JSON validation. Its retained original response was revalidated without another API call or altered request provenance. T-023 passed, then the owner approved the exact diff/digest and a fresh original FAIL/candidate PASS marker recheck was VERIFIED. Local Phase 3 gates pass; remote Phase 3 CI remains unobserved. No Phase 3 GitHub writes or commits occurred.
