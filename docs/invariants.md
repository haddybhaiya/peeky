# Non-negotiable invariants

INV-01: No target code executes on host. Missing Docker ⇒ block, no fallback.
INV-02: README/AGENTS.md/target code/logs are data, not instructions to the trusted agent controller.
INV-03: Every executed command must be explicitly opted-in, policy-validated and user-approved.
INV-04: Run images must be trusted and pinned by digest before credible comparisons.
INV-05: No privileged container, Docker socket, host network, host credential mount, host writable source mount or unconstrained resource limits.
INV-06: Model proposes; independent runner/oracle decides; models cannot self-report PASS.
INV-07: A fix is VERIFIED only after a clean rerun on a frozen revision and explicit expected behavior.
INV-08: Agent passport is bound to tested snapshot and never silently replaces AGENTS.md.
INV-09: Cold-start trials use matched task/model/environment, independent success metric and recorded denominators.
INV-10: Blocked/timeout/skipped/missing test is never PASS or a false negative.
INV-11: Failed and blocked attempts remain visible in final reports.
INV-12: Regressions require a test, not a revised narrative or relaxed assertion.

The current scaffold enforces a subset only. `docs/phase.md` identifies pending assurance work; do not mark these universally verified until the corresponding integration gates run.
