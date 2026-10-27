"""Pure verdict computation and canonical evidence creation."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path

from .domain import DEFAULT_POLICY, RunPolicy, RunRecord, RunState, SourceIdentity
from .models import Step, StepResult
from .provenance import authenticate
from .redaction import sanitized


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
        if result.outcome not in {"PASS", "FAIL", "BLOCKED", "TIMEOUT", "INCONCLUSIVE"}:
            return "INCONCLUSIVE"
    if any(r.outcome == "FAIL" for r in results):
        return "FAIL"
    if any(r.outcome in ("TIMEOUT", "BLOCKED", "INCONCLUSIVE") for r in results):
        return "INCONCLUSIVE"
    if len(steps) != len(results):
        return "INCONCLUSIVE"
    return "PASS" if all(r.outcome == "PASS" for r in results) else "INCONCLUSIVE"


def runtime_verified(result: StepResult, source: SourceIdentity, image: str) -> bool:
    p = result.provenance
    return (
        p.get("source_sha256") == source.source_sha256
        and p.get("policy_sha256") == DEFAULT_POLICY.sha256
        and image in DEFAULT_POLICY.approved_images
        and p.get("image_digest") == image
        and bool(p.get("image_id"))
        and bool(p.get("container_id"))
        and p.get("target_started") is True
        and p.get("logs_complete") is True
        and p.get("cleanup_verified") is True
        and p.get("stdout_sha256") == hashlib.sha256(result.stdout.encode()).hexdigest()
        and p.get("stderr_sha256") == hashlib.sha256(result.stderr.encode()).hexdigest()
    )


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
    computed = verdict(steps, results)
    if computed == "PASS" and (
        len(steps) != DEFAULT_POLICY.max_audit_steps
        or not all(runtime_verified(r, source, image) for r in results)
    ):
        computed = "INCONCLUSIVE"
    return {
        "schema_version": "1.2",
        "repo": str(repo.resolve()),
        "readme_sha256": readme_hash,
        "source": asdict(source),
        "policy": asdict(policy),
        "policy_sha256": policy.sha256,
        "run": run.dict(),
        "image": image,
        "execution": "offline-docker-single-command",
        "image_digest": next(
            (r.provenance.get("image_digest") for r in results if r.provenance.get("image_digest")),
            None,
        ),
        "coverage": {
            "planned": len(steps),
            "observed": len(results),
            "complete": bool(steps) and len(steps) == len(results),
        },
        "limitations": [
            "One smoke command per audit; no shared installation/dependency setup state",
            "Logs preserve observed streams after redaction within explicit byte budgets",
            "Local HMAC is tamper evidence under the controller key, not public execution attestation",
            "PASS demonstrates only annotated command success, not full installation correctness",
        ],
        "steps": [asdict(s) for s in steps],
        "results": [r.dict() for r in results],
        "verdict": computed,
    }


def write_report(data: dict[str, object], output: Path) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    import uuid

    target = output / (f"{uuid.uuid4().hex}.json")
    clean = sanitized(data)
    assert isinstance(clean, dict)
    for item in clean.get("results", []):
        if isinstance(item, dict) and isinstance(item.get("provenance"), dict):
            for field in ("stdout", "stderr"):
                if isinstance(item.get(field), str):
                    item["provenance"][field + "_sha256"] = hashlib.sha256(
                        item[field].encode()
                    ).hexdigest()
    encoded = json.dumps(authenticate(clean), indent=2, sort_keys=True) + "\n"
    temporary = target.with_suffix(".tmp")
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        # Atomic, exclusive visibility on supported local filesystems; never replace a record.
        os.link(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target
