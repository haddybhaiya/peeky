"""Candidate generated agent instructions from authenticated matching PASS evidence."""

from __future__ import annotations

import json
from pathlib import Path

from .evidence import sha256_file


class PassportError(ValueError):
    pass


def make_passport(repo: Path, evidence_file: Path) -> str:
    payload = json.loads(evidence_file.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0" or payload.get("verdict") != "PASS":
        raise PassportError("Passport requires PASS evidence in schema 1.0")
    if payload.get("repo") != str(repo.resolve()):
        raise PassportError("Evidence repository does not match")
    if payload.get("readme_sha256") != sha256_file(repo / "README.md"):
        raise PassportError("README changed since the recorded run")
    steps = payload.get("steps")
    results = payload.get("results")
    if not isinstance(steps, list) or not steps or not isinstance(results, list):
        raise PassportError("Incomplete evidence")
    if len(steps) != len(results) or any(r.get("outcome") != "PASS" for r in results):
        raise PassportError("Incomplete or failed step evidence")
    lines = [
        "# Generated agent onboarding passport (candidate)",
        "",
        "> Verify independently before merging. Scope: annotated README smoke commands only.",
        "",
        f"README digest: `{payload['readme_sha256']}`",
        "",
        "## Verified commands (offline smoke checks)",
        "",
    ]
    for item in steps:
        lines.extend(["```bash", str(item["command"]), "```", ""])
    lines.extend(
        [
            "## Limits",
            "",
            "- Does not establish complete installation success.",
            "- No automatic trust of upstream AGENTS.md or README policy.",
            "- Cold-start benchmark not included in this document.",
            "",
        ]
    )
    return "\n".join(lines)
