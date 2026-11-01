"""Real Git fetch/capture with a local transport fixture; no live GitHub dependency."""

import json
from pathlib import Path

import pytest

from peeky import github
from peeky.cli import main
from peeky.sources import fingerprint

pytestmark = pytest.mark.integration
URL = "https://github.com/fixture/project"


@pytest.fixture
def local_transport(repo: Path, monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    original = github._git_command
    roots: list[Path] = []

    def command(root: Path, *args: str) -> list[str]:
        roots.append(root)
        trusted = original(root, *args)
        prefix = trusted[: -len(args)]
        # The test alone substitutes a local repository for the approved HTTPS URL.
        # The production URL validator and transport never allow file protocols.
        translated = [str(repo) if value == URL else value for value in args]
        return [*prefix, "-c", "protocol.file.allow=always", *translated]

    monkeypatch.setattr(github, "_git_command", command)
    return roots


@pytest.mark.parametrize("interrupt", [False, True])
def test_remote_snapshot_matches_local_and_cleans_all_storage(
    repo: Path, local_transport: list[Path], interrupt: bool
) -> None:
    expected = fingerprint(repo)
    try:
        with github.github_snapshot(URL) as captured:
            exported = captured.source.path
            assert captured.source.identity == expected
            assert captured.remote.url == URL
            assert captured.remote.requested_ref is None
            assert captured.remote.git_commit == expected.git_commit
            assert captured.remote.resolved_ref is not None
            assert [path.name for path in local_transport[0].iterdir()] == [".git"]
            captured.source.verify()
            if interrupt:
                raise KeyboardInterrupt
    except KeyboardInterrupt:
        assert interrupt
    assert not exported.exists()
    assert local_transport and all(not path.exists() for path in local_transport)


def test_cli_remote_json_is_a_plan_and_never_executes(
    repo: Path,
    local_transport: list[Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("Inspection reached Docker or target execution")

    monkeypatch.setattr("peeky.cli.doctor", forbidden)
    monkeypatch.setattr("peeky.cli.execute", forbidden)
    expected = fingerprint(repo)
    assert main(["inspect", URL, "--ref", expected.git_commit, "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["remote"] == {
        "url": URL,
        "requested_ref": expected.git_commit,
        "resolved_ref": None,
        "git_commit": expected.git_commit,
    }
    assert data["source"]["git_commit"] == expected.git_commit
    assert data["source"]["source_sha256"] == expected.source_sha256
    assert data["steps"][0]["command"] == "python smoke.py"
    assert data["run"]["state"] == "INSPECTED" and "verdict" not in data
    assert all(not path.exists() for path in local_transport)
