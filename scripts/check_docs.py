"""Credential-free docs reference validation (fast, intentionally simple)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md",
    "AGENTS.md",
    "pyproject.toml",
    "docs/phase.md",
    "docs/mvp-contract.md",
    "docs/architecture.md",
    "docs/test-plan.md",
    "docs/open-models.md",
    "docs/runner-security.md",
    "docs/agent-benchmark.md",
    "docs/invariants.md",
    "docs/work_review.md",
    "docs/assumptions.md",
    "docs/decisions.md",
    "docs/source-capture.md",
    "docs/phase2-runner.md",
    "docs/phase3-repair.md",
    "docs/phase4-onboarding.md",
    "docs/phase5-review.md",
]


def main() -> int:
    absent = [path for path in REQUIRED if not (ROOT / path).is_file()]
    assert not absent, f"Missing required documents: {absent}"
    for rel in REQUIRED:
        if rel.endswith(".md"):
            content = (ROOT / rel).read_text(encoding="utf-8")
            assert content.startswith("# "), f"Missing first-level title: {rel}"
            assert len(content.strip()) > 80, f"Too little text: {rel}"
    print(f"Checked {len(REQUIRED)} required files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
