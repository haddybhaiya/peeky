# Evidence, competitors, and honest market gap

**Research basis (linked sources; verify details before public marketing):**

1. Tan et al. (2023), *Empirical Software Engineering*, code-element references become outdated over project histories. https://link.springer.com/article/10.1007/s10664-023-10397-6
2. *Automated Extraction of Research Software Installation Instructions from README Files* (2024). Extraction of branching/optional instructions is nontrivial. Search article title for accessible published copy.
3. Prior studies of newcomer onboarding documented setup/documentation barriers years before LLM agents; do not frame this as an invented AI-only pain point.
4. EnvBench by JetBrains Research benchmarks software environment setup for agentic use: https://kairos.jetbrains.com/research/articles/envbench-automated-environment-setup

**Adjacent tools:**

- Runme: Markdown workflow execution and CI support. https://runme.dev/
- Mintlify: automated documentation writing and maintenance. https://mintlify.com/
- ReadMe: API docs and AI-assisted content. https://readme.com/

**Opportunity hypothesis:** These tools may support overlapping capabilities, but a narrow no-SaaS CLI that measures first-time reproducibility, generates a verified agent onboarding passport and A/B tests agent cold starts could be differentiated. This is a hypothesis, not evidence competitors lack every feature.

**Research validation after MVP:** 5 maintainers, 10 real Python repos, transparent categories (PASS / FAIL / INCONCLUSIVE), rate of genuinely fixable docs drift, time saved, false fixes, agent setup success. No fabricated counts or model speedups.
