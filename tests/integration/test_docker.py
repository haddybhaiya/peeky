from pathlib import Path

import pytest

from peeky.models import Step
from peeky.runner import doctor, execute


@pytest.mark.integration
@pytest.mark.docker
def test_real_good_fixture() -> None:
    if not doctor()["docker_daemon"]:
        pytest.skip("Docker daemon unavailable")
    good = execute(Step("good", "python smoke.py", 1), Path("tests/fixtures/good_repo"),
                   "python:3.12-slim")
    assert good.outcome == "PASS", good.stderr
    assert "HELLO_FROM_GOOD_FIXTURE" in good.stdout


@pytest.mark.integration
@pytest.mark.docker
def test_real_bad_fixture() -> None:
    if not doctor()["docker_daemon"]:
        pytest.skip("Docker daemon unavailable")
    bad = execute(Step("bad", "python -m missing_onboarding_entrypoint", 1),
                  Path("tests/fixtures/bad_repo"), "python:3.12-slim")
    assert bad.outcome == "FAIL", bad.stderr
