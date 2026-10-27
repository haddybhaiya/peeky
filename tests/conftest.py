"""Synthetic local Git fixtures. No fixture code, hooks or package imports execute."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from peeky.domain import DEFAULT_POLICY, RunRecord, RunState
from peeky.evidence import report, write_report
from peeky.models import StepResult
from peeky.parser import read_steps
from peeky.sources import fingerprint


@pytest.fixture
def git() -> Callable[..., bytes]:
    def run(repo: Path, *args: str, input: bytes | None = None) -> bytes:
        binary = shutil.which("git")
        assert binary is not None, "Git required for Phase 1 tests"
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
        env.update(
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_AUTHOR_NAME="Peeky fixture",
            GIT_AUTHOR_EMAIL="fixture@example.invalid",
            GIT_COMMITTER_NAME="Peeky fixture",
            GIT_COMMITTER_EMAIL="fixture@example.invalid",
        )
        return subprocess.run(
            [
                binary,
                "-c",
                "core.autocrlf=false",
                "-c",
                f"core.hooksPath={os.devnull}",
                "-c",
                "commit.gpgSign=false",
                *args,
            ],
            cwd=repo,
            input=input,
            capture_output=True,
            check=True,
            env=env,
            timeout=10,
        ).stdout

    return run


@pytest.fixture
def repo(tmp_path: Path, git: Callable[..., bytes]) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "--template=", "-q")
    (root / "README.md").write_bytes(b"# Fixture\n\n```bash peeky\npython smoke.py\n```\n")
    (root / "smoke.py").write_bytes(b"raise RuntimeError('must not execute on host')\n")
    (root / ".gitignore").write_bytes(b".cache/\n.env\n")
    git(root, "add", ".")
    git(root, "commit", "-qm", "synthetic source")
    return root


@pytest.fixture
def evidence_file(repo: Path, tmp_path: Path) -> Path:
    # Synthetic result tests schema consistency only, never real Docker success.
    source = fingerprint(repo)
    steps = read_steps(repo)
    run = RunRecord(source, tuple(steps))
    for state in (
        RunState.INSPECTED,
        RunState.APPROVED,
        RunState.SANDBOX_RUN,
        RunState.OBSERVED,
        RunState.FINALIZED,
    ):
        run.advance(state)
    results = [
        StepResult(s.id, s.command, 0, "synthetic unit result", "", "PASS", 1) for s in steps
    ]
    return write_report(
        report(repo, "python:3.12-slim", steps, results, source, run, DEFAULT_POLICY),
        tmp_path / "evidence",
    )
