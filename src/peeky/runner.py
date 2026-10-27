"""Digest-pinned offline Docker execution with bounded logs and owned cleanup."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO

from .domain import DEFAULT_POLICY
from .hosttools import host_tool
from .models import Step, StepResult
from .parser import read_steps
from .policy import PolicyError, safe_argv, validate_image, validate_run_image
from .redaction import redact
from .sources import SourceSnapshot

LABEL = "org.peeky.run_id"


class InfrastructureError(ValueError):
    def __init__(self, reason: str, detail: str) -> None:
        self.reason = reason
        super().__init__(redact(detail))


@dataclass(frozen=True)
class Captured:
    code: int
    stdout: bytes
    stderr: bytes
    bytes_seen: tuple[int, int]
    timed_out: bool
    limited: bool


def _collect(command: list[str], timeout: float, limit: int) -> Captured:
    """Bound raw memory; caller redacts before any result or artifact leaves runner."""
    buffers = [bytearray(), bytearray()]
    sizes = [0, 0]
    exceeded = threading.Event()
    with subprocess.Popen(
        command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ) as process:
        assert process.stdout is not None and process.stderr is not None

        def drain(stream: BinaryIO, index: int) -> None:
            while chunk := stream.read(4096):
                sizes[index] += len(chunk)
                remaining = max(0, limit - len(buffers[index]))
                buffers[index].extend(chunk[:remaining])
                if sizes[index] > limit:
                    exceeded.set()

        readers = [
            threading.Thread(target=drain, args=(stream, i), daemon=True)
            for i, stream in enumerate((process.stdout, process.stderr))
        ]
        for reader in readers:
            reader.start()
        deadline = time.monotonic() + timeout
        timed_out = False
        while process.poll() is None:
            if exceeded.is_set() or time.monotonic() >= deadline:
                timed_out = not exceeded.is_set()
                process.kill()
                break
            time.sleep(0.02)
        code = process.wait(timeout=5)
        for reader in readers:
            reader.join(timeout=5)
        if any(reader.is_alive() for reader in readers):
            raise InfrastructureError("LOG_CAPTURE_UNCERTAIN", "Docker stream did not close")
    return Captured(
        code,
        bytes(buffers[0]),
        bytes(buffers[1]),
        (sizes[0], sizes[1]),
        timed_out,
        exceeded.is_set(),
    )


def _control(binary: str, *args: str) -> Captured:
    try:
        result = _collect([binary, *args], DEFAULT_POLICY.docker_metadata_timeout_seconds, 65_536)
    except (OSError, subprocess.SubprocessError) as exc:
        raise InfrastructureError("DOCKER_UNAVAILABLE", str(exc)) from exc
    if result.timed_out or result.limited:
        raise InfrastructureError("DOCKER_CONTROL_LIMIT", "Docker metadata exceeded its budget")
    return result


def _json(binary: str, *args: str, reason: str) -> dict[str, object]:
    response = _control(binary, *args)
    if response.code != 0:
        raise InfrastructureError(reason, response.stderr.decode("utf-8", errors="replace"))
    try:
        data = json.loads(response.stdout)
    except (ValueError, UnicodeError) as exc:
        raise InfrastructureError("DOCKER_METADATA_INVALID", "Invalid Docker metadata") from exc
    if not isinstance(data, dict):
        raise InfrastructureError("DOCKER_METADATA_INVALID", "Expected Docker metadata object")
    return data


def doctor(avoid: Path | None = None) -> dict[str, object]:
    binary = host_tool("docker", avoid=avoid)
    if not binary:
        return {"docker_cli": False, "docker_daemon": False, "linux": False}
    try:
        run = _control(binary, "info", "--format", "{{.OSType}}")
        return {
            "docker_cli": True,
            "docker_daemon": run.code == 0,
            "linux": run.code == 0 and run.stdout.strip() == b"linux",
        }
    except InfrastructureError:
        return {"docker_cli": True, "docker_daemon": False, "linux": False}


def inspect_image(binary: str, reference: str) -> dict[str, object]:
    """Metadata-only cache query; execution separately requires reviewed allowlist."""
    validate_image(reference)
    data = _json(
        binary, "image", "inspect", "--format", "{{json .}}", reference, reason="IMAGE_UNAVAILABLE"
    )
    digests = data.get("RepoDigests")
    if not isinstance(digests, list) or reference not in digests or data.get("Os") != "linux":
        raise InfrastructureError("IMAGE_IDENTITY_MISMATCH", "Cached Linux image digest mismatch")
    if not isinstance(data.get("Id"), str) or not str(data["Id"]).startswith("sha256:"):
        raise InfrastructureError("IMAGE_IDENTITY_MISMATCH", "Missing immutable image ID")
    config = data.get("Config")
    if not isinstance(config, dict) or config.get("Volumes"):
        raise InfrastructureError(
            "IMAGE_CONFIG_UNSUPPORTED", "Image-declared volumes are forbidden"
        )
    return data


def inspect_final_state(
    binary: str, name: str
) -> tuple[dict[str, object], list[dict[str, object]]]:
    """Allow Docker's separate exit/OOM events to settle, without inferring OOM from 137."""
    observations: list[dict[str, object]] = []
    deadline = time.monotonic() + 1.0
    for delay in (0.0, 0.05, 0.1, 0.2, 0.4, 0.25):
        if observations:
            if time.monotonic() >= deadline:
                break
            time.sleep(min(delay, max(0.0, deadline - time.monotonic())))
        state = _json(
            binary, "inspect", "--format", "{{json .State}}", name, reason="STATE_UNAVAILABLE"
        )
        observations.append(state)
        if not (
            state.get("Status") == "exited"
            and state.get("ExitCode") == 137
            and state.get("OOMKilled") is False
        ):
            break
    return observations[-1], observations


def create_command(
    binary: str, step: Step, source: SourceSnapshot, image: str, name: str, run_id: str
) -> list[str]:
    args = safe_argv(step.command)
    command = [
        binary,
        "create",
        "--name",
        name,
        "--label",
        f"{LABEL}={run_id}",
        "--label",
        f"org.peeky.source_sha256={source.identity.source_sha256}",
        "--pull=never",
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--pids-limit=64",
        "--memory=256m",
        "--memory-swap=256m",
        "--cpus=1",
        "--user=65534:65534",
        "--restart=no",
        "--no-healthcheck",
        "--log-driver=none",
        "--ulimit",
        "nofile=128:128",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,noexec,size=32m,mode=1777",
        "--mount",
        f"type=bind,source={source.path},target=/repo,readonly",
        "--workdir=/repo",
    ]
    for value in DEFAULT_POLICY.container_environment:
        command.extend(["--env", value])
    return command + ["--entrypoint", args[0], image, *args[1:]]


def verify_environment(config: dict[str, object], image_config: dict[str, object]) -> list[str]:
    def values(raw: object) -> dict[str, str]:
        if not isinstance(raw, list) or not all(
            isinstance(item, str) and "=" in item for item in raw
        ):
            raise InfrastructureError(
                "CONTAINER_ENVIRONMENT_MISMATCH", "Invalid environment metadata"
            )
        parsed: dict[str, str] = {}
        for item in raw:
            name, _, value = item.partition("=")
            if name in parsed:
                raise InfrastructureError(
                    "CONTAINER_ENVIRONMENT_MISMATCH", "Duplicate environment key"
                )
            parsed[name] = value
        return parsed

    expected = values(image_config.get("Env") or [])
    expected.update(
        {
            value.partition("=")[0]: value.partition("=")[2]
            for value in DEFAULT_POLICY.container_environment
        }
    )
    observed = values(config.get("Env") or [])
    if observed != expected:
        raise InfrastructureError(
            "CONTAINER_ENVIRONMENT_MISMATCH",
            "Effective container environment differs from trusted image/policy",
        )
    return sorted(observed)


def _source_matches(path: Path, observed: str) -> bool:
    expected = str(path).replace("\\", "/")
    allowed = {expected}
    if os.name == "nt" and len(expected) > 2 and expected[1] == ":":
        suffix = expected[0].lower() + expected[2:]
        allowed.update({"/run/desktop/mnt/host/" + suffix, "/host_mnt/" + suffix})
    return observed.replace("\\", "/").casefold() in {p.casefold() for p in allowed}


def verify_container(
    data: dict[str, object],
    source: SourceSnapshot,
    image_id: str,
    run_id: str,
    image_config: dict[str, object],
) -> dict[str, object]:
    host, config, mounts = data.get("HostConfig"), data.get("Config"), data.get("Mounts")
    if not isinstance(host, dict) or not isinstance(config, dict) or not isinstance(mounts, list):
        raise InfrastructureError("CONTAINER_POLICY_MISMATCH", "Incomplete container configuration")
    labels = config.get("Labels")
    environment_names = verify_environment(config, image_config)
    opts = host.get("SecurityOpt") or []
    log_config = host.get("LogConfig")
    required = (
        data.get("Image") == image_id
        and isinstance(labels, dict)
        and labels.get(LABEL) == run_id
        and config.get("User") == DEFAULT_POLICY.user
        and config.get("WorkingDir") == "/repo"
        and not config.get("Tty")
        and not config.get("OpenStdin")
        and host.get("NetworkMode") == "none"
        and host.get("ReadonlyRootfs") is True
        and host.get("Privileged") is False
        and host.get("Memory") == 268_435_456
        and host.get("MemorySwap") == 268_435_456
        and host.get("NanoCpus") == 1_000_000_000
        and host.get("PidsLimit") == 64
        and set(host.get("CapDrop") or []) == {"ALL"}
        and not host.get("CapAdd")
        and isinstance(opts, list)
        and any(str(opt) in {"no-new-privileges", "no-new-privileges:true"} for opt in opts)
        and not any("unconfined" in str(opt) for opt in opts)
        and host.get("PidMode") != "host"
        and host.get("IpcMode") != "host"
        and isinstance(log_config, dict)
        and log_config.get("Type") == "none"
        and not host.get("Devices")
        and not host.get("DeviceRequests")
        and not host.get("Binds")
        and not host.get("PublishAllPorts")
        and len(mounts) == 1
    )
    mount = mounts[0] if mounts and isinstance(mounts[0], dict) else {}
    if not (
        required
        and mount.get("Type") == "bind"
        and mount.get("Destination") == "/repo"
        and mount.get("RW") is False
        and _source_matches(source.path, str(mount.get("Source")))
    ):
        raise InfrastructureError(
            "CONTAINER_POLICY_MISMATCH", "Effective Docker isolation differs from policy"
        )
    return {
        key: host.get(key)
        for key in (
            "NetworkMode",
            "ReadonlyRootfs",
            "Privileged",
            "Memory",
            "MemorySwap",
            "NanoCpus",
            "PidsLimit",
            "CapDrop",
            "CapAdd",
            "SecurityOpt",
            "LogConfig",
            "Tmpfs",
            "Ulimits",
            "PidMode",
            "IpcMode",
        )
    } | {"mounts": mounts, "user": config["User"], "environment_names": environment_names}


def _cleanup(binary: str, name: str, run_id: str) -> bool:
    try:
        inspected = _control(binary, "inspect", "--format", "{{json .Config.Labels}}", name)
        if inspected.code == 0:
            labels = json.loads(inspected.stdout)
            if not isinstance(labels, dict) or labels.get(LABEL) != run_id:
                return False
            removed = _control(binary, "rm", "--force", name)
            if removed.code != 0:
                return False
        remaining = _control(
            binary, "ps", "--all", "--quiet", "--filter", f"label={LABEL}={run_id}"
        )
        return remaining.code == 0 and not remaining.stdout.strip()
    except (InfrastructureError, ValueError, OSError):
        return False


def execute(step: Step, source: SourceSnapshot, image: str, timeout: float = 20) -> StepResult:
    if not isinstance(source, SourceSnapshot):
        raise PolicyError("Runner requires a controller-created immutable source snapshot")
    source.verify()
    safe_argv(step.command)
    validate_run_image(image)
    if step not in read_steps(source.path):
        raise PolicyError("Step does not match the captured README plan")
    if not 0 < timeout <= DEFAULT_POLICY.command_timeout_seconds:
        raise PolicyError("Execution timeout exceeds controller policy")
    start = time.monotonic()
    run_id = uuid.uuid4().hex
    name = "peeky-" + run_id
    provenance: dict[str, object] = {
        "runner_version": "2.1",
        "image_requested": image,
        "image_digest": "",
        "image_id": "",
        "source_sha256": source.identity.source_sha256,
        "policy_sha256": DEFAULT_POLICY.sha256,
        "container_id": "",
        "container_name": name,
        "run_id": run_id,
        "started_at": datetime.now(UTC).isoformat(),
        "timeout_seconds": timeout,
        "command_sha256": hashlib.sha256(step.command.encode()).hexdigest(),
        "logs_complete": True,
        "cleanup_verified": True,
        "target_started": False,
    }
    outcome, reason, exit_code = "INCONCLUSIVE", "DOCKER_UNAVAILABLE", None
    stdout = stderr = ""
    binary = host_tool("docker", avoid=source._origin)
    attempted_create = False
    try:
        status = doctor(avoid=source._origin)
        if binary is None or not status["docker_daemon"] or not status["linux"]:
            raise InfrastructureError(
                "DOCKER_UNAVAILABLE", "Linux Docker unavailable; no host fallback"
            )
        cached = inspect_image(binary, image)
        provenance.update(
            image_digest=image, image_id=cached["Id"], platform=cached.get("Architecture")
        )
        command = create_command(binary, step, source, image, name, run_id)
        provenance["docker_create_argv"] = command[1:]
        attempted_create = True
        created = _control(binary, *command[1:])
        if created.code != 0 or created.stderr.strip():
            raise InfrastructureError(
                "CONTAINER_CREATE_FAILED", created.stderr.decode("utf-8", errors="replace")
            )
        container_id = created.stdout.decode().strip()
        if len(container_id) != 64 or any(c not in "0123456789abcdef" for c in container_id):
            raise InfrastructureError("DOCKER_METADATA_INVALID", "Missing container ID")
        provenance["container_id"] = container_id
        container = _json(
            binary, "inspect", "--format", "{{json .}}", name, reason="CONTAINER_UNAVAILABLE"
        )
        image_config = cached["Config"]
        assert isinstance(image_config, dict)
        provenance["isolation"] = verify_container(
            container, source, str(cached["Id"]), run_id, image_config
        )
        source.verify()
        collected = _collect(
            [binary, "start", "--attach", name], timeout, DEFAULT_POLICY.log_bytes_per_stream
        )
        # Raw buffers stay transient and bounded. Only redacted transcripts leave this boundary.
        stdout = redact(collected.stdout.decode("utf-8", errors="replace"))
        stderr = redact(collected.stderr.decode("utf-8", errors="replace"))
        provenance.update(
            stdout_bytes_seen=collected.bytes_seen[0],
            stderr_bytes_seen=collected.bytes_seen[1],
            logs_complete=not (collected.limited or collected.timed_out),
            attach_exit_code=collected.code,
        )
        state_data, state_observations = inspect_final_state(binary, name)
        provenance["container_state"] = state_data
        provenance["container_state_observations"] = state_observations
        target_started = bool(state_data.get("StartedAt")) and not str(
            state_data["StartedAt"]
        ).startswith("0001-")
        provenance["target_started"] = target_started
        raw_code = state_data.get("ExitCode")
        exit_code = (
            raw_code
            if type(raw_code) is int and target_started and state_data.get("Status") == "exited"
            else None
        )
        if collected.limited:
            reason = "LOG_LIMIT"
        elif collected.timed_out:
            outcome, reason = (
                ("TIMEOUT", "COMMAND_TIMEOUT")
                if target_started
                else ("INCONCLUSIVE", "CONTAINER_START_TIMEOUT")
            )
        elif state_data.get("OOMKilled") is True:
            reason = "MEMORY_LIMIT"
        elif state_data.get("Error") or not target_started:
            reason = "COMMAND_NOT_STARTED"
        elif state_data.get("Status") != "exited" or exit_code is None:
            reason = "STATE_UNCERTAIN"
        elif collected.code != exit_code:
            reason = "ATTACH_STATUS_MISMATCH"
        elif exit_code == 137:
            # Signal-derived exit codes and explicit target exits overlap. No
            # observed OOM flag means the cause is unknown, not proven OOM/FAIL.
            reason = "TERMINATION_UNCERTAIN"
        else:
            outcome, reason = (
                ("PASS", "COMMAND_EXIT_ZERO")
                if exit_code == 0
                else ("FAIL", "COMMAND_EXIT_NONZERO")
            )
    except InfrastructureError as exc:
        reason = exc.reason
        stderr = (stderr + "\n" + str(exc)).strip()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        reason = "RUNNER_INFRASTRUCTURE_ERROR"
        stderr = (stderr + "\n" + redact(str(exc))).strip()
    finally:
        if binary is not None and attempted_create:
            provenance["cleanup_verified"] = _cleanup(binary, name, run_id)
        if not provenance["cleanup_verified"] and outcome == "PASS":
            outcome, reason = "INCONCLUSIVE", "CLEANUP_UNVERIFIED"
        provenance["finished_at"] = datetime.now(UTC).isoformat()
        provenance["stdout_sha256"] = hashlib.sha256(stdout.encode()).hexdigest()
        provenance["stderr_sha256"] = hashlib.sha256(stderr.encode()).hexdigest()
    return StepResult(
        step.id,
        step.command,
        exit_code,
        stdout,
        stderr,
        outcome,
        round((time.monotonic() - start) * 1000),
        reason,
        provenance,
    )
