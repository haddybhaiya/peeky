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
        assert status["preflight_ok"] is True and status["ready"] is True
        assert status["execution_supported"] is True
        assert status["checks"]["execution"] == "supported"
    else:
        assert "InstaBox: READY" in output


def test_instabox_audit_unapproved_never_fetches_reads_keys_or_falls_back_to_docker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("INSTABOX_API_KEY", KEY)

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("Unapproved cloud audit touched credentials, source or Docker")

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
        ]
    )
    assert code == 2
    message = capsys.readouterr().err
    assert "not authorized" in message
    assert KEY not in message and not output.exists()


def test_instabox_audit_approved_executes_cloud_and_writes_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("INSTABOX_API_KEY", KEY)
    mid = "m_test12345678"
    data = {
        "/v1/me": {"userId": 42, "login": "testuser", "activated": True},
        "/v1/templates": {"templates": [{"id": "ci", "arch": "x86_64", "creatable": True}]},
        "/v1/usage": {"machines": 0, "limits": {"maxMachines": 5, "unlimited": []}},
    }

    def transport(request: urllib.request.Request, timeout: float, limit: int) -> MetadataResponse:
        url = request.full_url
        method = request.get_method()
        if method == "GET":
            selector = request.selector
            if selector in data:
                return MetadataResponse(200, json.dumps(data[selector]).encode())
        if method == "POST" and url.endswith("/v1/machines"):
            return MetadataResponse(201, json.dumps({"id": mid, "status": "running"}).encode())
        if method == "PUT" and "/files/" in url:
            return MetadataResponse(204, b"")
        if method == "POST" and url.endswith(f"/v1/machines/{mid}/exec"):
            return MetadataResponse(
                200,
                json.dumps(
                    {"exitCode": 0, "stdout": "smoke ok\n", "stderr": "", "timedOut": False}
                ).encode(),
            )
        if method == "DELETE" and url.endswith(f"/v1/machines/{mid}"):
            return MetadataResponse(204, b"")
        return MetadataResponse(404, b"")

    original = InstaboxClient
    monkeypatch.setattr(
        "peeky.backends.instabox.InstaboxClient", lambda config: original(config, transport)
    )

    def forbidden_docker(*args: object, **kwargs: object) -> None:
        pytest.fail("InstaBox audit fell back to Docker")

    monkeypatch.setattr("peeky.runner.execute", forbidden_docker)

    output = tmp_path / "runs"
    code = main(
        [
            "audit",
            "tests/fixtures/good_repo",
            "--backend",
            "instabox",
            "--output",
            str(output),
            "--approve",
        ]
    )
    assert code == 0
    records = list(output.glob("*.json"))
    assert len(records) == 1
    evidence = json.loads(records[0].read_text(encoding="utf-8"))
    assert evidence["verdict"] == "PASS"
    assert evidence["execution"] == "instabox-cloud-single-command"
    assert evidence["results"][0]["provenance"]["backend"] == "instabox"
    assert evidence["results"][0]["provenance"]["cleanup_verified"] is True
