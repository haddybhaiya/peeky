# Phase 2 runner, logs and local evidence contract

## Preparation and execution boundary

The reviewed default is official Python `python@sha256:12316debbfb86890f6b2d825820612741ba527ad5a44e3902759141d572bfe8f`. It was prefetched from `library/python:3.12-slim` on 2026-10-27 and observed locally as Linux/amd64. Source, policy and the exact requested/resolved image identity are recorded per run. The image allowlist is controller code, not README/model/config input. To change it, review and update the constant, policy/CI/docs and real gates together.

Image download is a separate trusted setup operation. Audit uses the cache only (`--pull=never`) and refuses mutable tags or unreviewed digests. Before creating a container, it confirms the requested RepoDigest, immutable image ID, Linux OS and absence of image-declared volumes. No arbitrary dependency download, package install or online target setup is supported.

The runner requires a controller-created `SourceSnapshot`; a live Path or a constructed lookalike is rejected. Source byte/file/link integrity is checked before create/start. The chosen step must exactly match the captured README. Only the verified export is mounted, once, read-only at `/repo`. Host source mutation after capture does not change the export. As in Phase 1, the host operator, Docker daemon and filesystem are trusted; these controls do not defeat a hostile concurrent host owner or compromised kernel/daemon.

Host-tool discovery ignores current-directory, relative and target-repository paths, including Windows implicit current-directory executable lookup. Source contents cannot supply the Git/Docker binaries used by the controller.

## One-command stage semantics

Inspect may propose multiple commands, but audit accepts exactly one smoke command per run. No-op and multi-step plans write BLOCKED state with INCONCLUSIVE verdict and zero results. The runner does not imply that independent containers share setup state. Installing dependencies, session-dependent workflows and arbitrary project bootstrap remain unsupported.

Creation, attachment, state inspection and cleanup are separate controller operations. `docker create` is checked before `docker start --attach`; actual inspected State and target-start timestamps distinguish target exit codes from Docker startup/transport errors. A target that really exits 125, 126 or 127 is FAIL; a missing executable or image is infrastructure, not target failure. Exit code is absent when no target exit has been observed, including a still-running timed-out command.

## Enforced and measured restrictions

The effective container configuration is inspected before start. Required settings include Linux, non-root UID/GID 65534, no network, read-only root/source, all capabilities dropped, no-new-privileges, no privileged/device/host PID/IPC access, no extra source or socket mounts, no restart/healthcheck, and no daemon log driver. Only fixed controller environment values are supplied; host credential/environment values are not passed through.

Docker client proxy defaults are explicitly cleared in uppercase/lowercase environment names. Effective environment must exactly match the pinned image plus controller overrides; unknown or duplicate variables block before start. The recorded isolation includes environment names, not host secret values.

Budgets: 256 MiB RAM, equal memory+swap limit (no extra swap), one CPU, 64 PIDs, 128 open files, and a 32 MiB noexec/nosuid/nodev tmpfs at `/tmp`. Command attachment defaults to a 20-second monotonic deadline; callers can only lower it. Docker control calls have separate eight-second metadata budgets. Tests read actual kernel cgroup settings, UID, capabilities and no-new-privileges, attempt forbidden filesystem writes and network egress, and trigger a real container OOM.

Each container has a random name and ownership label. A `finally` path checks that label, forcibly removes only that owned container, and queries for remaining containers under its exact run ID. A zero target exit cannot produce PASS if cleanup is unverified. Timeouts/output limits kill the attached CLI and then remove the owned container, so terminating the client is not mistaken for stopping target execution. Hard controller termination or an unavailable daemon can still prevent cleanup; normal-return uncertainty is visible and never PASS. Do not use broad container pruning to recover an unrelated failure.

## Logs, redaction and retention

Two drainers retain at most 65,536 raw bytes per stream in transient memory, continue draining while the controller reacts, and stop a log-flooding run. Raw stdout/stderr and credentials are not persisted. Retained transcripts preserve observed text after UTF-8 decoding, credential redaction and terminal-control removal; they are not model summaries or just 5,000-character excerpts. Output beyond budget is explicitly incomplete and cannot pass.

Redaction covers known secret environment values, credential assignments and authorization headers, common token/JWT formats, URL queries/user-info and private-key blocks. Environment values are used only for redaction, never injected into containers. Docker's log driver is `none` to avoid another persistent raw container-log copy. This is bounded pattern-based redaction, not a guarantee that every possible secret format is recognized. Unknown hostile repositories still require disposable infrastructure.

Each step records full bounded redacted stdout/stderr, hashes of those stored transcripts, observed input byte counts, completeness, reason code, start/end UTC, monotonic duration, effective timeout, actual container State, image ID/digest, source/policy hashes, create argv, effective isolation and cleanup status. State/control data is sanitized at storage too. Hashes describe redacted retained transcripts, not secret-bearing originals. Coverage reports planned versus observed result slots; full observed coverage does not imply all checks passed or that infrastructure executed a target.

## Local authentication and finalization

Schema 1.2 records carry `integrity`: HMAC-SHA256, controller key ID and canonical payload SHA-256. A random 32-byte controller key lives at `%LOCALAPPDATA%/Peeky/controller.key` on Windows (or `~/.local/state/Peeky/controller.key` on Linux), excluded from Git and tracked source exports. Verification uses the trusted controller key location, never a path supplied by evidence. Do not include this private key in shared evidence bundles. Other hosts need separately trusted key handling; HMAC is not a public signature, third-party attestation or protection from an operator who can read/change the key.

Evidence is sanitized and authenticated before publication. A fully written/fsynced temporary file is linked atomically and exclusively to a unique JSON name, then the temporary name is removed. Existing records are not replaced. This requires a local filesystem supporting hard links (validated on NTFS here); full crash-durable journaling and resumable intermediate state remain unimplemented.

Passport generation now requires schema 1.2, valid local authentication, full source/commit/policy/plan consistency, matching complete zero-exit results, resolved image identity, complete logs and verified cleanup. Older schemas must be rerun. Synthetic signed unit fixtures test consistency/authentication only and are never claimed as Docker runs. Clean docs-repair/retest and benchmark assurance remain later phases.

## Gates and evidence locations

`uv run --locked pytest -m 'not live' -q` includes real Docker cases; selecting Docker tests requires a running Linux daemon and cached reviewed image and fails instead of skipping missing prerequisites. Plain pytest excludes Docker/live by default. CI prefetches the pinned digest in its trusted setup step, then runs the Docker suite and fixture validator; workflow edits alone are not CI success.

`uv run --locked python scripts/validate_phase2.py` audits the committed good, bad and no-op fixtures, verifies their expected PASS/FAIL/INCONCLUSIVE outcomes and local authentication, and retains the original redacted JSON records under `.peeky/phase2-validation/<fixture>/`. `summary.json` is a convenience index, not an authenticated verdict source. Exact local results and remaining CI/platform limits are in `work_review.md`.


## T-014 portability correction

Runner 2.1 records bounded final-State observations to accommodate separate Docker exit/OOM events. Confirmed OOM remains INCONCLUSIVE/MEMORY_LIMIT. Ambiguous 137 without confirmation is INCONCLUSIVE/TERMINATION_UNCERTAIN. The memory test still allocates 600 MiB under the unchanged 256 MiB limit and now explicitly asserts OOMKilled=true; it is not skipped or weakened to accept uncertainty. Separate real explicit-137 and propagated-child-SIGKILL fixtures assert the uncertain classification without an OOM claim. Unit histories cover delayed flags, bounded polling, elapsed deadline and no extra polling for ordinary exits. CI regression and actual results are in work review; a passing local run is not remote CI proof.
