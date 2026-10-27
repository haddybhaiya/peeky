"""One explicitly authorized live Gemma proposal; stop for human approval before recheck."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from peeky.evidence import write_report
from peeky.hosttools import host_tool
from peeky.providers.openai_compatible import load_config
from peeky.repair import FrozenOracle, claim_attempt, diagnose, load_record, run_snapshot
from peeky.sources import snapshot

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--output", type=Path, default=Path(".peeky/phase3-validation"))
    args = parser.parse_args()
    if not args.live:
        parser.error("Explicit --live is required; no provider request was made")
    config = load_config(args.env_file)
    args.output.mkdir(parents=True, exist_ok=True)
    claim_attempt(args.output / "attempts", "live", "one-authorized-Gemma-provider-test")
    fixture = args.output.resolve() / "fixture"
    fixture.mkdir(exist_ok=False)
    for name in ("README.md", "repair_smoke.py"):
        (fixture / name).write_bytes((ROOT / "tests/fixtures/outdated_repo" / name).read_bytes())
    binary = host_tool("git", avoid=fixture)
    if binary is None:
        raise ValueError("Trusted Git is required")
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_AUTHOR_NAME="Peeky live fixture",
        GIT_AUTHOR_EMAIL="fixture@example.invalid",
        GIT_COMMITTER_NAME="Peeky live fixture",
        GIT_COMMITTER_EMAIL="fixture@example.invalid",
    )
    for command in (
        ("init", "--template=", "-q"),
        ("add", "--", "."),
        ("commit", "-qm", "Reviewed Phase 3 live fixture"),
    ):
        subprocess.run(
            [
                binary,
                "-c",
                f"core.hooksPath={os.devnull}",
                "-c",
                "core.autocrlf=false",
                "-c",
                "commit.gpgSign=false",
                *command,
            ],
            cwd=fixture,
            env=env,
            check=True,
            capture_output=True,
            timeout=15,
        )
    with snapshot(fixture) as captured:
        baseline = run_snapshot(captured)
    baseline_path = write_report(baseline, args.output / "baseline")
    if baseline["verdict"] != "FAIL":
        raise ValueError("Actual baseline must FAIL; no provider call was made")
    proposal_path = diagnose(
        fixture,
        baseline_path,
        FrozenOracle("python repair_smoke.py", "PEEKY_RECHECK_OK"),
        config,
        args.output / "proposals",
        args.output / "attempts",
        consent=True,
    )
    proposal = load_record(proposal_path)
    summary = {
        "fixture": str(fixture),
        "baseline_evidence": str(baseline_path.resolve()),
        "proposal_evidence": str(proposal_path.resolve()),
        "status": proposal["status"],
        "approval_digest": proposal["approval_digest"],
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    trace = proposal["provider_trace"]
    print(
        json.dumps(
            {
                **summary,
                "model": trace.get("observed_model"),
                "model_version": trace["model_version"],
                "cost_usd": trace.get("cost_usd"),
                "cost_basis": trace.get("cost_basis"),
                "usage": trace.get("usage"),
            },
            indent=2,
        )
    )
    if proposal["status"] == "PROPOSED":
        print(proposal["proposal"]["candidate_diff"])
        print("STOP: human approval of the exact proposal is required before recheck.")
        return 0
    print("Concrete live-provider blocker:", proposal.get("error", trace.get("error")))
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
