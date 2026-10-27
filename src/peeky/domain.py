"""Controller-owned source, policy and run identities. No target-defined policy."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from enum import StrEnum

from .models import Step


def canonical_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RunPolicy:
    version: str = "1"
    max_commands: int = 12
    max_command_chars: int = 400
    max_arguments: int = 24
    max_argument_chars: int = 300
    max_readme_bytes: int = 128_000
    max_files: int = 2000
    max_file_bytes: int = 4 * 1024 * 1024
    max_source_bytes: int = 32 * 1024 * 1024
    max_tree_bytes: int = 1024 * 1024
    max_depth: int = 32
    git_timeout_seconds: int = 15
    command_timeout_seconds: int = 20
    memory: str = "256m"
    cpus: str = "1"
    pids_limit: int = 64
    user: str = "65534:65534"
    network: str = "none"
    source_mount: str = "readonly"
    max_capture_chars: int = 5000
    allowed_binaries: tuple[str, ...] = ("python", "python3", "pytest")
    forbidden_shell_chars: str = ";&|<>`$\\"
    image_namespace: str = "official-python-only"
    checkout_normalization: str = "utf8-crlf-to-lf-only"

    def __post_init__(self) -> None:
        for value in asdict(self).values():
            if isinstance(value, int) and value <= 0:
                raise ValueError("Policy limits must be positive")

    @property
    def sha256(self) -> str:
        return canonical_hash(asdict(self))


DEFAULT_POLICY = RunPolicy()


@dataclass(frozen=True)
class SourceFile:
    path: str
    mode: str
    sha256: str
    size: int


@dataclass(frozen=True)
class SourceIdentity:
    git_commit: str
    git_tree: str
    scope: str
    source_sha256: str
    files: tuple[SourceFile, ...]
    dirty: bool = False


class RunState(StrEnum):
    CREATED = "CREATED"
    INSPECTED = "INSPECTED"
    APPROVED = "APPROVED"
    SANDBOX_RUN = "SANDBOX_RUN"
    OBSERVED = "OBSERVED"
    FINALIZED = "FINALIZED"
    BLOCKED = "BLOCKED"


_NEXT: dict[RunState, set[RunState]] = {
    RunState.CREATED: {RunState.INSPECTED, RunState.BLOCKED},
    RunState.INSPECTED: {RunState.APPROVED, RunState.BLOCKED},
    RunState.APPROVED: {RunState.SANDBOX_RUN, RunState.BLOCKED},
    RunState.SANDBOX_RUN: {RunState.OBSERVED, RunState.BLOCKED},
    RunState.OBSERVED: {RunState.FINALIZED},
    RunState.FINALIZED: set(),
    RunState.BLOCKED: set(),
}


def valid_history(history: object, final: RunState) -> bool:
    if not isinstance(history, list) or not history or history[0] != RunState.CREATED:
        return False
    try:
        states = [RunState(value) for value in history]
    except (ValueError, TypeError):
        return False
    return states[-1] == final and all(
        b in _NEXT[a] for a, b in zip(states, states[1:], strict=False)
    )


def plan_hash(source: SourceIdentity, steps: tuple[Step, ...], policy: RunPolicy) -> str:
    return canonical_hash(
        {
            "source": asdict(source),
            "steps": [asdict(s) for s in steps],
            "policy_sha256": policy.sha256,
        }
    )


@dataclass
class RunRecord:
    source: SourceIdentity
    steps: tuple[Step, ...]
    policy: RunPolicy = DEFAULT_POLICY
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    state: RunState = field(default=RunState.CREATED, init=False)
    history: list[str] = field(default_factory=lambda: [RunState.CREATED], init=False)

    def advance(self, state: RunState) -> None:
        if state not in _NEXT[self.state]:
            raise ValueError(f"Forbidden run transition: {self.state} -> {state}")
        self.state = state
        self.history.append(state)

    def dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "state": self.state,
            "history": list(self.history),
            "plan_sha256": plan_hash(self.source, self.steps, self.policy),
        }
