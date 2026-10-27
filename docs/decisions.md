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
