# Security policy (MVP)

Peeky handles **untrusted project material**. The present runner offers useful restrictions, NOT a hardened multi-tenant sandbox. Do not run unknown hostile repositories on personal or shared machines. Use an isolated, disposable build worker and no credentials.

Controls: no target host execution fallback; installed-tool lookup independent of target/cwd; opted-in single-command audit; reviewed cached image digest and snapshot-only mount; inspected environment/proxy exclusion; network disabled; non-root UID; all Linux capabilities dropped; no-new-privileges; read-only root/source; CPU/RAM/PID/file/log/time budgets; owned container removal and absence checks; redacted bounded transcripts; private per-user HMAC integrity and atomic exclusive evidence; no Docker socket or host credential mount.

Remaining risks: compromised host/kernel/runtime/key owner, hostile concurrent host mutation, unknown secret formats, controller hard termination/daemon loss and data-dependent scripts. Model calls are disabled by default; the opted-in BYOK Gemma proposal flow has bounded disclosure, strict README-only validation and digest-bound human approval (see `docs/phase3-repair.md`). Arbitrary dependency fetching and public scans remain unimplemented. Local HMAC is not a public signature or third-party execution proof. Verified local fixture constraints do not establish a hardened multi-tenant sandbox. See `docs/runner-security.md`, `docs/phase2-runner.md` and `docs/threat-model.md`.

No GitHub issue should disclose exploitable security details. Report vulnerabilities privately to the repository owner by GitHub security advisory once configured. Do not claim this template's contact channel has been set up.
