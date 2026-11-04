import json
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from peeky.domain import DEFAULT_POLICY, RunRecord, RunState
from peeky.evidence import report, write_report
from peeky.github import RemoteSource, remote_from_record
from peeky.models import StepResult
from peeky.parser import read_steps
from peeky.provenance import verify
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


def test_url_report_binds_and_authenticates_durable_origin(repo: Path, tmp_path: Path) -> None:
    source = fingerprint(repo)
    steps = read_steps(repo)
    run = RunRecord(source, tuple(steps))
    run.advance(RunState.INSPECTED)
    run.advance(RunState.BLOCKED)
    remote = RemoteSource(
        "https://github.com/fixture/project", "main", "refs/heads/main", source.git_commit
    )
    data = report(remote, "python:3.12-slim", steps, [], source, run, DEFAULT_POLICY)
    assert data["repo"] == remote.url and data["remote"] == asdict(remote)
    assert str(repo) not in json.dumps(data)
    artifact = write_report(data, tmp_path / "evidence")
    saved = json.loads(artifact.read_text())
    verify(saved)
    saved["remote"]["git_commit"] = "0" * 40
    with pytest.raises(ValueError, match="integrity"):
        verify(saved)


@pytest.mark.parametrize(
    "changes",
    [
        {"url": "https://github.com/fixture/project.git"},
        {"url": "https://other.example/fixture/project"},
        {"git_commit": "0" * 40},
        {"resolved_ref": "refs/heads/other"},
        {"requested_ref": "0" * 40, "resolved_ref": None},
        {"requested_ref": 123},
    ],
)
def test_remote_origin_rejects_inconsistent_fields(repo: Path, changes: dict[str, object]) -> None:
    source = fingerprint(repo)
    value = asdict(
        RemoteSource(
            "https://github.com/fixture/project", "main", "refs/heads/main", source.git_commit
        )
    )
    value.update(changes)
    with pytest.raises(ValueError):
        remote_from_record(value, source)
    with pytest.raises(ValueError):
        remote_from_record(
            asdict(
                RemoteSource(
                    "https://github.com/fixture/project",
                    "main",
                    "refs/heads/main",
                    source.git_commit,
                )
            ),
            replace(source, scope="subdir"),
        )


@pytest.mark.parametrize(
    ("requested", "resolved"),
    [
        ("api_key=[REDACTED]", "refs/heads/api_key=[REDACTED]"),
        (None, "refs/heads/api_key=[REDACTED]"),
        ("HEAD", "refs/heads/[REDACTED]"),
        ("[REDACTED]", "[REDACTED]"),
        ("api_key=[REDACTED]", "refs/tags/api_key=[REDACTED]"),
    ],
)
def test_stored_redacted_labels_preserve_commit_binding(
    repo: Path, requested: str | None, resolved: str
) -> None:
    source = fingerprint(repo)
    remote = RemoteSource(
        "https://github.com/fixture/project", requested, resolved, source.git_commit
    )
    assert remote_from_record(asdict(remote), source) == remote
    with pytest.raises(ValueError):
        remote.validate(source)  # The same label must never become a live Git input.
    with pytest.raises(ValueError):
        remote_from_record(asdict(remote), replace(source, git_commit="0" * 40))
    with pytest.raises(ValueError):
        remote_from_record(asdict(remote), replace(source, scope="subdir"))
    with pytest.raises(ValueError):
        remote_from_record(asdict(replace(remote, url="https://other.example/o/r")), source)


@pytest.mark.parametrize(
    ("requested", "resolved"),
    [
        ("api_key=[REDACTED]", None),
        (123, "refs/heads/api_key=[REDACTED]"),
        ("api_key=[REDACTED]", "not-a-qualified-ref"),
        ("bad~ref", "refs/heads/api_key=[REDACTED]"),
        ("api_key=[REDACTED]\n", "refs/heads/api_key=[REDACTED]"),
        ("bad[unmarked]", "refs/heads/bad[unmarked]"),
    ],
)
def test_stored_labels_do_not_allow_unrelated_invalid_metadata(
    repo: Path, requested: object, resolved: object
) -> None:
    source = fingerprint(repo)
    value = {
        "url": "https://github.com/fixture/project",
        "requested_ref": requested,
        "resolved_ref": resolved,
        "git_commit": source.git_commit,
    }
    with pytest.raises(ValueError):
        remote_from_record(value, source)
