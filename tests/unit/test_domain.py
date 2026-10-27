from dataclasses import replace
from pathlib import Path

import pytest

from peeky.domain import DEFAULT_POLICY, RunRecord, RunState, valid_history
from peeky.parser import read_steps
from peeky.sources import fingerprint

pytestmark = pytest.mark.unit


def test_policy_and_plan_identity_are_deterministic_and_sensitive(repo: Path) -> None:
    source = fingerprint(repo)
    steps = tuple(read_steps(repo))
    first, second = RunRecord(source, steps), RunRecord(source, steps)
    assert first.id != second.id
    assert first.dict()["plan_sha256"] == second.dict()["plan_sha256"]
    changed = replace(DEFAULT_POLICY, max_commands=11)
    assert changed.sha256 != DEFAULT_POLICY.sha256
    assert RunRecord(source, steps, changed).dict()["plan_sha256"] != first.dict()["plan_sha256"]
    assert RunRecord(source, ()).dict()["plan_sha256"] != first.dict()["plan_sha256"]


def test_state_rejects_execution_without_approval_and_terminal_rewrites(repo: Path) -> None:
    run = RunRecord(fingerprint(repo), tuple(read_steps(repo)))
    with pytest.raises(ValueError, match="Forbidden"):
        run.advance(RunState.SANDBOX_RUN)
    run.advance(RunState.INSPECTED)
    run.advance(RunState.BLOCKED)
    assert valid_history(run.history, RunState.BLOCKED)
    with pytest.raises(ValueError, match="Forbidden"):
        run.advance(RunState.APPROVED)
    assert not valid_history(["CREATED", "FINALIZED"], RunState.FINALIZED)
    assert not valid_history(["CREATED", {}], RunState.FINALIZED)
