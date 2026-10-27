# Peeky — OpenFire MVP engineering kit

**Product hypothesis:** A repository should be demonstrably installable for a first-time human and bootstrappable for a fresh coding agent, not merely documented as such.

**Status:** Development scaffold, **not a completed OpenFire submission**. `inspect`, `doctor`, `audit` (restricted offline single-command Docker checks) and `passport` (verified-step guidance) are implemented. Model-driven diagnosis/repair and **agent cold-start A/B evaluation are planned development phases**, not shipped functionality in this kit. Never represent the scaffold as the complete MVP until [acceptance gates](docs/mvp-contract.md) pass.

This kit borrows the **documentation-first engineering discipline** of `haddybhaiya/recheck-`: same general Hatchling/pytest/ruff/mypy `pyproject.toml` pattern, phase-gated implementation, explicit safety boundaries, credential-free checks and auditable evidence. It does not copy Recheck's domain logic.

## Quick start

Requires Python 3.12+, Git, and Docker for real target execution. Model credentials **not** required for scaffold smoke checks. Sources must be committed local Git directories: modified, staged or untracked non-ignored files in the selected directory block capture. A committed subdirectory (including the fixtures below) can be selected without requiring unrelated directories to be clean.

```bash
python -m pip install -e .
peeky --version
peeky inspect tests/fixtures/good_repo
peeky doctor
```

Approved restricted sandbox smoke (requires a Docker daemon and a cached/built image):

```bash
peeky audit tests/fixtures/good_repo --approve --image python:3.12-slim
peeky passport tests/fixtures/good_repo --evidence .peeky/runs/REPLACE_WITH_RUN_ID.json
```

The `audit` command creates schema 1.1 evidence JSON in `.peeky/runs/`. It captures verified committed Git bytes into a temporary read-only source export and mounts that export for execution. It does **not** rewrite your repository, use an LLM, install dependencies, or access the network. It executes only **explicitly annotated** README blocks, only after `--approve`, inside a restricted, offline container. Missing Docker records a BLOCKED attempt with INCONCLUSIVE verdict and no target execution. Each approved command uses its own fresh container; session-dependent workflows are **out of scaffold scope**. Use image digests and pre-pulled images for reproducible evidence.

For contributors:

```bash
python -m pip install uv==0.12.19
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy src tests
uv run --locked pytest tests/unit tests/smoke tests/integration/test_source_capture.py -m 'not live and not docker'
uv run --locked python scripts/check_docs.py
uv build --wheel
uv run --locked python scripts/smoke_wheel.py
```

## Deliverable boundaries

**Hackathon MVP target:** local Python repo; annotated README setup/smoke steps; restricted Docker execution; failure classification; opt-in open coding model generating a proposed doc patch; independent clean recheck; verified `AGENTS.generated.md`; one fixed controlled cold-start comparison; evidence JSON + Markdown; 3 deterministic fixtures; 90–120-second screen-recordable demo. No hosted backend, arbitrary GitHub scraping, auto-merge or public remote execution.

See `docs/phase.md` for exact implementation gates, `docs/architecture.md`, `docs/runner-security.md`, `docs/test-plan.md`, `docs/open-models.md`, and `docs/decisions.md`.

The [repository analysis](docs/repository-analysis.md) records the current implementation, validation results and remaining trust-boundary gaps. The chosen distribution, import and CLI name is `peeky`; package-index availability has not been checked.

## CLI contracts

- `peeky inspect PATH [--json]`: capture committed source and extract **opted-in** fenced `bash peeky` commands as a proposal; never run them. JSON is now an object containing `source`, `policy_sha256`, `run` and `steps`, replacing the scaffold's bare step list.
- `peeky doctor [--json]`: check whether Docker CLI/daemon is available; never install Docker.
- `peeky audit PATH --approve [--image IMAGE] [--output DIR]`: execute strictly gated commands in Docker; output the exact evidence file location. Default `--image python:3.12-slim` is a **development convenience, not a pinned release image**.
- `peeky passport PATH --evidence FILE [--output FILE]`: generate **unmerged** candidate `AGENTS.generated.md` only from internally consistent schema 1.1 evidence bound to the current clean commit, full selected source and policy. Legacy schema 1.0 is rejected; rerun the audit. JSON is not signed execution proof.

See [source capture and identity](docs/source-capture.md) for path rules, limits, CRLF handling and unsupported Git worktrees/filters. Git metadata is read on the host through trusted Git plumbing; target scripts, imports and hooks are never run there.

Annotated README syntax:

````markdown
```bash peeky
python -m compileall -q .
```
````

**No fenced code is implicitly trustworthy.** Inspect planned commands before approval. Never run this against repositories you do not trust on your primary host. Docker is defense-in-depth, not a strong adversarial-code guarantee.

## Build reproducibility

`uv.lock` records the resolved development dependencies, and CI installs them with `uv sync --locked`. Use the locked contributor commands above to reproduce the local gate. The wheel smoke check installs the built artifact without network access in a clean temporary environment and runs both its module and installed console command outside this checkout. Local validation and deferred Docker checks are recorded separately in [the evidence ledger](docs/work_review.md); a local pass does not establish CI or full product success.

## Important notes

- An incomplete setup check is `INCONCLUSIVE`, **not** `PASS`.
- One passed smoke test is not proof that all installation workflows function.
- The agent benchmark must run on the same immutable revision, runner, model and budgets on both sides.
- Existing AGENTS.md is never overwritten by this package.
- This repo is public-ready only after secrets review, documentation review and all MVP phase gates pass.
