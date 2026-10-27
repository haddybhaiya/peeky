# Test plan and exact acceptance scenarios

**Levels:** unit (pure), smoke (CLI/package), integration (real Docker), live (opt-in model), e2e (full clean-run and agent benchmark). Real integration must not be faked with monkeypatching. CI currently covers `unit`, `smoke`, Docker fixture tests; `live` explicitly excluded.

| ID | Test/claim | Phase | Evidence |
|---|---|---|---|
| T-001 | Unannotated README blocks ignored | 1 | parser unit |
| T-002 | Annotated one-line commands extract with line number | 1 | parser unit |
| T-003 | Malformed/unterminated block blocked | 1 | parser unit |
| T-004 | Pipelining, substitution, redirection rejected | 1 | policy unit |
| T-005 | Wrong target path/symlink README rejected | 1 | parser/source unit |
| T-006 | No `--approve` means zero target execution | 1 | CLI smoke |
| T-007 | No Docker does not fall back to host | 1 | mock + inspect code |
| T-008 | Source revision/hash recorded, mutation invalidates passport | 1 | evidence unit |
| T-009 | Good annotated command PASS in real Docker | 2 | Docker integration |
| T-010 | Bad deterministic command FAIL in real Docker | 2 | Docker integration |
| T-011 | Missing image/daemon => INCONCLUSIVE | 2 | Docker integration |
| T-012 | Timeout reported, cannot become PASS | 2 | Docker integration |
| T-013 | Read-only source and no egress enforced | 2 | integration/adversarial |
| T-014 | Resource budget/prohibited flags verified | 2 | runner arg contract |
| T-015 | Secrets excluded and logs redacted | 2 | adversarial |
| T-016 | Digest identity and source SHA available | 2 | evidence |
| T-017 | Skipped steps cannot yield PASS | 2 | verdict unit |
| T-018 | Provider parse accepts only typed patch proposal | 3 | contract mock |
| T-019 | Provider missing/unauthorized not fatal to core audit | 3 | contract |
| T-020 | Diff only touches permitted documentation | 3 | adversarial |
| T-021 | Test weakening/evidence rewriting rejected | 3 | adversarial |
| T-022 | Clean recheck under matching environment required | 3 | e2e |
| T-023 | One actual open model diagnosis on fixture | 3 | live opt-in |
| T-024 | Attempt budget prevents endless repair loop | 3 | unit |
| T-025 | Malicious README prompt never modifies policy | 3 | adversarial |
| T-026 | Passport refuses non-PASS or missing evidence | 4 | unit |
| T-027 | Passport refuses changed README/source | 4 | unit |
| T-028 | Existing AGENTS.md not overwritten | 4 | unit |
| T-029 | Cold-start agent can use tools; not fabricated answer | 4 | live e2e |
| T-030 | Same model, source SHA, task, budgets | 4 | benchmark contract |
| T-031 | Benchmark records failures/cost/time, not just successes | 4 | report contract |
| T-032 | Baseline and treatment judge identical oracle | 4 | e2e |
| T-033 | JSON/Markdown describe incomplete verification honestly | 5 | report snapshot |
| T-034 | Wheel CLI runs in clean venv | 5 | wheel smoke |
| T-035 | CI has no credentials in deterministic gates | 5 | inspection |
| T-036 | Full README docs and source refs present | 5 | docs checker |
| T-037 | Demo artifacts show only actually executed cases | 5 | human review |

## Fixed fixtures

- `good_repo` passes `python -m compileall -q .` and a toy smoke script.
- `bad_repo` has deliberately wrong module, must FAIL.
- `no_optin_repo` must produce no steps, INCONCLUSIVE; never auto-infer commands.

## CI gates and counts

Core job: `uv sync`; `ruff check`, `ruff format --check`, `mypy`, tests excluding docker/live, docs checker, wheel build/install. Docker job: explicit image pull and `pytest -m docker`. No CI key. Record tests run/skipped in work review. **Coverage percentages or passed tests cannot be claimed from this document alone.**
