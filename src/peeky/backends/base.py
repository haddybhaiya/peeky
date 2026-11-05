"""Controller-owned backend contract and explicit preflight observations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Protocol

from ..models import Step, StepResult
from ..sources import SourceSnapshot


class BackendUnavailable(ValueError):
    """A selected backend cannot perform an audit; never fall back implicitly."""


@dataclass(frozen=True)
class BackendReadiness:
    backend: str
    preflight_ok: bool
    execution_supported: bool
    reason: str
    message: str
    checks: dict[str, str] = field(default_factory=dict)
    details: dict[str, object] = field(default_factory=dict)

    @property
    def ready(self) -> bool:
        return self.preflight_ok and self.execution_supported

    def to_dict(self) -> dict[str, object]:
        return {**asdict(self), "ready": self.ready}


class SandboxBackend(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def execution_supported(self) -> bool: ...

    def doctor(self, avoid: Path | None = None) -> BackendReadiness: ...

    def execute(
        self, step: Step, source: SourceSnapshot, image: str, timeout: float
    ) -> StepResult: ...
