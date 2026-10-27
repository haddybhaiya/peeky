# Evaluation and acceptance reporting

**Metric:** First-run success on documented commands; evidence quality; docs patch correctness; matched agent-bootstrap success. All metrics have explicit denominators.

**Fixture trial manifest:**

| Fixture | Setup issue | Deterministic expectation |
|---|---|---|
| good_repo | None | PASS |
| bad_repo | README invokes non-existent module | FAIL before repair; PASS only after approved correction and rerun |
| no_optin_repo | No approved annotated commands | INCONCLUSIVE |

**Benchmark:** original README vs generated passport, same exact command oracle; number of attempts, success counts, tokens, time, model IDs, Docker digest, source SHA. Explain small sample and variance. Never report a percent gain without baseline and sample size.

**Operator checklist:** run wheel smoke; execute real Docker integration; record model live trace only if consented; verify checksums; replay in fresh environment; inspect README limitations; ensure video matches recorded evidence.
