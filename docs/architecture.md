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
- `policy.py`: trusted allowlist and no shell metacharacters, independent of model.
- `runner.py`: only Docker command producer, no shell on host; target code runs inside containers.
- `evidence.py`: deterministic reducer and write-once records; no model authority over success verdicts.
- `passport.py`: drafts candidate onboarding guidance after basic JSON/README checks; the CLI refuses overwrite of existing output. Authenticated evidence and full-source binding remain unimplemented (see `repository-analysis.md`).
- **To implement:** `sources.py` immutable git snapshot and SHA/dirty-tree checks; `providers/` typed open-model adapters; `repair.py` candidate patch validation; `benchmark.py` fixed-task agent harness; `reports.py` rich exported Markdown.

## State machine

`CREATED → INSPECTED → APPROVED → SANDBOX_RUN → OBSERVED → [PATCH_PROPOSED → REVIEWED → RECHECKED] → [PASSPORT_CREATED → BENCHMARKED] → FINALIZED`.

Failures end in `BLOCKED` or `INCONCLUSIVE` and preserve artifacts. No state transition driven exclusively by model content. Current scaffold has no persistent state machine; implement before enabling auto-repair.

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

Default local `.peeky/runs/<uuid>.json` relative to CLI's current working directory. Future safe export should add dedicated state root, atomic writes and manifest hashing. Do not include tokens, raw .env, SSH keys, hidden credential folders, auth headers, or sensitive full source in reports.
