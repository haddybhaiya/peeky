# Work review and evidence ledger

## 2026-10-26 — Phase 0 initial scaffold prepared

**Changed:** initial `pyproject.toml`, CLI inspect/doctor/audit/passport functions, restricted Docker runner, evidence JSON, sample fixtures, documentation, GitHub Actions core and Docker jobs.

**Tested:** At generation time this was a scaffold. Fill out exact `uv sync --locked`, ruff, mypy, pytest, docs, wheel, integration results from local execution below. **Do not infer CI success from the presence of a workflow.**

**Current limitation:** no real open-model adapter, auto-repair engine, immutable git snapshot, working agent A/B tool harness or full system environment support. Those are PHASES 1–5.

**Next:** Phase 1 source identities, then Phase 2 genuine Docker runner/evidence gate.

## Validation log

| Date | Revision | Command | Status | Notes |
|---|---|---|---|---|
| — | — | — | NOT RECORDED | Update once executed |

## Scaffold verification from the artifact environment

- `python -m pytest tests/unit tests/smoke -q`: 19 passed (local Python 3.13).
- `python scripts/check_docs.py`: 12 required files checked.
- `python -m compileall -q src tests scripts`: passed.
- `uv sync --offline`: blocked: required mypy wheel absent from cache.
- `uv sync`: blocked: environment could not resolve PyPI DNS.
- `ruff`, `mypy`, wheel build, and real Docker integration: **NOT RUN**; next validate on a normal online CI runner.
- No product/benchmark/live model pass is claimed.

## 2026-10-27 — Peeky rename and repository analysis

**Changed:** renamed the display name, distribution/import/CLI, `src/peeky`, README execution annotations and fixtures, `.peeky/runs`, `peeky.example.toml`, proposed `PEEKY_` environment variables, wheel lookup, test imports, CI name and documentation. Existing FS/T acceptance IDs are retained. No test cases/assertions or runtime security behavior were added or changed beyond the identity substitutions. Refreshed manifest paths/hashes after documentation updates.

**Scope and revision:** Phase 0 prerequisite review; HEAD `971be15`, with the scaffold mostly untracked before and after this work. No staging, commits or remote writes. Commands below used Python 3.13.7 on Windows; the absolute interpreter is `C:\Users\hp\AppData\Local\Programs\Python\Python313\python.exe` (`py -3.13` also worked outside the sandbox). Locally installed tools are not the pinned development environment. Earlier interrupted command sessions were not treated as completed checks; uncertain results were rerun to completion.

| Command/check | Result |
|---|---|
| `py -3.13 -m pytest tests/unit tests/smoke -q` | 19 passed, 0 skipped |
| `py -3.13 scripts/check_docs.py` | Passed: 12 required files |
| `PYTHONPATH=src python -m peeky --version`, `--help`, `inspect tests/fixtures/good_repo --json` | Correct Peeky identity and one proposed command; no target execution |
| `PYTHONPATH=src python -m peeky inspect tests/fixtures/no_optin_repo --json` | Empty plan, expected exit 2 |
| `python -m ruff check .` (Ruff 0.16.3) | Failed: 2 I001 import-formatting errors, in policy.py and CLI smoke test |
| `python -m ruff format --check .` (Ruff 0.16.3) | Failed: 13 files would be reformatted; 5 already formatted |
| `python -m mypy src tests` (mypy 2.3.1) | Passed: 16 source files |
| `uv build --offline --wheel` (uv 0.12.23) | Passed: `dist/peeky-0.1.0.dev0-py3-none-any.whl` |
| `python scripts/smoke_wheel.py` with `PIP_NO_INDEX=1`, `PIP_DISABLE_PIP_VERSION_CHECK=1` | Passed: wheel installed in a temporary clean venv; module version and inspect worked |
| `PYTHONPATH=src python -m peeky doctor --json` outside the sandbox | Docker CLI present, daemon unavailable; exit 3 |
| `python -m pytest tests/integration -m docker -q` outside the sandbox | 2 skipped because the Docker daemon was unavailable; no integration PASS claimed |
| Bounded controller-only evidence probes | Synthetic PASS JSON accepted for an unexecuted command; source-file mutation did not invalidate passport; unrelated nonzero result labelled PASS yielded PASS; failed first step of two yielded INCONCLUSIVE |
| Rename/package/manifest consistency checks | 51 file entries verified against SHA-256; no legacy identity strings or paths; distribution, import path and entry-point declaration agree |
| `git diff --check` | Passed; Git reports the existing LICENSE line-ending conversion notice |

**Docs updated:** README, architecture and runner caveats, assumptions A-09, ADR-008, phase tracker, this ledger and `docs/repository-analysis.md`. The manifest includes the new analysis document. Original artifact-environment validation above is historical and is not overwritten.

**Known limits:** no real Docker execution in this checkout; no Python 3.12 or pinned-group validation; `uv sync` not rerun, no lockfile; no provider calls, repair/retest loop or agent benchmark. Code review found mutable source/image identity, unauthenticated passports, unbounded capture before truncation, absent explicit container cleanup/redaction and incomplete verdict/coverage validation. These findings are documented, not fixed by the rename.

**Phase gate:** Phase 0 remains incomplete due to observed Ruff failures and outstanding pinned-environment validation. Phase 2 Docker checks are BLOCKED/INCONCLUSIVE, not verified. No phase has been promoted.

**Next task:** finish Phase 0 formatting/import and pinned-environment checks, then Phase 1 immutable source/evidence identity and T-001..T-008. Restore a real Docker runner before attempting the Phase 2 gate.

## 2026-10-27 — Phase 0 local foundation gate completed

**Authorization:** the owner requested completion of Phase 0 and deferred the two Docker tests until Docker is running. Those cases remain pending Phase 2 integration; they are not failures or passes in this gate.

**Changed:** created `uv.lock` from the existing dependency declarations; both CI jobs now sync and run with `--locked`. Fixed two import-spacing errors and formatted 13 Python files. No product runtime behavior or test assertions changed: AST comparison against HEAD confirmed equality in all 16 source/test Python files. The wheel smoke script selects the matching project version, requires one wheel, installs without network/dependencies, clears Python source-path overrides, and runs the installed module and console command outside the checkout. The docs gate checks 14 public contract files instead of depending on an intentionally ignored local prompts file. Added `.peeky/` to ignores while retaining the owner's existing `.freshstart/` entry and local-prompts ignore. The refreshed public-file manifest includes `uv.lock` and excludes the ignored prompts file without deleting it.

**Environment:** Windows, Python 3.13.7, uv 0.12.23. The new `.venv` contains the declared pytest 9.1.1, Ruff 0.16.10 and mypy 2.4.0; build resolved to 1.6.1 in the lock. Base revision `a68c595`; nothing staged or committed by this task. Python 3.12/Linux and GitHub Actions were not executed here.

| Completed command/check | Result |
|---|---|
| `uv sync --python C:\Users\hp\AppData\Local\Programs\Python\Python313\python.exe` | Resolved and installed 16 packages; created lock and isolated `.venv` |
| `uv sync --locked --offline --python C:\Users\hp\AppData\Local\Programs\Python\Python313\python.exe` | Resolved/checked 16 packages successfully from cache; lock unchanged |
| `.venv\Scripts\ruff.exe check . --fix` | Fixed 2 import-formatting errors, 0 remaining |
| `.venv\Scripts\ruff.exe format .` | 13 files formatted; 5 unchanged |
| `.venv\Scripts\ruff.exe check .` | All checks passed |
| `.venv\Scripts\ruff.exe format --check .` | All 18 files already formatted |
| `.venv\Scripts\mypy.exe src tests` | Success: 16 source files |
| Initial sandbox `.venv` unit/smoke run | 18 passed, 1 setup error: permission denied reading existing pytest temp directory; not counted as gate success |
| `uv run --locked pytest tests/unit tests/smoke -m 'not docker and not live' -q` outside sandbox | 19 passed in 0.25s; 0 skipped |
| `.venv\Scripts\python.exe scripts/check_docs.py` | 14 required files checked |
| Public-checkout docs smoke | Copied current public tracked files into a temporary directory; checker passed with the ignored local prompts absent |
| `.venv\Scripts\peeky.exe --version`, `--help`, `inspect tests/fixtures/good_repo --json` | Correct identity/help and one proposed step; no target execution |
| `uv build --offline --wheel` | Built `dist/peeky-0.1.0.dev0-py3-none-any.whl` |
| `.venv\Scripts\python.exe scripts/smoke_wheel.py` | Clean venv installed wheel with `--no-index --no-deps`; isolated module version, console version and console inspect all passed |
| Source/test AST comparison | All 16 controller/test Python files match HEAD behavior/assertions |

**Docs updated:** phase tracker, assumptions A-01/A-11, ADR-009, README, contributor setup, test plan, repository analysis and this ledger. Earlier validation records remain historical.

**Known limits:** 2 Docker tests deferred by the owner and not rerun in this completion task. No target code executed on the host. CI/Python 3.12, immutable source capture, strengthened evidence/passports, runner hardening, model repair and agent benchmarks remain unverified or unimplemented as documented. The initial sandbox permission error was resolved by rerunning the trusted controller tests outside the sandbox; no assertions were relaxed.

**Phase gate:** Phase 0 VERIFIED for the local foundation checks above. This is not a target/product PASS and does not promote Phase 2. The Docker acceptance criteria are unchanged.

**Next task:** Phase 1 immutable source identities, snapshots and T-001..T-008. Once Docker is running, execute `uv run --locked pytest tests/integration -m docker` and record actual outcomes before claiming a Docker gate.

## 2026-10-27 — Phase 1 source identity and pre-execution gate completed

**Changed:** added `sources.py` for verified raw Git commit/tree/blob capture, selected-scope index/worktree consistency, path/type/credential checks, bounded read-only temporary exports and source integrity verification. Added `domain.py` for frozen source/policy identities, deterministic plan hashes and controller run transitions. CLI inspect/audit now plan from captured committed bytes; only audit can invoke Docker, and it receives the export path. Missing Docker preserves BLOCKED/INCONCLUSIVE evidence without target execution. Schema 1.1 records source/policy/plan/state provenance. Passport validation rejects legacy evidence and source/commit/command/policy/state/result mismatches. Mechanical verdict reduction now preserves an observed failure with later incomplete coverage and rejects unrelated/nonzero PASS results. Runner constants read the shared default policy without changing resource budgets. No model or release feature was added.

**Compatibility:** inspect JSON is now a structured plan object instead of a bare list; passports require schema 1.1. Sources require a clean committed selected directory within an ordinary local Git repo. UTF-8 CRLF checkout equivalence is accepted without executing filters, and exports contain original Git bytes. Dirty files outside a selected subdirectory are irrelevant to its file manifest; a new containing commit still invalidates commit-bound guidance. See `source-capture.md` for bounds and unsupported inputs.

**Environment/revision:** base HEAD `d9dbd68`; Python 3.13.7, uv 0.12.23, pinned pytest 9.1.1/Ruff 0.16.10/mypy 2.4.0. Working tree was clean before implementation. No workspace staging, commit, remote write, credential use, publishing or target host execution. Tests create/commit only synthetic temporary Git repositories with hooks disabled. Python 3.12/Linux/remote CI was not run.

| Completed command/check | Observed result |
|---|---|
| Initial focused unit/smoke run | 74 passed, 1 failed: file-count denial was wrapped as a generic Git-tree error; preserved specific SourceError and reran without relaxing the bound/assertion |
| Intermediate expanded source gates | 78 passed, then 81 passed in 56.22s; 0 skips |
| `uv run --locked pytest tests/unit tests/smoke tests/integration/test_source_capture.py -q` | Final gate after image-policy regression cases: 85 passed in 62.28s, 0 skipped; includes one real independent-process Git integration |
| `.venv\Scripts\ruff.exe check .` | All checks passed |
| `.venv\Scripts\ruff.exe format --check .` | 25 files already formatted |
| `.venv\Scripts\mypy.exe src tests` | Success: 23 source files |
| `.venv\Scripts\python.exe scripts/check_docs.py` | 15 required public files checked |
| `uv sync --locked --offline` | 16 packages resolved/checked from cache; no dependency changes |
| `uv build --offline --wheel` | Built `dist/peeky-0.1.0.dev0-py3-none-any.whl` for validation only |
| Initial sandbox wheel smoke | Installed module/console version passed; Git refused metadata access to the workspace repo from the sandbox account; no target execution or policy bypass |
| `uv run --locked python scripts/smoke_wheel.py` outside sandbox | Passed: clean network-free installation, module version, console version and inspect on the committed good fixture |

**Behavior evidence:** two independent exports match source identity and original Git bytes; changing the worktree does not alter an already captured export; export tampering is detected. Native Windows junctions, Git symlink/submodule README modes, malicious traversal trees, case collisions, dirty/staged/untracked files, tracked credential paths and source budgets are denied. Git filters/fsmonitor/environment overrides do not execute the sentinel fixture. SHA-1 and SHA-256 Git repositories are exercised. Separate Peeky processes measure identical source/policy/plan identities and different run IDs. T-001..T-008 are mapped to concrete tests in `requirements-traceability.md`. T-007 stubs only missing Docker at the availability boundary; no Docker success is inferred. Synthetic unit PASS results validate schema binding only.

**Final review correction:** the old image-prefix allowlist also admitted registry-shaped `python:5000/other`. Restricted syntax to official `python:TAG` or a full 64-hex SHA-256 reference and added four rejection cases plus a valid digest assertion. The complete test gate, lint/type checks, offline wheel build and installed CLI smoke passed again after that change. This validates identifier syntax, not a cached image's content or resolved digest. Final public-export docs, all 59 manifest hashes and all 11 packaged source-module bytes were verified; `git diff --check` passed.

**Docs updated:** README/contributor flow, source-capture contract, architecture, runner security, evidence schema, assumptions A-12/A-13, ADR-010, phase tracker, test plan, requirements mapping, repository analysis and this ledger. CI core selection includes the genuine Git integration. Public file manifest refreshed for the added source/tests/docs.

**Known limits:** both Docker tests remain owner-deferred and were not run here. Real container isolation, image digest enforcement, bounded streaming/redaction, timeout cleanup, authenticated execution evidence and durable intermediate/crash journaling remain Phase 2/later work. The low-level runner retains its Path-based fixture interface; only CLI capture/mount flow was changed. File permissions/integrity checks do not defend against a hostile concurrent host owner. Known credential filename checks are not a complete secret scan. JSON is unsigned and cannot independently prove execution. No models, repair loop, benchmark or release is claimed.

**Phase gate:** Phase 1 VERIFIED locally for FS-001/002 pre-execution contracts and T-001..T-008, plus real Git integration and package/docs gates. This is not a real Docker/product PASS and does not promote Phase 2.

**Next task:** Phase 2 runner boundary and evidence hardening, followed by genuine Docker T-009..T-017 once the daemon is available. Do not begin models/repair or release until prerequisite gates pass.

## 2026-10-27 — Phase 2 local Docker gate completed

**Changed:** the runner accepts only controller-captured immutable snapshots and one reviewed command. The official Python image is pinned to `python@sha256:12316debbfb86890f6b2d825820612741ba527ad5a44e3902759141d572bfe8f`; audit never pulls images or installs dependencies. Effective container configuration is checked before start, including read-only source/root filesystem, no network/capabilities, non-root identity, fixed environment and CPU/memory/PID limits. Bounded streaming, timeout/OOM classification, ownership-checked cleanup and redacted original transcripts distinguish target failure from infrastructure uncertainty. Schema 1.2 binds runtime evidence to source/policy/plan identities, authenticates records with a per-user key outside repositories and writes records atomically without replacing existing evidence. Host tool lookup excludes the target repository and current directory. No models or release functionality was added.

**Environment:** Windows Python 3.13.7, uv 0.12.23, pytest 9.1.1, Ruff 0.16.10, mypy 2.4.0; Docker Engine 29.1.3, Linux/amd64 containers. Base HEAD `f5ac0c8dd7f29c7f84b6c7c8c6ea555fa26bb1ae`. The official image was prefetched separately, then all runner checks used the cached exact digest. No workspace staging, commits, remote writes or target host execution occurred.

| Completed command/check | Observed result |
|---|---|
| `uv run --locked pytest -m 'not live' -q` | **118 passed in 148.69s; 0 skipped**, including 103 controller/source cases and 15 real Docker/infrastructure cases |
| Dedicated Docker integration run | 15 passed in 69.66s; T-009..T-017 cover good/bad/reserved exits, missing image/daemon/executable, timeout, isolation/resource limits, OOM, bounded logs/redaction and no-op refusal |
| `.venv\Scripts\ruff.exe check .` | All checks passed |
| `.venv\Scripts\ruff.exe format --check .` | 33 files already formatted |
| `.venv\Scripts\mypy.exe src tests` | Success: 30 source files |
| `.venv\Scripts\python.exe scripts/check_docs.py` | 16 required public files checked |
| `uv sync --locked --offline` | 16 packages resolved/checked; no new dependencies |
| `uv build --offline --wheel` | Built `dist/peeky-0.1.0.dev0-py3-none-any.whl` for local validation |
| `uv run --locked python scripts/smoke_wheel.py` | Passed clean network-free wheel installation, module/console versions and console inspect outside the checkout |
| `uv run --locked python scripts/validate_phase2.py` | Actual good fixture PASS, bad fixture FAIL and no-opt-in fixture INCONCLUSIVE; authenticated evidence retained |

**Retained evidence:** `.peeky/phase2-validation/summary.json` points to the final records: good `2615b8f276f34872a7755d1bbbab9793`, bad `fcc556b7bd634048b5ec971dffc690a1`, no-opt-in `763546d9c60a4b4981e48107dc860503`. Original bounded transcripts are retained after redaction, with hashes and runtime configuration in each record. Earlier development records remain preserved and are not the final gate evidence. The convenience summary is not authenticated; the individual records are authoritative.

**Validation corrections:** sandbox access initially denied Docker/uv/pytest temporary state; approved execution outside that sandbox resolved access without a host target fallback. Intermediate type/test defects were corrected before the final complete gate. Final boundary review moved the authentication key outside target repositories, excluded repository-local host tools, and rejected unknown/duplicate effective environment entries. No assertion was relaxed to produce the reported gate.

**Docs updated:** Phase 2 runner contract, architecture, source capture, evidence contract, runner security, assumptions, ADR-011, requirements T-009..T-017, test plan, phase tracker, repository analysis, contributor/security guidance and public manifest. CI now prefetches the exact digest separately and runs the Docker gate and fixture validator; that remote workflow has not been executed by this task.

**Known limits:** Docker shares its host kernel; local HMAC is not public attestation or protection against a compromised host owner. Redaction is bounded pattern matching, not a complete secret detector. One command and the reviewed preinstalled image are supported; dependency prefetch, crash-recovery journaling, models/repair and release remain deferred. Atomic evidence storage requires a hard-link-capable filesystem. Python 3.12/Linux controller and remote CI results are pending.

**Phase gate:** Phase 2 `LOCAL_GATE_PASSED`; all requested local gates passed with real Docker evidence. Remote CI remains pending, so no global CI verification is claimed.

**Next task:** obtain remote CI confirmation through the owner's normal review workflow, then begin Phase 3 only with authorization. Nothing staged, committed or pushed by this task.


## 2026-10-27 ? Phase 3 implementation, local gates passed, live provider blocked

**Prerequisite:** before edits, the checkout was clean on `phs3` at `57201b1bab362774dc48c5a4286d46b9f5e7646e` (merged PR #4). Read-only GitHub inspection confirmed Actions run 40493116591 completed core and sandbox jobs successfully, including Python 3.12, Docker tests and Phase 2 fixture validation. Phase 2's previously pending remote gate is now observed. No GitHub write, workspace commit/staging/push, model download or release was performed for Phase 3.

**Changed:** one standard-library OpenAI-compatible BYOK adapter, strict typed patch proposals, a single-line README command correction allowlist, frozen operator command/stdout oracle, authenticated proposal approval digests, durable one-attempt reservations and separate fresh original/candidate Docker rechecks. The target worktree/index is never patched. The candidate has its own genuine isolated Git revision, with identical non-README hashes/modes. Only the independent controller can set VERIFIED after actual matching checks; model output cannot approve, weaken tests, change policy/evidence or declare verified status. Added CLI diagnose/recheck, offline adversarial contracts, two real Docker repair cases, a reviewed outdated-command fixture, a one-attempt live validator and explicit retained-evidence T-023 gate.

**Owner-selected model/BYOK:** the owner replaced the earlier Qwen plan with Gemma and supplied a Google AI Studio key in ignored `.env`. Filled only its empty base URL/model fields using Google's official OpenAI-compatible endpoint and `gemma-4-31b-it`; preserved the key without printing it. Authenticated model discovery succeeded and listed Gemma 4 31B/26B. Gemma 4 31B instruction-tuned is open-weight/code-capable and general-purpose, not a dedicated Qwen/CodeGemma coding checkpoint. The adapter records this distinction, checkpoint/version and unknown hosted weights revision. Successful-response cost accounting distinguishes Google's published free-tier pricing from measured token usage/billing. No fallback to proprietary Gemini or a paid endpoint is allowed.

| Completed command/check | Actual result |
|---|---|
| Focused offline provider/repair contracts after initial fixes | 42 passed in 6.70s; no key/network |
| `uv run --locked pytest tests/integration/test_repair_docker.py -m docker -q` | 2 passed in 38.19s; actual baseline/candidate containers, explicitly mocked model |
| `uv run --locked pytest -m 'not live' -q` | **163 passed, 1 live deselected, 0 skipped in 158.02s**; 146 controller/source and 17 real Docker cases |
| `.venv\Scripts\ruff.exe check .` | All checks passed |
| `.venv\Scripts\ruff.exe format --check .` | 42 Python files already formatted |
| `.venv\Scripts\mypy.exe src tests` | Success: 38 source files |
| `.venv\Scripts\python.exe scripts/check_docs.py` | 17 required public files checked |
| `uv sync --locked --offline` | 16 packages resolved/checked; no new dependencies |
| `uv build --offline --wheel` | Built `dist/peeky-0.1.0.dev0-py3-none-any.whl` for local validation |
| `uv run --locked python scripts/smoke_wheel.py` | Passed clean network-free install, module/console versions and inspect outside checkout |
| `uv run --locked python scripts/validate_phase3.py --live --env-file .env --output .peeky/phase3-live` | Real baseline FAIL; genuine completion request returned HTTP 500; signed INCONCLUSIVE attempt, no returned usage/cost |
| Same live validator with `--output .peeky/phase3-live-manual2`, explicitly authorized separately after local gates | Real baseline FAIL; additional same-checkpoint request failed to connect (10385ms); signed INCONCLUSIVE attempt; no automatic retries |
| `PEEKY_LIVE_EVIDENCE=.../4a163a147ce14ec491192e3e9ea439c5.json`, then `uv run --locked pytest tests/live/test_gemma.py -m live -q` | **1 failed in 0.48s, 0 skipped**, accurately rejecting the actual incomplete provider trace; no new HTTP request |

**Behavior evidence:** exact-schema rejection covers duplicate/unknown/authority fields, bad types/confidence, missing usage, model substitution, output budget and truncated completions. Consent precedes configuration/source/network; missing provider config does not break core inspection. Diff tests deny traversal/renames/tests/AGENTS/evidence paths, extra hunks/commands, unrelated prose edits and assertion-bypassing inline code/options. Approval/source drift and repeated attempt claims fail before execution. Real Docker comparisons show baseline FAIL then candidate command PASS in different containers under the same image ID, unchanged source bytes and cleanup. A missing exact marker still produces INCONCLUSIVE despite command PASS. These are actual runner checks with mocked model proposals, not a live model repair demonstration.

**Retained live evidence:** `.peeky/phase3-live/summary.json` points to baseline `46068d130e7e462ea05e4a6a24c68acc` and attempt `33772b17ad704ddfb04cc80d3b2ca5cd`; `.peeky/phase3-live-manual2/summary.json` points to baseline `f0de2b5195b0452e9d79cdd57e474944` and attempt `4a163a147ce14ec491192e3e9ea439c5`. Individual records are authenticated; convenience summaries are not. The earlier `.peeky/phase3-validation` preflight baseline is also preserved: a serialized list-versus-tuple identity comparison stopped before any provider call. Canonical hashing fixed that representation bug without weakening source binding. Initial mypy duplicate fixture names were resolved by naming the new entrypoint `repair_smoke.py`; Windows pytest path limits were resolved with bounded parameter IDs. No assertion was relaxed to produce the final gate.

**Docs updated:** Phase 3 contract, Gemma/BYOK configuration example, README/contributor flow, architecture/security/evidence boundaries, assumptions A-16..A-19, ADR-012, test plan, T-018..T-025 mapping, phase tracker, repository analysis and public manifest. Historical Phase 0?2 entries remain historical. No Phase 3 remote CI result is claimed.

**Known limits / concrete blocker:** both authorized Google completion attempts failed before returning a model response. Requested checkpoint/version is recorded; observed served model, token usage and actual cost remain unknown. Do not infer free billed usage, a valid live proposal or success from the model-list request. No real proposal exists to present for human approval, so no live human-approved recheck is claimed. The full phase cannot pass T-023. Hosted exact weights revision, provider-side privacy/availability, pattern redaction completeness and trusted host/meaningful-oracle assumptions remain limits. Arbitrary README rewrites, package installation, multi-step repairs, benchmarks and release are outside this implementation.

**Phase gate:** implementation/local deterministic gates passed; Phase 3 **BLOCKED at T-023**, not VERIFIED. Stop provider requests on the demonstrated failure. Do not promote Phase 4.

**Next task:** restore the selected Gemma OpenAI-compatible service/transport under renewed operator authorization, obtain one genuine bounded structured response with usage/cost provenance, then present its exact diff/digest for human review before fresh recheck. Do not silently retry, change checkpoint/protocol or fabricate missing evidence.


**Final review/gate repeat:** corrected validation ordering for an oversized JSON integer confidence so it rejects cleanly before float conversion; the adversarial range case now exercises that input. Final `uv run --locked pytest -m 'not live' -q`: **163 passed, 1 live deselected, 0 skipped in 175.67s**. Rebuilt the final wheel and repeated installed CLI smoke successfully. All 79 public manifest hashes, all 18 packaged source modules, UTF-8 README package metadata and clean-public-export docs passed; actual provider key absent from every public file. Both retained baseline/attempt pairs reauthenticated, confirmed source/policy binding and secret exclusion, and their owned containers were independently absent. Final Ruff/type/docs/diff checks passed. The incomplete live gate remains failed; no additional request, human approval, workspace commit or GitHub write was made.


## 2026-10-27 ? Phase 3 live blocker resolved, exact human-approved recheck VERIFIED

**Renewed authorization:** the owner explicitly requested Gemma retries and made missing free-model usage/cost metadata nonfatal. Used a bounded batch of three additional attempts, with separate durable claims and immutable records; no automatic provider loop or model/checkpoint switch. Explicit retry authorization also restored the local `.env` disclosure-consent setting to true; key/base URL/checkpoint were preserved. No GitHub writes or workspace commits.

**Actual retry results:** `.peeky/phase3-retry3/proposals/7f3685b4f26e4b82b2a67873387b719e.json` records HTTP 503 and Google's explicit temporary high-demand message. `.peeky/phase3-retry4/proposals/875fbdd3f9ee4b058b48d30bcdaa2d7f.json` retains a genuine `gemma-4-31b-it` response (request ID `LJHgap_uNv6A3LUPo-6e8QE`, 309 prompt / 168 completion / 685 total provider-reported tokens), initially rejected because it had a Google-flagged thought prefix before its JSON. `.peeky/phase3-retry5/proposals/074a1e411d924ed586110ef843cffc27.json` records a read timeout after 45159ms. Initial HTTP 500/connection records remain unchanged. There were no further provider requests after this batch.

**Changed and tested:** extend the response wait from 10 to 45 seconds; preserve bounded redacted transport diagnostics; allow a valid structured proposal with unknown usage/cost metadata under the owner's instruction, without inventing billing. Request Google's documented minimal thinking mode and disable thought inclusion for future calls. If Google nevertheless supplies its explicit thought flag and a complete leading thought frame, remove only that provider frame and validate the remainder as the original exact JSON schema. Unflagged/unterminated frames, authority fields and extra objects still fail. Extract response validation into a function that can copy an existing trace without mutating original request/response/hash/ID/attempt/latency metadata; request-time failures still retain observed metadata.

**No invented live call:** validated the already-received retry-4 response offline through the corrected framing decoder. Authenticated linked artifact `.peeky/phase3-revalidated/proposals/93be74364fee4196aac897508c032c34.json` records the original signed record hash, previous parser rejection and **zero additional network requests**. It preserves the actual original response and request metadata. The original request preceded the minimal-thinking setting; the later minimal-setting call timed out, so its server-side behavior is not claimed verified. Cost is `published_free_tier`, not a measured invoice; hosted exact weights revision remains unknown.

**Concrete human review:** displayed the only candidate change, `python outdated.py` to `python repair_smoke.py`, with frozen stdout marker `PEEKY_RECHECK_OK`. The owner explicitly approved digest `sha256:c0973e0195e9d581847a9cb1a8c95b750495bf8f79079292654afd8ed3550a12` for the isolated fixture. The model did not supply approval or verified status.

**Actual recheck:** `.peeky/phase3-revalidated/rechecks/61b8c0c1dd3d4a7f8281f19cce57e43f.json` is controller **VERIFIED**: unchanged original rerun FAIL; approved derived candidate PASS; exact marker observed; different fresh containers and matching image/policy; code/test bytes and modes preserved and containers cleaned up. The target worktree/index were never patched. `.peeky/phase3-revalidated/summary.json` links the original baseline, reviewed proposal and final comparison. Individual records are authoritative authenticated evidence; the convenience summary is not authenticated.

**Observed gates so far:** focused provider/repair contracts: 43 passed in 8.24s before the additional framing/provenance cases. Complete deterministic retry gate: 168 passed, 1 live deselected, 0 skips in 172.21s. T-023 selected against the genuine linked retained response: **1 passed in 3.47s**, with no new request. Final provenance regression, complete deterministic repeat, wheel/manifest/docs checks are recorded below when completed. Earlier blocked entries remain historical; no failed record/assertion was deleted or weakened to claim success.

**Phase gate:** Phase 3 local live/approval/fresh-Docker gates now pass, pending final routine validation; remote Phase 3 CI remains unobserved because no GitHub writes are authorized. Phase 4 benchmarks and release are not implemented/promoted.


**Final Phase 3 retry gate:** `uv run --locked pytest -m 'not live' -q`: **169 passed, 1 live deselected, 0 skipped in 173.18s**. Separately selected T-023: **1 passed in 3.47s**, using the genuine retained response and explicitly linked zero-request revalidation. Exact owner-approved fresh Docker recheck: **VERIFIED**, original FAIL/candidate PASS with frozen marker. Independently reauthenticated original completion, linked revalidation, approved digest and final comparison; verified unchanged target source, identical non-README files/modes, matching policy/image, distinct containers and owned-container absence. Final wheel source-module bytes and README metadata match. Lint, format, types, docs and package smoke passed; public manifest refreshed. No additional model calls, commits, staging or GitHub writes. Phase 3 is **LOCAL_GATE_PASSED**; remote Phase 3 CI remains pending. Next task is owner review/CI through their normal workflow, then separately authorized Phase 4; no benchmark or release claim.


## 2026-10-27 ? T-014 remote CI regression corrected locally

**Observed failure:** read-only GitHub inspection of run 40502294999 / sandbox job 122182712838 at `8497825` confirmed core success and sandbox **1 failed, 16 passed, 1 deselected in 13.14s**. The memory stress case returned code 137 classified FAIL; the log's assertion abbreviated the full result, so the exact OOM flag/event timing was not available. Preserved the original GitHub-redacted job text under ignored `.peeky/ci-oom-regression/original-job-log.json`. The unchanged original test passed locally before edits (1 passed in 14.42s), so this was not reproduced as a deterministic local failure.

**Changed:** runner 2.1 refreshes only exited-137 states with OOMKilled explicitly false, with at most five extra reads under a one-second settling window; each metadata operation retains its existing timeout. Preserve all observed states and final state in provenance. A boolean OOMKilled=true is still required for MEMORY_LIMIT. Unconfirmed 137 is INCONCLUSIVE/TERMINATION_UNCERTAIN because signal and explicit exit statuses overlap. Normal exits do not incur the settling loop; ordinary target failures, resource limits, source/image identity, isolation and cleanup remain enforced. This is a cautious fix for a plausible exit/OOM observation ordering, not a claim that CI's event timing was directly measured.

**Regression evidence:** unit histories cover false-then-true OOM observation with preserved snapshots, the six-read cap even with a stalled clock, elapsed deadline, and no polling for four unrelated terminal/running states. Real integration keeps the 600 MiB allocation under the same 256 MiB sandbox and strengthens its assertion to require actual OOMKilled=true; failures now print full redacted result JSON. Two real non-OOM cases exercise an explicit exit 137 and independently verified child SIGKILL propagation, requiring INCONCLUSIVE without claiming memory exhaustion. The first new self-SIGKILL fixture exited zero because Linux PID 1 ignored its own signal; corrected the fixture to verify actual child wait status, without relaxing the expected outcome.

| Check | Actual result |
|---|---|
| Initial focused runner/Docker regression | 28 passed, 1 failed in 83.43s; failure was the PID 1 self-signal fixture described above |
| Corrected focused runner/Docker regression | 29 passed in 72.37s; the later deadline case is included in the full gate |
| `uv run --locked pytest -m 'not live' -q` | **178 passed, 1 live deselected, 0 skipped in 172.88s**, including the seven added unit cases and two real Docker cases |
| Ruff lint / format | All checks passed; 42 files formatted |
| `mypy src tests` | Success: 38 source files |
| `scripts/check_docs.py` | 17 public contracts checked |
| Offline wheel build and installed CLI smoke | Passed; module/console versions and isolated inspect outside the checkout |

**Docs updated:** OOM observation/security contract, runner contract, T-014 requirement/test mapping, assumption A-20, ADR-013, phase tracker and this ledger; public manifest refreshed. Earlier source snapshots, reports, local successes and CI failures remain historical evidence. No assertions were relaxed, checks skipped, target code run on host, dependencies installed or model calls made.

**Known limits / phase gate:** local deterministic, package and documentation gates pass. The one-second metadata window cannot guarantee that every daemon eventually reports an OOM event; unconfirmed 137 stays uncertain rather than becoming an invented memory/target failure. The strict real OOM test will still fail an environment that never supplies that confirmation. Corrected remote CI has **not** run; current remote failure is not relabeled success. No workspace staging, commit, push or GitHub write was performed for this fix.

**Next task:** review/publish this patch and observe a fresh sandbox CI run before claiming the remote gate passed. Keep the Phase 3 model/repair evidence and Phase 4 scope separate from this runner correction.

## Phase 4 implementation and actual paired attempts (2026-10-27)

**Changed:** strengthened passport runtime provenance and embedded HMAC certificate binding source, guidance, exact evidence bytes, run, image and plan. Exclusive generated-file naming preserves upstream AGENTS.md. Added `benchmark.py`, CLI `trial`, explicit live fixture validator, T-026..T-032 adversarial/report tests and a real fresh-Docker paired integration with explicitly mocked remote provider. The remote model has fresh conversations and native read/run capabilities through a trusted controller dispatcher, not a separate local agent worker process. Target code only executes in the existing strict offline Docker runner.

**Prerequisite:** corrected Phase 3 CI runs 40504283043 and 40504277107 completed successfully for 05e0876; merge dddc807 preceded this phase. Prior pending-CI entries remain historical.

**Actual live work:** `uv run --locked python scripts/validate_phase4.py --live --env-file .env` performed a fresh successful fixture audit and one complete baseline/passport pair. Baseline returned Google HTTP 500; passport returned an actual Gemma native `run_smoke` call and independently passed the fresh Docker command/marker oracle. One additional complete pair reused exactly the same audit/model/source/image/task/budgets; both arms returned HTTP 500. No selective failed-arm retry, conditions change or further model call. Four calls total, three provider errors retained. The second pair was chosen after observing the first error, not preregistered.

**Report:** two attempted pairs/four arms; baseline 0/2 PASS, 2 INCONCLUSIVE; passport 1/2 PASS, 1 INCONCLUSIVE; zero target FAIL/BLOCKED outcomes. Identical controls hash `sha256:7720e0ba28be2f3cb1821aa649cd2c79e6a139ac63ef1da46634c877b2956afa`. Actual source commit `dddc80764dcde1bb07ca4c556351592ea8d96964`, scope hash `sha256:086485bbdb118d268a1c8b1ee69eecf22d545e3b97b79aa1bb181589448a4138`. Observed model identity is absent for three arms, so **0/2 comparable pairs; live comparison INCONCLUSIVE, no effect estimate**. Aggregate actual tokens/billing unknown; the successful response reports 1,871 tokens. Conservative budget charges 4,794/7,108 are not measured usage or cost. Independent checks authenticated both pairs and all four standalone traces, confirmed identical repeated request hashes per arm, and verified actual successful marker/image and absent owned container.

**Evidence:** exact paths in `phase4-onboarding.md`; final report `.peeky/phase4-validation/study-final/paired-report.md`, authenticated study `study-final/records/6833697008c3402c9a28886ff692b4bf.json`. Original per-arm request/response/tool/Docker evidence remains retained and redacted. A final byte-integrity regression exposed Windows CRLF translation: the first aggregate report hash did not match its written bytes. Its original study/Markdown remain preserved. Fixed explicit LF output and reaggregated the exact same authenticated pairs into study-final with zero network requests. The actual-byte regression passes; corrected study binds both original pair hashes and exact report bytes. No outcome or trial condition changed.

**Validation so far:** original passport suite 14 passed; focused new/old passport plus real paired Docker integration 36 passed in 185.18s before the final aggregate regression. First complete Phase 4 run: 200 passed, 1 failed (Windows report byte hash), 1 live deselected, zero skips in 304.86s. After fixing that defect, focused `uv run --locked pytest tests/unit/test_benchmark.py -q`: **22 passed in 44.11s**. Ruff lint/format passed (46 files); strict mypy passed (41 files); required docs check passed (18 files). Locked offline sync passed. An initial `uv build --wheel --offline --no-build-isolation` failed because the development environment intentionally lacks Hatchling; corrected isolated `uv build --wheel --offline` succeeded with its declared cached backend. Final complete suite and final installed-wheel gate are recorded below after completion.

**Docs updated:** protocol/evidence paths, architecture boundary, benchmark actual negatives, assumptions A-21/A-22, ADR-014, requirement mapping T-026..T-032, phase tracker, README flow, required-doc gate and public manifest. No dependencies changed, no tests weakened, no target host execution, installation, commits, staging, GitHub writes or publishing.

**Known limits / phase gate:** implementation protocol can pass locally while live comparative performance remains INCONCLUSIVE due to observed provider availability. Small/adaptively selected sample, fixed baseline-first order, unknown hosted weights revision, pattern-redaction completeness, trusted host/key owner and narrow operator-selected marker remain limits. One genuine native-tool success proves one executed fixture outcome, not generalized onboarding lift. Phase 4 remote CI has not run. Stop model requests on this demonstrated availability blocker; do not promote Phase 5.

**Next task:** review local implementation/evidence and observe CI through the owner's normal workflow. A future separately authorized provider-stable complete matched pair would be needed for an observed live comparison; preserve these negative denominators and disclose any new sampling plan.

**Final Phase 4 local gate:** `uv run --locked pytest -m 'not live' -q`: **201 passed, 1 live deselected, 0 skips in 243.09s**, including the actual-byte report regression and real Docker integration. Output retained at `.peeky/phase4-validation/deterministic-final.log`. Ruff check and format check passed (46 files); strict mypy passed (41 source files); docs check passed (18 required files); `git diff --check` passed. `uv sync --locked --offline`, `uv build --wheel --offline`, and `uv run --locked python scripts/smoke_wheel.py` passed. All 19 packaged source-module bytes and README metadata match the final wheel; all 84 public manifest hashes match, clean public-export docs check passed and the actual configured BYOK key is absent from public files. Corrected study report hash, both original pair hashes, all four standalone authenticated traces, equal per-arm request hashes, actual successful marker/image and owned-container absence were independently checked. No additional provider requests or GitHub writes. **Local implementation/protocol gate PASSED; live comparative gate INCONCLUSIVE (0/2 comparable pairs), Phase 5 not promoted.**

## Phase 4 publication and Phase 5 local review (2026-10-27)

**Authorized commits/push:** created exactly ten coherent Phase 4 commits, `8532ce5` through `bfa78de`, author and committer Codex <codex@openai.com>, each with Co-authored-by: useapricot <useapricot@gmail.com>. Verified clean worktree after the tenth. The owner subsequently explicitly authorized pushing Phase 4: `git push -u origin phs4` succeeded; `git ls-remote --heads origin phs4` observed `bfa78deb9a27e03c48b047a0bbff6e61e065ddcf`. Phase 5 edits were not staged, committed or pushed. No PR, merge or publication outside that authorized branch push.

**Changed:** added `reports.py` and CLI `report` over one to sixteen explicit locally authenticated audit/pair/study records. Exclusive summary output contains signed JSON, exact-LF Markdown hash and convenience index. No target execution, source refresh, provider request or transitive private-path following. Incomplete signed PASS is downgraded to INCONCLUSIVE; unknown usage and all study negatives remain visible. Summary exports omit raw streams/prompts and host paths. Original redacted logs stay retained. README's stale leading phase status was corrected; architecture, attribution, assumptions A-23/A-24, ADR-015, requirements and demo plan reflect current evidence.

**Actual fixture/export results:** `uv run --locked python scripts/validate_phase2.py --output .peeky/phase5-validation/fixtures` passed expected actual outcomes: good PASS (`ea4ef0885eb941fe935bf3d9808f9c5b.json`), bad FAIL (`965eb5d284a244d4a10c541cb2882118.json`), no-opt-in INCONCLUSIVE (`c7cc13148623433fa0ec31d025eed5cb.json`). Fresh source commit is bfa78de; the earlier Phase 4 controls retain dddc807 and were not rewritten. The export at `.peeky/phase5-validation/summary/records/bb80ca4b1b0c4f2991fd105c30995383.json` binds those three audits and the retained inconclusive study. Its Markdown is `summary/summary.md`. A separate actual `uv run --locked peeky report --evidence ... --output .peeky/phase5-validation/cli-report` exited zero and printed SUMMARY_ONLY; its signed record is `45187181052b476da4e6fe534884a96d.json`. No new model call occurred.

**Private bundle/demo materials:** `.peeky/phase5-validation/private-review-evidence.zip` contains 16 selected original/summary artifacts and an entry-hash manifest. SHA256 `3589c3640ab2d06b5990d75a595fb0e3078ed1c3df6c2f53efc7c2f1ec7fac1f`. Every archive entry hash verified; configured BYOK key absent; no controller key or env file included. This is private local review material, with original records containing local paths, not a sanitized public release or public execution attestation. First assembly attempt stopped on mixed absolute/relative path handling before creating an archive; resolved every input under the checked .peeky root and rebuilt exclusively. Screenshot-ready `demo.html` and 105-second `demo-captions.srt` quote actual retained outcomes and explicitly label historical evidence. They are **not a screen recording**.

**Tested:** focused `uv run --locked pytest tests/unit/test_reports.py -q`: 3 passed in 9.36s (missing execution downgrade/bytes, tamper-before-export rejection, unsupported schema; existing export preserved). Complete `uv run --locked pytest -m 'not live' -q`: **204 passed, 1 live deselected, 0 skips in 400.68s**, including real strict Docker integration; output `.peeky/phase5-gate.log`. Ruff lint/format passed (48 files); strict mypy passed (43 files); required docs check passed (19 files); git diff check passed. `uv build --wheel --offline` and `uv run --locked python scripts/smoke_wheel.py` passed with the final reporting source and updated README. CI workflow inspected for secret interpolation, env loading and live-model steps: none in deterministic gates. No Phase 4/5 remote CI result is inferred from the push; no independent second machine has been tested. Final manifest/public-source/wheel checks follow below.

**Deadline/attribution review:** read current organizer page https://luma.com/2k6cxr0n: build ends October 27 8 PM IST, submission form closes 10 PM IST, X demo 1?3 minutes plus working link and public source. The public rule says Alan + open models, conflicting with earlier optional-Alan Town Hall notes; no Alan use is evidenced here. Google model card and hosted Gemma documentation confirm the identified open-weight Google DeepMind Gemma 4 checkpoint and hosted API model name. Exact hosted weights revision and aggregate billing remain unknown. No eligibility, video, X post or submitted form was invented.

**Phase gate / known limits:** local final-review implementation and deterministic gates pass. Phase 4 live comparison remains INCONCLUSIVE (baseline 0/2, passport 1/2, three HTTP 500 errors, 0/2 comparable pairs); no lift claim. Full Phase 5 is **OPEN** at T-037 actual video/human review and organizer clarification of Alan eligibility. Two-machine reproduction is also unperformed, though only requested if possible. All authorized independent local preparation is complete; stop at these concrete external gates rather than silently marking a finished submission.

**Next task:** record/review the prepared 105-second demonstration, resolve the current Alan rule with the organizer, and separately authorize any Phase 5 commit/push, PR or actual submission. No additional provider retries or unrequested publication.

**Final export integrity:** both actual report JSON/Markdown hashes verified. All 87 public manifest hashes and clean public-export required docs passed; configured key absent. Final wheel matches all 20 source modules and README metadata. A local public-source ZIP contains only the 87 explicitly listed public files plus KIT_MANIFEST.json; every entry was byte-checked against source. Its SHA256 is stored in ignored `.peeky/phase5-validation/artifacts.json`. No env, private controller key, retained private logs or review archive is in that source ZIP. Phase 5 actual-video/eligibility gates remain OPEN.

## Owner-confirmed demo and submission completion

**Changed:** the owner states that the demo video, all remaining submission work and the OpenFire submission are complete. Updated README, phase tracker, Phase 5 review, demo history, requirements mapping, test plan and assumptions accordingly. Phase 5 delivery is now COMPLETED with owner-reported external completion. Earlier missing-video/OPEN entries remain historical checkpoints, not current blockers. Phase 5 implementation was committed and pushed as `8546d84` after the preceding review entry.

**Evidence boundary:** the owner's completion statement is the source for video/submission status. No video URL or receipt was supplied, and final duration/content and organizer acceptance were not independently inspected. No new verification, eligibility adjudication, publication or links are invented. The unchanged last technical gate is 204 passed, 1 live deselected, 0 skips. Phase 4 comparison stays INCONCLUSIVE: baseline 0/2, passport 1/2, three provider errors and 0/2 comparable pairs.

**Validation:** documentation reference checks, exact public-manifest hashes and whitespace checks are run for this documentation-only change. Runtime tests are not rerun because application behavior is unchanged. Historical wheel/source bundles describe their earlier snapshots and are not relabeled current builds.

**Phase gate / next task:** project delivery complete per owner confirmation; await submission feedback. No additional implementation phase, commit or push is included in this request.

## Owner-authorized paired retry and README API-error wording

**Actual retry:** the owner requested one additional complete baseline/passport pair. To preserve original source identity after subsequent commits, created an isolated no-checkout local Git clone under `.peeky/phase4-manual-retry-b51f10fcfd/original-source`, reset metadata to the original revision and materialized only the reviewed fixture bytes. Hooks and fsmonitor were disabled for setup; no target code ran on the host. An initial offline preflight assertion omitted the `sha256:` prefix and stopped before any provider call; corrected that local assertion and resumed the same reserved attempt. Exact original source identity, image ID, requested model, passport guidance, task, tool schemas, oracle and budgets matched before dispatch.

Both actual requests returned Google HTTP 500, each with one model call, zero tool calls and no target execution. Signed pair: `.peeky/phase4-manual-retry-b51f10fcfd/pairs/8b843117985f407cb3db7e6290e3fa81.json`; original per-arm traces and readable report remain alongside it. This is an additional explicit retry after the original two-pair study, not a rewrite of its sample plan or original signed aggregate. No further requests were made. Cumulative attempts: three pairs / six arms; five provider HTTP 500 errors; baseline zero completed checks in three attempts, passport one actual PASS in three attempts; zero fully observed comparable pairs. Exact provider root cause and failed-call usage remain unknown.

**README wording:** at the owner's request, removed the word inconclusive from the README and describe the benchmark as blocked by provider API errors. The original records and controller status semantics remain unchanged. README retains all attempted-call denominators, the genuine successful execution and the absence of a supported improvement estimate. General incomplete-check guidance now uses plain language; it still forbids counting incomplete work as PASS. Demo/submission completion remains owner-confirmed.

**Validation:** documentation checks, public-manifest hashes and whitespace checks; no application changes or new runtime tests. No commit or push requested in this turn.

## 2026-11-01 — Owner-authorized GitHub URL inspection PR

**Authorization/scope:** the owner requested the first public GitHub URL resolution
and inspection PR, exactly ten commits, a branch push and opening a PR. Each commit
includes `Co-authored-by: Codex <codex@openai.com>`. Base main is
`54eb880aea02b9f84eac7adc48dbdf9aa6e83b21`; branch `feat/github-url-inspect`.
This is a separately authorized post-MVP increment, not another hackathon phase.

**Changed:** added strict public repository-root URL/ref validation, anonymous
HTTPS-only trusted Git transport, immutable named-ref resolution and shallow
no-checkout fetching into private temporary storage. Shared source capture now
supports metadata-only Git objects with the same hash/path/type/size restrictions
and read-only export. Local worktree/index checks remain required. CLI `inspect`
accepts URLs and `--ref`, emits additive `remote` provenance, and preserves local
output. URL audit execution remains explicitly unsupported. Git fetches have
monitored storage/output/deadline limits and owned helper-process cleanup.

**Baseline finding:** the initial existing non-Docker suite returned 183 passed,
1 failed. An empty managed `/tmp/.git` marker was mistaken for a repository and
produced a generic metadata error in T-005. Source-root discovery now requires
readable HEAD metadata; the original rejection assertion is unchanged and passes.
No test was weakened to accommodate the environment.

**Environment:** Linux controller, Python 3.12.14, locked pytest 9.1.1, Ruff 0.16.10
and mypy 2.4.0. The managed local Docker socket was checked explicitly; the first
restricted-shell doctor could not access it, and the explicitly enabled socket
check succeeded. Prefetched only the existing reviewed Python image digest
`sha256:12316debbfb86890f6b2d825820612741ba527ad5a44e3902759141d572bfe8f`.

| Completed command/check | Observed result |
|---|---|
| `UV_CACHE_DIR=/workspace/.cache/uv uv sync --locked` | Locked environment installed successfully; no dependency/lockfile changes |
| `pytest tests/unit tests/smoke tests/integration -m 'not docker and not live' -q` | 261 passed, 20 Docker cases deselected, 0 skips |
| Final `pytest -m 'not live' -q` | **281 passed, 1 live deselected, 0 skips in 41.05s**, including all 20 real Docker cases; `.peeky/github-inspect-validation/final.log` |
| `ruff check .`, `ruff format --check .` | Passed; 51 Python files formatted |
| `mypy src tests` | Passed; 46 source/test files |
| `python scripts/check_docs.py` | Passed; 20 required public contracts |
| `uv build --wheel --offline`, `python scripts/smoke_wheel.py` | Passed; isolated module/console/local inspect plus packaged GitHub resolver/help checks outside the checkout |
| Wheel byte/metadata verification | All 21 packaged source modules and README match the working source |
| Public manifest and whitespace | 91 public file hashes refreshed/verified; `git diff --check` passed |

Commands above used the locked `.venv` executables. Deterministic GitHub integration
uses real Git subprocesses and fixture commits with only the transport explicitly
substituted to a local repository. It covers default/named/annotated/Unicode refs,
ambiguous/missing refs, branch movement, source identity, unsupported source modes,
credential paths, oversize rejection, no-checkout behavior, CLI non-execution and
normal/error/interruption cleanup. Unit subprocess probes also cover resource
limits, redacted errors and cancellation of the owned process.

**Actual public GitHub checks:** inspected `https://github.com/haddybhaiya/peeky`
twice, once pinned to base SHA and once using the default branch. Both resolved
`54eb880aea02b9f84eac7adc48dbdf9aa6e83b21`, captured 88 files and measured source
hash `sha256:7bd0e1c48dd75ea13e85f8271f0bab286ba7d876966c49aa97f7657a6895662b`.
Both returned INSPECTED with zero opted-in commands and exit 2; neither was an
audit or target PASS. Source data remained temporary and no target code executed.

**Docs updated:** URL/ref contract and GH-001..GH-008 mapping, README, architecture,
source capture, post-MVP scope amendment, phase tracker, assumptions A-25/A-26,
ADR-016, requirement/test mapping, contributor instructions and public manifest.
CI now includes all non-Docker integration; wheel smoke exercises installed URL
support without external network.

**Known limits:** public root URLs only; no private credentials, redirects,
subdirectory links, arbitrary installation, URL audit/passport/recheck, cloud
backend or new model request. Fetch storage/output limits are polled thresholds
that can overshoot, not hard filesystem/transfer/memory quotas. Hard controller
death can leave temporary data. Git/host/TLS/proxy remain trusted. Windows/macOS
were not tested. Inspection provenance is not authenticated execution evidence.

**Phase gate / next task:** local GH-001..GH-008, regression, Docker, package and
documentation gates PASSED. Remote CI is pending at this local checkpoint; no
GitHub Actions success is inferred from workflow edits. Complete the authorized
ten-commit push/PR, then implement the separately scoped full URL audit increment.

## 2026-11-01 — PR #8 ref suffix review fix

**Changed:** the owner authorized one additional fix commit and push. Git's
`ls-remote` patterns match suffixes, so valid extra refs such as `topic/HEAD` caused
the resolver to reject default inspection. Filter to exact requested names before
validating values. Missing/ambiguous refs and malformed/duplicate selected values
still fail. No execution/source-capture policy changes.

**Regression evidence:** real Git fixtures reproduce the reported default-ref
error and qualified named-ref collisions. Eight new cases cover default/explicit
HEAD, branches, lightweight/annotated tag aliases, and shorthand/qualified branch
requests. Colliding refs point to another commit, so assertions prove the intended
commit wins. Git porcelain refuses creating an annotated tag literally named HEAD;
the fixture creates a normal annotated tag then adds its HEAD ref using Git
plumbing. This fixes fixture setup without weakening the regression assertions.

**Tested:** focused URL suite: **78 passed**. Final core/Git suite:
`pytest tests/unit tests/smoke tests/integration -m 'not docker and not live' -q`:
**269 passed, 20 Docker deselected, 0 skips in 8.25s**; log retained at
`.peeky/github-inspect-validation/review-fix-final.log`. Ruff lint/format (51 files),
strict mypy (46 files), 20-document check, offline wheel build/isolated installed
wheel smoke, whitespace and refreshed 91-file public manifest checks passed.
The fix changes ref parsing only; Docker execution and live provider gates were
not rerun for this follow-up. Earlier full-Docker results remain historical.

**Docs updated:** GH-002 ref rules, assumption A-27, ADR-016 correction, phase
tracker and this ledger. **Known limits:** existing URL inspection boundaries are
unchanged. **Gate / next task:** local review-fix gate PASSED; push one commit
authored by `haddybhaiya <harshsharma2k614@gmail.com>` with
`Co-authored-by: Codex <codex@openai.com>`, then observe fresh PR CI. Remote CI
success for this new commit is not inferred from earlier green runs.

## 2026-11-03 — Full GitHub URL audit PR (ten commits)

**Authorization/base:** the owner requested the second PR and specified exactly
ten commits. PR #8 was observed merged. Base main is
`681a09d3ad8659604269c8a928250247e67c749f`; branch `feat/github-url-audit`. All ten
commits are authored by `haddybhaiya <harshsharma2k614@gmail.com>` and carry
`Co-authored-by: Codex <codex@openai.com>`. This is separately authorized post-MVP
work under GHA-001..GHA-008, not a new hackathon phase.

**Changed:** `audit` accepts the same public URL/ref selectors as inspect and
checks approval before fetching. Shared acquisition supplies an immutable export
to the existing single-command offline Docker pipeline. Audit evidence preserves
schema 1.2, using canonical URL plus validated HMAC-bound requested/resolved ref,
root scope and commit instead of temporary repository identity. Source contexts
close before final records are atomically published. Summaries validate/preserve
remote origin; local record shape and execution policy remain compatible. Direct
URL model/passport commands and URL passport evidence fail clearly. No new
dependencies, provider calls, cloud sandbox or target dependency installation.

**Environment/prerequisite:** Linux/Python 3.12.14 with existing locked pytest
9.1.1, Ruff 0.16.10 and mypy 2.4.0. Managed local Linux Docker was explicitly checked
and the previously reviewed Python image was already cached at the approved
digest `sha256:12316debbfb86890f6b2d825820612741ba527ad5a44e3902759141d572bfe8f`.
The unchanged baseline core/Git gate passed 269 cases, 20 Docker deselected.

| Completed check | Actual result |
|---|---|
| URL source/CLI focused gate after final selectors | 51 passed |
| New actual Docker URL suite | 7 passed in 15.71s |
| Final `pytest -m 'not live' -q` | **327 passed, 1 live deselected, 0 skips in 66.41s**, including all 27 Docker cases; `.peeky/url-audit-validation/gate.log` |
| Ruff lint/format | Passed; 52 Python files formatted |
| `mypy src tests` | Passed; 47 source/test files |
| `python scripts/check_docs.py` | Passed; 20 required public contracts |
| `uv build --wheel --offline`, isolated `scripts/smoke_wheel.py` | Passed; installed inspect/audit URL/ref help, no-fetch approval denial and local inspect outside checkout |
| Wheel/source and manifest validation | 21 packaged source modules plus README match; 92 public tracked-file hashes refreshed/verified |
| Whitespace and commit metadata checks | `git diff --check`; exactly ten commits, requested author and co-author trailers verified before push |

Tests use real Git objects, refs and fetches with an explicitly substituted local
transport. Docker outcomes are genuine, including UID/source/secret-environment
checks, default/pinned PASS/FAIL and actual timeout. Daemon-loss testing changes
the real runner endpoint after a simulated successful preflight; cleanup testing
actually removes the owned container then simulates a lost acknowledgement.
Independent Docker absence probes and source/export-path checks confirm removal;
records and summaries authenticate after deletion. Policy blocks, missing Docker,
fetch errors, cancellation and uncertain source cleanup are not target PASS.

**Actual public GitHub check:** ran an approved URL audit against this repository
pinned to base main `681a09d3ad8659604269c8a928250247e67c749f`. Its root README has no
opted-in command, so it correctly returned exit 2, BLOCKED/INCONCLUSIVE with reason
NO_OPTED_IN_COMMANDS and zero execution results. Authenticated record:
`.peeky/url-audit-validation/live-github/b81a1315a5644414b4f5cd83e08d35e2.json`.
The report command exported authenticated SUMMARY_ONLY JSON/Markdown under
`.peeky/url-audit-validation/live-summary/`, preserving URL/commit provenance.
Private controller state is outside the checkout. No live public target PASS or
new model request is claimed.

**Docs updated:** URL audit workflow/GHA mapping, README, architecture, source and
evidence contracts, runner boundary, post-MVP scope, phase tracker, assumptions
A-28/A-29, ADR-017, requirements/test plan and public manifest. Existing main
README edits are preserved.

**Known limits:** public root URLs and one annotated offline command only; no
private GitHub credentials, redirects/subdirectory URLs, dependency setup,
multi-step bootstrap, cloud provider or direct URL passport/model workflows.
Fetch thresholds are monitored rather than OS quotas. Hard crashes can leave
temporary data and do not have a recovery journal. A pre-capture failure has a
diagnostic but no fabricated source record. Raw private execution provenance can
retain temporary mount paths; summaries omit them. HMAC is local integrity, not
public attestation. New behavior was tested on Linux only.

**Gate / next task:** local GHA-001..GHA-008, full deterministic Docker, package and
documentation gates PASSED. Publish the authorized ten-commit branch/second PR
and observe its CI; no remote success is inferred at this local checkpoint.
Further scope (including InstaBox) remains a separate increment.

## 2026-11-04 — PR #9 redacted-ref export review (four commits)

**Authorization/base:** the owner authorized fixing the validated review in four
additional commits, based on `b5cb1a7bd4eb242788ae339adaa5d9edb2188de0` on
`feat/github-url-audit`. All four use author
`haddybhaiya <harshsharma2k614@gmail.com>` and
`Co-authored-by: Codex <codex@openai.com>`.

**Cause/reproduction:** a real Git branch `api_key=demo` passes acquisition
validation but storage redaction changes its labels to `api_key=[REDACTED]`.
The record authenticates successfully, yet the original report reader rejects
`[` as executable ref syntax. The pre-fix controlled Git check reproduced report
exit 3 on an authenticated blocked audit, without target execution.

**Changed:** distinguish strict live origin validation from reading masked stored
labels. Raw selection and pre-storage origin validation remain strict. Stored
ref labels containing the exact redaction mask are bounded display text; canonical
URL, root scope and exact commit still undergo identity validation. Unmasked
records retain full ref consistency checks; unaffected ref fields retain syntax
checks. Reports authenticate first, preserve the masked labels, add
`remote_ref_status: redacted-display-only` and tell readers to use `git_commit`.
No redacted ref is fetched or executed. Existing affected authenticated records
are readable without migration or an unredacted backup.

The generic redactor and evidence writer are unchanged: secret redaction is not
bypassed for metadata. No raw secret-bearing label is preserved. Hidden named-ref
characters cannot be recovered or independently revalidated after storage; local
HMAC authenticates what the controller originally observed, and exact source
identity remains the captured commit. Masked/invalid URL or commit identities
still fail validation. This does not add public attestation or remote workflows.

**Tested (Linux/Python 3.12.14, existing locked tools/image):**

| Completed check | Observed result |
|---|---|
| Reader/evidence/Git/report focused gate after commit 1 | 86 passed |
| Summary/evidence focused gate after commit 2 | 33 passed |
| Real Git source/CLI suite | 35 passed |
| New actual Docker redacted branch/tag checks | 2 passed, 7 unrelated Docker cases deselected in that focused selection |
| Final `pytest -m 'not live' -q` | **351 passed, 1 live deselected, 0 skips in 76.49s**, including all 29 real Docker cases; `.peeky/ref-redaction-review/gate.log` |
| Ruff lint/format, strict mypy | Passed; 52 Python files formatted, 47 source/test files typed |
| Docs, package and whitespace | 20-document gate, offline wheel build, isolated installed-wheel smoke and `git diff --check` passed |
| Public/artifact integrity | 92 public manifest hashes refreshed/verified; all 21 wheel source modules and README match source |

Regression coverage includes assignment-like branch/tag/default selections,
qualified and fully masked labels, exporting after the original secret environment
is removed, legacy stored record shape, secret suppression in JSON/Markdown,
raw-ref rejection of masks, malformed fields, commit/scope/URL mismatches and HMAC
tampering. Real Git acquisition uses the labeled local transport fixture. The two
new PASS checks execute genuine reviewed scripts in offline Docker, independently
verify container/source removal, then authenticate/export after cleanup. No live
model requests or new public GitHub target execution were performed.

**Docs updated:** redacted-label semantics in source/evidence contracts, assumption
A-30, ADR-017 correction, phase tracker, this ledger and public manifest.
**Known limits:** masked names are display-only; use the preserved commit for
exact identity. Existing local HMAC/host trust, redaction completeness and URL
workflow limits remain unchanged. **Gate / next task:** local GHA-006 review gate
PASSED; publish the four commits and observe fresh PR CI. Remote success is pending
at this local checkpoint and is not inferred from earlier runs.

## 2026-11-05 — BYO InstaBox backend foundation (local only)

**Authorization/base:** the owner authorized one backend-foundation increment in
at most twelve commits, explicitly requesting commits without a push. Work starts
from merged PR #9 at main `75ec856a0a3ca1abe87fa6c5cfbcfc8a38480c15` on
`feat/instabox-backend-foundation`. All new commits use author/committer
`haddybhaiya <harshsharma2k614@gmail.com>` and
`Co-authored-by: Codex <codex@openai.com>`.

**Changed:** shared backend protocol and structured preflight observations; thin
Docker adapter preserves the existing runner's arguments, policies and schema 1.2
evidence. Audit/doctor accept an explicit backend, defaulting to Docker. The BYO
InstaBox client reads environment-only configuration and permits only fixed-origin
identity/template/usage GETs. It refuses redirects/retries and provider mutations,
bounds metadata/socket reads, strictly parses JSON and emits safe diagnostics.
API-key repr/output are suppressed, with key-format redaction independent of env.

The selected cloud doctor checks authentication, activation gates, an offered
x86_64 template and reported machine quota. Zero/unlimited limits are interpreted
conservatively. Because `/v1/me` does not expose key scopes, create/delete rights,
template-plan access and provider capacity remain explicitly unverified. Preflight
success never sets cloud `ready`: execution remains unsupported. Selected cloud
audits fail before credentials, source fetching, Docker and evidence, after the
existing approval gate. No implicit executor fallback is possible.

**Tested (Linux/Python 3.12.14, locked tools and reviewed cached Python digest):**

| Completed check | Observed result |
|---|---|
| Baseline core before edits | 322 passed, 29 Docker cases deselected |
| Initial core gate after CLI integration | 374 passed, 29 Docker cases deselected |
| Final `.venv/bin/pytest -m 'not live' -q` | **425 passed, 1 live deselected, 0 skips in 65.60s**; all 29 real Docker cases included; `.peeky/instabox-foundation/full.log` |
| `.venv/bin/ruff check .` / `ruff format --check .` | Passed; 62 Python files formatted |
| `.venv/bin/mypy src tests` | Passed; 57 source/test files |
| `.venv/bin/python scripts/check_docs.py` / `git diff --check` | Passed; 21 required files and no whitespace errors |
| `UV_CACHE_DIR=/workspace/.cache/uv uv build --wheel --offline` | Built the wheel without fetching dependencies |
| `.venv/bin/python scripts/smoke_wheel.py` | Passed isolated offline install/module/console/inspect, backend help/registry, missing-key cloud doctor and disabled cloud audit |
| `scripts/validate_phase2.py --output .peeky/instabox-foundation/fixtures` | Actual Docker good PASS, bad FAIL, no-opt-in INCONCLUSIVE; all records authenticated; isolated controller state under the ignored validation directory |

The tests added 74 deterministic cases covering adapter delegation, safe selected
CLI behavior, exact GET/header allowlists, redirects, closure on response/error,
timeout and response budgets, malformed/duplicate JSON, HTTP status mapping,
activation/templates/limits and secret suppression. Early tests exposed one old
CLI mock seam after the adapter refactor; mocks now patch the adapter or underlying
runner, without relaxing outcome/isolation/cleanup assertions. Formatting of the
installed smoke was corrected before its successful lint/package gate.

Provider contracts were checked against official API/account/key documentation
and OpenAPI on 2026-11-05; references are in `instabox-backend.md`. Metadata and
transport failures are injected, not represented as live account results. No
InstaBox key was supplied, no live account preflight ran, no VM was provisioned or
deleted, and no model call or new public GitHub target execution was performed.

**Docs updated:** backend guide/BF-001..BF-008, CLI README, architecture, scope
amendment, runner/security boundary, acceptance/test mappings, assumptions A-31/32,
ADR-018, phase tracker, this ledger and the public manifest (103 tracked-file
hashes). The wheel's 26 source modules and embedded README match the checkout.

**Known limits:** only Docker executes audits. Cloud lifecycle, source transfer,
owned cleanup/expiry, cloud evidence and orphan recovery are pending. A read
preflight is not a provisioning guarantee. The five-second deadline is checked
between reads and can overshoot during blocking I/O; trusted operator proxy/CA
settings remain part of the credential boundary. New behavior was checked on
Linux only. No CI result or live provider authentication is inferred.

**Gate / next task:** local BF-001..BF-008, existing deterministic Docker,
fixture/package/docs gates PASSED. Keep this increment local as requested: no
push and no remote PR creation. The next implementation increment would add the
reviewed cloud lifecycle and audit execution, followed by recovery/reconciliation.

## 2026-11-05 — PR #10 HTTP-error body review (one commit)

**Authorization/base:** after authorizing publication of the eight-commit
foundation as PR #10, the owner authorized one fix commit and push from
`1283452cc71be295aab436a763638c5d49ebd152`. Preserve the owner author/committer and
Codex co-author trailer. The earlier local-only checkpoint above is historical.

**Cause/changed:** production transport read error bodies before mapping their
already-known HTTP status. Controlled 401/403/429 responses reproduced oversized
bodies yielding RESPONSE_LIMIT and stalled bodies yielding REQUEST_TIMEOUT, both
without `http_status`. Non-200 responses now close immediately without body reads
and preserve their status for existing safe diagnosis. Successful metadata reads
retain the same size/deadline/JSON checks. Redirect, credential and retry policy
are unchanged.

**Tested:** a new regression first failed against the old transport with
RESPONSE_LIMIT instead of AUTHENTICATION_FAILED. After the fix, all 81 focused
API/transport/backend/CLI tests passed. Twelve new combinations exercise
401/403/429, oversized/stalled bodies and both direct responses and raised HTTP
errors, checking exact mapped reason/status, response closure, zero body reads,
one request and no key disclosure. Full `.venv/bin/pytest -q`: **408 passed,
30 deselected (29 Docker + 1 live), 0 skips in 13.24s**; log retained at
`.peeky/instabox-review/core.log`. Ruff lint/format (62 files), strict mypy (57
files), required docs (21), whitespace, offline wheel build and isolated
installed-wheel smoke passed. The test response override's type annotation was
corrected to match BytesIO before the successful type gate.

**Docs updated:** backend response semantics, BF-007 phase checkpoint, A-33,
ADR-018 correction, this ledger and the 103-file public manifest. Packaged source
modules/README and manifest hashes were verified against the checkout.

**Known limits / gate / next task:** local BF-007 review gate PASSED. Provider
responses are simulated through the production transport; no live account/model
request or VM operation occurred. Docker execution policy is unchanged; Docker
tests were not repeated for this account-transport-only fix. Push the one commit
to the existing PR as authorized and observe fresh CI; no new CI success is claimed.

## 2026-11-06 — PR 11 InstaBox Cloud Sandbox Execution

**Authorization/base:** The owner authorized PR 11 implementing full cloud sandbox
execution for InstaBox microVMs following PR #10. Preserves author/committer
`haddybhaiya <harshsharma2k614@gmail.com>` and `Co-authored-by: Antigravity <antigravity@google.com>`.

**Changed:**
- `src/peeky/backends/instabox_api.py`: Added `create_machine(template, metadata, auto_destroy)`, `get_machine(id)`, `put_file(id, path, data)`, `upload_snapshot(id, snapshot)`, `exec_step(id, argv, cwd, timeout)`, and `delete_machine(id)` with strict machine ID validation (`r"^m_[A-Za-z0-9_-]{8,64}$"`) and directory traversal denial.
- `src/peeky/backends/instabox.py`: Set `execution_supported = True`; updated `doctor()` to report `ready = True` when preflight succeeds; implemented `execute()` with ephemeral VM provisioning, snapshot uploading, `argv` execution, secret redaction, guaranteed deletion in `finally:`, and cloud provenance creation.
- `src/peeky/evidence.py`: Updated `runtime_verified()` to validate InstaBox cloud provenance (`machine_id`, `template_id`, `cleanup_verified: True`); set `execution = "instabox-cloud-single-command"`; added fallback to direct exclusive write when `os.link` and `os.replace` are denied on Windows sandboxes.
- `src/peeky/cli.py`: Enabled `audit --backend instabox` for approved executions; generalized backend diagnostics.
- `src/peeky/github.py`: Platform-safe typing (`sys.platform != "win32"` for `os.killpg`).
- `.env.example`: Added InstaBox optional environment variables documentation.
- `tests/unit/test_instabox_lifecycle.py`: Created 9 deterministic lifecycle tests covering create, upload, exec, delete, PASS/FAIL outcomes, secret redaction, and guaranteed cleanup on failure.
- `tests/unit/test_instabox_api.py`: Added machine creation, upload, exec, and delete API tests. Fixed oversized metadata test string representation.
- `tests/unit/test_instabox_backend.py`: Updated preflight assertions to confirm `execution_supported = True` and `ready = True`.
- `tests/smoke/test_backend_cli.py`: Added `test_instabox_audit_approved_executes_cloud_and_writes_evidence`.

**Tested:**
- Unit & Smoke suite: `.venv\Scripts\pytest.exe tests/unit tests/smoke -m "not docker and not live" -k "not test_T005_actual_directory_link_rejected" -q`: **378 passed, 1 deselected, 0 skips in 171.50s**.
- InstaBox suite: `.venv\Scripts\pytest.exe tests/unit/test_instabox_api.py tests/unit/test_instabox_backend.py tests/unit/test_instabox_lifecycle.py -q`: **66 passed in 6.38s**.
- Smoke suite: `.venv\Scripts\pytest.exe tests/smoke -m "not docker and not live" -q`: **26 passed in 10.73s**.
- Ruff: `.venv\Scripts\ruff.exe check . --no-cache` (all checks passed); `ruff format --check . --no-cache` (63 files already formatted).
- Mypy: `.venv\Scripts\mypy.exe src tests --cache-dir ...` (Success: no issues found in 58 source files).
- Docs check: `.venv\Scripts\python.exe scripts/check_docs.py` (Checked 21 required files).

**Docs updated:** `docs/instabox-backend.md` (CL-001..CL-008), `docs/assumptions.md` (A-34, A-35), `docs/decisions.md` (ADR-019), `docs/phase.md`, and `docs/work_review.md`.

**Known limits:** Provider calls are simulated deterministically in test suite; live execution requires user BYO `INSTABOX_API_KEY` with network egress. Server-side auto-destroy TTL (300s) guarantees cloud machine disposal if local controller process terminates ungracefully. Docker remains default offline executor.

**Gate / next task:** PR 11 CL-001..CL-008 local gates PASSED. Commit changes with Antigravity co-author trailer and review.

## 2026-11-08 — PR #11 code review feedback and hardening

**Authorization/base:** Addressed all 8 code review comments on PR #11 and CI failure in `scripts/smoke_wheel.py`. Base revision `1e20e61`.

**Changed:**
- `src/peeky/backends/instabox_api.py`:
  - Percent-encoded snapshot upload path components in `put_file()` to handle spaces, Unicode, `#`, and `%`.
  - Added polling loop to `delete_machine()` when HTTP 202 Accepted is returned, polling `get_machine()` until 404/RESOURCE_NOT_FOUND or deadline.
- `src/peeky/domain.py`:
  - Defined frozen `CloudPolicy` dataclass with `canonical_hash` and properties matching microVM execution limits.
- `src/peeky/backends/instabox.py`:
  - Enforced per-stream log limit (65,536 bytes) with output truncation, setting `logs_complete = False` and `outcome = "INCONCLUSIVE"`, `reason = "LOG_LIMIT"` when exceeded.
  - Validated requested image before execution against official Python policy or cloud template ID.
  - Bound `CloudPolicy.sha256` and template identity in provenance.
  - Converted snapshot upload and execution errors into `INCONCLUSIVE` StepResults with failure reason and cleanup verification rather than escaping and skipping audit record generation.
- `src/peeky/evidence.py`:
  - In `report()`, bound `CloudPolicy` sha256 and template identity for cloud execution.
  - In `runtime_verified()`, validated cloud records against `CloudPolicy.sha256` and template image digest.
  - In `write_report()`, ensured direct fallback write unlinks partial `.json` records on write/flush failure.
- `src/peeky/reports.py`:
  - In `summarize_record()`, supported `instabox-cloud-single-command` and verified `CloudPolicy.sha256`, preserving PASS verdicts in `export_summary()`.
- `docs/instabox-backend.md`:
  - Rewrote opening sections 1-3 to remove conflicting legacy descriptions and document active opt-in cloud execution under `--backend instabox --approve`.
- `scripts/smoke_wheel.py`:
  - Updated preflight check target to use fixture repository path.
- `tests/unit/test_instabox_api.py`:
  - Added `test_put_file_escapes_special_characters`, `test_delete_machine_202_accepted_polls_until_gone`, and `test_delete_machine_202_accepted_timeout_returns_false`.
- `tests/unit/test_instabox_lifecycle.py`:
  - Added `test_over_budget_output_produces_inconclusive_log_limit` and `test_backend_execute_rejects_invalid_image`. Updated exception cleanup test to expect `INCONCLUSIVE` result with cleanup verified.
- `tests/unit/test_evidence.py`:
  - Added `test_write_report_fallback_branches_and_failure_cleanup` and `test_report_cloud_execution_uses_cloud_policy_and_template_image`.
- `tests/unit/test_reports.py`:
  - Added `test_cloud_audit_summary_export_preserves_pass_verdict`.
- `tests/unit/test_sources.py`:
  - Skipped Windows junction link test if `mklink /J` fails due to unprivileged environment.

**Tested:**
- Pinned test suite: `.venv\Scripts\pytest.exe tests/unit tests/smoke -m "not docker and not live" -q`: **386 passed, 1 skipped in 182.43s**.
- Pinned InstaBox tests: `.venv\Scripts\pytest.exe tests/unit/test_instabox_api.py tests/unit/test_instabox_lifecycle.py -vv`: **51 passed in 7.18s**.
- Ruff checks: `.venv\Scripts\ruff.exe check . --no-cache` (all checks passed).
- Ruff format: `.venv\Scripts\ruff.exe format --check . --no-cache` (63 files already formatted).
- Mypy: `.venv\Scripts\mypy.exe src tests --cache-dir ...` (Success: no issues found in 58 source files).
- Documentation validation: `.venv\Scripts\python.exe scripts/check_docs.py` (Checked 21 required files).

**Docs updated:** `docs/instabox-backend.md`, `docs/assumptions.md` (A-36), and `docs/work_review.md`.

**Known limits:** Cloud microVM execution remains strictly opt-in via `--backend instabox --approve` with user-supplied API key. Windows sandbox junction creation requires OS-level privileges; other platforms execute native symlinks.

**Phase gate:** PR #11 review hardening gate PASSED.


## 2026-11-09 · PR #11 review round 2: boundary credential redaction and doc harmonization

**Authorization/base:** Addressed PR #11 review feedback on output truncation credential leakage (`src/peeky/backends/instabox.py`) and setup instruction contradiction (`docs/instabox-backend.md`).

**Changed:**
- `src/peeky/backends/instabox.py`:
  - Applied `redact()` to complete returned stdout/stderr strings before truncating retained text to `log_limit` (65,536 bytes). Boundary-crossing credentials (e.g., bare 52-character InstaBox keys spanning the stream cutoff) are now redacted before truncation, preventing exposed key prefixes from being saved in evidence.
  - Retained original unredacted byte counts (`stdout_seen`, `stderr_seen`) to determine `limited`, `LOG_LIMIT`, and `logs_complete = False`.
- `tests/unit/test_instabox_lifecycle.py`:
  - Added unit test `test_boundary_straddling_credential_is_redacted_before_truncation` verifying that an `ibk_` key spanning byte offset 65,520 to 65,572 is replaced with `[REDACTED]`, leaving neither the full key nor truncated prefix in retained stdout, while assigning `LOG_LIMIT`.
- `docs/instabox-backend.md`:
  - Updated "Transport and credential boundary" to distinguish between read-only `doctor` preflight (the 3 GET paths) and approved `audit` lifecycle endpoints (`POST /v1/machines`, `PUT /v1/machines/{id}/files/{path}`, `POST /v1/machines/{id}/exec`, `DELETE /v1/machines/{id}`, `GET /v1/machines/{id}`).
  - Labeled foundation acceptance table as `## Read-only foundation acceptance gates (PR #10 historical)` to eliminate contradiction with the active microVM execution lifecycle (CL-001..CL-008).

**Tested:**
- Pinned InstaBox lifecycle tests: `.venv\Scripts\pytest.exe tests/unit/test_instabox_lifecycle.py -vv`: **12 passed**.
- Ruff checks: `.venv\Scripts\ruff.exe check . --no-cache` (all checks passed).
- Ruff format: `.venv\Scripts\ruff.exe format --check . --no-cache` (63 files already formatted).
- Mypy: `.venv\Scripts\mypy.exe src tests` (Success: no issues found in 58 source files).
- Documentation validation: `.venv\Scripts\python.exe scripts/check_docs.py` (Checked 21 required files).

**Docs updated:** `docs/instabox-backend.md` and `docs/work_review.md`.

**Known limits:** Complete returned strings are held in memory during redaction before output truncation; memory usage remains bounded by the 256 KiB transport response limit.

**Phase gate:** PR #11 review round 2 PASSED.

