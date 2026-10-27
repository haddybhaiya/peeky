from dataclasses import replace
from pathlib import Path

import pytest

from peeky.domain import DEFAULT_POLICY
from peeky.parser import ParseError, extract_steps, read_steps


@pytest.mark.unit
def test_explicit_fence_only() -> None:
    content = "```bash\npython nope.py\n```\n```bash peeky\npython yep.py\n```"
    steps = extract_steps(content)
    assert len(steps) == 1
    assert steps[0].command == "python yep.py"
    assert steps[0].line == 5


@pytest.mark.unit
def test_unterminated_fence_rejected() -> None:
    with pytest.raises(ParseError):
        extract_steps("```bash peeky\npython yep.py")


@pytest.mark.unit
def test_example_fixture() -> None:
    steps = read_steps(Path("tests/fixtures/good_repo"))
    assert len(steps) == 1
    assert steps[0].command == "python smoke.py"


@pytest.mark.unit
def test_T001_nested_fence_examples_are_not_instructions() -> None:
    content = "````markdown\n```bash peeky\npython forbidden.py\n```\n````\n"
    assert extract_steps(content) == []


@pytest.mark.unit
@pytest.mark.parametrize(
    "content",
    [
        "```bash peeky extra\npython x.py\n```",
        "```bash peeky\npython x.py\n```` bad",
        "```bash peeky\npython x.py",
    ],
)
def test_T003_malformed_annotations_rejected(content: str) -> None:
    with pytest.raises(ParseError):
        extract_steps(content)


@pytest.mark.unit
def test_parser_limits_enforced() -> None:
    with pytest.raises(ParseError, match="count"):
        extract_steps(
            "```bash peeky\npython a.py\npython b.py\n```", replace(DEFAULT_POLICY, max_commands=1)
        )
    with pytest.raises(ParseError, match="length"):
        extract_steps(
            "```bash peeky\npython a.py\n```", replace(DEFAULT_POLICY, max_command_chars=5)
        )
    with pytest.raises(ParseError, match="byte"):
        extract_steps("x" * 20, replace(DEFAULT_POLICY, max_readme_bytes=10))
