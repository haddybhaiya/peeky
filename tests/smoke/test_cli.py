import json
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

from peeky import __version__
from peeky.cli import main


@pytest.mark.smoke
def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


@pytest.mark.smoke
def test_inspect_good(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["inspect", "tests/fixtures/good_repo", "--json"]) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["source"]["git_commit"] and plan["source"]["source_sha256"].startswith("sha256:")
    assert plan["run"]["state"] == "INSPECTED"
    items = plan["steps"]
    assert len(items) == 1 and items[0]["command"] == "python smoke.py"


@pytest.mark.smoke
def test_no_approval_does_not_execute(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["audit", "tests/fixtures/good_repo"]) == 2
    assert "not authorized" in capsys.readouterr().err


@pytest.mark.smoke
def test_no_opted_in_steps(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["inspect", "tests/fixtures/no_optin_repo"]) == 2


def test_T001_T002_inspect_never_executes_target(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("Inspect attempted target execution or Docker readiness check")

    monkeypatch.setattr("peeky.cli.execute", forbidden)
    monkeypatch.setattr("peeky.cli.doctor", forbidden)
    assert main(["inspect", str(repo), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["steps"][0]["command"] == "python smoke.py"


def test_T006_no_approval_never_reads_or_executes_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("Approval gate attempted source capture or execution")

    monkeypatch.setattr("peeky.cli.snapshot", forbidden)
    monkeypatch.setattr("peeky.cli.execute", forbidden)
    assert main(["audit", "nonexistent-target"]) == 2


def test_T007_missing_docker_records_blocked_without_host_fallback(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    original = shutil.which
    monkeypatch.setattr(shutil, "which", lambda name: None if name == "docker" else original(name))

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("Missing Docker triggered target execution")

    monkeypatch.setattr("peeky.cli.execute", forbidden)
    output = tmp_path / "blocked-evidence"
    assert main(["audit", str(repo), "--approve", "--output", str(output)]) == 3
    assert "refusing host execution" in capsys.readouterr().err
    files = list(output.glob("*.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text(encoding="utf-8"))
    assert data["verdict"] == "INCONCLUSIVE" and data["results"] == []
    assert data["run"]["state"] == "BLOCKED"
    assert data["source"]["dirty"] is False


def test_T004_rejected_command_never_reaches_docker(
    repo: Path,
    git: Callable[..., bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (repo / "README.md").write_bytes(b"```bash peeky\npython smoke.py; echo bad\n```\n")
    git(repo, "add", "README.md")
    git(repo, "commit", "-qm", "unsafe command fixture")

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("Unsafe command reached Docker")

    monkeypatch.setattr("peeky.cli.doctor", forbidden)
    monkeypatch.setattr("peeky.cli.execute", forbidden)
    assert main(["audit", str(repo), "--approve"]) == 3
