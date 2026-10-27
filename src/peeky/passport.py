"""Candidate guidance bound to current clean Git source and consistent evidence."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .domain import DEFAULT_POLICY, RunState, canonical_hash, plan_hash, valid_history
from .evidence import runtime_verified, verdict
from .models import StepResult
from .parser import read_steps
from .policy import safe_argv
from .provenance import verify
from .redaction import sanitized
from .sources import SourceError, read_regular, safe_root, snapshot


class PassportError(ValueError):
    pass


def make_passport(repo: Path, evidence_file: Path) -> str:
    try:
        raw = read_regular(safe_root(evidence_file.parent), evidence_file.name, 2 * 1024 * 1024)
        payload = json.loads(raw.decode("utf-8"))
    except (SourceError, OSError, ValueError) as exc:
        raise PassportError("Invalid or oversized evidence file") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != "1.2":
        raise PassportError("Passport requires controller-bound evidence in schema 1.2")
    try:
        verify(payload)
    except (ValueError, OSError) as exc:
        raise PassportError("Controller evidence authentication failed") from exc
    if payload.get("verdict") != "PASS":
        raise PassportError("Passport requires PASS evidence")
    if payload.get("execution") != "offline-docker-single-command":
        raise PassportError("Evidence execution mode is unsupported")
    try:
        repo = safe_root(repo)
        with snapshot(repo) as captured:
            source = captured.identity
            steps = read_steps(captured.path)
        for step in steps:
            safe_argv(step.command)
        if payload.get("repo") != str(repo):
            raise PassportError("Evidence repository does not match")
        if canonical_hash(payload.get("source")) != canonical_hash(asdict(source)):
            raise PassportError("Source revision or bytes changed since the run")
        if payload.get("readme_sha256") != next(
            f.sha256 for f in source.files if f.path == "README.md"
        ):
            raise PassportError("README evidence mismatch")
        if (
            payload.get("policy_sha256") != DEFAULT_POLICY.sha256
            or canonical_hash(payload.get("policy")) != DEFAULT_POLICY.sha256
        ):
            raise PassportError("Evidence policy does not match the controller")
        if payload.get("steps") != sanitized([asdict(step) for step in steps]):
            raise PassportError("Evidence commands do not match source instructions")
        run = payload.get("run")
        if (
            not isinstance(run, dict)
            or run.get("state") != RunState.FINALIZED
            or not (valid_history(run.get("history"), RunState.FINALIZED))
            or run.get("plan_sha256") != plan_hash(source, tuple(steps), DEFAULT_POLICY)
        ):
            raise PassportError("Incomplete or mismatched controller run")
        raw_results = payload.get("results")
        if not isinstance(raw_results, list):
            raise PassportError("Missing result evidence")
        results = [StepResult(**item) for item in raw_results]
        if (
            len(steps) != DEFAULT_POLICY.max_audit_steps
            or verdict(steps, results) != "PASS"
            or not all(runtime_verified(r, source, str(payload.get("image"))) for r in results)
        ):
            raise PassportError("Incomplete or inconsistent step evidence")
    except (SourceError, OSError, TypeError, KeyError) as exc:
        raise PassportError("Source or evidence cannot be validated") from exc
    lines = [
        "# Generated agent onboarding passport (candidate)",
        "",
        "> Independently verify before merging; local HMAC is not a public execution attestation.",
        "",
        f"Git commit: `{source.git_commit}`",
        f"Source digest: `{source.source_sha256}`",
        f"Policy digest: `{DEFAULT_POLICY.sha256}`",
        "",
        "## Recorded commands (offline smoke checks)",
        "",
    ]
    for step in steps:
        lines.extend(["```bash", step.command, "```", ""])
    lines.extend(
        [
            "## Limits",
            "",
            "- Scope: selected committed Git directory only.",
            "- Does not establish complete installation success or an agent benchmark.",
            "- No automatic trust of upstream AGENTS.md or README policy.",
            "",
        ]
    )
    return "\n".join(lines)
