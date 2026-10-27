import os
from pathlib import Path

import pytest

from peeky.hosttools import host_tool

pytestmark = pytest.mark.unit


def test_repository_tools_and_cwd_cannot_shadow_installed_git(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = host_tool("git")
    assert expected is not None
    target = tmp_path / "target"
    binaries = target / "bin"
    binaries.mkdir(parents=True)
    fake = binaries / ("git.exe" if os.name == "nt" else "git")
    fake.write_bytes(b"not a host executable; must never run")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", str(binaries) + os.pathsep + os.environ["PATH"])
    assert host_tool("git", avoid=target) == expected
    monkeypatch.chdir(target)
    assert host_tool("git") == expected
