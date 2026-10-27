"""Pure verdict computation and canonical evidence creation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from .models import Step, StepResult


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def verdict(steps: list[Step], results: list[StepResult]) -> str:
    if not steps or len(steps) != len(results):
        return "INCONCLUSIVE"
    if any(r.outcome in ("TIMEOUT", "BLOCKED") for r in results):
        return "INCONCLUSIVE"
    if any(r.outcome == "FAIL" for r in results):
        return "FAIL"
    return "PASS" if all(r.outcome == "PASS" for r in results) else "INCONCLUSIVE"


def report(
    repo: Path, image: str, steps: list[Step], results: list[StepResult]
) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "repo": str(repo.resolve()),
        "readme_sha256": sha256_file(repo / "README.md"),
        "image": image,
        "execution": "offline-docker-per-command",
        "limitations": [
            "Each step has an independent read-only Docker container; no shared installation state",
            "Image may be tag-based; for comparable evidence pin to a verified digest",
            "PASS demonstrates only annotated command success, not full installation correctness",
        ],
        "steps": [asdict(s) for s in steps],
        "results": [r.dict() for r in results],
        "verdict": verdict(steps, results),
    }


def write_report(data: dict[str, object], output: Path) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    import uuid

    target = output / (f"{uuid.uuid4().hex}.json")
    with target.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return target
