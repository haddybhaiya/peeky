# Requirements ↔ implementation ↔ tests

| Requirement | Core source | Tests | Completion |
|---|---|---|---|
| FS-001 | parser.py, sources.py, domain.py, cli.py | T-001..T-003 | Phase 1 local inspect/parser gates verified; no target execution |
| FS-002 | policy.py, sources.py, runner.py, cli.py | T-004..T-007 | Phase 1 pre-execution/path/no-fallback contract gates verified; genuine Docker isolation pending Phase 2 |
| FS-003 | evidence.py, domain.py, runner.py, sources.py | T-008,T-014,T-016 | Phase 1 source/commit/policy/plan provenance verified; image/time/log attestation pending |
| FS-004 | runner.py, fixtures | T-009..T-017 | pending Docker gate |
| FS-005 | providers/ (planned) | T-018,T-019,T-023 | not implemented |
| FS-006 | repair.py (planned), runner.py | T-020..T-025 | not implemented |
| FS-007 | passport.py, sources.py, evidence.py, domain.py | T-008,T-026..T-028 | source/commit/policy invalidation verified in Phase 1; authentic clean execution and full Phase 4 gate pending |
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
