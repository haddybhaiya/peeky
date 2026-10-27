import pytest

from peeky.policy import PolicyError, safe_argv, validate_image


@pytest.mark.unit
@pytest.mark.parametrize(
    "command",
    [
        "python foo.py; rm -rf /",
        "python foo.py | tee out",
        "sh -c whoami",
        "python $(curl example.com)",
        "python foo.py > output",
        "python foo.py && echo ok",
    ],
)
def test_dangerous_commands_rejected(command: str) -> None:
    with pytest.raises(PolicyError):
        safe_argv(command)


@pytest.mark.unit
def test_approved_argv() -> None:
    assert safe_argv("python smoke.py") == ["python", "smoke.py"]


@pytest.mark.unit
def test_image_policy() -> None:
    assert validate_image("python:3.12-slim") == "python:3.12-slim"
    with pytest.raises(PolicyError):
        validate_image("--privileged")
