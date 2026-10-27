# Architecture decisions (ADRs)

## ADR-001 — CLI-first local package

**Chosen:** Python 3.12, Typer not required (argparse stdlib), Hatchling, isolated local artifacts. **Why:** hackathon time, testable on CI without tokens, recheck-style package. **Alternatives:** hosted SaaS, Electron — rejected as scope expansion.

## ADR-002 — Explicit README execution annotations

**Chosen:** only `bash peeky` fences, policy filtered and approved. **Why:** a README is untrusted data; executing arbitrary code automatically is unacceptable. **Tradeoff:** excludes many real repos in first MVP. Future analyzer can propose annotations for review.

## ADR-003 — Docker run, no host fallback

**Chosen:** bounded offline Docker. **Why:** target source may contain hooks and malicious commands. **Tradeoff:** not hardened against a kernel escape, restricted dependency workflows. Must use disposable host for unknown repos.

## ADR-004 — Deterministic verifier over generative judge

**Chosen:** return code / test oracles decide mechanics; open models only propose explanation/patch. **Why:** models can hallucinate success.

## ADR-005 — Open coding model + optional Laya classifier

**Chosen:** one Apache-2.0/open-weight coding model for repair; Laya optional triage only. **Why:** Laya cannot generate patches; adding it without measured benefit is bloat. Jev closed hosted service is not the preferred open-weight choice.

## ADR-006 — Agent cold-start A/B

**Chosen:** single matched fixed-task trial, no swarm. **Why:** demonstrates agent compatibility without claiming generic intelligence gains. **Constraint:** no benchmark chart without actual paired runs.

## ADR-007 — OpenFire scope cutoff

No autopublish, remote repo mass scans, auto PR merge, hosted agent, or subscription monetization until MVP gates complete and separately authorized.

## ADR-008 — Peeky project identity

**Chosen:** display name `Peeky`, distribution/import/console command `peeky`, README annotations `bash peeky`, local evidence under `.peeky/runs/`, example configuration `peeky.example.toml` and proposed environment variables prefixed `PEEKY_`. **Why:** the owner selected this name on 2026-10-27. The example configuration and model environment variables remain templates, not implemented integrations. Existing FS acceptance IDs remain stable for traceability. The scaffold has no compatibility aliases for the previous identity. Package-index availability has not been checked; no release or publication is implied.

## ADR-009 — Locked foundation gate and installed-artifact smoke

**Chosen:** retain `uv.lock` and require `uv sync --locked` in both CI jobs. Keep the intentionally ignored local implementation prompts outside the public docs gate; require invariants, assumptions and decisions instead. Verify the version-matching wheel with network-free installation in a fresh venv, cleared Python source-path overrides, a working directory outside the checkout, and both module and console entry points. **Why:** a source-tree test alone cannot demonstrate that the distributed CLI works or that a clean checkout contains the required docs. **Validation scope:** Phase 0 passed locally on Python 3.13.7; no remote CI or Python 3.12 result is claimed. The owner's Docker-test deferral applies to the pending Phase 2 integration gate, not to its acceptance criteria.

## ADR-010 — Raw Git objects and scoped source-bound plans

**Chosen:** verify raw commit/tree/blob object hashes and materialize a bounded temporary export, with no checkout/archive filters or target imports. Check selected index entries and working bytes, then recheck HEAD/index; reject unsupported modes, symlinks/reparse paths and nonportable names. Allow only UTF-8 CRLF-to-LF checkout equivalence, exporting original Git bytes. **Why:** use the code actually named by the commit without allowing repository hooks, filters or fsmonitor commands to run on the host. **Tradeoff:** only clean committed selected scopes are supported; bare/linked worktrees, LFS/custom transformations and hostile concurrent host mutation are outside scope. Unrelated dirty files outside a selected subdirectory do not block it, but any new containing commit invalidates earlier commit-bound guidance.

**Evidence:** schema 1.1 stores source, policy, plan and controller terminal-state identity. Inspection emits a structured plan rather than the earlier bare JSON list. Passports reject schema 1.0 and remeasure the complete current source. Result IDs/commands/exit codes must be consistent; an observed failure remains visible despite incomplete later coverage. These are source/consistency controls, not signatures or independent execution attestations. Durable intermediate journaling, image digest checks, log redaction and real Docker assurance remain later gates.

## ADR-011 — Pinned one-command Docker runner and authenticated redacted records

**Chosen:** one reviewed official Python digest, separate trusted image prefetch, cache-only execution, controller snapshot capability and exactly one smoke command per audit. Create/inspect/start/state/owned-cleanup are separate operations; actual Docker State distinguishes target exits (including 125/126/127) from infrastructure. Resource/log/time limits or uncertain cleanup cannot pass. **Why:** meet the bounded offline fixture gate without inventing shared installation state or fetching arbitrary dependencies.

**Logs and integrity:** retain full observed redacted streams up to explicit byte budgets, with hashes, completeness, timestamps, isolation and source/image/policy identity. Disable daemon container logging, authenticate sanitized JSON with a private per-user HMAC key, and atomically/exclusively publish records. The key is outside scanned repos and never selected by payload input. Reject tracked controller keys, source-controlled host tools and unexpected/duplicate container environment; explicitly clear Docker proxy defaults. **Tradeoff:** local HMAC is not a public signature or protection against host/key compromise. Hard controller death, crash journaling and universal secret discovery remain outside assurance. Real local tests verify the declared cases; remote CI must be observed separately. No model, hosted service or release feature is added.


## ADR-012: BYOK Gemma, exact README proposals and frozen fresh rechecks

**Chosen:** one standard-library OpenAI-compatible adapter to Google AI Studio Gemma, using the owner's key and exact `gemma-4-31b-it` identifier. This explicit owner preference replaces the earlier Qwen recommendation. Gemma is openly weighted and code-capable, but general-purpose; do not relabel it a dedicated coding checkpoint. No proprietary Gemini or paid fallback. Record model/version, token usage, price source/basis and unknown hosted weights revision honestly.

**Chosen:** reserve attempts before dispatch, require exact typed proposals and permit only the single frozen README command-line correction. Bind human approval to the complete authenticated source/patch/oracle artifact. Rerun unchanged baseline and clean derived candidate in different restricted containers with the same image ID/policy, unchanged executable bytes and a frozen exact marker. Models never approve patches, alter permissions or assign verified status. Never patch the target worktree/index.

**Tradeoffs/evidence:** no arbitrary doc rewriting, entrypoint discovery, dependency installation or repair loop. The operator supplies a meaningful oracle. Offline and real-Docker mocked-model gates pass; the two separately authorized live Gemma attempts returned HTTP 500 and connection failure. Phase 3 stops at that provider blocker; no successful live model/version/usage/cost or human-approved repair is claimed. Records and the failing T-023 gate are preserved.


**ADR-012 update after owner-authorized retries:** missing free-tier usage/cost is nonfatal metadata, recorded as unknown. Use the full 45-second response wait; retain error diagnostics and use only explicitly authorized bounded attempts. Google may frame a completion with a flagged thought prefix; discard only that delimited provider frame, then enforce the same strict JSON/schema/path/command rules. Request minimal thinking going forward. Retained-response validation may link immutable original evidence and keep request identity/latency/usage unchanged without inventing another network call. This resolved the real-response parser blocker; T-023 and the human-approved fresh Docker comparison then passed.


## ADR-013: settle OOM metadata and preserve ambiguous termination

**Chosen:** refresh only exited code-137 states whose OOM flag is explicitly false, for at most five extra reads under a one-second settling window, using the existing per-read Docker metadata timeout. Preserve observations and identify runner 2.1. Confirmed OOM is MEMORY_LIMIT; unconfirmed 137 is TERMINATION_UNCERTAIN, both INCONCLUSIVE. Normal target nonzero codes, including 125/126/127, retain FAIL classification. No change to target execution budgets, image, mounts, network or policy identity.

**Why:** CI run 40502294999 failed T-014 after the first State observation while the original fixture passed locally. Moby handles exit and OOM events separately. A bounded refresh handles that possible ordering; code 137 alone cannot distinguish an explicit exit, propagated SIGKILL or actual OOM. Do not relabel all 137 outcomes as MEMORY_LIMIT or weaken the real OOM assertion. Additional strict real and metadata-history regressions verify the behavior. Remote success must be observed after publication, not assumed from local checks.

## ADR-014: Restricted native-tool onboarding with authenticated paired evidence

Use the existing opt-in Gemma adapter configuration with fresh remote conversations and a small trusted dispatcher. Native tools can read bounded captured files or request controller-owned `step-001`; no command override, host shell, writes, installation, credentials, network tools or model verdicts. This implements remote conversation separation instead of the earlier proposed separate local agent worker process. Actual target code remains in fresh strict offline Docker containers.

Bind passport guidance to exact source/evidence/run/image using local HMAC. Freeze source, image, model identity, base prompt/tools, task, oracle, temperature and budgets across arms. Retain original redacted model and tool traces plus independent outcomes. Use exclusive pair reservations, no automatic retries, and bounded calls/tokens/tools/time. Missing usage uses a labeled conservative reservation for budget accounting, never fabricated billing. Keep all negative attempts in denominators and require observed model/source matching for comparative eligibility. The second actual pair was added after an error; disclose that choice. Three HTTP 500 responses prevent a comparative claim; preserve the 0/2 comparable-pair result rather than searching for a favorable sample.
