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
