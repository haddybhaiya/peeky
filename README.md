# Peeky — OpenFire MVP engineering kit

**Product hypothesis:** A repository should be demonstrably installable for a first-time human and bootstrappable for a fresh coding agent, not merely documented as such.

**Status:** Development scaffold, **not a completed OpenFire submission**. `inspect`, `doctor`, `audit` (restricted offline single-command Docker checks) and `passport` (verified-step guidance) are implemented. Model-driven diagnosis/repair and **agent cold-start A/B evaluation are planned development phases**, not shipped functionality in this kit. Never represent the scaffold as the complete MVP until [acceptance gates](docs/mvp-contract.md) pass.

This kit borrows the **documentation-first engineering discipline** of `haddybhaiya/recheck-`: same general Hatchling/pytest/ruff/mypy `pyproject.toml` pattern, phase-gated implementation, explicit safety boundaries, credential-free checks and auditable evidence. It does not copy Recheck's domain logic.

## Quick start

Requires Python 3.12+, and Docker for real target execution. Model credentials **not** required for scaffold smoke checks.

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

The `audit` command creates an evidence JSON in `.peeky/runs/`. It does **not** rewrite your repository, use an LLM, install dependencies, or access the network. It executes only **explicitly annotated** README blocks, only after `--approve`, inside a restricted, offline container. Each approved command uses its own fresh container; session-dependent workflows are **out of scaffold scope**. Use image digests and pre-pulled images for reproducible evidence.

For contributors:

```bash
python -m pip install uv==0.12.19
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy src tests
uv run --locked pytest tests/unit tests/smoke -m 'not live and not docker'
uv run --locked python scripts/check_docs.py
uv build --wheel
uv run --locked python scripts/smoke_wheel.py
```

## Deliverable boundaries

**Hackathon MVP target:** local Python repo; annotated README setup/smoke steps; restricted Docker execution; failure classification; opt-in open coding model generating a proposed doc patch; independent clean recheck; verified `AGENTS.generated.md`; one fixed controlled cold-start comparison; evidence JSON + Markdown; 3 deterministic fixtures; 90–120-second screen-recordable demo. No hosted backend, arbitrary GitHub scraping, auto-merge or public remote execution.

See `docs/phase.md` for exact implementation gates, `docs/architecture.md`, `docs/runner-security.md`, `docs/test-plan.md`, `docs/open-models.md`, and `docs/decisions.md`.

The [repository analysis](docs/repository-analysis.md) records the current implementation, validation results and remaining trust-boundary gaps. The chosen distribution, import and CLI name is `peeky`; package-index availability has not been checked.

## CLI contracts

- `peeky inspect PATH [--json]`: extract **opted-in** fenced `bash peeky` commands as a proposal; never run them.
- `peeky doctor [--json]`: check whether Docker CLI/daemon is available; never install Docker.
- `peeky audit PATH --approve [--image IMAGE] [--output DIR]`: execute strictly gated commands in Docker; output the exact evidence file location. Default `--image python:3.12-slim` is a **development convenience, not a pinned release image**.
- `peeky passport PATH --evidence FILE [--output FILE]`: generate **unmerged** `AGENTS.generated.md` only from a successful, matching run.

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
