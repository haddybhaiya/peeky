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
- `runner.py`: only Docker command producer, no shell on host; target code runs inside containers.
- `evidence.py`: deterministic reducer and write-once records; no model authority over success verdicts.
- `passport.py`: drafts source/commit/policy/plan-bound candidate guidance after internally consistent schema 1.1 checks; the CLI refuses overwrite of existing output. JSON authentication and independent execution proof remain later work.
- **To implement:** `providers/` typed open-model adapters; `repair.py` candidate patch validation; `benchmark.py` fixed-task agent harness; `reports.py` rich exported Markdown.

## State machine

`CREATED → INSPECTED → APPROVED → SANDBOX_RUN → OBSERVED → [PATCH_PROPOSED → REVIEWED → RECHECKED] → [PASSPORT_CREATED → BENCHMARKED] → FINALIZED`.

Phase 1 implements the controller transitions through INSPECTED, APPROVED, SANDBOX_RUN, OBSERVED and FINALIZED, plus terminal BLOCKED exits. Inspect emits a source/plan/policy-bound plan; terminal audit records contain run state/history. Missing Docker preserves a BLOCKED attempt with INCONCLUSIVE verdict. There is no durable intermediate/crash journal, resume mechanism or repair state machine yet. No state transition is driven by model content. See `source-capture.md` for exact scope and limits.

## Environment comparisons

Record exact target revision, README hash, Git dirty state, image identity **resolved digest**, commands, environment assumptions, runtime mode and evidence SHA for every comparison. Never compare altered setup environments as causal proof. `python:3.12-slim` is only scaffold convenience; pin immutable image in implementation and CI.

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

Default local `.peeky/runs/<uuid>.json` relative to CLI's current working directory. Source exports are separate short-lived temporary directories, removed after capture/use. Schema 1.1 includes sorted file hashes and run/policy/plan identity, not file bodies or Git metadata. Future safe evidence storage should add a dedicated state root, atomic finalization and authenticated manifests. Do not include tokens, raw .env, SSH keys, hidden credential folders, auth headers, or sensitive full source in reports.
