# Runner isolation and security contract

**Threat:** malicious commands/source/instructions in a target repo; unsafe image/environment choices; resource exhaustion; credential leakage in logs; confusing infrastructure errors with target failures. Target README, AGENTS, code and output remain data, never controller instructions.

## Current controls

Phase 1 validates clean scoped committed Git source and exports original verified bytes with portable path/type/link/credential checks. Phase 2's runner accepts only controller-created verified snapshots and captured policy-validated steps. It never mounts the live repo or an arbitrary supplied Path. No target imports, scripts, package installs, Git hooks or filters execute on the host.

Audit permits exactly one opted-in smoke command after `--approve`. Source planning can describe more steps, but no-op and unsupported multi-step plans retain BLOCKED/INCONCLUSIVE evidence without execution. A controller allowlist permits only the reviewed cached official Python digest. Image ID/RepoDigest/Linux identity and effective container configuration are checked before start. Target execution uses `--pull=never`, no network, read-only root/source, UID/GID 65534, cap-drop ALL, no-new-privileges, no privileged/devices/host PID/IPC/socket mounts, fixed non-secret environment and no persistent container log driver.

Runtime budgets are 256 MiB RAM with no extra swap, one CPU, 64 PIDs, 128 open files, 32 MiB noexec/nosuid/nodev tmpfs and a default 20-second command deadline. Host log collection retains at most 65,536 raw bytes per stream, redacts before returning/storing transcripts, and stops output floods. Timeout and exceptions trigger label-checked removal of the owned container plus a follow-up remaining-container query. Uncertain cleanup cannot yield PASS. Real integration reads kernel cgroups, checks filesystem/network/UID/capabilities, triggers OOM/timeout/log limits and verifies container absence.

Creation, target attachment, inspected State and cleanup are separate. Missing image/daemon/executable or ambiguous transport is INCONCLUSIVE; a target actually exiting 125/126/127 is FAIL. Redacted full bounded streams, hashes, byte/completeness information, reason codes, source/image/policy identity, timestamps and inspected isolation are retained. Evidence uses private per-user HMAC integrity and atomic exclusive finalization; source/controller key material is not mounted or shared. See `phase2-runner.md` for exact key locations, retention and filesystem requirements.

## Limits and remaining gates

These controls are not a hardened multi-tenant boundary. Docker shares a kernel with the host. Host operator, local Docker daemon and source filesystem are trusted; hostile concurrent host mutation, daemon/kernel compromise and hard controller termination are not defeated by file permissions or normal-return cleanup. Unknown code still belongs on disposable infrastructure, without host secrets.

Credential filename checks and pattern-based redaction are not complete secret discovery. Raw streams are not persisted by Peeky/container logging, but arbitrary secret formats can evade patterns. Local HMAC is not an independent public execution attestation and does not resist an operator with key access. Protect per-user controller state separately from scanned repos and shared reports. Crash-resumable/intermediate journaling remains unimplemented.

Online dependency installation/prefetch from target README remains deferred. The one separately reviewed official image preparation is not permission to fetch arbitrary packages or expand runtime egress. Models, docs patch validation, clean retest and matched agent benchmarks remain later phases; their injection/permission gates must be verified before enabling those features. CI execution and additional platforms must be recorded as actually observed, never inferred from workflow edits.

## Prohibited shortcuts

- No host target execution or `shell=True` fallback.
- No privileged Docker, Docker socket, host network/PID namespace, root user, credential passthrough, mutable host source mounts or broad container pruning.
- No target CI/README/AGENTS/model content controlling permissions, evidence verdicts, budgets, image trust or cleanup ownership.
- No host `pip install` for a scanned target and no automatic dependency fetch while auditing.


## Phase 3 model boundary

BYOK Gemma is a separate opted-in controller HTTP call, never a target-container capability. Endpoint/model allowlists, explicit disclosure consent, bounded redacted prompts/responses, no tools/redirects/ambient proxies/retries and strict typed output constrain it. A frozen operator command/marker plus exact README-only diff prevents model edits to code, tests, assertions, evidence or policy. Human approval binds the entire authenticated proposal; drift/replay fails before dispatch. Fresh baseline/candidate containers keep the existing Phase 2 restrictions. Actual live failures are INCONCLUSIVE and cannot be promoted by model claims or offline mocks; see `phase3-repair.md`.


## Exit-137/OOM observation correction (runner 2.1)

Docker handles exit and OOM as separate events. The first State read after attached-client completion may be insufficient to identify a memory kill. Only for exited code 137 with OOMKilled explicitly false, perform at most five extra metadata reads under a one-second settling window (checked between reads; each call retains the existing bounded metadata timeout). Preserve all states in `container_state_observations`, with the final state also in `container_state`. Actual OOM confirmation remains required for MEMORY_LIMIT. A settled unconfirmed 137 is INCONCLUSIVE/TERMINATION_UNCERTAIN because explicit exits and signal-derived exits overlap; it cannot be inferred as OOM from the code alone. Normal exits are not polled; target timeout/resource/isolation/cleanup budgets are unchanged. This bug fix does not change the execution-policy identity, and runtime provenance identifies runner version 2.1.
