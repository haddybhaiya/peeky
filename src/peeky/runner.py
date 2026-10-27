"""Restricted Docker invocation; not a hardened untrusted multi-tenant sandbox."""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from .domain import DEFAULT_POLICY
from .models import Step, StepResult
from .policy import PolicyError, safe_argv, validate_image

MAX_CAPTURE = DEFAULT_POLICY.max_capture_chars


def doctor() -> dict[str, object]:
    binary = shutil.which("docker")
    if not binary:
        return {"docker_cli": False, "docker_daemon": False}
    try:
        run = subprocess.run(
            [binary, "info", "--format", "{{.ServerVersion}}"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        return {"docker_cli": True, "docker_daemon": run.returncode == 0}
    except (OSError, subprocess.TimeoutExpired):
        return {"docker_cli": True, "docker_daemon": False}


def execute(step: Step, repo: Path, image: str, timeout: int = 20) -> StepResult:
    args = safe_argv(step.command)
    validate_image(image)
    binary = shutil.which("docker")
    if binary is None:
        raise PolicyError("Docker is not installed; refusing host execution")
    repo_path = repo.resolve(strict=True)
    started = time.monotonic()
    cmd = [
        binary,
        "run",
        "--rm",
        "--pull=never",
        f"--network={DEFAULT_POLICY.network}",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        f"--pids-limit={DEFAULT_POLICY.pids_limit}",
        f"--memory={DEFAULT_POLICY.memory}",
        f"--cpus={DEFAULT_POLICY.cpus}",
        f"--user={DEFAULT_POLICY.user}",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,size=32m",
        "--mount",
        f"type=bind,source={repo_path},target=/repo,readonly",
        "--workdir=/repo",
        image,
        *args,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        outcome = (
            "PASS"
            if result.returncode == 0
            else ("BLOCKED" if result.returncode in (125, 126, 127) else "FAIL")
        )
        return StepResult(
            step.id,
            step.command,
            result.returncode,
            result.stdout[:MAX_CAPTURE],
            result.stderr[:MAX_CAPTURE],
            outcome,
            round((time.monotonic() - started) * 1000),
        )
    except subprocess.TimeoutExpired as exc:
        return StepResult(
            step.id,
            step.command,
            None,
            (exc.stdout or b"")[:MAX_CAPTURE].decode("utf-8", errors="replace")
            if isinstance(exc.stdout, bytes)
            else (exc.stdout or "")[:MAX_CAPTURE],
            "Docker execution timed out",
            "TIMEOUT",
            round((time.monotonic() - started) * 1000),
        )
    except OSError as exc:
        return StepResult(
            step.id,
            step.command,
            None,
            "",
            str(exc)[:MAX_CAPTURE],
            "BLOCKED",
            round((time.monotonic() - started) * 1000),
        )
