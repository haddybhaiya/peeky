# Test plan and exact acceptance scenarios

**Levels:** unit (controller/data checks with temporary files and synthetic Git repositories), smoke (CLI/package), integration (real independent-process Git capture or Docker), live (opt-in model), e2e (full clean-run and agent benchmark). Real integration must not be faked with monkeypatching. CI covers unit/smoke, `test_source_capture.py` and a separate Docker job; live tests remain opt-in. Git fixture commits are synthetic temporary repositories, never the workspace repository.

| ID | Test/claim | Phase | Evidence |
|---|---|---|---|
| T-001 | Unannotated README blocks ignored | 1 | parser unit |
| T-002 | Annotated one-line commands extract with line number | 1 | parser unit |
| T-003 | Malformed/unterminated block blocked | 1 | parser unit |
| T-004 | Pipelining, substitution, redirection rejected | 1 | policy unit |
| T-005 | Wrong target path/symlink README rejected | 1 | parser/source unit |
| T-006 | No `--approve` means zero target execution | 1 | CLI smoke |
| T-007 | No Docker does not fall back to host | 1 | mock + inspect code |
| T-008 | Source revision/hash recorded, mutation invalidates passport | 1 | evidence unit |
| T-009 | Good annotated command PASS in real Docker | 2 | Docker integration |
| T-010 | Bad deterministic command FAIL in real Docker | 2 | Docker integration |
| T-011 | Missing image/daemon => INCONCLUSIVE | 2 | Docker integration |
| T-012 | Timeout reported, cannot become PASS | 2 | Docker integration |
| T-013 | Read-only source and no egress enforced | 2 | integration/adversarial |
| T-014 | Resource budget/prohibited flags verified | 2 | runner arg contract |
| T-015 | Secrets excluded and logs redacted | 2 | adversarial |
| T-016 | Digest identity and source SHA available | 2 | evidence |
| T-017 | Skipped steps cannot yield PASS | 2 | verdict unit |
| T-018 | Provider parse accepts only typed patch proposal | 3 | contract mock |
| T-019 | Provider missing/unauthorized not fatal to core audit | 3 | contract |
| T-020 | Diff only touches permitted documentation | 3 | adversarial |
| T-021 | Test weakening/evidence rewriting rejected | 3 | adversarial |
| T-022 | Clean recheck under matching environment required | 3 | e2e |
| T-023 | One actual open model diagnosis on fixture | 3 | live opt-in |
| T-024 | Attempt budget prevents endless repair loop | 3 | unit |
| T-025 | Malicious README prompt never modifies policy | 3 | adversarial |
| T-026 | Passport refuses non-PASS or missing evidence | 4 | unit |
| T-027 | Passport refuses changed README/source | 4 | unit |
| T-028 | Existing AGENTS.md not overwritten | 4 | unit |
| T-029 | Cold-start agent can use tools; not fabricated answer | 4 | live e2e |
| T-030 | Same model, source SHA, task, budgets | 4 | benchmark contract |
| T-031 | Benchmark records failures/cost/time, not just successes | 4 | report contract |
| T-032 | Baseline and treatment judge identical oracle | 4 | e2e |
| T-033 | JSON/Markdown describe incomplete verification honestly | 5 | report snapshot |
| T-034 | Wheel CLI runs in clean venv | 5 | wheel smoke |
| T-035 | CI has no credentials in deterministic gates | 5 | inspection |
| T-036 | Full README docs and source refs present | 5 | docs checker |
| T-037 | Demo artifacts show only actually executed cases | 5 | human review |

## Fixed fixtures

- `good_repo` declares one `python smoke.py` command that prints `HELLO_FROM_GOOD_FIXTURE`; target execution requires the separate real Docker gate.
- `bad_repo` has deliberately wrong module, must FAIL.
- `no_optin_repo` must produce no steps, INCONCLUSIVE; never auto-infer commands.

## CI gates and counts

Core job: `uv sync --locked`; Ruff lint/format, mypy, unit/smoke plus real Git capture integration, public docs and installed-wheel smoke. Docker job separately prefetches the reviewed digest, explicitly selects Docker tests, then retains good/bad/no-op validator evidence. Plain pytest excludes docker/live; explicitly requested Docker cases fail rather than skip unavailable prerequisites. The final local `uv run --locked pytest -m 'not live' -q` completed 118 tests with 0 skips (103 controller/source cases plus 15 Docker/infrastructure cases). Phase 2 core/sandbox CI was subsequently observed successful before Phase 3; no Phase 3 CI is claimed. T-007 is still a capability-boundary unit stub; Phase 2 also performs real daemon/cache/target tests. Synthetic signed PASS records in passport units test consistency only, not real execution. See requirements mapping and work review. **No coverage percentage, general reproducibility or CI pass is inferred from these counts.**


## Phase 3 actual gates

The final deterministic gate passed 169 tests with 1 live deselected and 0 skips in 173.18s (earlier retry gate: 168 passed in 172.21s). This includes the retained-request provenance and Google framing regressions; exact commands are in work review. These deterministic gates include 17 real Docker cases, two of which use explicitly mocked models for repair comparisons. Offline tests require no model key.

T-023 subsequently passed against the genuine Gemma retained response and its authenticated linked revalidation: 1 passed in 3.47s, with no new network request. The owner approved the exact proposal digest, then actual fresh original FAIL/candidate PASS with `PEEKY_RECHECK_OK` produced VERIFIED comparison evidence. Failed/transient/rejected attempts remain retained. Missing free-tier usage/cost alone is now nonfatal by owner instruction; strict JSON/schema/allowlist/approval/oracle checks remain required.


## T-014 regression after the Phase 3 push

The observed remote sandbox run failed 1 case (16 passed, 1 deselected); core passed. The original OOM case passed locally before edits, establishing a cross-environment/intermittent observation problem rather than a deterministic local failure. Add strict delayed-OOM/deadline/bounded-state unit histories and two real non-OOM 137 cases. The original memory-limit assertion is not relaxed; it now also requires OOMKilled=true and prints full redacted result JSON on failure. Initial focused regression run found Linux PID 1 ignores a self-sent SIGKILL; the corrected fixture verifies SIGKILL on a child and propagates its actual wait status. Focused runner/Docker gate then passed 29 cases in 72.37s; a subsequent deadline unit is included in the final full gate. No host target execution, untrusted installation or remote CI success is inferred.

Final local T-014 correction gate: 178 passed, 1 live deselected, 0 skipped in 172.88s; lint/type/docs and installed-wheel smoke passed. Corrected remote CI is awaiting publication/rerun, not claimed green.

## Phase 4 acceptance gates

T-026..T-032 map to concrete passport, native-tool, controls, real paired Docker and report-integrity tests in `requirements-traceability.md`. The Docker pair uses explicitly mocked provider responses but real independent containers and the same frozen oracle. Genuine live attempts are separately retained: two pairs/four attempts, three HTTP 500 responses, one native-tool Docker PASS, zero comparable pairs. Missing provider usage/billing remains unknown. No key is required for mocks. Phase 3 corrected remote CI runs 40504283043 and 40504277107 succeeded before this phase; no Phase 4 remote CI success is claimed. Final deterministic counts are recorded in work review; actual live comparative gate remains INCONCLUSIVE.

Final Phase 4 deterministic gate: **201 passed, 1 live deselected, 0 skips in 243.09s**. Ruff lint/format, mypy (41 files), required docs (18), installed wheel, public export and 84 manifest hashes passed. This does not promote the separate live comparative result: 0/2 comparable pairs, INCONCLUSIVE.

## Phase 5 local review

T-033 is covered by `tests/unit/test_reports.py`; T-034..T-036 use installed-wheel smoke, CI inspection, docs and manifest/package checks. T-037 requires the actual video; prepared captions/HTML are not a recording. Fresh good/bad/no-opt-in fixture audit evidence is retained under `.peeky/phase5-validation/fixtures`. Summary JSON/Markdown and private evidence archive are under that same root. Final observed gate counts are in work review. No model calls are part of Phase 5 validation.

## Owner-confirmed delivery completion

The owner confirms the actual demo video and OpenFire submission are complete. T-037 delivery status is updated from pending recording to owner-reported completion; the controller has not independently checked final recording duration/content or a submission receipt. Existing local technical gate remains 204 passed, 1 live deselected, 0 skips. No new model run, Docker run, benchmark improvement, second-machine reproduction or remote CI result is inferred from this documentation update.
