"""Bounded Git object capture; no checkout, archive filters, hooks or target imports."""

from __future__ import annotations

import hashlib
import os
import re
import stat
import subprocess
import tempfile
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath

from .domain import DEFAULT_POLICY, RunPolicy, SourceFile, SourceIdentity, canonical_hash
from .hosttools import host_tool


class SourceError(ValueError):
    pass


def _linked(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    )


def safe_root(path: Path) -> Path:
    if ".." in path.parts:
        raise SourceError("Parent traversal is not accepted in source paths")
    root = path.absolute()
    for part in (*reversed(root.parents), root):
        if _linked(part.lstat()):
            raise SourceError("Symlinks and reparse points are not accepted")
    if not root.is_dir():
        raise SourceError("Expected a repository directory")
    return root


def safe_relative(name: str) -> PurePosixPath:
    parts = name.split("/")
    reserved = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
    if not name or any(
        not part
        or part in {".", ".."}
        or part.endswith((".", " "))
        or any(ord(c) < 32 or ord(c) == 127 or c in '\\<>:"|?*' for c in part)
        or part.split(".")[0].upper() in reserved
        or len(part.encode("utf-8")) > 255
        for part in parts
    ):
        raise SourceError("Unsafe or non-portable source path")
    if len(name.encode("utf-8")) > 1024:
        raise SourceError("Source path exceeds limit")
    return PurePosixPath(name)


def read_regular(root: Path, name: str, limit: int) -> bytes:
    rel = safe_relative(name)
    target = root.joinpath(*rel.parts)
    for part in rel.parents:
        parent = root.joinpath(*part.parts)
        if _linked(parent.lstat()) or not parent.is_dir():
            raise SourceError("Unsafe source parent")
    before = target.lstat()
    if _linked(before) or not stat.S_ISREG(before.st_mode):
        raise SourceError("Expected a regular non-symlink source file")
    if before.st_size > limit:
        raise SourceError("Source file exceeds byte limit")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    with os.fdopen(os.open(target, flags), "rb") as stream:
        opened = os.fstat(stream.fileno())
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise SourceError("Source changed while opening")
        data = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    if len(data) > limit or (opened.st_size, opened.st_mtime_ns) != (
        after.st_size,
        after.st_mtime_ns,
    ):
        raise SourceError("Source changed or exceeded byte limit")
    return data


def _git(root: Path, policy: RunPolicy, *args: str, limit: int | None = None) -> bytes:
    binary = host_tool("git", avoid=root)
    if binary is None:
        raise SourceError("Git is required for immutable source capture")
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_ATTR_NOSYSTEM="1",
        GIT_TERMINAL_PROMPT="0",
        GIT_NO_LAZY_FETCH="1",
    )
    command = [
        binary,
        "--no-optional-locks",
        "--no-replace-objects",
        "--literal-pathspecs",
        "-c",
        "core.fsmonitor=false",
        "-c",
        f"core.hooksPath={os.devnull}",
        "-c",
        "core.untrackedCache=false",
        "-c",
        "protocol.allow=never",
        *args,
    ]
    cap = policy.max_tree_bytes if limit is None else limit
    with subprocess.Popen(
        command,
        cwd=root,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    ) as process:
        assert process.stdout is not None
        with ThreadPoolExecutor(max_workers=1) as reader:
            future = reader.submit(process.stdout.read, cap + 1)
            try:
                output = future.result(timeout=policy.git_timeout_seconds)
                if len(output) > cap:
                    raise SourceError("Git output exceeds capture limit")
                if process.wait(timeout=policy.git_timeout_seconds) != 0:
                    raise SourceError("Git metadata unavailable or unsupported repository")
                return output
            except (TimeoutError, subprocess.TimeoutExpired) as exc:
                raise SourceError("Git metadata read timed out") from exc
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()


def _object(root: Path, policy: RunPolicy, kind: str, oid: str, limit: int) -> bytes:
    if not re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})", oid):
        raise SourceError("Invalid Git object identity")
    data = _git(root, policy, "cat-file", kind, oid, limit=limit)
    header = f"{kind} {len(data)}\0".encode()
    digest = hashlib.sha1(header + data) if len(oid) == 40 else hashlib.sha256(header + data)
    if digest.hexdigest() != oid:
        raise SourceError("Git object bytes do not match their identity")
    return data


def _tree(root: Path, policy: RunPolicy, oid: str) -> list[tuple[str, str, str]]:
    data = _object(root, policy, "tree", oid, policy.max_tree_bytes)
    entries = []
    offset = 0
    width = len(oid) // 2
    try:
        while offset < len(data):
            space = data.index(b" ", offset)
            end = data.index(b"\0", space)
            mode = data[offset:space].decode("ascii")
            name = data[space + 1 : end].decode("utf-8")
            if "/" in name:
                raise SourceError("Invalid Git tree name")
            safe_relative(name)
            offset = end + 1 + width
            if offset > len(data):
                raise SourceError("Truncated Git tree")
            entries.append((name, mode, data[end + 1 : offset].hex()))
            if len(entries) > policy.max_files:
                raise SourceError("Git tree entry limit exceeded")
    except SourceError:
        raise
    except (ValueError, UnicodeError) as exc:
        raise SourceError("Invalid Git tree") from exc
    if len({name.casefold() for name, _, _ in entries}) != len(entries):
        raise SourceError("Case-colliding source paths")
    return entries


def _repo_root(selected: Path) -> Path:
    for candidate in (selected, *selected.parents):
        marker = candidate / ".git"
        if marker.exists() or marker.is_symlink():
            info = marker.lstat()
            if _linked(info) or not stat.S_ISDIR(info.st_mode):
                raise SourceError("Linked worktrees and redirected Git directories are unsupported")
            return candidate
    raise SourceError("Source must belong to a local Git repository")


def _equivalent(worktree: bytes, committed: bytes) -> bool:
    if worktree == committed:
        return True
    # Only harmless UTF-8 CRLF checkout conversion is supported; never call Git filters.
    try:
        worktree.decode("utf-8")
    except UnicodeError:
        return False
    return b"\0" not in worktree and worktree.replace(b"\r\n", b"\n") == committed


def _secret_path(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return any(
        part.casefold() in {".git", ".ssh", ".aws", ".azure", ".gnupg", ".peeky", ".freshstart"}
        or part.casefold() in {"id_rsa", "id_ed25519", "controller.key"}
        or (
            part.casefold().startswith(".env")
            and part.casefold() not in {".env.example", ".env.template"}
        )
        for part in parts
    )


def _capture(repo: Path, policy: RunPolicy) -> tuple[SourceIdentity, dict[str, bytes]]:
    selected = safe_root(repo)
    root = _repo_root(selected)
    scope = selected.relative_to(root).as_posix()
    if scope != ".":
        safe_relative(scope)
    commit = (
        _git(root, policy, "rev-parse", "--verify", "HEAD^{commit}", limit=100).strip().decode()
    )
    raw_commit = _object(root, policy, "commit", commit, policy.max_tree_bytes)
    tree = raw_commit.split(b"\n", 1)[0].removeprefix(b"tree ").decode("ascii")
    for component in () if scope == "." else PurePosixPath(scope).parts:
        matches = [
            (mode, oid) for name, mode, oid in _tree(root, policy, tree) if name == component
        ]
        if len(matches) != 1 or matches[0][0] != "40000":
            raise SourceError("Selected scope is not a committed directory")
        tree = matches[0][1]
    records: list[SourceFile] = []
    contents: dict[str, bytes] = {}
    expected_index: dict[str, tuple[str, str]] = {}
    nodes = 0
    total = 0

    def walk(oid: str, prefix: str, depth: int) -> None:
        nonlocal nodes, total
        if depth > policy.max_depth:
            raise SourceError("Source directory depth limit exceeded")
        for name, mode, child in _tree(root, policy, oid):
            nodes += 1
            if nodes > policy.max_files:
                raise SourceError("Source entry limit exceeded")
            rel = f"{prefix}/{name}" if prefix else name
            safe_relative(rel)
            if _secret_path(rel):
                raise SourceError("Tracked credential paths are not accepted")
            if mode == "40000":
                walk(child, rel, depth + 1)
                continue
            if mode not in {"100644", "100755"}:
                raise SourceError("Symlinks, submodules and special files are unsupported")
            data = _object(root, policy, "blob", child, policy.max_file_bytes)
            total += len(data)
            if total > policy.max_source_bytes:
                raise SourceError("Total source byte limit exceeded")
            if not _equivalent(read_regular(selected, rel, policy.max_file_bytes), data):
                raise SourceError("Dirty source bytes differ from the recorded commit")
            if os.name != "nt" and bool((selected / rel).stat().st_mode & 0o111) != (
                mode == "100755"
            ):
                raise SourceError("Dirty source executable mode")
            records.append(
                SourceFile(rel, mode, "sha256:" + hashlib.sha256(data).hexdigest(), len(data))
            )
            contents[rel] = data
            expected_index[rel if scope == "." else f"{scope}/{rel}"] = (mode, child)

    walk(tree, "", 0)
    pathspec = "." if scope == "." else scope + "/"
    index_args = ("ls-files", "--stage", "-z", "--", pathspec)
    index_before = _git(root, policy, *index_args)
    index: dict[str, tuple[str, str]] = {}
    try:
        for entry in index_before.split(b"\0"):
            if entry:
                metadata, name = entry.split(b"\t", 1)
                mode, oid, stage = metadata.decode("ascii").split()
                if stage != "0" or name.decode("utf-8") in index:
                    raise SourceError("Unmerged or duplicate index entries")
                index[name.decode("utf-8")] = (mode, oid)
    except (ValueError, UnicodeError) as exc:
        raise SourceError("Invalid Git index entries") from exc
    if index != expected_index:
        raise SourceError("Staged source differs from the recorded commit")
    if _git(root, policy, "ls-files", "--others", "--exclude-standard", "-z", "--", pathspec):
        raise SourceError("Untracked source files must be committed or ignored")
    head_after = _git(root, policy, "rev-parse", "--verify", "HEAD^{commit}", limit=100).strip()
    if head_after.decode() != commit or _git(root, policy, *index_args) != index_before:
        raise SourceError("Git revision or index changed during capture")
    if "README.md" not in contents:
        raise SourceError("Selected source requires a committed README.md")
    if len(contents["README.md"]) > policy.max_readme_bytes:
        raise SourceError("README exceeds byte limit")
    ordered = tuple(sorted(records, key=lambda item: item.path))
    identity = SourceIdentity(
        commit, tree, scope, canonical_hash([asdict(item) for item in ordered]), ordered
    )
    return identity, contents


def fingerprint(repo: Path, policy: RunPolicy = DEFAULT_POLICY) -> SourceIdentity:
    return _capture(repo, policy)[0]


_EXPORT_TOKEN = object()


@dataclass(frozen=True)
class SourceSnapshot:
    path: Path
    identity: SourceIdentity
    _token: object | None = None
    _origin: Path | None = None

    def verify(self, policy: RunPolicy = DEFAULT_POLICY) -> None:
        if self._token is not _EXPORT_TOKEN:
            raise SourceError("Only controller-created source exports are accepted")
        safe_root(self.path)
        for path in self.path.rglob("*"):
            if _linked(path.lstat()):
                raise SourceError("Snapshot contains a symlink or reparse point")
        expected = {item.path for item in self.identity.files}
        actual = {p.relative_to(self.path).as_posix() for p in self.path.rglob("*") if p.is_file()}
        if actual != expected:
            raise SourceError("Snapshot file set changed")
        for item in self.identity.files:
            data = read_regular(self.path, item.path, policy.max_file_bytes)
            if "sha256:" + hashlib.sha256(data).hexdigest() != item.sha256:
                raise SourceError("Snapshot bytes changed")


@contextmanager
def snapshot(repo: Path, policy: RunPolicy = DEFAULT_POLICY) -> Iterator[SourceSnapshot]:
    identity, contents = _capture(repo, policy)
    with tempfile.TemporaryDirectory(prefix="peeky-source-") as temporary:
        exported = Path(temporary) / "repo"
        exported.mkdir()
        for item in identity.files:
            target = exported / item.path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(contents[item.path])
            target.chmod(0o555 if item.mode == "100755" else 0o444)
        captured = SourceSnapshot(exported, identity, _EXPORT_TOKEN, _repo_root(safe_root(repo)))
        captured.verify(policy)
        for directory in sorted(
            (p for p in exported.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True
        ):
            directory.chmod(0o555)
        exported.chmod(0o555)
        yield captured
