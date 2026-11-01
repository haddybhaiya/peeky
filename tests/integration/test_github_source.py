"""Real Git fetch/capture with a local transport fixture; no live GitHub dependency."""

import json
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from peeky import github
from peeky.cli import main
from peeky.domain import DEFAULT_POLICY
from peeky.sources import SourceError, fingerprint

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


def test_branches_tags_and_missing_refs(
    repo: Path, git: Callable[..., bytes], local_transport: list[Path]
) -> None:
    commit = fingerprint(repo).git_commit
    git(repo, "branch", "topic")
    git(repo, "branch", "feature/añadir")
    git(repo, "tag", "-a", "v1", "-m", "annotated fixture tag")
    for ref in ("topic", "refs/heads/topic", "feature/añadir", "v1", "refs/tags/v1", commit):
        with github.github_snapshot(URL, ref) as captured:
            assert captured.source.identity.git_commit == commit
            assert captured.remote.requested_ref == ref
    git(repo, "tag", "topic")
    with pytest.raises(SourceError, match="ambiguous"):
        with github.github_snapshot(URL, "topic"):
            pytest.fail("Ambiguous branch/tag accepted")
    with pytest.raises(SourceError, match="source unavailable"):
        with github.github_snapshot(URL, "missing"):
            pytest.fail("Missing ref accepted")
    assert all(not path.exists() for path in local_transport)


@pytest.mark.parametrize("ref", [None, "HEAD"])
@pytest.mark.parametrize("collision", ["branch", "lightweight_tag", "annotated_tag"])
def test_default_ref_ignores_other_refs_ending_in_head(
    repo: Path,
    git: Callable[..., bytes],
    local_transport: list[Path],
    ref: str | None,
    collision: str,
) -> None:
    expected = fingerprint(repo)
    default_ref = git(repo, "symbolic-ref", "HEAD").strip().decode()
    other = (
        git(
            repo,
            "commit-tree",
            expected.git_tree,
            "-p",
            expected.git_commit,
            input=b"different fixture revision for suffix match\n",
        )
        .strip()
        .decode()
    )
    assert other != expected.git_commit
    if collision == "branch":
        git(repo, "update-ref", "refs/heads/topic/HEAD", other)
    elif collision == "lightweight_tag":
        git(repo, "update-ref", "refs/tags/HEAD", other)
    else:
        git(repo, "tag", "-a", "collision-tag", other, "-m", "annotated collision fixture")
        tag = git(repo, "rev-parse", "refs/tags/collision-tag").strip().decode()
        git(repo, "update-ref", "refs/tags/HEAD", tag)
    with github.github_snapshot(URL, ref) as captured:
        assert captured.source.identity == expected
        assert captured.remote.git_commit == expected.git_commit
        assert captured.remote.resolved_ref == default_ref
    assert local_transport and all(not path.exists() for path in local_transport)


@pytest.mark.parametrize("ref", ["topic", "refs/heads/topic"])
def test_named_ref_ignores_suffix_matches_for_qualified_names(
    repo: Path, git: Callable[..., bytes], local_transport: list[Path], ref: str
) -> None:
    expected = fingerprint(repo)
    git(repo, "branch", "topic")
    other = (
        git(
            repo,
            "commit-tree",
            expected.git_tree,
            "-p",
            expected.git_commit,
            input=b"different fixture revision for qualified suffix match\n",
        )
        .strip()
        .decode()
    )
    git(repo, "update-ref", "refs/heads/nested/refs/heads/topic", other)
    with github.github_snapshot(URL, ref) as captured:
        assert captured.source.identity == expected
        assert captured.remote.resolved_ref == "refs/heads/topic"
    assert local_transport and all(not path.exists() for path in local_transport)


def test_branch_movement_does_not_change_selected_commit(
    repo: Path,
    git: Callable[..., bytes],
    local_transport: list[Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = fingerprint(repo)
    git(repo, "branch", "moving")
    (repo / "README.md").write_bytes(b"# A different commit\n")
    git(repo, "add", "README.md")
    git(repo, "commit", "-qm", "second fixture revision")
    second = git(repo, "rev-parse", "HEAD").strip().decode()
    original = github._resolve

    def resolve(
        root: Path, repository: github.GitHubRepository, ref: str | None, limits: github.FetchLimits
    ) -> github.RemoteSource:
        result = original(root, repository, ref, limits)
        git(repo, "update-ref", "refs/heads/moving", second)
        return result

    monkeypatch.setattr(github, "_resolve", resolve)
    with github.github_snapshot(URL, "moving") as captured:
        assert captured.source.identity == first
        assert captured.remote.git_commit == first.git_commit
    assert all(not path.exists() for path in local_transport)


@pytest.mark.parametrize("kind", ["symlink", "submodule", "credential", "oversized"])
def test_remote_source_denials_leave_no_checkout_or_storage(
    repo: Path, git: Callable[..., bytes], local_transport: list[Path], kind: str
) -> None:
    policy = DEFAULT_POLICY
    if kind == "symlink":
        oid = git(repo, "hash-object", "-w", "--stdin", input=b"/etc/passwd").strip().decode()
        git(repo, "update-index", "--add", "--cacheinfo", "120000", oid, "link")
    elif kind == "submodule":
        oid = git(repo, "rev-parse", "HEAD").strip().decode()
        git(repo, "update-index", "--add", "--cacheinfo", "160000", oid, "dependency")
    elif kind == "credential":
        oid = git(repo, "hash-object", "-w", "--stdin", input=b"FAKE_KEY=fixture").strip().decode()
        git(repo, "update-index", "--add", "--cacheinfo", "100644", oid, ".env")
    else:
        policy = replace(DEFAULT_POLICY, max_file_bytes=16)
    git(repo, "commit", "--allow-empty", "-qm", "unsupported source fixture")
    with pytest.raises(SourceError):
        with github.github_snapshot(URL, policy=policy):
            pytest.fail("Unsupported source was exposed")
    assert local_transport and all(not path.exists() for path in local_transport)


def test_cli_empty_plan_and_readable_provenance(
    repo: Path,
    git: Callable[..., bytes],
    local_transport: list[Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    (repo / "README.md").write_bytes(b"# No opted-in commands\n")
    git(repo, "add", "README.md")
    git(repo, "commit", "-qm", "empty plan fixture")
    assert main(["inspect", URL]) == 2
    output = capsys.readouterr()
    assert f"Repository: {URL}" in output.out
    assert "Proposed steps: 0 (never executed)" in output.out
    assert "PASS" not in output.out and not output.err
    assert all(not path.exists() for path in local_transport)
