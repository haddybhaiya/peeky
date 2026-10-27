"""Run only reviewed fixtures in Docker and retain authenticated redacted evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from peeky.cli import main as cli_main
from peeky.images import DEFAULT_IMAGE
from peeky.provenance import verify

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / ".peeky/phase2-validation")
    args = parser.parse_args()
    summaries = []
    for fixture, expected, expected_exit in (
        ("good_repo", "PASS", 0),
        ("bad_repo", "FAIL", 1),
        ("no_optin_repo", "INCONCLUSIVE", 2),
    ):
        output = args.output / fixture
        before = set(output.glob("*.json"))
        code = cli_main(
            [
                "audit",
                str(ROOT / "tests/fixtures" / fixture),
                "--approve",
                "--image",
                DEFAULT_IMAGE,
                "--output",
                str(output),
            ]
        )
        produced = set(output.glob("*.json")) - before
        if code != expected_exit or len(produced) != 1:
            raise RuntimeError(f"Unexpected {fixture} exit/evidence count: {code}, {len(produced)}")
        artifact = produced.pop()
        payload = json.loads(artifact.read_text(encoding="utf-8"))
        verify(payload)
        if payload["verdict"] != expected:
            raise RuntimeError(f"{fixture}: expected {expected}, observed {payload['verdict']}")
        if (
            fixture == "good_repo"
            and "HELLO_FROM_GOOD_FIXTURE" not in payload["results"][0]["stdout"]
        ):
            raise RuntimeError("Good fixture success marker absent")
        summaries.append(
            {
                "fixture": fixture,
                "verdict": expected,
                "evidence": str(artifact),
                "source_commit": payload["source"]["git_commit"],
            }
        )
    args.output.mkdir(parents=True, exist_ok=True)
    summary = args.output / "summary.json"
    summary.write_text(
        json.dumps({"image": DEFAULT_IMAGE, "runs": summaries}, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Verified fixture evidence: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
