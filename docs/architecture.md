# Architecture and trust boundaries

## Diagram

```text
Trusted CLI / Policy / Evidence controller
     |  read-only, size-bounded
     v
Repository snapshot + README parser ----> Reviewable step plan
     |                                          |
     |                                  explicit user approval
     |                                          v
     |                                Offline Docker Runner
     |                                          |
     |                             raw exit/logs/time/resource data
     |                                          v
     +--------------------------------> Evidence + verdict reducer
                                                |
            optional and consented               v
  selected redacted logs ---------> Open coding model (proposal only)
                                                |
                                         docs-only candidate
                                                v
                                     user review + clean rerun
                                                |
                                   Verified agent passport candidate
                                                |
                                     controlled cold-start A/B
                                                v
                                   final evidence JSON and summary
```

## Component boundaries

- `parser.py`: extract only designated Markdown fences. Source text is untrusted data.
- `sources.py`: bounded verified Git object reads, clean scoped source identity and temporary read-only exports; no target checkout/hooks/filters/imports.
- `domain.py`: frozen source/policy identities, canonical plan hashes and controller-owned run transitions.
- `policy.py`: trusted allowlist and no shell metacharacters, independent of model.
- `runner.py`: snapshot-only, digest-allowlisted Docker create/attach/inspect/owned-cleanup controller; target code runs only in restricted containers with bounded/redacted streams.
- `evidence.py`: deterministic reducer, observed coverage, redacted log hashes and atomic exclusive records; no model authority over success verdicts.
- `images.py`, `redaction.py`, `provenance.py`: reviewed digest allowlist, bounded collection/storage redaction and private per-user controller HMAC integrity.
- `passport.py`: drafts source/commit/policy/plan-bound candidate guidance only after schema 1.2 local authentication and complete runtime-evidence checks; existing output is never overwritten. Public third-party attestation and clean repair/retest assurance remain later work.
- **To implement:** `providers/` typed open-model adapters; `repair.py` candidate patch validation; `benchmark.py` fixed-task agent harness; `reports.py` rich exported Markdown.

## State machine

`CREATED → INSPECTED → APPROVED → SANDBOX_RUN → OBSERVED → [PATCH_PROPOSED → REVIEWED → RECHECKED] → [PASSPORT_CREATED → BENCHMARKED] → FINALIZED`.

Phase 1 implements the controller transitions through INSPECTED, APPROVED, SANDBOX_RUN, OBSERVED and FINALIZED, plus terminal BLOCKED exits. Inspect emits a source/plan/policy-bound plan; terminal audit records contain run state/history. Missing Docker preserves a BLOCKED attempt with INCONCLUSIVE verdict. There is no durable intermediate/crash journal, resume mechanism or repair state machine yet. No state transition is driven by model content. See `source-capture.md` for exact scope and limits.

## Environment comparisons

Record exact target revision, README hash, Git dirty state, resolved image digest/ID, commands, policy, isolation, runtime mode and evidence SHA for every comparison. Phase 2 enforces a reviewed cached digest in execution and CI setup, measures effective container constraints and records actual State/start/end/duration. It supports one command per audit; multi-step installation comparisons are unsupported. Never compare altered setup environments as causal proof. Local fixture results are not generalized benchmark evidence.

## Interface contracts (proposed)

```python
class StepExtractor(Protocol):
    def extract(self, readme: bytes) -> list[Step]: ...
class SandboxRunner(Protocol):
    def run(self, repo_snapshot: Path, steps: list[Step], policy: Policy) -> list[StepResult]: ...
class DiagnosisProvider(Protocol):
    def suggest(self, sanitized_context: dict) -> PatchProposal: ...
class AgentHarness(Protocol):
    def run(self, repo_snapshot: Path, instructions: str, task: FixedTask) -> AgentTrial: ...
```

## Storage

Default report storage is local `.peeky/runs/<uuid>.json` relative to the CLI working directory. Source exports are separate short-lived temporary directories, removed after use. Schema 1.2 includes sorted file hashes, run/policy/plan identity, actual runtime provenance and bounded redacted transcripts, not source bodies or Git metadata. Authenticated records are finalized atomically/exclusively. The private HMAC key is per-user state outside scanned repositories: `%LOCALAPPDATA%/Peeky/controller.key` on Windows or `~/.local/state/Peeky/controller.key` on Linux. It is never taken from evidence or mounted in a container. Public-key attestation and durable intermediate/crash journaling remain unimplemented. See `phase2-runner.md`.
