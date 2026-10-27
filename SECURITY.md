# Security policy (MVP)

Peeky handles **untrusted project material**. The present runner offers useful restrictions, NOT a hardened multi-tenant sandbox. Do not run unknown hostile repositories on personal or shared machines. Use an isolated, disposable build worker and no credentials.

Controls: no host execution fallback; opt-in command allowlist; image validation; network disabled; non-root UID; all Linux capabilities dropped; no-new-privileges; read-only root and repository mount; CPU/RAM/PID caps; command timeout; temporary directories; no Docker socket or secrets inside the container.

Remaining risks: compromised kernel/runtime, source disclosure to opted-in remote model, output/terminal escape tricks, resource consumption, data-dependent scripts, unsafe preexisting Docker configuration, malicious base image, and package install fetching. Verify the actual Docker command line before enabling public scans. See `docs/runner-security.md` and `docs/threat-model.md`.

No GitHub issue should disclose exploitable security details. Report vulnerabilities privately to the repository owner by GitHub security advisory once configured. Do not claim this template's contact channel has been set up.
