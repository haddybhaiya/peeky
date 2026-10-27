from pathlib import Path
from typing import Any

import pytest

from peeky.domain import DEFAULT_POLICY
from peeky.images import DEFAULT_IMAGE
from peeky.models import Step
from peeky.parser import read_steps
from peeky.policy import PolicyError, validate_run_image
from peeky.runner import InfrastructureError, create_command, execute, verify_environment
from peeky.sources import SourceError, SourceSnapshot, fingerprint, snapshot

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("reference", ["python:3.12-slim", "python@sha256:" + "0" * 64])
def test_T016_unreviewed_or_mutable_images_rejected(reference: str) -> None:
    with pytest.raises(PolicyError):
        validate_run_image(reference)


def test_T013_T014_command_has_only_restricted_mounts_and_resources(repo: Path) -> None:
    with snapshot(repo) as source:
        step = read_steps(source.path)[0]
        command = create_command("docker", step, source, DEFAULT_IMAGE, "peeky-unit", "unit")
        for expected in (
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
            "--log-driver=none",
        ):
            assert expected in command
        mounts = [command[i + 1] for i, part in enumerate(command) if part == "--mount"]
        assert mounts == [f"type=bind,source={source.path},target=/repo,readonly"]
        assert not any(
            part in {"--privileged", "--network=host", "--pid=host", "-v"} for part in command
        )
        assert "docker.sock" not in " ".join(command)


def test_live_path_and_forged_snapshot_never_reach_docker(repo: Path) -> None:
    unsafe: Any = repo
    with pytest.raises(PolicyError, match="snapshot"):
        execute(Step("s", "python smoke.py", 1), unsafe, DEFAULT_IMAGE)
    forged = SourceSnapshot(repo, fingerprint(repo))
    with pytest.raises(SourceError, match="controller-created"):
        execute(Step("s", "python smoke.py", 1), forged, DEFAULT_IMAGE)


def test_mismatched_step_and_excess_timeout_block_before_docker(repo: Path) -> None:
    with snapshot(repo) as source:
        with pytest.raises(PolicyError, match="plan"):
            execute(Step("wrong", "python other.py", 1), source, DEFAULT_IMAGE)
        with pytest.raises(PolicyError, match="timeout"):
            execute(
                read_steps(source.path)[0],
                source,
                DEFAULT_IMAGE,
                timeout=DEFAULT_POLICY.command_timeout_seconds + 1,
            )


def test_host_proxy_or_secret_environment_cannot_enter_container() -> None:
    image: dict[str, object] = {"Env": ["PATH=/usr/local/bin:/usr/bin"]}
    allowed = ["PATH=/usr/local/bin:/usr/bin", *DEFAULT_POLICY.container_environment]
    assert "HTTP_PROXY" in verify_environment({"Env": allowed}, image)
    with pytest.raises(InfrastructureError) as caught:
        verify_environment({"Env": [*allowed, "HOST_SECRET=must-never-reach-target"]}, image)
    assert caught.value.reason == "CONTAINER_ENVIRONMENT_MISMATCH"
    with pytest.raises(InfrastructureError, match="Duplicate"):
        verify_environment({"Env": [*allowed, "HTTP_PROXY=secret-must-not-shadow-empty"]}, image)
