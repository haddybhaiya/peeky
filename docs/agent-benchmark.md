# Agent cold-start A/B benchmark (AI-era feature)

**Question:** Does a verified generated agent passport help an unfamiliar agent complete first-time setup reliably and at lower cost than original documentation alone?

**Fixed inputs:** same immutable SHA, same read-only source snapshot, same sandbox image digest, same open-weight tool-using code model/checkpoint, identical token/time/tool budgets, same task and independent command-based oracle. Vary **only** whether candidate AGENTS.generated.md is provided. Do not inject extra task hints into treatment.

**Task:** "You are new to this repo. Prepare it and execute the documented smoke test; finish by providing the exact command and exit status." Do not count text-only confidence as success; inspect actual runner records.

**Trial records:** trial ID, baseline/treatment, model/checkpoint, prompt digest, repo revision, image digest, fixed task digest, steps, tokens, wall time, result, failure reason, seed/temp when supported. Run at least one pair, ideally two or more to expose variance. Small-N cannot establish generalized causal lift.

**Metrics:** success rate with denominator, attempts-to-first-success, tool calls, time, tokens; annotate blocked and environment errors separately. Show both raw runs and a cautious summary. If no tool-enabled agent harness exists, mark this **NOT RUN**, not a simulated benchmark.

**Implementation choice:** keep benchmark process isolated from controller with a restricted tool subset: read files, approved Docker executor, no arbitrary host shell, no Git write, no network, no secrets. A multi-agent swarm is explicitly not required.
