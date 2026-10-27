"""Immutable records: data from targets never decides trusted policy."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class Step:
    id: str
    command: str
    line: int


@dataclass(frozen=True)
class StepResult:
    id: str
    command: str
    exit_code: int | None
    stdout: str
    stderr: str
    outcome: str
    duration_ms: int
    reason: str = ""
    provenance: dict[str, object] = field(default_factory=dict)

    def dict(self) -> dict[str, object]:
        return asdict(self)
