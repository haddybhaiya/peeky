"""Real controller/Git integration without Docker or target execution."""

import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from peeky.sources import SourceError, _committed_snapshot, fingerprint

pytestmark = pytest.mark.integration


def test_two_processes_measure_identical_source_and_policy(repo: Path, tmp_path: Path) -> None:
    def inspect() -> dict[str, object]:
        output = subprocess.run(
            [sys.executable, "-I", "-m", "peeky", "inspect", str(repo), "--json"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        data: dict[str, object] = json.loads(output.stdout)
        return data

    first, second = inspect(), inspect()
    assert first["source"] == second["source"]
    assert first["policy_sha256"] == second["policy_sha256"]
    first_run, second_run = first["run"], second["run"]
    assert isinstance(first_run, dict) and isinstance(second_run, dict)
    assert first_run["plan_sha256"] == second_run["plan_sha256"]
    assert first_run["id"] != second_run["id"]
    (repo / "smoke.py").write_bytes(b"dirty source")
    denied = subprocess.run(
        [sys.executable, "-I", "-m", "peeky", "inspect", str(repo), "--json"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert denied.returncode == 3 and "Dirty" in denied.stderr
    assert denied.stdout == ""


def test_metadata_only_capture_matches_local_without_checkout(
    repo: Path, tmp_path: Path, git: Callable[..., bytes]
) -> None:
    expected = fingerprint(repo)
    remote = tmp_path / "metadata"
    git(repo, "clone", "--no-checkout", "--no-hardlinks", "--template=", str(repo), str(remote))
    assert [path.name for path in remote.iterdir()] == [".git"]
    with _committed_snapshot(remote, expected.git_commit) as captured:
        exported = captured.path
        assert captured.identity == expected
        assert (exported / "smoke.py").read_bytes() == (repo / "smoke.py").read_bytes()
        assert not (exported / ".git").exists()
        captured.verify()
    assert not exported.exists()
    with pytest.raises(SourceError, match="differs"):
        with _committed_snapshot(remote, "0" * 40):
            pytest.fail("Wrong expected commit accepted")
    (remote / "README.md").write_bytes(b"untrusted worktree")
    with pytest.raises(SourceError, match="metadata-only"):
        with _committed_snapshot(remote, expected.git_commit):
            pytest.fail("Object-only capture accepted a worktree")


def test_metadata_only_capture_rejects_symlink_objects(
    repo: Path, tmp_path: Path, git: Callable[..., bytes]
) -> None:
    blob = git(repo, "hash-object", "-w", "--stdin", input=b"/etc/passwd").strip().decode()
    git(repo, "update-index", "--add", "--cacheinfo", "120000", blob, "link")
    git(repo, "commit", "-qm", "synthetic symlink object")
    commit = git(repo, "rev-parse", "HEAD").strip().decode()
    remote = tmp_path / "metadata"
    git(repo, "clone", "--no-checkout", "--no-hardlinks", "--template=", str(repo), str(remote))
    with pytest.raises(SourceError, match="Symlinks"):
        with _committed_snapshot(remote, commit):
            pytest.fail("Symlink object was exported")
    assert not (remote / "link").exists()
