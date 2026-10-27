# Product brief

**Who:** Maintainers and newcomers using Python OSS, plus engineers delegating new repositories to coding agents.

**Job:** Determine if another developer/agent can reliably bootstrap and smoke-test a repository, and produce a minimal independently verifiable improvement when it cannot.

**Problem:** README setup and actual source/config drift. First-time setup failures waste time and make AI coding agents burn context and tokens. Related tools exist (Runme, Mintlify, ReadMe); we target the specific *fresh onboarding contract* and clean-run proof.

**Primary claim:** "Don't just trust the README. Verify the first run — for humans and AI agents."

**Input:** local public Python repo, README with explicit opted-in commands, selected image and open-model endpoint (optional). **Output:** per-step sandbox records; blocked/failed/pass outcome; optional model patch proposal; fresh recheck; candidate AGENTS.generated.md; A/B cold-start evidence.

**Uncertainty:** No users recruited, market size not quantified, model value and measured agent lift unverified. See `docs/research.md` and `docs/evaluation.md`.

**Positioning:** CLI-first, permissively licensed, local evidence; no subscriptions, API tokens or hosted service required for deterministic checks. External open-model inference is opted into explicitly.
