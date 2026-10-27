"""Credential-free CLI for the initial Peeky foundation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .evidence import report, write_report
from .parser import ParseError, read_steps
from .passport import PassportError, make_passport
from .policy import PolicyError, safe_argv, validate_image
from .runner import doctor, execute


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="peeky")
    parser.add_argument("--version", action="version", version=f"peeky {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="Preview annotated README commands")
    inspect.add_argument("repo", type=Path)
    inspect.add_argument("--json", action="store_true")
    check = commands.add_parser("doctor", help="Check Docker readiness")
    check.add_argument("--json", action="store_true")
    audit = commands.add_parser("audit", help="Run approved smoke steps inside Docker")
    audit.add_argument("repo", type=Path)
    audit.add_argument("--approve", action="store_true", help="Acknowledge listed commands may execute")
    audit.add_argument("--image", default="python:3.12-slim")
    audit.add_argument("--output", type=Path, default=Path(".peeky/runs"))
    passport = commands.add_parser("passport", help="Create candidate onboarding instructions")
    passport.add_argument("repo", type=Path)
    passport.add_argument("--evidence", type=Path, required=True)
    passport.add_argument("--output", type=Path, default=Path("AGENTS.generated.md"))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            status = doctor()
            print(json.dumps(status, sort_keys=True) if args.json else f"Docker: {status}")
            return 0 if status["docker_daemon"] else 3
        if args.command == "passport":
            contents = make_passport(args.repo.resolve(strict=True), args.evidence)
            if args.output.exists():
                raise PassportError("Refusing to overwrite an existing passport")
            args.output.write_text(contents, encoding="utf-8")
            print(args.output)
            return 0
        repo = args.repo.resolve(strict=True)
        steps = read_steps(repo)
        for step in steps:
            safe_argv(step.command)
        if args.command == "inspect":
            if args.json:
                print(json.dumps([s.__dict__ for s in steps], indent=2))
            else:
                print(f"Proposed steps: {len(steps)} (never executed)")
                for s in steps:
                    print(f"{s.id} README:{s.line}: {s.command}")
            return 0 if steps else 2
        if args.command == "audit":
            validate_image(args.image)
            if not args.approve:
                print("Execution not authorized. Review with `inspect` then pass --approve.", file=sys.stderr)
                return 2
            if not steps:
                print("No opted-in `bash peeky` steps; no execution.", file=sys.stderr)
                return 2
            if not doctor()["docker_daemon"]:
                print("Docker daemon unavailable; refusing host execution.", file=sys.stderr)
                return 3
            results = []
            for step in steps:
                result = execute(step, repo, args.image)
                results.append(result)
                print(f"{step.id}: {result.outcome}")
                if result.outcome != "PASS":
                    break
            path = write_report(report(repo, args.image, steps, results), args.output)
            print(f"Evidence: {path}")
            return 0 if len(results) == len(steps) and all(r.outcome == "PASS" for r in results) else 1
        parser.error("Unknown command")
    except (OSError, ParseError, PolicyError, PassportError, ValueError, json.JSONDecodeError) as exc:
        print(f"Peeky: {exc}", file=sys.stderr)
        return 3
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
