# Runner isolation and security contract

**Threat:** malicious or accidental commands in README; source files whose scripts do unsafe things; hostile model output; unknown dependencies; secrets printed in logs.

## What foundation currently enforces

Annotated fences only; max 12 commands; one command per line; simple `shlex` invocation with no shell metacharacters; python/python3/pytest allowlist; explicit `--approve`; `docker run --rm --pull=never --network none --read-only --cap-drop ALL --security-opt=no-new-privileges --pids-limit=64 --memory=256m --cpus=1 --user 65534:65534 --tmpfs /tmp`; repository bound read-only at /repo; per-command client timeout; stored stdout/stderr excerpt cap. Capture memory is not bounded before truncation, and timeout handling does not explicitly remove a still-running container; see `repository-analysis.md`.

These controls are **not equivalent to secure execution of arbitrary hostile repos**. A malicious Python script still executes code inside the container. Docker shares a kernel with the host and may have exploitable vulnerabilities. Execute unknown code only on disposable infrastructure.

Phase 1 adds committed, bounded source exports to the CLI path: raw Git object identities and index/worktree bytes are checked, source symlink/submodule/reparse paths are denied, and known credential paths/Git metadata are excluded. Inspect never invokes Docker; audit gives Docker a verified temporary export instead of the live input tree. Policy limits and run/plan identities are recorded. Git plumbing is trusted host tooling; target commands, imports, hooks and filters are not executed on the host. See `source-capture.md`. The low-level runner still accepts a Path for its internal fixture API; Phase 2 must enforce the full runner boundary and validate real container behavior.

## Must implement before final MVP

1. Phase 1 completed the CLI source-capture prerequisite (verified Git identities, selected-scope cleanliness, regular bounded exports). Before the final MVP, validate the complete runner boundary on real Docker, including filesystem race assumptions and credential exclusion; do not treat filename checks as a full secret scanner.
2. Verify image digest and fail closed if chosen digest unavailable. CI must pin actual digest, not mutable tag.
3. Redaction of tokens, suspicious URL query strings and environment values from all traces; discard raw secrets at collection boundary.
4. Distinguish infrastructure failures (image missing, daemon unreachable) from target FAIL by inspecting Docker errors, not merely return code.
5. Report incomplete command coverage and do not pretend that isolated sequential containers share installed dependencies.
6. Reserve online dependency install for a separate explicitly approved network-controlled prefetch mechanism; **not** arbitrary `pip install` from a README in an unrestricted networked shell.
7. Test path traversal, symlink escapes, command substitution, shell chaining, resource timeouts, missing Docker, writable mount, model tool injection, poisoned README, and untrusted AGENTS.md.

## Explicitly prohibited shortcuts

- `subprocess.run(..., shell=True)` on host.
- Docker `--privileged`, `-v /var/run/docker.sock`, `--network host`, `--user root`, `--pid host` or credential environment passthrough.
- Trusting target CI workflows as Peeky controller policy.
- Using `pip install -e .` directly on host for a target repository.
