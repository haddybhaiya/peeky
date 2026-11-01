"""Public GitHub source inputs; repository contents never become host instructions."""

from __future__ import annotations

import os
import re
import signal
import subprocess
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .domain import DEFAULT_POLICY, RunPolicy
from .hosttools import host_tool
from .sources import SourceError, SourceSnapshot, _committed_snapshot


@dataclass(frozen=True)
class GitHubRepository:
    owner: str
    name: str

    @property
    def url(self) -> str:
        return f"https://github.com/{self.owner}/{self.name}"


def parse_url(value: str) -> GitHubRepository:
    """Accept only literal HTTPS repository roots, without credentials or redirects."""
    match = re.fullmatch(
        r"https://github\.com/([A-Za-z0-9][A-Za-z0-9-]{0,38})/([A-Za-z0-9_.-]{1,104})/?",
        value,
    )
    if match is None:
        raise SourceError(
            "Use a public repository root: https://github.com/OWNER/REPO; "
            "subdirectory URLs, credentials, queries and other hosts are unsupported"
        )
    owner, name = match.groups()
    if name.endswith(".git"):
        name = name[:-4]
    if not name or name in {".", ".."} or len(name) > 100 or owner.endswith("-"):
        raise SourceError("Invalid GitHub repository name or owner")
    return GitHubRepository(owner, name)


def validate_ref(value: str | None) -> str | None:
    """Validate a branch/tag/full SHA before constructing any Git argument."""
    if value is None:
        return None
    if re.fullmatch(r"[a-fA-F0-9]{40}", value):
        return value.lower()
    if (
        not value
        or len(value) > 255
        or value == "@"
        or value.startswith(("-", "/"))
        or value.endswith(("/", "."))
        or ".." in value
        or "@{" in value
        or any(ord(c) <= 32 or ord(c) == 127 or c in "~^:?*[\\" for c in value)
        or any(
            not part or part.startswith(".") or part.endswith(".lock") for part in value.split("/")
        )
        or (value.startswith("refs/") and not value.startswith(("refs/heads/", "refs/tags/")))
        or value in {"refs/heads/", "refs/tags/"}
    ):
        raise SourceError("--ref must be a branch, tag or full 40-character commit SHA")
    return value


@dataclass(frozen=True)
class FetchLimits:
    timeout_seconds: float = 60
    max_output_bytes: int = 128 * 1024
    max_storage_bytes: int = 64 * 1024 * 1024

    def __post_init__(self) -> None:
        if any(
            value <= 0
            for value in (self.timeout_seconds, self.max_output_bytes, self.max_storage_bytes)
        ):
            raise ValueError("GitHub fetch limits must be positive")


def _git_environment() -> dict[str, str]:
    # Keep platform, proxy and CA configuration; omit unrelated controller secrets
    # and every inherited GIT_* override (including injected config/askpass).
    allowed = {
        "PATH",
        "SYSTEMROOT",
        "WINDIR",
        "COMSPEC",
        "PATHEXT",
        "TEMP",
        "TMP",
        "TMPDIR",
        "LANG",
        "LC_ALL",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "NO_PROXY",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
    }
    env = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    env.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_ATTR_NOSYSTEM="1",
        GIT_TERMINAL_PROMPT="0",
        GIT_NO_LAZY_FETCH="1",
        GCM_INTERACTIVE="never",
    )
    return env


def _git_command(root: Path, *args: str) -> list[str]:
    binary = host_tool("git", avoid=root)
    if binary is None:
        raise SourceError("Git is required to inspect a GitHub URL")
    settings = (
        "core.fsmonitor=false",
        f"core.hooksPath={os.devnull}",
        "core.askPass=",
        "credential.helper=",
        "protocol.allow=never",
        "protocol.https.allow=always",
        "http.followRedirects=false",
        "http.sslVerify=true",
        "http.extraHeader=",
        "submodule.recurse=false",
        "fetch.fsckObjects=true",
        "maintenance.auto=false",
        "gc.auto=0",
    )
    return [
        binary,
        "--no-replace-objects",
        *(part for setting in settings for part in ("-c", setting)),
        *args,
    ]


def _stop(process: subprocess.Popen[bytes]) -> None:
    if os.name == "posix":
        # HTTPS Git uses helper children; terminate the whole owned process group.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    else:
        binary = host_tool("taskkill")
        if binary is not None:
            subprocess.run(
                [binary, "/PID", str(process.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                check=False,
            )
        if process.poll() is None:
            process.kill()
    process.wait(timeout=5)


DEFAULT_FETCH_LIMITS = FetchLimits()


def _storage_size(root: Path) -> int:
    total = 0
    for path in root.rglob("*"):
        try:
            if path.is_file():
                total += path.stat().st_size
        except FileNotFoundError:
            # Git atomically renames temporary packs during a fetch. The next
            # observation, including the final one, counts their destination.
            continue
    return total


def _check_limits(root: Path, streams: tuple[int, int], limits: FetchLimits) -> None:
    if _storage_size(root) > limits.max_storage_bytes:
        raise SourceError("GitHub fetch exceeded temporary Git storage limit")
    if any(os.fstat(descriptor).st_size > limits.max_output_bytes for descriptor in streams):
        raise SourceError("GitHub fetch exceeded diagnostic output limit")


def _run_git(root: Path, *args: str, limits: FetchLimits = DEFAULT_FETCH_LIMITS) -> bytes:
    """Monitor owned Git storage/output and wall time; never print server diagnostics."""
    command = _git_command(root, *args)
    deadline = time.monotonic() + limits.timeout_seconds
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        with subprocess.Popen(
            command,
            cwd=root,
            env=_git_environment(),
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            start_new_session=os.name == "posix",
        ) as process:
            try:
                while True:
                    _check_limits(root, (stdout.fileno(), stderr.fileno()), limits)
                    if time.monotonic() >= deadline:
                        raise SourceError("GitHub fetch timed out; retry with a smaller repository")
                    if process.poll() is not None:
                        break
                    time.sleep(0.02)
                # A fast child may finish writing between measurement and poll.
                _check_limits(root, (stdout.fileno(), stderr.fileno()), limits)
                if process.returncode != 0:
                    raise SourceError(
                        "GitHub source unavailable: check the public URL/ref, network and Git TLS setup; "
                        "private repositories, redirects and credential prompts are unsupported"
                    )
                stdout.seek(0)
                output = stdout.read(limits.max_output_bytes + 1)
                if len(output) > limits.max_output_bytes:
                    raise SourceError("GitHub fetch exceeded diagnostic output limit")
                return output
            finally:
                # Also reap helper processes when cancellation interrupts a fetch.
                if os.name == "posix" or process.poll() is None:
                    _stop(process)


@dataclass(frozen=True)
class RemoteSource:
    url: str
    requested_ref: str | None
    resolved_ref: str | None
    git_commit: str


def _resolve(
    root: Path, repository: GitHubRepository, ref: str | None, limits: FetchLimits
) -> RemoteSource:
    if ref is not None and re.fullmatch(r"[a-f0-9]{40}", ref):
        return RemoteSource(repository.url, ref, None, ref)
    if ref is None or ref == "HEAD":
        patterns = ["HEAD"]
    elif ref.startswith("refs/"):
        patterns = [ref, ref + "^{}"] if ref.startswith("refs/tags/") else [ref]
    else:
        patterns = [f"refs/heads/{ref}", f"refs/tags/{ref}", f"refs/tags/{ref}^{{}}"]
    output = _run_git(
        root, "ls-remote", "--symref", "--exit-code", "--", repository.url, *patterns, limits=limits
    )
    records: dict[str, str] = {}
    default_ref: str | None = None
    try:
        for line in output.decode("ascii").splitlines():
            value, name = line.split("\t")
            if name == "HEAD" and value.startswith("ref: refs/heads/"):
                default_ref = value.removeprefix("ref: ")
            elif name in patterns and re.fullmatch(r"[a-f0-9]{40}", value):
                if name in records:
                    raise ValueError("Duplicate advertised ref")
                records[name] = value
            else:
                raise ValueError("Unexpected advertised ref")
    except (ValueError, UnicodeError) as exc:
        raise SourceError("Invalid GitHub ref advertisement") from exc
    choices = [name for name in records if not name.endswith("^{}")]
    if len(choices) != 1:
        raise SourceError("GitHub ref missing or ambiguous; use refs/heads/NAME or refs/tags/NAME")
    name = choices[0]
    commit = records.get(name + "^{}", records[name])
    return RemoteSource(repository.url, ref, default_ref if name == "HEAD" else name, commit)


@dataclass(frozen=True)
class FetchedRepository:
    path: Path
    remote: RemoteSource


@contextmanager
def fetched_repository(
    url: str, ref: str | None = None, *, limits: FetchLimits = DEFAULT_FETCH_LIMITS
) -> Iterator[FetchedRepository]:
    """Fetch one resolved revision into controller-owned Git storage, without checkout."""
    repository, selected_ref = parse_url(url), validate_ref(ref)
    with tempfile.TemporaryDirectory(prefix="peeky-github-") as temporary:
        root = Path(temporary)
        _run_git(root, "init", "--template=", "-q", limits=limits)
        remote = _resolve(root, repository, selected_ref, limits)
        _run_git(
            root,
            "fetch",
            "--quiet",
            "--depth=1",
            "--no-tags",
            "--no-recurse-submodules",
            "--no-auto-maintenance",
            "--",
            repository.url,
            remote.git_commit,
            limits=limits,
        )
        actual = (
            _run_git(root, "rev-parse", "--verify", "FETCH_HEAD^{commit}", limits=limits)
            .strip()
            .decode("ascii")
        )
        if actual != remote.git_commit:
            raise SourceError("Fetched GitHub commit differs from the resolved revision")
        _run_git(root, "update-ref", "HEAD", remote.git_commit, limits=limits)
        yield FetchedRepository(root, remote)


@dataclass(frozen=True)
class GitHubSnapshot:
    source: SourceSnapshot
    remote: RemoteSource


@contextmanager
def github_snapshot(
    url: str,
    ref: str | None = None,
    *,
    policy: RunPolicy = DEFAULT_POLICY,
    limits: FetchLimits = DEFAULT_FETCH_LIMITS,
) -> Iterator[GitHubSnapshot]:
    """Tie temporary Git storage and a verified read-only export to one lifecycle."""
    with fetched_repository(url, ref, limits=limits) as fetched:
        with _committed_snapshot(fetched.path, fetched.remote.git_commit, policy) as source:
            yield GitHubSnapshot(source, fetched.remote)
