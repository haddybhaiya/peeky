import pytest

from peeky.evidence import verdict
from peeky.models import Step, StepResult

S = [Step("s1", "python good.py", 1)]


@pytest.mark.unit
def test_pass_only_with_complete_real_result() -> None:
    good = StepResult("s1", "python good.py", 0, "", "", "PASS", 1)
    assert verdict(S, [good]) == "PASS"
    assert verdict(S, []) == "INCONCLUSIVE"
    assert verdict([], []) == "INCONCLUSIVE"


@pytest.mark.unit
def test_blocked_or_timeout_cannot_pass() -> None:
    for state in ("BLOCKED", "TIMEOUT"):
        result = StepResult("s1", "python good.py", None, "", "", state, 1)
        assert verdict(S, [result]) == "INCONCLUSIVE"


@pytest.mark.unit
def test_failure() -> None:
    result = StepResult("s1", "python good.py", 1, "", "", "FAIL", 1)
    assert verdict(S, [result]) == "FAIL"


def test_failure_remains_visible_when_later_steps_are_unexecuted() -> None:
    result = StepResult("s1", "python good.py", 1, "", "", "FAIL", 1)
    assert verdict(S + [Step("s2", "python next.py", 2)], [result]) == "FAIL"


def test_unrelated_or_nonzero_pass_result_is_inconclusive() -> None:
    assert (
        verdict(S, [StepResult("wrong", "python other.py", 0, "", "", "PASS", 1)]) == "INCONCLUSIVE"
    )
    assert verdict(S, [StepResult("s1", "python good.py", 7, "", "", "PASS", 1)]) == "INCONCLUSIVE"
