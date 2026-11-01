"""Public GitHub URL/ref boundaries; no external network required."""

import pytest

from peeky.github import parse_url, validate_ref
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
