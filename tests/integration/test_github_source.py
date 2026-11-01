"""Real Git fetch/capture with a local transport fixture; no live GitHub dependency."""

from pathlib import Path

import pytest

from peeky import github
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
