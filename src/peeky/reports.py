"""Bounded, locally authenticated evidence summaries; no execution or model calls."""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from typing import Any

from .benchmark import summarize
from .domain import DEFAULT_POLICY, SourceFile, SourceIdentity, canonical_hash
from .evidence import runtime_verified, write_report
from .models import Step, StepResult
from .redaction import sanitized
from .repair import load_record

LIMITS = [
    "Summary only: no new execution, recheck, source refresh or model request",
    "Local HMAC authentication is not a public execution attestation",
    "Original redacted logs remain in private evidence; this export omits logs and host paths",
    "PASS concerns one permitted smoke command, not complete installation correctness",
    "Unknown usage, billing and hosted weights revision remain unknown",
]


def summarize_record(record: dict[str, Any]) -> dict[str, Any]:
    schema = record.get("schema_version")
    result: dict[str, Any] = {"source_schema": schema, "record_sha256": canonical_hash(record)}
    if schema == "1.2":
        source_data = dict(record["source"])
        source_data["files"] = tuple(SourceFile(**f) for f in source_data["files"])
        source = SourceIdentity(**source_data)
        steps = [Step(**s) for s in record["steps"]]
        results = [StepResult(**r) for r in record["results"]]
        outcome = record["verdict"]
        coverage = record.get("coverage", {})
        complete = (
            len(steps) == len(results) == 1
            and coverage.get("complete") is True
            and coverage.get("planned") == coverage.get("observed") == 1
            and record.get("policy_sha256") == DEFAULT_POLICY.sha256
            and record.get("execution") == "offline-docker-single-command"
            and record.get("run", {}).get("state") == "FINALIZED"
            and all(r.outcome == "PASS" and r.exit_code == 0 for r in results)
            and all(runtime_verified(r, source, record["image"]) for r in results)
        )
        if outcome == "PASS" and not complete:
            outcome = "INCONCLUSIVE"
        if outcome not in ("PASS", "FAIL", "BLOCKED", "INCONCLUSIVE"):
            raise ValueError("Unknown audit outcome")
        result.update(
            outcome=outcome,
            complete_pass_observation=complete,
            git_commit=source.git_commit,
            source_sha256=source.source_sha256,
            policy_sha256=record["policy_sha256"],
            image=record["image"],
            coverage=coverage,
            commands=[s.command for s in steps],
            observed=[
                {"outcome": r.outcome, "exit_code": r.exit_code, "reason": r.reason}
                for r in results
            ],
        )
    elif schema == "onboarding-pair-1":
        result.update(outcome="COMPARISON_ONLY", comparison=summarize(record["trials"]))
    elif schema == "onboarding-study-1":
        # Preserve the authenticated recorded aggregate, without silently rerunning its study.
        result.update(
            outcome="COMPARISON_ONLY",
            comparison=record["summary"],
            pair_sha256=record["pair_sha256"],
            report_sha256=record["report_sha256"],
            dependency_revalidation="not performed; original pair/trace records retained separately",
        )
    else:
        raise ValueError("Unsupported evidence schema; no guessed summary")
    clean = sanitized(result)
    assert isinstance(clean, dict)
    return clean


def render_markdown(summary: dict[str, Any]) -> str:
    lines = ["# Peeky evidence summary", "", "Status: SUMMARY_ONLY", ""]
    for index, record in enumerate(summary["records"], 1):
        lines.extend([f"## Record {index}", ""])
        for key in ("source_schema", "record_sha256", "outcome", "git_commit", "source_sha256"):
            if key in record:
                lines.append(f"- {key}: {html.escape(str(record[key]))}")
        if "comparison" in record:
            comparison = record["comparison"]
            lines.append(
                f"- Comparable pairs: {comparison['comparable_pairs']}/{comparison['attempted_pairs']}"
            )
            for row in comparison["rows"]:
                lines.append(
                    f"- {html.escape(str(row['arm']))}: {row['PASS']}/{row['attempted']} PASS; "
                    f"FAIL {row['FAIL']}; BLOCKED {row['BLOCKED']}; "
                    f"INCONCLUSIVE {row['INCONCLUSIVE']}; "
                    f"reported tokens {row['reported_tokens'] if row.get('reported_tokens') is not None else 'unknown'}"
                )
            lines.append("- No generalized or causal improvement claim.")
        lines.append("")
    lines.extend(["## Limits", "", *[f"- {line}" for line in LIMITS], ""])
    return "\n".join(lines)


def export_summary(paths: list[Path], output: Path) -> Path:
    if not 1 <= len(paths) <= 16:
        raise ValueError("Select between one and sixteen explicit evidence files")
    records = []
    for path in paths:
        # Bounded safe regular-file read plus local HMAC verification; no transitive path following.
        record = load_record(path)
        records.append(summarize_record(record))
    summary: dict[str, Any] = {
        "schema_version": "summary-1",
        "status": "SUMMARY_ONLY",
        "records": records,
        "limitations": LIMITS,
    }
    markdown = render_markdown(summary)
    summary["markdown_sha256"] = "sha256:" + hashlib.sha256(markdown.encode()).hexdigest()
    # A new directory avoids overwriting or mixing unrelated exports.
    output.mkdir(parents=True, exist_ok=False)
    with (output / "summary.md").open("x", encoding="utf-8", newline="") as stream:
        stream.write(markdown)
    path = write_report(summary, output / "records")
    with (output / "index.json").open("x", encoding="utf-8", newline="") as stream:
        json.dump({"summary_record": path.name, "markdown": "summary.md"}, stream, indent=2)
        stream.write("\n")
    return path
