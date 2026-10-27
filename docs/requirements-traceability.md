# Requirements ↔ implementation ↔ tests

| Requirement | Core source | Tests | Completion |
|---|---|---|---|
| FS-001 | parser.py, sources.py, domain.py, cli.py | T-001..T-003 | Phase 1 local inspect/parser gates verified; no target execution |
| FS-002 | policy.py, sources.py, hosttools.py, runner.py, cli.py | T-004..T-007,T-011,T-013 | local pre-execution/no-fallback and real isolation cases passed |
| FS-003 | evidence.py, provenance.py, redaction.py, runner.py, sources.py | T-008,T-014..T-016 | local source/image/policy/time/log/cleanup provenance and HMAC integrity passed; no public attestation claim |
| FS-004 | runner.py, fixtures, validate_phase2.py | T-009..T-017 | local real Docker gate passed; digest-pinned CI workflow updated, remote execution pending |
| FS-005 | providers/ (planned) | T-018,T-019,T-023 | not implemented |
| FS-006 | repair.py (planned), runner.py | T-020..T-025 | not implemented |
| FS-007 | passport.py, sources.py, evidence.py, provenance.py | T-008,T-015,T-016,T-026..T-028 | source/policy/runtime/HMAC consistency verified locally; clean repair/retest and full Phase 4 gate pending |
| FS-008 | benchmark.py (planned) | T-029..T-032 | not implemented |
| FS-009 | reports.py (planned), evidence.py | T-033 | partial JSON |
| FS-010 | docs/, scripts/ | T-034..T-037 | partial |

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
