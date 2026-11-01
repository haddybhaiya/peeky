"""Public GitHub source inputs; repository contents never become host instructions."""

from __future__ import annotations

import os
import re
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from .hosttools import host_tool
from .sources import SourceError


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
                    size = sum(path.stat().st_size for path in root.rglob("*") if path.is_file())
                    if size > limits.max_storage_bytes:
                        raise SourceError("GitHub fetch exceeded temporary Git storage limit")
                    if any(
                        os.fstat(stream.fileno()).st_size > limits.max_output_bytes
                        for stream in (stdout, stderr)
                    ):
                        raise SourceError("GitHub fetch exceeded diagnostic output limit")
                    if time.monotonic() >= deadline:
                        raise SourceError("GitHub fetch timed out; retry with a smaller repository")
                    if process.poll() is not None:
                        break
                    time.sleep(0.02)
                if process.returncode != 0:
                    raise SourceError(
                        "GitHub source unavailable: check the public URL/ref, network and Git TLS setup; "
                        "private repositories, redirects and credential prompts are unsupported"
                    )
                stdout.seek(0)
                return stdout.read(limits.max_output_bytes + 1)
            finally:
                # Also reap helper processes when cancellation interrupts a fetch.
                if process.poll() is None:
                    _stop(process)
