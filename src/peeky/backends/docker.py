"""Thin adapter over the existing reviewed offline Docker runner."""

from __future__ import annotations

from pathlib import Path

from .. import runner
from ..models import Step, StepResult
from ..sources import SourceSnapshot
from .base import BackendReadiness


class DockerBackend:
    name = "docker"
    execution_supported = True

    def doctor(self, avoid: Path | None = None) -> BackendReadiness:
        status = runner.doctor(avoid=avoid)
        available = bool(status["docker_daemon"] and status.get("linux"))
        return BackendReadiness(
            backend=self.name,
            preflight_ok=available,
            execution_supported=True,
            reason="DOCKER_AVAILABLE" if available else "DOCKER_UNAVAILABLE",
            message="Linux Docker is available" if available else "Linux Docker is unavailable",
            checks={
                name: "passed" if value is True else "failed" for name, value in status.items()
            },
            details=status,
        )

    def execute(self, step: Step, source: SourceSnapshot, image: str, timeout: float) -> StepResult:
        return runner.execute(step, source, image, timeout=timeout)
