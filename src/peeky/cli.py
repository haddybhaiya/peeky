"""Credential-free CLI for the initial Peeky foundation."""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import ExitStack
from dataclasses import asdict
from pathlib import Path

from . import __version__
from .backends import get_backend
from .backends.base import BackendUnavailable, SandboxBackend
from .domain import DEFAULT_POLICY, RunRecord, RunState
from .evidence import report, write_report
from .github import RemoteSource, github_snapshot
from .images import DEFAULT_IMAGE
from .parser import ParseError, read_steps
from .passport import PassportError, make_passport
from .policy import PolicyError, safe_argv, validate_run_image
from .sources import SourceError, SourceSnapshot, safe_root, snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="peeky")
    parser.add_argument("--version", action="version", version=f"peeky {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="Preview annotated README commands")
    inspect.add_argument("repo", help="Local Git directory or public GitHub repository URL")
    inspect.add_argument("--ref", help="GitHub branch, tag or full commit SHA (URL inputs only)")
    inspect.add_argument("--json", action="store_true")
    check = commands.add_parser("doctor", help="Check Docker readiness")
    check.add_argument("--json", action="store_true")
    check.add_argument("--backend", choices=("docker", "instabox"), default="docker")
    audit = commands.add_parser("audit", help="Run approved smoke steps inside Docker")
    audit.add_argument("repo", help="Local Git directory or public GitHub repository URL")
    audit.add_argument("--ref", help="GitHub branch, tag or full commit SHA (URL inputs only)")
    audit.add_argument("--backend", choices=("docker", "instabox"), default="docker")
    audit.add_argument(
        "--approve", action="store_true", help="Acknowledge listed commands may execute"
    )
    audit.add_argument(
        "--image", default=DEFAULT_IMAGE, help="Reviewed cached official Python digest"
    )
    audit.add_argument("--output", type=Path, default=Path(".peeky/runs"))
    passport = commands.add_parser("passport", help="Create candidate onboarding instructions")
    passport.add_argument("repo", type=Path)
    passport.add_argument("--evidence", type=Path, required=True)
    passport.add_argument("--output", type=Path, default=Path("AGENTS.generated.md"))
    diagnosis = commands.add_parser("diagnose", help="Opt in to one bounded README patch proposal")
    diagnosis.add_argument("repo", type=Path)
    diagnosis.add_argument("--evidence", type=Path, required=True)
    diagnosis.add_argument("--expected-command", required=True)
    diagnosis.add_argument("--expected-stdout", required=True)
    diagnosis.add_argument("--model-consent", action="store_true")
    diagnosis.add_argument("--env-file", type=Path)
    diagnosis.add_argument("--output", type=Path, default=Path(".peeky/repairs/proposals"))
    diagnosis.add_argument("--state", type=Path, default=Path(".peeky/repair-attempts"))
    recheck = commands.add_parser(
        "recheck", help="Recheck the exact human-approved README proposal"
    )
    recheck.add_argument("repo", type=Path)
    recheck.add_argument("--proposal", type=Path, required=True)
    recheck.add_argument("--approve-proposal", required=True)
    recheck.add_argument("--output", type=Path, default=Path(".peeky/repairs/rechecks"))
    recheck.add_argument("--state", type=Path, default=Path(".peeky/repair-attempts"))
    trial = commands.add_parser("trial", help="Run one matched restricted fresh-agent pair")
    trial.add_argument("repo", type=Path)
    trial.add_argument("--evidence", type=Path, required=True)
    trial.add_argument("--expected-command", required=True)
    trial.add_argument("--expected-stdout", required=True)
    trial.add_argument("--approve", action="store_true")
    trial.add_argument("--model-consent", action="store_true")
    trial.add_argument("--env-file", type=Path)
    trial.add_argument("--output", type=Path, default=Path(".peeky/trials"))
    summary = commands.add_parser("report", help="Export an authenticated evidence summary")
    summary.add_argument("--evidence", type=Path, action="append", required=True)
    summary.add_argument("--output", type=Path, required=True)
    return parser


def _remote_input(value: str) -> bool:
    return "://" in value or value.startswith(("http:", "https:", "git:", "ssh:", "file:", "git@"))


def _print_inspection(captured: SourceSnapshot, remote: RemoteSource | None, as_json: bool) -> int:
    steps = read_steps(captured.path)
    for step in steps:
        safe_argv(step.command)
    run = RunRecord(captured.identity, tuple(steps))
    run.advance(RunState.INSPECTED)
    if as_json:
        data: dict[str, object] = {
            "schema_version": "1.1",
            "source": asdict(captured.identity),
            "policy_sha256": DEFAULT_POLICY.sha256,
            "run": run.dict(),
            "steps": [asdict(step) for step in steps],
        }
        if remote is not None:
            data["remote"] = asdict(remote)
        print(json.dumps(data, indent=2))
    else:
        if remote is not None:
            print(f"Repository: {remote.url}")
            print(f"Ref: {remote.requested_ref or '(default)'} -> {remote.git_commit}")
        print(f"Source: {captured.identity.git_commit} {captured.identity.source_sha256}")
        print(f"Plan: {run.dict()['plan_sha256']}")
        print(f"Proposed steps: {len(steps)} (never executed)")
        for step in steps:
            print(f"{step.id} README:{step.line}: {step.command}")
    return 0 if steps else 2


def _audit_source(
    captured: SourceSnapshot, repo: Path | RemoteSource, image: str, backend: SandboxBackend
) -> tuple[dict[str, object], int]:
    """Observe the audit; finalize its record only after source contexts close."""
    steps = read_steps(captured.path)
    run = RunRecord(captured.identity, tuple(steps))
    run.advance(RunState.INSPECTED)
    reason = ""
    try:
        validate_run_image(image)
        for step in steps:
            safe_argv(step.command)
        if not steps:
            reason = "NO_OPTED_IN_COMMANDS"
        elif len(steps) != DEFAULT_POLICY.max_audit_steps:
            reason = "MULTI_STEP_UNSUPPORTED"
    except PolicyError as exc:
        reason = str(exc)
    if reason:
        run.advance(RunState.BLOCKED)
        data = report(repo, image, steps, [], captured.identity, run, DEFAULT_POLICY)
        data["reason"] = reason
        print(f"No execution: {reason}", file=sys.stderr)
        return data, 2
    run.advance(RunState.APPROVED)
    readiness = backend.doctor(avoid=captured._origin)
    if not readiness.ready:
        run.advance(RunState.BLOCKED)
        data = report(repo, image, steps, [], captured.identity, run, DEFAULT_POLICY)
        data["reason"] = "Docker daemon unavailable; no target execution"
        print("Docker daemon unavailable; refusing host execution.", file=sys.stderr)
        return data, 3
    run.advance(RunState.SANDBOX_RUN)
    results = []
    for step in steps:
        captured.verify()
        result = backend.execute(
            step, captured, image, timeout=DEFAULT_POLICY.command_timeout_seconds
        )
        results.append(result)
        print(f"{step.id}: {result.outcome}")
        if result.outcome != "PASS":
            break
    captured.verify()
    run.advance(RunState.OBSERVED)
    run.advance(RunState.FINALIZED)
    data = report(repo, image, steps, results, captured.identity, run, DEFAULT_POLICY)
    code = 0 if data["verdict"] == "PASS" else 1 if data["verdict"] == "FAIL" else 3
    return data, code


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command in {"passport", "diagnose", "recheck", "trial"} and _remote_input(
            str(args.repo)
        ):
            raise SourceError(
                "GitHub URLs are supported by inspect and audit; this command requires a local repository"
            )
        if args.command == "report":
            from .reports import export_summary

            path = export_summary(args.evidence, args.output)
            print(f"Summary evidence: {path}")
            print(f"Readable report: {args.output / 'summary.md'}")
            print("SUMMARY_ONLY: no new execution or verification")
            return 0
        if args.command == "trial":
            if not args.approve or not args.model_consent:
                print("Trial requires --approve and --model-consent.", file=sys.stderr)
                return 2
            from .benchmark import run_pair
            from .providers.openai_compatible import load_config
            from .repair import FrozenOracle

            path = run_pair(
                args.repo,
                args.evidence,
                FrozenOracle(args.expected_command, args.expected_stdout),
                load_config(args.env_file),
                args.output,
                consent=True,
                approve=True,
            )
            print(f"Paired evidence: {path}")
            print(f"Report: {args.output / 'paired-report.md'}")
            return 0
        if args.command in {"diagnose", "recheck"}:
            from .providers.openai_compatible import load_config
            from .repair import FrozenOracle, diagnose, load_record, recheck

            if args.command == "diagnose":
                if not args.model_consent:
                    print(
                        "Model disclosure not authorized; pass --model-consent after review.",
                        file=sys.stderr,
                    )
                    return 2
                config = load_config(args.env_file)
                path = diagnose(
                    args.repo,
                    args.evidence,
                    FrozenOracle(args.expected_command, args.expected_stdout),
                    config,
                    args.output,
                    args.state,
                    consent=True,
                )
            else:
                path = recheck(
                    args.repo, args.proposal, args.approve_proposal, args.output, args.state
                )
            data = load_record(path)
            print(f"Evidence: {path}")
            print(f"Status: {data['status']}")
            if data["status"] == "PROPOSED":
                print(data["proposal"]["candidate_diff"])
                print(
                    f"Review this exact proposal, then --approve-proposal {data['approval_digest']}"
                )
            return 0 if data["status"] in {"PROPOSED", "VERIFIED"} else 3
        if args.command == "doctor":
            selected = get_backend(args.backend)
            readiness = selected.doctor()
            if selected.name == "docker":
                status = readiness.details
                print(json.dumps(status, sort_keys=True) if args.json else f"Docker: {status}")
            elif args.json:
                print(json.dumps(readiness.to_dict(), sort_keys=True))
            else:
                print(f"InstaBox: {readiness.reason}")
                print(readiness.message)
            return 0 if readiness.preflight_ok else 3
        if args.command == "passport":
            if args.output.name != "AGENTS.generated.md":
                raise PassportError("Passport output must be AGENTS.generated.md; never AGENTS.md")
            contents = make_passport(args.repo, args.evidence)
            if args.output.exists():
                raise PassportError("Refusing to overwrite an existing passport")
            with args.output.open("x", encoding="utf-8") as output:
                output.write(contents)
            print(args.output)
            return 0
        backend: SandboxBackend | None = None
        if args.command == "audit":
            if not args.approve:
                print(
                    "Execution not authorized. Review with `inspect` then pass --approve.",
                    file=sys.stderr,
                )
                return 2
            backend = get_backend(args.backend)
            if not backend.execution_supported:
                raise BackendUnavailable(
                    "InstaBox audit execution is not implemented; use doctor --backend instabox for read-only account checks"
                )
        with ExitStack() as stack:
            repo: Path | RemoteSource
            if _remote_input(args.repo):
                fetched = stack.enter_context(github_snapshot(args.repo, args.ref))
                captured = fetched.source
                repo = fetched.remote
            else:
                if args.ref is not None:
                    raise SourceError(
                        "--ref is supported only for GitHub URL inspection and audits"
                    )
                repo = safe_root(Path(args.repo))
                captured = stack.enter_context(snapshot(repo))
            if args.command == "inspect":
                return _print_inspection(
                    captured, repo if isinstance(repo, RemoteSource) else None, args.json
                )
            assert backend is not None
            data, code = _audit_source(captured, repo, args.image, backend)
        # No record is published until temporary Git storage and exports close.
        path = write_report(data, args.output)
        print(f"Evidence: {path}")
        return code
    except (
        OSError,
        ParseError,
        PolicyError,
        PassportError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(f"Peeky: {exc}", file=sys.stderr)
        return 3
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
