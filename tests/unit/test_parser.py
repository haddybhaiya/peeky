from pathlib import Path

import pytest

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
