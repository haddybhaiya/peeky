"""Candidate guidance bound to current clean Git source and consistent evidence."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path

from .domain import DEFAULT_POLICY, RunState, canonical_hash, plan_hash, valid_history
from .evidence import runtime_verified, verdict
from .models import StepResult
from .parser import read_steps
from .policy import safe_argv
from .provenance import authenticate, verify
from .redaction import sanitized
from .sources import SourceError, read_regular, safe_root, snapshot


class PassportError(ValueError):
    pass


_FOOTER = "\n<!-- peeky-passport-provenance -->\n"


def validate_passport_snapshot(captured: object, contents: str) -> dict[str, object]:
    from .sources import SourceSnapshot

    if not isinstance(captured, SourceSnapshot):
        raise PassportError("Passport validation requires a controller snapshot")
    captured.verify()
    if len(contents.encode()) > 512_000 or contents.count(_FOOTER) != 1:
        raise PassportError("Missing or oversized authenticated passport")
    guidance, certificate = contents.split(_FOOTER)
    if not certificate.startswith("```json\n") or not certificate.endswith("\n```\n"):
        raise PassportError("Invalid passport certificate framing")
    try:
        record = json.loads(certificate[8:-5])
        if not isinstance(record, dict):
            raise PassportError("Invalid passport provenance")
        verify(record)
        steps = read_steps(captured.path)
        if (
            record.get("schema_version") != "passport-1"
            or record.get("guidance_sha256")
            != "sha256:" + hashlib.sha256(guidance.encode()).hexdigest()
            or canonical_hash(record.get("source")) != canonical_hash(asdict(captured.identity))
            or record.get("policy_sha256") != DEFAULT_POLICY.sha256
            or record.get("plan_sha256")
            != plan_hash(captured.identity, tuple(steps), DEFAULT_POLICY)
            or record.get("image") not in DEFAULT_POLICY.approved_images
            or record.get("steps") != [asdict(s) for s in steps]
            or not re.fullmatch(r"sha256:[a-f0-9]{64}", str(record.get("evidence_sha256")))
            or not re.fullmatch(r"sha256:[a-f0-9]{64}", str(record.get("image_id")))
        ):
            raise PassportError("Passport source/guidance/policy/evidence identity changed")
        return record
    except (ValueError, TypeError, KeyError, OSError) as exc:
        raise PassportError("Passport authentication or provenance failed") from exc


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
        for step, result in zip(steps, results, strict=True):
            p = result.provenance
            state = p.get("container_state")
            if (
                not re.fullmatch(r"sha256:[a-f0-9]{64}", str(p.get("image_id")))
                or not re.fullmatch(r"[a-f0-9]{64}", str(p.get("container_id")))
                or p.get("command_sha256") != hashlib.sha256(step.command.encode()).hexdigest()
                or not isinstance(state, dict)
                or state.get("Status") != "exited"
                or state.get("Running") is not False
                or state.get("OOMKilled") is not False
                or type(state.get("ExitCode")) is not int
                or state.get("ExitCode") != 0
                or state.get("Error") != ""
            ):
                raise PassportError("Missing exact successful container provenance")
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
    guidance = "\n".join(lines)
    record = authenticate(
        {
            "schema_version": "passport-1",
            "source": asdict(source),
            "policy_sha256": DEFAULT_POLICY.sha256,
            "plan_sha256": plan_hash(source, tuple(steps), DEFAULT_POLICY),
            "steps": [asdict(s) for s in steps],
            "image": payload["image"],
            "image_id": results[0].provenance["image_id"],
            "run_id": run["id"],
            "evidence_sha256": canonical_hash(payload),
            "evidence_file_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
            "guidance_sha256": "sha256:" + hashlib.sha256(guidance.encode()).hexdigest(),
            "authority": "candidate guidance only; controller permissions and oracle remain independent",
        }
    )
    return guidance + _FOOTER + "```json\n" + json.dumps(record, sort_keys=True) + "\n```\n"
