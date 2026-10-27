# Agent cold-start A/B benchmark (AI-era feature)

**Question:** Does a verified generated agent passport help an unfamiliar agent complete first-time setup reliably and at lower cost than original documentation alone?

**Fixed inputs:** same immutable SHA, same read-only source snapshot, same sandbox image digest, same open-weight tool-using code model/checkpoint, identical token/time/tool budgets, same task and independent command-based oracle. Vary **only** whether candidate AGENTS.generated.md is provided. Do not inject extra task hints into treatment.

**Task:** "You are new to this repo. Prepare it and execute the documented smoke test; finish by providing the exact command and exit status." Do not count text-only confidence as success; inspect actual runner records.

**Trial records:** trial ID, baseline/treatment, model/checkpoint, prompt digest, repo revision, image digest, fixed task digest, steps, tokens, wall time, result, failure reason, seed/temp when supported. Run at least one pair, ideally two or more to expose variance. Small-N cannot establish generalized causal lift.

**Metrics:** success rate with denominator, attempts-to-first-success, tool calls, time, tokens; annotate blocked and environment errors separately. Show both raw runs and a cautious summary. If no tool-enabled agent harness exists, mark this **NOT RUN**, not a simulated benchmark.

**Implemented boundary:** each remote model conversation is fresh; the trusted dispatcher remains in the controller process. Its only tools read bounded captured files or request the approved fresh offline Docker executor. No local untrusted agent process, arbitrary host shell, Git write, network tool or secret access is exposed. This narrows the original proposed separate-worker architecture; see `phase4-onboarding.md` and ADR-014.

## Phase 4 observed result

The harness is implemented and genuine native-tool use was observed. Two complete pairs used identical frozen controls: baseline 0/2 PASS (2 INCONCLUSIVE), passport 1/2 PASS (1 INCONCLUSIVE). Three of four provider responses were HTTP 500. Only the successful passport arm invoked the real fresh Docker executor and matched the independent marker. Comparable pairs are 0/2 because three served model identities are unavailable. No lift estimate is justified. The second pair followed the first error and is disclosed as adaptive sampling, not a preregistered replication. Both actual traces and all negative outcomes remain in authenticated local records; see `phase4-onboarding.md` for paths, exact protocol, usage limits and report.
