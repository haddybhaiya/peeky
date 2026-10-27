import json
import pytest

from peeky import __version__
from peeky.cli import main


@pytest.mark.smoke
def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


@pytest.mark.smoke
def test_inspect_good(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["inspect", "tests/fixtures/good_repo", "--json"]) == 0
    items = json.loads(capsys.readouterr().out)
    assert len(items) == 1 and items[0]["command"] == "python smoke.py"


@pytest.mark.smoke
def test_no_approval_does_not_execute(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["audit", "tests/fixtures/good_repo"]) == 2
    assert "not authorized" in capsys.readouterr().err


@pytest.mark.smoke
def test_no_opted_in_steps(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["inspect", "tests/fixtures/no_optin_repo"]) == 2
