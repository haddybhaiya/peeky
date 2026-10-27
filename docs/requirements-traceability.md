# Requirements ↔ implementation ↔ tests

| Requirement | Core source | Tests | Completion |
|---|---|---|---|
| FS-001 | parser.py, sources.py, domain.py, cli.py | T-001..T-003 | Phase 1 local inspect/parser gates verified; no target execution |
| FS-002 | policy.py, sources.py, hosttools.py, runner.py, cli.py | T-004..T-007,T-011,T-013 | local pre-execution/no-fallback and real isolation cases passed |
| FS-003 | evidence.py, provenance.py, redaction.py, runner.py, sources.py | T-008,T-014..T-016 | local source/image/policy/time/log/cleanup provenance and HMAC integrity passed; no public attestation claim |
| FS-004 | runner.py, fixtures, validate_phase2.py | T-009..T-017 | local real Docker gate and observed remote core/sandbox jobs passed (Actions 40493116591) |
| FS-005 | providers/openai_compatible.py, cli.py | T-018,T-019,T-023 | BYOK Gemma, strict schema and genuine retained-response T-023 passed; Google frame normalization and preserved request provenance documented |
| FS-006 | repair.py, runner.py | T-020..T-025 | strict README diff/approval gates and real fresh Docker tests passed; genuine Gemma proposal explicitly approved by owner, then matching fresh recheck VERIFIED |
| FS-007 | passport.py, sources.py, evidence.py, provenance.py | T-008,T-015,T-016,T-026..T-028 | exact source/policy/plan/guidance/evidence bytes/run/image/container-state binding tested; local HMAC only |
| FS-008 | benchmark.py, cli.py, validate_phase4.py | T-029..T-032 | native tools and fresh Docker protocol implemented; genuine paired attempts retained; comparative live result INCONCLUSIVE (0/2 comparable pairs) |
| FS-009 | reports.py, evidence.py, cli.py | T-033 | authenticated JSON/Markdown summary implemented; incomplete PASS downgraded, unknowns and negative denominators retained |
| FS-010 | docs/, scripts/ | T-034..T-037 | local package/setup/review passed; demo video and submission completed per owner confirmation; final recording not independently inspected |

A requirement is not VERIFIED because code exists; record exact test outcome in work review.

## Phase 1 acceptance evidence

The combined local gate completed 85 tests with 0 skips (84 unit/smoke plus one real independent-process Git integration). These are controller/source checks, not a Docker/product PASS. Exact commands and initial failures are in `work_review.md`.

| ID | Demonstrated behavior | Tests |
|---|---|---|
| T-001 | Unannotated blocks and nested examples ignored | `test_parser.py::test_explicit_fence_only`, `test_T001_nested_fence_examples_are_not_instructions` |
| T-002 | Annotated command and original line retained; inspect never runs target | `test_explicit_fence_only`, `test_cli.py::test_T001_T002_inspect_never_executes_target` |
| T-003 | Unterminated/malformed annotations and parser budgets rejected | `test_unterminated_fence_rejected`, `test_T003_malformed_annotations_rejected`, `test_parser_limits_enforced` |
| T-004 | Shell composition rejected before Docker; image namespace/digest syntax fails closed | `test_policy.py::test_dangerous_commands_rejected`, `test_T004_image_namespace_and_digest_syntax_fail_closed`, `test_cli.py::test_T004_rejected_command_never_reaches_docker` |
| T-005 | Git symlink/submodule modes, real Windows junction, traversal/malicious tree paths, dirty/index/untracked source rejected | `test_sources.py::test_T005_*`, case-collision/secret/limit tests |
| T-006 | Missing approval performs no source capture or execution | `test_cli.py::test_T006_no_approval_never_reads_or_executes_source` |
| T-007 | Missing Docker CLI yields BLOCKED/INCONCLUSIVE evidence with no execution results or host fallback | `test_cli.py::test_T007_missing_docker_records_blocked_without_host_fallback` (Docker availability boundary stub; actual Git capture) |
| T-008 | Two exports hash identically; evidence records source/policy; source or commit changes invalidate passports | `test_sources.py::test_T008_two_independent_snapshots_match_commit_and_bytes`, `test_evidence.py::test_T008_report_binds_run_source_and_policy`, `test_passport.py::test_T008_*`, `test_source_capture.py::test_two_processes_measure_identical_source_and_policy` |

## Phase 2 acceptance evidence

The full local deterministic command `uv run --locked pytest -m 'not live' -q` passed 118 cases with 0 skips, including 15 selected real Docker/infrastructure cases. Missing prerequisites fail the requested Docker gate instead of skipping it. Unit fixtures remain explicitly synthetic; actual Docker cases and retained signed records establish local execution. No remote CI result is claimed.

| ID | Demonstrated behavior | Concrete tests in `tests/integration/test_docker.py` unless noted |
|---|---|---|
| T-009 | Good committed fixture exits zero and emits its marker; owned container removed | `test_T009_real_good_fixture` |
| T-010 | Bad fixture fails; actual target exits 125/126/127 remain FAIL | `test_T010_real_bad_fixture`, `test_T010_target_reserved_exit_codes_are_failures` |
| T-011 | Real missing-cache query, unavailable endpoint and missing executable are infrastructure; no target host fallback | `test_T011_real_missing_image_is_infrastructure`, `test_T011_unreachable_daemon_never_executes`, `test_T011_missing_executable_is_not_target_failure` |
| T-012 | Sleeping target hits deadline, unobserved exit stays absent, owned container removed | `test_T012_timeout_kills_and_removes_container` |
| T-013 | Real source/root writes fail, network connection fails, UID/capabilities/no-new-privileges and env isolation hold | `test_T013_T014_real_filesystem_network_identity_and_kernel_budgets`; unit live/forged snapshot and host-tool denial tests |
| T-014 | Actual cgroup RAM/PID/CPU values and real OOM classification; prohibited flags/mounts and unexpected env denied | `test_T013_T014_*`, `test_T014_real_memory_budget_is_inconclusive`; unit runner/environment contracts |
| T-015 | Synthetic secrets redacted across stream reads; long retained logs preserved; output flood stopped and cleaned up; record tampering rejected | `test_T015_T016_full_redacted_logs_and_authenticated_provenance`, `test_T015_log_budget_stops_flood_and_removes_container`; redaction/HMAC/atomic-file units |
| T-016 | Actual reviewed RepoDigest/image ID, source/policy, timestamps, log hashes and cleanup recorded under local HMAC | `test_T015_T016_*`; mutable/unreviewed-image policy rejection units |
| T-017 | No-op and multi-step plans preserve zero-execution INCONCLUSIVE records; incomplete/timeout/blocked cannot pass | `test_T017_noop_fixture_preserves_inconclusive_evidence`, `test_T017_multiple_steps_block_before_execution`; verdict regression units |

The missing-image integration queries an intentionally absent digest through the metadata-only cache inspector; execution still rejects unreviewed digests before Docker. It does not delete the shared reviewed image to simulate a cache miss. The standalone validator retains original redacted good/bad/no-op JSON with verified local authentication and expected outcomes.

## Phase 3 acceptance evidence

The deterministic gate completed 163 tests, 1 live test deselected, 0 skips. The additional two real Docker repair cases exercise actual containers; their model responses are explicitly mocked. They establish no genuine provider success. No Phase 3 CI run or human approval is inferred from these results.

| ID | Concrete checks | Evidence boundary |
|---|---|---|
| T-018 | `test_providers.py::test_T018_*`, incomplete provider data cases | Strict typed JSON; authority/duplicate/type/budget/truncation/model mismatch rejected |
| T-019 | `test_T019_*` | Consent before disclosure; explicit BYOK config; missing credentials leave core inspect functional; endpoint/model fail closed |
| T-020 | `test_repair.py::test_T020_*` | Exact-context README-only command correction; traversal/renames/other files rejected |
| T-021 | `test_T020_T021_all_other_paths_rejected`, `test_T021_*` | Tests/evidence/config paths and assertion-bypassing or extra commands cannot be changed |
| T-022 | `test_repair_docker.py::test_T022_real_fresh_recheck_requires_frozen_oracle` (2 cases); candidate/source/approval units | Real fresh baseline FAIL/candidate PASS, equal image ID, different containers, unchanged code; missing marker remains INCONCLUSIVE; changed revision invalidates approval |
| T-023 | `scripts/validate_phase3.py --live`; `tests/live/test_gemma.py` | Separately authorized actual Gemma trace with checkpoint/version/usage/cost; provider errors fail the gate, never skips |
| T-024 | `test_T024_persistent_reservation_survives_process_restart`; real diagnosis/recheck replay assertions | Exclusive persistent claims prevent retries/repair loops; explicit new operator authorization required for a separate attempt |
| T-025 | `test_T025_*`; model authority-field rejection cases | Injected README/model content stays data; frozen oracle/policy and permissions remain controller-owned |

Updated T-023: the owner authorized further retries. A real `gemma-4-31b-it` response was retained with request ID and provider usage (309 prompt, 168 completion, 685 total tokens). A Google-flagged thought frame was normalized without relaxing strict JSON/schema/diff checks. Offline response revalidation preserved the original request/response/attempt metadata and signed record; it made no extra HTTP request. Live evidence gate: 1 passed in 3.47s. The owner then approved the exact artifact digest, and fresh baseline FAIL/candidate PASS plus the frozen marker was VERIFIED. Earlier failures remain preserved. Cost basis is published free-tier pricing, not an observed invoice; missing usage/cost is nonfatal but explicitly unknown under the latest owner instruction.

Final retry validation: 169 deterministic tests passed, 1 live deselected, 0 skipped in 173.18s; separately selected genuine-response T-023 passed (1 passed in 3.47s). The human-approved fresh recheck is VERIFIED in `61b8c0c1dd3d4a7f8281f19cce57e43f.json`. No Phase 3 remote CI or Phase 4 benchmark is claimed.


T-014 follow-up: `test_T014_delayed_oom_flag_preserves_both_state_observations`, `test_T014_unconfirmed_137_has_bounded_probes_even_if_clock_stalls`, `test_T014_state_settle_deadline_prevents_more_probes` and the four `test_T014_other_states_are_not_polled` cases exercise state ordering/bounds. The original real OOM test now explicitly requires Docker's OOM flag. `test_T014_unconfirmed_137_is_not_claimed_as_oom_or_target_failure` runs real explicit exits and independently verified child SIGKILL propagation under the same sandbox, preserving INCONCLUSIVE without claiming OOM. Run 40502294999 failed before this local correction; a corrected remote CI result is pending.

## Phase 4 acceptance mapping

Tests in `tests/unit/test_benchmark.py`, plus `tests/integration/test_benchmark_docker.py`:

| ID | Concrete behavior and evidence |
|---|---|
| T-026 | `test_T026_passport_binds_exact_evidence_and_image`, `test_T026_incomplete_runtime_provenance_is_denied`; existing passport missing/non-PASS/inconsistent evidence tests remain required |
| T-027 | `test_T027_guidance_tampering_and_source_change_invalidate_certificate`; existing source/commit-change passport cases |
| T-028 | `test_T028_existing_agent_files_never_overwritten`; exact generated basename and exclusive creation |
| T-029 | `test_T029_text_only_success_claim_never_executes_or_passes`, permission/duplicate-key denials; integration `test_T029_T030_T032_native_tool_pair_has_independent_fresh_runtime_outcomes`; actual live native `run_smoke` and real marker PASS retained for one passport arm |
| T-030 | `test_T030_condition_drift_prevents_comparison` covers source, image, model, task and budget drift; real integration checks equal controls and distinct fresh containers |
| T-031 | `test_T031_native_tool_loop_is_bounded_and_uses_real_reads`; negative/error/usage/time reporting in the T-032 cases and all actual live records |
| T-032 | `test_T032_negatives_and_missing_provider_stay_in_denominators`, `test_T032_study_retains_all_pairs_and_authenticates_report`; Docker integration independently judges both arms against the same command/marker |

Synthetic provider responses in integration exercise the actual runner, not remote model ability. The live report retains 2 pairs / 4 attempts: baseline 0/2, passport 1/2; three provider errors; 0 comparable pairs. Protocol controls match but live comparative performance remains INCONCLUSIVE. See `phase4-onboarding.md`. Corrected Phase 3 CI runs 40504283043 and 40504277107 succeeded for 05e0876 before this phase; historical pending-CI entries above describe the earlier state.

## Phase 5 acceptance mapping

- T-033: `test_reports.py` exercises incomplete signed PASS downgrade, exact Markdown bytes hash, export overwrite refusal, tamper rejection before output and unsupported-schema rejection. Actual CLI export preserves fresh PASS/FAIL/INCONCLUSIVE audits and all historical study negatives. Summary-only, no new verification.
- T-034: `scripts/smoke_wheel.py` installs the built wheel without index/dependencies into a clean venv and runs module/console/inspect smoke outside the checkout.
- T-035: manual `.github/workflows/ci.yml` inspection confirms deterministic gates contain no secrets interpolation, `.env` loading or live model invocation. Remote Phase 4/5 execution not claimed.
- T-036: `scripts/check_docs.py`, source/package byte comparison and refreshed public manifest; README scope/status, setup, architecture and model attribution reviewed.
- T-037: actual-value captions, static retained-evidence display and original records prepared. **Actual demo video and submission completed, confirmed by the owner**; final duration/content not independently inspected. Prepared HTML/captions are not substituted for the actual video.

The current organizer page also requires Alan + open models, conflicting with earlier optional-Alan Town Hall notes. Google-hosted Gemma use is evidenced; Alan use is not. This was a preparation-time eligibility question. The owner subsequently completed submission. Phase 5 delivery is complete per that confirmation; organizer acceptance is not inferred.
