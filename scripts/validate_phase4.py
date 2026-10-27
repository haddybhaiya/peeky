"""One explicit live matched pair. Failures stay in both actual trial denominators."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from peeky.benchmark import run_pair
from peeky.cli import main as cli
from peeky.providers.openai_compatible import load_config
from peeky.repair import FrozenOracle, claim_attempt, load_record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--output", type=Path, default=Path(".peeky/phase4-validation"))
    args = parser.parse_args()
    if not args.live:
        parser.error("Explicit --live authorizes model disclosure and the reviewed smoke fixture")
    config = load_config(args.env_file)
    claim_attempt(args.output / "attempts", "validation", "one-matched-Gemma-pair")
    repo = Path(__file__).resolve().parents[1] / "tests/fixtures/good_repo"
    audit = args.output / "audit"
    if cli(["audit", str(repo), "--approve", "--output", str(audit)]) != 0:
        raise ValueError("Fresh trusted audit failed; no pair/model request started")
    records = list(audit.glob("*.json"))
    if len(records) != 1:
        raise ValueError("Expected exactly one fresh audit record")
    pair = run_pair(
        repo,
        records[0],
        FrozenOracle("python smoke.py", "HELLO_FROM_GOOD_FIXTURE"),
        config,
        args.output / "pair",
        consent=True,
        approve=True,
    )
    record = load_record(pair)
    summary = {
        "paired_evidence": str(pair.resolve()),
        "report": str((args.output / "pair/paired-report.md").resolve()),
        "summary": record["summary"],
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
