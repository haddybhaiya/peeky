from dataclasses import asdict, replace
from pathlib import Path

import pytest

from peeky.domain import DEFAULT_POLICY, RunRecord, RunState
from peeky.evidence import report
from peeky.models import StepResult
from peeky.parser import read_steps
from peeky.sources import fingerprint

pytestmark = pytest.mark.unit


def test_T008_report_binds_run_source_and_policy(repo: Path) -> None:
    source = fingerprint(repo)
    steps = read_steps(repo)
    run = RunRecord(source, tuple(steps))
    with pytest.raises(ValueError, match="terminal"):
        report(repo, "python:3.12-slim", steps, [], source, run, DEFAULT_POLICY)
    run.advance(RunState.INSPECTED)
    run.advance(RunState.BLOCKED)
    data = report(repo, "python:3.12-slim", steps, [], source, run, DEFAULT_POLICY)
    assert data["verdict"] == "INCONCLUSIVE"
    assert data["policy_sha256"] == DEFAULT_POLICY.sha256
    assert data["source"] == asdict(source)
    (repo / "README.md").write_bytes(b"changed after capture\n")
    assert (
        report(repo, "python:3.12-slim", steps, [], source, run, DEFAULT_POLICY)["readme_sha256"]
        == data["readme_sha256"]
    )
    with pytest.raises(ValueError, match="mismatch"):
        report(
            repo,
            "python:3.12-slim",
            steps,
            [],
            source,
            run,
            replace(DEFAULT_POLICY, max_commands=11),
        )
    result = StepResult(steps[0].id, steps[0].command, 0, "synthetic", "", "PASS", 1)
    with pytest.raises(ValueError, match="Blocked"):
        report(repo, "python:3.12-slim", steps, [result], source, run, DEFAULT_POLICY)
