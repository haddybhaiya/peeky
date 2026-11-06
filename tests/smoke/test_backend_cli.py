import json
import urllib.request
from pathlib import Path

import pytest

from peeky.backends.instabox_api import InstaboxClient, InstaboxConfig, MetadataResponse
from peeky.cli import main

KEY = "ibk_" + "a" * 48


def test_default_doctor_keeps_legacy_json_and_never_reads_cloud_credentials(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    status = {"docker_cli": True, "docker_daemon": True, "linux": True}
    monkeypatch.setattr("peeky.runner.doctor", lambda **kwargs: status)

    def forbidden(*args: object) -> InstaboxConfig:
        pytest.fail("Default Docker operation inspected InstaBox credentials")

    monkeypatch.setattr(InstaboxConfig, "from_environment", forbidden)
    assert main(["doctor", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == status
    assert main(["doctor", "--backend", "docker", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == status


def test_instabox_doctor_missing_key_is_offline_and_actionable(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("INSTABOX_API_KEY", raising=False)

    def forbidden(*args: object) -> dict[str, object]:
        pytest.fail("Missing key caused an account request")

    monkeypatch.setattr(InstaboxClient, "get", forbidden)
    assert main(["doctor", "--backend", "instabox", "--json"]) == 3
    status = json.loads(capsys.readouterr().out)
    assert status["reason"] == "MISSING_API_KEY" and status["ready"] is False
    assert "INSTABOX_API_KEY" in status["message"]


@pytest.mark.parametrize("as_json", [False, True])
def test_instabox_doctor_only_reads_metadata_and_never_exposes_keys(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], as_json: bool
) -> None:
    monkeypatch.setenv("INSTABOX_API_KEY", KEY)
    monkeypatch.delenv("INSTABOX_API_URL", raising=False)
    monkeypatch.delenv("PEEKY_INSTABOX_TEMPLATE", raising=False)
    calls: list[str] = []
    data = {
        "/v1/me": {"userId": 42, "login": KEY, "csrfToken": KEY, "activated": True},
        "/v1/templates": {
            "templates": [{"id": "ci", "arch": "x86_64", "creatable": True, "description": KEY}]
        },
        "/v1/usage": {"machines": 0, "limits": {"maxMachines": 1, "unlimited": []}, "secret": KEY},
    }

    def transport(request: urllib.request.Request, timeout: float, limit: int) -> MetadataResponse:
        assert request.get_method() == "GET"
        calls.append(request.selector)
        return MetadataResponse(200, json.dumps(data[request.selector]).encode())

    original = InstaboxClient
    monkeypatch.setattr(
        "peeky.backends.instabox.InstaboxClient", lambda config: original(config, transport)
    )
    assert main(["doctor", "--backend", "instabox", *(["--json"] if as_json else [])]) == 0
    output = capsys.readouterr().out
    assert KEY not in output and calls == ["/v1/me", "/v1/templates", "/v1/usage"]
    if as_json:
        status = json.loads(output)
        assert status["preflight_ok"] is True and status["ready"] is False
        assert status["execution_supported"] is False
        assert status["checks"]["create_delete_permissions"] == "not_verified"
    else:
        assert "not implemented" in output


@pytest.mark.parametrize("approved", [False, True])
def test_instabox_audit_never_fetches_reads_keys_or_falls_back_to_docker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    approved: bool,
) -> None:
    monkeypatch.setenv("INSTABOX_API_KEY", KEY)

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("Unsupported cloud execution touched credentials, source or Docker")

    monkeypatch.setattr(InstaboxConfig, "from_environment", forbidden)
    monkeypatch.setattr("peeky.cli.github_snapshot", forbidden)
    monkeypatch.setattr("peeky.cli.snapshot", forbidden)
    monkeypatch.setattr("peeky.runner.doctor", forbidden)
    monkeypatch.setattr("peeky.runner.execute", forbidden)
    output = tmp_path / "must-not-exist"
    code = main(
        [
            "audit",
            "https://github.com/o/r",
            "--backend",
            "instabox",
            "--output",
            str(output),
            *(["--approve"] if approved else []),
        ]
    )
    assert code == (3 if approved else 2)
    message = capsys.readouterr().err
    assert ("not implemented" if approved else "not authorized") in message
    assert KEY not in message and not output.exists()
