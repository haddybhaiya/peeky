# Assumptions and checks

- A-01: Candidate user has Docker on a suitable isolated host. **Local Docker daemon is unavailable; the owner deferred the two Docker tests on 2026-10-27. Phase 2 integration remains unverified; test on CI and another laptop.**
- A-02: Python image can execute selected offline fixture commands. **Test required.**
- A-03: README annotations are acceptable for initial adopter and demo. **Likely friction; compare manual plan later.**
- A-04: Open-weight coding provider fits model credits/budget. **Provider pricing, tokens, uptime TBD.**
- A-05: A controlled cold-start agent can access policy-restricted Docker tools. **Harness integration not implemented.**
- A-06: README patch can fix chosen fixture without modifying package code or tests. **Construct and validate fixture.**
- A-07: Live demonstration can be silent/captioned. **Organizer not explicitly requiring voiceover according to Town Hall.**
- A-08: Submission timing: Town Hall indicates Tuesday evening while public Luma lists Oct 27 8 PM build end and 10 PM form close. **Confirm; don't assume an eight-hour grace period.**
- A-09: The chosen project, Python package and CLI name is `peeky` (display name `Peeky`). **Confirmed by the owner on 2026-10-27; PyPI availability and trademark clearance remain unchecked. No publication is authorized by this rename.**
- A-10: Docker CLI options work on target CI host and kernel. **Real integration required; no mocked assurance.**
- A-11: The declared development group can be resolved and installed reproducibly. **Validated locally on Python 3.13.7 with pytest 9.1.1, Ruff 0.16.10 and mypy 2.4.0; `uv.lock` generated and `uv sync --locked --offline` succeeded. Python 3.12/Linux CI remains unexecuted locally.**
