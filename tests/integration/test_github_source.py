"""Real Git fetch/capture with a local transport fixture; no live GitHub dependency."""

import json
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import pytest

from peeky import cli, github
from peeky.cli import main
from peeky.domain import DEFAULT_POLICY
from peeky.images import DEFAULT_IMAGE
from peeky.repair import load_record
from peeky.sources import SourceError, SourceSnapshot, fingerprint

pytestmark = pytest.mark.integration
URL = "https://github.com/fixture/project"


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


@pytest.mark.parametrize(
    ("readme", "image", "reason"),
    [
        ("# No opted-in command\n", DEFAULT_IMAGE, "NO_OPTED_IN_COMMANDS"),
        (
            "```bash peeky\npython smoke.py\npython smoke.py\n```\n",
            DEFAULT_IMAGE,
            "MULTI_STEP_UNSUPPORTED",
        ),
        ("```bash peeky\npython smoke.py; echo unsafe\n```\n", DEFAULT_IMAGE, "Shell composition"),
        ("```bash peeky\npython smoke.py\n```\n", "python:latest", "reviewed, cached"),
    ],
)
def test_url_audit_policy_blocks_preserve_authenticated_origin_without_execution(
    repo: Path,
    git: Callable[..., bytes],
    local_transport: list[Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    readme: str,
    image: str,
    reason: str,
) -> None:
    (repo / "README.md").write_text(readme)
    git(repo, "add", "README.md")
    git(repo, "commit", "-qm", "blocked audit fixture")

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("Policy-denied URL audit reached Docker")

    monkeypatch.setattr("peeky.cli.doctor", forbidden)
    monkeypatch.setattr("peeky.cli.execute", forbidden)
    output = tmp_path / "blocked-url"
    assert main(["audit", URL, "--approve", "--image", image, "--output", str(output)]) == 2
    record = load_record(next(output.glob("*.json")))
    assert record["repo"] == URL and record["remote"]["url"] == URL
    assert reason in record["reason"]
    assert record["results"] == [] and record["run"]["state"] == "BLOCKED"
    assert record["verdict"] == "INCONCLUSIVE"
    assert all(not path.exists() for path in local_transport)


def test_url_audit_missing_docker_retains_bound_evidence_after_source_cleanup(
    repo: Path, local_transport: list[Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = fingerprint(repo)
    monkeypatch.setattr(cli, "doctor", lambda **kwargs: {"docker_daemon": False, "linux": False})

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("Missing Docker reached target execution")

    monkeypatch.setattr(cli, "execute", forbidden)
    output = tmp_path / "missing-docker"
    assert (
        main(["audit", URL, "--ref", expected.git_commit, "--approve", "--output", str(output)])
        == 3
    )
    assert all(not root.exists() for root in local_transport)
    record = load_record(next(output.glob("*.json")))
    assert record["source"]["git_commit"] == expected.git_commit
    assert record["remote"]["requested_ref"] == expected.git_commit
    assert record["run"]["state"] == "BLOCKED" and record["results"] == []
    assert record["verdict"] == "INCONCLUSIVE" and record["repo"] == URL


@pytest.mark.parametrize("interrupt", [False, True])
def test_url_audit_execution_error_or_interrupt_cleans_source(
    local_transport: list[Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, interrupt: bool
) -> None:
    paths: list[Path] = []
    monkeypatch.setattr(cli, "doctor", lambda **kwargs: {"docker_daemon": True, "linux": True})

    def interrupted(*args: object, **kwargs: object) -> None:
        captured = args[1]
        assert isinstance(captured, SourceSnapshot)
        paths.append(captured.path)
        assert captured.path.exists()
        if interrupt:
            raise KeyboardInterrupt
        raise OSError("synthetic controller failure")

    monkeypatch.setattr(cli, "execute", interrupted)
    output = tmp_path / "interrupted"
    if interrupt:
        with pytest.raises(KeyboardInterrupt):
            main(["audit", URL, "--approve", "--output", str(output)])
    else:
        assert main(["audit", URL, "--approve", "--output", str(output)]) == 3
    assert paths and all(not path.exists() for path in paths + local_transport)
    assert not output.exists()


def test_url_audit_does_not_publish_before_source_cleanup_completes(
    local_transport: list[Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = github.github_snapshot

    @contextmanager
    def cleanup_failure(*args: str) -> Iterator[github.GitHubSnapshot]:
        with original(*args) as captured:
            yield captured
        raise OSError("source cleanup could not be confirmed")

    monkeypatch.setattr(cli, "github_snapshot", cleanup_failure)
    monkeypatch.setattr(cli, "doctor", lambda **kwargs: {"docker_daemon": False, "linux": False})
    output = tmp_path / "unconfirmed-cleanup"
    assert main(["audit", URL, "--approve", "--output", str(output)]) == 3
    assert all(not path.exists() for path in local_transport)
    assert not output.exists()


@pytest.mark.parametrize("ref", ["topic", "refs/heads/topic", "v1", "refs/tags/v1", "HEAD"])
def test_url_audit_named_selections_and_dot_git_share_canonical_evidence(
    repo: Path,
    git: Callable[..., bytes],
    local_transport: list[Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    ref: str,
) -> None:
    expected = fingerprint(repo)
    git(repo, "branch", "topic")
    git(repo, "tag", "-a", "v1", "-m", "annotated audit selection fixture")
    monkeypatch.setattr(cli, "doctor", lambda **kwargs: {"docker_daemon": False, "linux": False})
    output = tmp_path / "named-selection"
    assert main(["audit", URL + ".git", "--ref", ref, "--approve", "--output", str(output)]) == 3
    record = load_record(next(output.glob("*.json")))
    assert record["repo"] == URL and record["remote"]["url"] == URL
    assert record["remote"]["requested_ref"] == ref
    assert record["remote"]["git_commit"] == expected.git_commit
    assert record["source"]["source_sha256"] == expected.source_sha256
    assert all(not path.exists() for path in local_transport)


@pytest.mark.parametrize("selector", ["branch", "tag", "default"])
def test_real_git_redacted_ref_blocked_audit_exports(
    repo: Path,
    git: Callable[..., bytes],
    local_transport: list[Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    selector: str,
) -> None:
    expected = fingerprint(repo)
    ref = "api_key=demo"
    if selector == "tag":
        git(repo, "tag", "-a", ref, "-m", "redaction regression fixture")
    else:
        git(repo, "branch", ref)
        if selector == "default":
            git(repo, "symbolic-ref", "HEAD", "refs/heads/" + ref)
    ref_args = [] if selector == "default" else ["--ref", ref]
    monkeypatch.setattr(cli, "doctor", lambda **kwargs: {"docker_daemon": False, "linux": False})
    output = tmp_path / "redacted-ref-audit"
    assert main(["audit", URL, *ref_args, "--approve", "--output", str(output)]) == 3
    artifact = next(output.glob("*.json"))
    record = load_record(artifact)
    assert record["source"]["git_commit"] == record["remote"]["git_commit"] == expected.git_commit
    assert record["remote"]["resolved_ref"].endswith("api_key=[REDACTED]")
    assert ref not in artifact.read_text()
    assert local_transport and all(not path.exists() for path in local_transport)
    summary_dir = tmp_path / "redacted-ref-summary"
    assert main(["report", "--evidence", str(artifact), "--output", str(summary_dir)]) == 0
    result = load_record(next((summary_dir / "records").glob("*.json")))["records"][0]
    assert result["remote_ref_status"] == "redacted-display-only"
    assert result["outcome"] == "INCONCLUSIVE"
    assert result["git_commit"] == expected.git_commit


def test_real_git_fully_masked_selector_exports_after_secret_is_removed(
    repo: Path,
    git: Callable[..., bytes],
    local_transport: list[Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ref = "refs/heads/confidential-name"
    git(repo, "branch", "confidential-name")
    monkeypatch.setattr(cli, "doctor", lambda **kwargs: {"docker_daemon": False, "linux": False})
    output = tmp_path / "masked-selector"
    with monkeypatch.context() as configured:
        configured.setenv("PEEKY_TEST_API_KEY", ref)
        assert main(["audit", URL, "--ref", ref, "--approve", "--output", str(output)]) == 3
    artifact = next(output.glob("*.json"))
    record = load_record(artifact)
    assert record["remote"]["requested_ref"] == record["remote"]["resolved_ref"] == "[REDACTED]"
    assert ref not in artifact.read_text()
    assert (
        main(["report", "--evidence", str(artifact), "--output", str(tmp_path / "masked-export")])
        == 0
    )
    assert local_transport and all(not path.exists() for path in local_transport)
