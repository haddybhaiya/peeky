from pathlib import Path

import pytest

from peeky.backends.base import BackendReadiness, SandboxBackend
from peeky.backends.docker import DockerBackend
from peeky.images import DEFAULT_IMAGE
from peeky.models import StepResult
from peeky.parser import read_steps
from peeky.sources import snapshot


@pytest.mark.parametrize("daemon,linux", [(True, True), (False, False), (True, False)])
def test_docker_adapter_preserves_observed_readiness(
    monkeypatch: pytest.MonkeyPatch, daemon: bool, linux: bool
) -> None:
    status = {"docker_cli": True, "docker_daemon": daemon, "linux": linux}
    monkeypatch.setattr("peeky.runner.doctor", lambda **kwargs: status)
    backend: SandboxBackend = DockerBackend()
    result = backend.doctor()
    assert result.preflight_ok is (daemon and linux)
    assert result.ready is (daemon and linux)
    assert result.details == status


def test_docker_adapter_delegates_exact_snapshot_and_budget(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    backend = DockerBackend()
    with snapshot(repo) as source:
        step = read_steps(source.path)[0]
        synthetic = StepResult(step.id, step.command, None, "", "", "INCONCLUSIVE", 0)

        def observed(*args: object, **kwargs: object) -> StepResult:
            assert args == (step, source, DEFAULT_IMAGE)
            assert kwargs == {"timeout": 2.0}
            return synthetic

        monkeypatch.setattr("peeky.runner.execute", observed)
        assert backend.execute(step, source, DEFAULT_IMAGE, timeout=2.0) is synthetic


def test_successful_preflight_does_not_imply_execution_support() -> None:
    result = BackendReadiness("instabox", True, False, "PREFLIGHT_OK", "Read-only checks passed")
    assert result.to_dict()["preflight_ok"] is True
    assert result.to_dict()["ready"] is False
