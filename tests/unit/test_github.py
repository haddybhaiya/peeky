"""Public GitHub URL/ref boundaries; no external network required."""

import os
import sys
from pathlib import Path

import pytest

from peeky.github import (
    FetchLimits,
    _git_command,
    _git_environment,
    _run_git,
    parse_url,
    validate_ref,
)
from peeky.sources import SourceError


@pytest.mark.parametrize("suffix", ["", "/", ".git", ".git/"])
def test_repository_url_is_canonical(suffix: str) -> None:
    repository = parse_url("https://github.com/owner/project" + suffix)
    assert repository.url == "https://github.com/owner/project"
    assert (repository.owner, repository.name) == ("owner", "project")


@pytest.mark.parametrize(
    "value",
    [
        "http://github.com/o/r",
        "git@github.com:o/r.git",
        "file:///tmp/repo",
        "https://github.com.evil.test/o/r",
        "https://user:secret@github.com/o/r",
        "https://github.com:443/o/r",
        "https://github.com/o/r/tree/main",
        "https://github.com/o/r?token=secret",
        "https://github.com/o/r#main",
        "https://github.com/o/%2e%2e",
        "https://github.com/o/..",
        "https://github.com/o/.git",
        "https://github.com/o/r\n",
    ],
)
def test_unsupported_url_is_rejected(value: str) -> None:
    with pytest.raises(SourceError):
        parse_url(value)


@pytest.mark.parametrize("value", [None, "HEAD", "main", "feature/url", "v1.0", "refs/tags/v1"])
def test_supported_refs(value: str | None) -> None:
    assert validate_ref(value) == value


def test_full_sha_is_normalized() -> None:
    assert validate_ref("A" * 40) == "a" * 40


@pytest.mark.parametrize(
    "value",
    [
        "",
        "-main",
        "main~1",
        "main^{}",
        "main:other",
        "../main",
        "a..b",
        "a@{1}",
        "a//b",
        "a.lock",
        ".hidden",
        "a/",
        "a.",
        "a b",
        "a\nb",
        "refs/pull/1/head",
        "@",
    ],
)
def test_unsafe_refs(value: str) -> None:
    with pytest.raises(SourceError):
        validate_ref(value)


def test_git_has_no_ambient_credentials_or_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_ASKPASS", "/malicious/helper")
    monkeypatch.setenv("INSTABOX_API_KEY", "must-not-forward")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.example:8080")
    env = _git_environment()
    assert "GIT_CONFIG_COUNT" not in env and "GIT_ASKPASS" not in env
    assert "INSTABOX_API_KEY" not in env
    assert env["HTTPS_PROXY"] == "http://proxy.example:8080"
    assert env["GIT_CONFIG_GLOBAL"] == os.devnull
    assert env["GIT_TERMINAL_PROMPT"] == "0"


def test_git_transport_is_https_only(tmp_path: Path) -> None:
    command = _git_command(tmp_path, "ls-remote", "--", "https://github.com/o/r")
    assert "credential.helper=" in command and "http.extraHeader=" in command
    assert "protocol.allow=never" in command
    assert "protocol.https.allow=always" in command
    assert "http.followRedirects=false" in command


@pytest.mark.parametrize(
    ("script", "limits", "reason"),
    [
        ("import time; time.sleep(30)", FetchLimits(timeout_seconds=0.1), "timed out"),
        ("print('x' * 8192)", FetchLimits(max_output_bytes=512), "output limit"),
        (
            "open('large', 'wb').write(b'x' * 8192)",
            FetchLimits(max_storage_bytes=512),
            "storage limit",
        ),
        (
            "import sys; print('secret-token', file=sys.stderr); sys.exit(1)",
            FetchLimits(),
            "source unavailable",
        ),
    ],
)
def test_fetch_resource_errors_are_bounded_and_redacted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, script: str, limits: FetchLimits, reason: str
) -> None:
    monkeypatch.setattr("peeky.github._git_command", lambda *args: [sys.executable, "-c", script])
    with pytest.raises(SourceError, match=reason) as exc:
        _run_git(tmp_path, limits=limits)
    assert "secret-token" not in str(exc.value)


def test_git_initialization_uses_real_git(tmp_path: Path) -> None:
    assert _run_git(tmp_path, "init", "--template=", "-q") == b""
    assert (tmp_path / ".git/HEAD").is_file()
    assert not (tmp_path / ".git/hooks").exists()
