# Threat model

| Threat | Impact | MVP mitigation | Remaining limitation |
|---|---|---|---|
| README prompt injection | Policy override | README treated as data, no model policy authority | Model can still be influenced; bounded schema and redaction needed |
| Host execution of scripts | Compromise | Docker only; explicit approval | Kernel/container runtime vulnerabilities |
| Shell injection / malicious flags | Escalation | argv parsing; reject metacharacters | Python code itself may be malicious |
| Model fabricated verification | False assurance | Independent mechanical checks | No proof of untested behavior |
| Secret exfiltration | Sensitive data | No network, no secret mounts, no auth passthrough | Leaks possible in local logs and external model prompts |
| CI supply-chain compromise | CI compromise | Pinned GitHub actions, limited permissions | Dependencies/image tags must be pinned |
| Provenance mismatch | Wrong recommendations | README digest and planned git SHA | Need full source snapshot + image digest |
| Resource exhaustion | Denial of service | CPU/RAM/PID/time caps | Kernel scheduler contention remains |
| Generated AGENTS.md overwrite | Destroy instructions | Write-once AGENTS.generated.md only | Human merge must be reviewed |
