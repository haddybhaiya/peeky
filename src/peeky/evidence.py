"""Pure verdict computation and canonical evidence creation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from .domain import RunPolicy, RunRecord, RunState, SourceIdentity
from .models import Step, StepResult


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def verdict(steps: list[Step], results: list[StepResult]) -> str:
    if not steps or len(results) > len(steps) or len({s.id for s in steps}) != len(steps):
        return "INCONCLUSIVE"
    for step, result in zip(steps, results, strict=False):
        if not all(
            isinstance(value, str)
            for value in (result.id, result.command, result.stdout, result.stderr, result.outcome)
        ):
            return "INCONCLUSIVE"
        if (result.id, result.command) != (step.id, step.command):
            return "INCONCLUSIVE"
        if type(result.duration_ms) is not int or result.duration_ms < 0:
            return "INCONCLUSIVE"
        if result.outcome == "PASS" and (
            type(result.exit_code) is not int or result.exit_code != 0
        ):
            return "INCONCLUSIVE"
        if result.outcome == "FAIL" and (
            type(result.exit_code) is not int or result.exit_code == 0
        ):
            return "INCONCLUSIVE"
        if result.outcome not in {"PASS", "FAIL", "BLOCKED", "TIMEOUT"}:
            return "INCONCLUSIVE"
    if any(r.outcome == "FAIL" for r in results):
        return "FAIL"
    if any(r.outcome in ("TIMEOUT", "BLOCKED") for r in results):
        return "INCONCLUSIVE"
    if len(steps) != len(results):
        return "INCONCLUSIVE"
    return "PASS" if all(r.outcome == "PASS" for r in results) else "INCONCLUSIVE"


def report(
    repo: Path,
    image: str,
    steps: list[Step],
    results: list[StepResult],
    source: SourceIdentity,
    run: RunRecord,
    policy: RunPolicy,
) -> dict[str, object]:
    if run.source != source or run.steps != tuple(steps) or run.policy != policy:
        raise ValueError("Run/source/plan/policy mismatch")
    if run.state not in {RunState.FINALIZED, RunState.BLOCKED}:
        raise ValueError("Only terminal run states may create evidence")
    if run.state == RunState.BLOCKED and results:
        raise ValueError("Blocked runs cannot contain execution results")
    readme_hash = next(item.sha256 for item in source.files if item.path == "README.md")
    return {
        "schema_version": "1.1",
        "repo": str(repo.resolve()),
        "readme_sha256": readme_hash,
        "source": asdict(source),
        "policy": asdict(policy),
        "policy_sha256": policy.sha256,
        "run": run.dict(),
        "image": image,
        "execution": "offline-docker-per-command",
        "limitations": [
            "Each step has an independent read-only Docker container; no shared installation state",
            "Image may be tag-based; for comparable evidence pin to a verified digest",
            "JSON provenance is not a signature or independent execution attestation",
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
