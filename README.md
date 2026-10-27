# Peeky — OpenFire MVP engineering kit

**Product hypothesis:** A repository should be demonstrably installable for a first-time human and bootstrappable for a fresh coding agent, not merely documented as such.

**Status:** Development MVP, **not a completed OpenFire submission**. `inspect`, `doctor`, `audit` (restricted offline Docker checks), `passport` and Phase 3's opt-in BYOK **Gemma** proposal/approved README recheck flow are implemented. The genuine Gemma response, exact human approval and fresh original/candidate Docker repair gate passed locally; remote Phase 3 CI remains pending. Exact evidence and earlier failures are in [work review](docs/work_review.md). Agent cold-start A/B evaluation remains planned. Never claim the complete MVP until [acceptance gates](docs/mvp-contract.md) pass.

This kit borrows the **documentation-first engineering discipline** of `haddybhaiya/recheck-`: same general Hatchling/pytest/ruff/mypy `pyproject.toml` pattern, phase-gated implementation, explicit safety boundaries, credential-free checks and auditable evidence. It does not copy Recheck's domain logic.

## BYOK Gemma README repair

Bring your own Google AI Studio key using the ignored `.env` and the settings in `.env.example`. The selected checkpoint is `gemma-4-31b-it`, an open-weight instruction-tuned Gemma model with coding capabilities. It is used through Google's OpenAI-compatible endpoint, with no proprietary Gemini fallback. Deterministic tests need no key. Set `PEEKY_MODEL_CONSENT=true` only after reviewing the bounded redacted disclosure.

After committing a target's clean source, collect a real failed audit, then freeze an independent expected command and stdout marker before diagnosis:

```powershell
uv run --locked peeky audit tests/fixtures/outdated_repo --approve
uv run --locked peeky diagnose tests/fixtures/outdated_repo --evidence PATH_TO_FAILED_RECORD --expected-command "python repair_smoke.py" --expected-stdout PEEKY_RECHECK_OK --model-consent --env-file .env
```

Review the returned README-only diff and exact approval digest. Only then run `peeky recheck TARGET --proposal PATH_TO_PROPOSAL --approve-proposal sha256:DIGEST`. This runs the unchanged baseline and approved candidate in separate fresh restricted containers; it never patches the target worktree. Only the controller's frozen command/marker oracle can record VERIFIED. A model cannot declare verified status. Missing completions, quota errors and uncertain execution remain INCONCLUSIVE; missing free-tier usage/cost alone is recorded as unknown without blocking a valid proposal. See [the complete repair contract](docs/phase3-repair.md) for limits, cost accounting and one-attempt budgets.

## Quick start

Requires Python 3.12+, Git, and Docker for real target execution. Model credentials **not** required for scaffold smoke checks. Sources must be committed local Git directories: modified, staged or untracked non-ignored files in the selected directory block capture. A committed subdirectory (including the fixtures below) can be selected without requiring unrelated directories to be clean.

```bash
python -m pip install -e .
peeky --version
peeky inspect tests/fixtures/good_repo
peeky doctor
```

Prepare the reviewed official image separately, then run an offline sandbox smoke check:

```bash
docker pull python@sha256:12316debbfb86890f6b2d825820612741ba527ad5a44e3902759141d572bfe8f
peeky audit tests/fixtures/good_repo --approve
peeky passport tests/fixtures/good_repo --evidence .peeky/runs/REPLACE_WITH_RUN_ID.json
```

The `audit` command creates schema 1.2 evidence JSON in `.peeky/runs/`. It accepts exactly one opted-in smoke command, captures committed Git bytes into a verified read-only export, and executes inside a fresh restricted container using the reviewed cached digest. It does **not** rewrite your repository, use an LLM, install dependencies, pull images or enable target networking. Missing Docker, no annotated commands and unsupported multi-step plans preserve BLOCKED/INCONCLUSIVE evidence. Actual target failures are FAIL; timeout, output/memory limits and ambiguous infrastructure are INCONCLUSIVE. Full observed stdout/stderr are retained after redaction within explicit byte budgets, with image/source/policy IDs and verified cleanup. Evidence has local HMAC integrity under `%LOCALAPPDATA%/Peeky/controller.key` on Windows (or `~/.local/state/Peeky/controller.key` on Linux); keep this private controller state out of shared evidence bundles. See [the runner contract](docs/phase2-runner.md).

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

With Linux Docker running and the pinned image cached, run `uv run --locked pytest -m 'not live'` for all deterministic gates, then `uv run --locked python scripts/validate_phase2.py` to retain authenticated good/bad/no-op fixture evidence. Plain `pytest` excludes Docker/live tests; explicitly selecting Docker tests fails rather than skips unavailable prerequisites.

## Deliverable boundaries

**Hackathon MVP target:** local Python repo; annotated README setup/smoke steps; restricted Docker execution; failure classification; opt-in open coding model generating a proposed doc patch; independent clean recheck; verified `AGENTS.generated.md`; one fixed controlled cold-start comparison; evidence JSON + Markdown; 3 deterministic fixtures; 90–120-second screen-recordable demo. No hosted backend, arbitrary GitHub scraping, auto-merge or public remote execution.

See `docs/phase.md` for exact implementation gates, `docs/architecture.md`, `docs/runner-security.md`, `docs/test-plan.md`, `docs/open-models.md`, and `docs/decisions.md`.

The [repository analysis](docs/repository-analysis.md) records the current implementation, validation results and remaining trust-boundary gaps. The chosen distribution, import and CLI name is `peeky`; package-index availability has not been checked.

## CLI contracts

- `peeky inspect PATH [--json]`: capture committed source and extract **opted-in** fenced `bash peeky` commands as a proposal; never run them. JSON is now an object containing `source`, `policy_sha256`, `run` and `steps`, replacing the scaffold's bare step list.
- `peeky doctor [--json]`: check whether Docker CLI/daemon is available; never install Docker.
- `peeky audit PATH --approve [--image IMAGE] [--output DIR]`: execute exactly one permitted smoke command in Docker. Default image is the reviewed immutable digest in `src/peeky/images.py`; mutable tags and unreviewed digests are blocked. Returns 0 for PASS, 1 for observed target FAIL, 2 for a pre-execution policy/no-op block, and 3 for unavailable/ambiguous infrastructure.
- `peeky passport PATH --evidence FILE [--output FILE]`: generate **unmerged** candidate `AGENTS.generated.md` only from controller-authenticated schema 1.2 evidence bound to the current clean commit, source, policy and finalized plan. Legacy schemas are rejected; rerun the audit. Local HMAC integrity is not a public signature or independent third-party execution attestation.

See [source capture and identity](docs/source-capture.md) for path rules, limits, CRLF handling and unsupported Git worktrees/filters. Git metadata is read on the host through trusted Git plumbing; target scripts, imports and hooks are never run there.

Annotated README syntax:

````markdown
```bash peeky
python smoke.py
```
````

**No fenced code is implicitly trustworthy.** Inspect planned commands before approval. Never run this against repositories you do not trust on your primary host. Docker is defense-in-depth, not a strong adversarial-code guarantee.

## Build reproducibility

`uv.lock` records the resolved development dependencies, and CI installs them with `uv sync --locked`. Use the locked contributor commands above to reproduce the local gate. The wheel smoke check installs the built artifact without network access in a clean temporary environment and runs both its module and installed console command outside this checkout. The Docker job separately prefetches the exact reviewed digest, runs the real container tests and validates fixture evidence. Local Docker results are recorded in [the evidence ledger](docs/work_review.md); they do not establish remote CI or full product success.

## Important notes

- An incomplete setup check is `INCONCLUSIVE`, **not** `PASS`.
- One passed smoke test is not proof that all installation workflows function.
- The agent benchmark must run on the same immutable revision, runner, model and budgets on both sides.
- Existing AGENTS.md is never overwritten by this package.
- This repo is public-ready only after secrets review, documentation review and all MVP phase gates pass.

## Restricted agent onboarding trial (Phase 4)

Passports now carry a local HMAC provenance certificate binding guidance, source, policy, plan, original audit bytes, run and image. Output must be `AGENTS.generated.md` and is never overwritten. This is candidate guidance, not public attestation.

After a successful audit, opt in explicitly:

```powershell
uv run --locked peeky trial tests/fixtures/good_repo --evidence PATH_TO_AUDIT.json --expected-command "python smoke.py" --expected-stdout "HELLO_FROM_GOOD_FIXTURE" --approve --model-consent --env-file .env
```

Use the existing ignored Gemma BYOK configuration. Each arm gets a fresh conversation and source capture with the same model, image, task and budgets; only passport guidance differs. Native tools can read bounded captured files or request the approved command in fresh offline Docker. The independent controller judges execution. No installation, host target execution or GitHub writes.

Actual local report: baseline **0/2 PASS**, passport **1/2 PASS**, three provider HTTP 500 errors, **0/2 comparable pairs**. All failures are retained; no improvement estimate is claimed. See [the Phase 4 protocol and evidence paths](docs/phase4-onboarding.md). This is an implemented harness with an inconclusive live comparison, not completion of the whole MVP.
