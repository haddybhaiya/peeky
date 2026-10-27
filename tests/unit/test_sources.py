from __future__ import annotations

import hashlib
import os
import stat
import subprocess
import sys
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from peeky.domain import DEFAULT_POLICY
from peeky.sources import SourceError, fingerprint, safe_relative, safe_root, snapshot

pytestmark = pytest.mark.unit


def test_T008_two_independent_snapshots_match_commit_and_bytes(
    repo: Path, git: Callable[..., bytes]
) -> None:
    (repo / ".env").write_text("excluded secret", encoding="utf-8")
    with snapshot(repo) as first, snapshot(repo) as second:
        assert first.path != second.path
        assert first.identity == second.identity == fingerprint(repo)
        assert first.identity.git_commit == git(repo, "rev-parse", "HEAD").strip().decode()
        assert not (first.path / ".git").exists() and not (first.path / ".env").exists()
        for item in first.identity.files:
            data = (first.path / item.path).read_bytes()
            assert item.sha256 == "sha256:" + hashlib.sha256(data).hexdigest()
            assert data == git(repo, "show", "HEAD:" + item.path)
            assert not (first.path / item.path).stat().st_mode & stat.S_IWUSR
        exported = first.path
    assert not exported.exists()


def test_snapshot_is_independent_of_later_worktree_changes(repo: Path) -> None:
    with snapshot(repo) as captured:
        old = (captured.path / "smoke.py").read_bytes()
        (repo / "smoke.py").write_bytes(b"changed source\n")
        assert (captured.path / "smoke.py").read_bytes() == old
        captured.verify()
        with pytest.raises(SourceError, match="Dirty"):
            fingerprint(repo)


def test_snapshot_detects_tampering(repo: Path) -> None:
    with snapshot(repo) as captured:
        target = captured.path / "smoke.py"
        target.chmod(0o644)
        target.write_bytes(b"tampered")
        with pytest.raises(SourceError, match="changed"):
            captured.verify()


@pytest.mark.parametrize("change", ["modified", "deleted", "staged", "untracked", "mode"])
def test_T005_dirty_sources_rejected(repo: Path, git: Callable[..., bytes], change: str) -> None:
    if change == "modified":
        (repo / "smoke.py").write_bytes(b"changed\n")
    elif change == "deleted":
        (repo / "smoke.py").unlink()
    elif change == "staged":
        (repo / "smoke.py").write_bytes(b"changed\n")
        git(repo, "add", "smoke.py")
        (repo / "smoke.py").write_bytes(git(repo, "show", "HEAD:smoke.py"))
    elif change == "untracked":
        (repo / "extra.py").write_bytes(b"untracked\n")
    else:
        git(repo, "update-index", "--chmod=+x", "smoke.py")
    with pytest.raises((SourceError, OSError)):
        fingerprint(repo)


def test_crlf_checkout_normalizes_without_filters(repo: Path) -> None:
    with snapshot(repo) as first:
        expected = first.identity
    readme = repo / "README.md"
    readme.write_bytes(readme.read_bytes().replace(b"\n", b"\r\n"))
    with snapshot(repo) as second:
        assert second.identity == expected
        assert b"\r\n" not in (second.path / "README.md").read_bytes()


@pytest.mark.parametrize("mode", ["120000", "160000"])
def test_T005_git_symlink_and_submodule_modes_rejected(
    repo: Path, git: Callable[..., bytes], mode: str
) -> None:
    oid = (
        git(repo, "hash-object", "-w", "--stdin", input=b"../outside").strip().decode()
        if mode == "120000"
        else git(repo, "rev-parse", "HEAD").strip().decode()
    )
    git(repo, "update-index", "--add", "--cacheinfo", mode, oid, "README.md")
    git(repo, "commit", "-qm", "unsafe tree fixture")
    with pytest.raises(SourceError, match="Symlinks, submodules"):
        fingerprint(repo)


def test_T005_actual_directory_link_rejected(repo: Path, tmp_path: Path) -> None:
    link = tmp_path / "linked"
    if os.name == "nt":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(repo)], check=True, capture_output=True
        )
    else:
        link.symlink_to(repo, target_is_directory=True)
    with pytest.raises(SourceError, match="reparse|Symlinks"):
        safe_root(link)


@pytest.mark.parametrize(
    "name",
    [
        "../escape",
        "/absolute",
        "a/../../b",
        "a\\b",
        "C:/x",
        "a//b",
        "AUX",
        "file.",
        "a\0b",
        ".",
        "",
    ],
)
def test_T005_unsafe_relative_paths_rejected(name: str) -> None:
    with pytest.raises(SourceError):
        safe_relative(name)


def test_T005_malicious_git_tree_path_never_exported(
    repo: Path, git: Callable[..., bytes], tmp_path: Path
) -> None:
    blob = git(repo, "hash-object", "-w", "--stdin", input=b"data").strip().decode()
    tree_data = b"100644 ../escaped\0" + bytes.fromhex(blob)
    tree = (
        git(repo, "hash-object", "--literally", "-t", "tree", "-w", "--stdin", input=tree_data)
        .strip()
        .decode()
    )
    commit_data = (
        f"tree {tree}\nauthor Test <test@example.invalid> 1 +0000\n"
        "committer Test <test@example.invalid> 1 +0000\n\nmalicious tree\n"
    ).encode()
    commit = (
        git(repo, "hash-object", "-t", "commit", "-w", "--stdin", input=commit_data)
        .strip()
        .decode()
    )
    git(repo, "update-ref", "HEAD", commit)
    with pytest.raises(SourceError):
        with snapshot(repo):
            pytest.fail("Unsafe source exported")
    assert not (tmp_path / "escaped").exists()


@pytest.mark.parametrize(
    "limit", ["max_files", "max_file_bytes", "max_source_bytes", "max_readme_bytes", "max_depth"]
)
def test_capture_limits_enforced(repo: Path, git: Callable[..., bytes], limit: str) -> None:
    if limit == "max_depth":
        (repo / "a/b").mkdir(parents=True)
        (repo / "a/b/data").write_bytes(b"x")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "nested fixture")
    with pytest.raises(SourceError, match="limit"):
        fingerprint(
            repo,
            {
                "max_files": replace(DEFAULT_POLICY, max_files=1),
                "max_file_bytes": replace(DEFAULT_POLICY, max_file_bytes=1),
                "max_source_bytes": replace(DEFAULT_POLICY, max_source_bytes=1),
                "max_readme_bytes": replace(DEFAULT_POLICY, max_readme_bytes=1),
                "max_depth": replace(DEFAULT_POLICY, max_depth=1),
            }[limit],
        )


@pytest.mark.parametrize("name", [".env", "controller.key"])
def test_tracked_secret_paths_rejected(repo: Path, git: Callable[..., bytes], name: str) -> None:
    (repo / name).write_bytes(b"SECRET=fixture")
    git(repo, "add", "-f", name)
    git(repo, "commit", "-qm", "tracked secret fixture")
    with pytest.raises(SourceError, match="credential"):
        fingerprint(repo)


def test_git_filters_fsmonitor_and_environment_cannot_execute(
    repo: Path, git: Callable[..., bytes], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (repo / ".gitattributes").write_bytes(b"smoke.py filter=poison\n")
    git(repo, "add", ".gitattributes")
    git(repo, "commit", "-qm", "attributes fixture")
    sentinel = tmp_path / "HOST_EXECUTED"
    script = tmp_path / "poison.py"
    script.write_text(
        f"from pathlib import Path\nPath({str(sentinel)!r}).touch()\n", encoding="utf-8"
    )
    command = f'"{sys.executable}" "{script}"'
    git(repo, "config", "filter.poison.clean", command)
    git(repo, "config", "filter.poison.required", "true")
    git(repo, "config", "core.fsmonitor", command)
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "invalid-git-dir"))
    with snapshot(repo) as captured:
        captured.verify()
    assert not sentinel.exists()


def test_selected_subdirectory_ignores_unrelated_dirty_files(
    repo: Path, git: Callable[..., bytes]
) -> None:
    selected = repo / "sample"
    selected.mkdir()
    (selected / "README.md").write_bytes(b"# Selected fixture\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "selected scope")
    (repo / "smoke.py").write_bytes(b"unrelated dirty source")
    source = fingerprint(selected)
    assert source.scope == "sample"
    assert [item.path for item in source.files] == ["README.md"]


def test_T005_non_git_and_redirected_git_roots_rejected(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_bytes(b"# no git")
    with pytest.raises(SourceError, match="local Git"):
        fingerprint(tmp_path)
    (tmp_path / ".git").write_bytes(b"gitdir: ../outside\n")
    with pytest.raises(SourceError, match="redirected"):
        fingerprint(tmp_path)


def test_case_collisions_in_git_tree_rejected(repo: Path, git: Callable[..., bytes]) -> None:
    oid = git(repo, "rev-parse", "HEAD:README.md").strip().decode()
    git(repo, "update-index", "--add", "--cacheinfo", "100644", oid, "readme.md")
    git(repo, "commit", "-qm", "case collision fixture")
    with pytest.raises(SourceError, match="Case-colliding"):
        fingerprint(repo)


def test_sha256_git_object_format(tmp_path: Path, git: Callable[..., bytes]) -> None:
    git(tmp_path, "init", "--template=", "--object-format=sha256", "-q")
    (tmp_path / "README.md").write_bytes(b"# SHA256 fixture\n")
    git(tmp_path, "add", "README.md")
    git(tmp_path, "commit", "-qm", "SHA256 fixture")
    with snapshot(tmp_path) as captured:
        assert len(captured.identity.git_commit) == 64
        captured.verify()
