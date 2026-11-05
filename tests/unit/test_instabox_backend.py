import json
import urllib.request
from pathlib import Path

import pytest

from peeky.backends import get_backend
from peeky.backends.base import BackendUnavailable, SandboxBackend
from peeky.backends.instabox import InstaboxBackend
from peeky.backends.instabox_api import InstaboxConfig, MetadataResponse
from peeky.images import DEFAULT_IMAGE
from peeky.parser import read_steps
from peeky.sources import snapshot

KEY = "ibk_" + "a" * 48


def responses() -> dict[str, object]:
    return {
        "/v1/me": {"userId": 42, "login": "fixture", "activated": True},
        "/v1/templates": {"templates": [{"id": "ci", "arch": "x86_64", "creatable": True}]},
        "/v1/usage": {"machines": 0, "limits": {"maxMachines": 1, "unlimited": []}},
    }


def backend(data: dict[str, object], calls: list[str]) -> InstaboxBackend:
    def transport(request: urllib.request.Request, timeout: float, limit: int) -> MetadataResponse:
        path = request.selector
        calls.append(path)
        assert request.get_method() == "GET"
        return MetadataResponse(200, json.dumps(data[path]).encode())

    return InstaboxBackend(InstaboxConfig(KEY), transport)


def test_read_only_success_never_claims_cloud_audit_readiness() -> None:
    calls: list[str] = []
    selected: SandboxBackend = backend(responses(), calls)
    status = selected.doctor()
    assert status.preflight_ok and not status.ready and not status.execution_supported
    assert calls == ["/v1/me", "/v1/templates", "/v1/usage"]
    assert status.checks["create_delete_permissions"] == "not_verified"
    assert KEY not in json.dumps(status.to_dict())


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        (
            {
                "/v1/me": {
                    "userId": 42,
                    "login": "fixture",
                    "inviteRequired": True,
                    "activated": False,
                }
            },
            "INVITE_REQUIRED",
        ),
        (
            {"/v1/templates": {"templates": [{"id": "ci", "arch": "x86_64", "creatable": False}]}},
            "TEMPLATE_UNAVAILABLE",
        ),
        (
            {"/v1/usage": {"machines": 1, "limits": {"maxMachines": 1, "unlimited": []}}},
            "MACHINE_LIMIT_REACHED",
        ),
        ({"/v1/usage": {"machines": 0, "limits": {"maxMachines": 0}}}, "LIMIT_UNKNOWN"),
        ({"/v1/me": {"userId": True, "login": "fixture"}}, "INVALID_RESPONSE"),
    ],
)
def test_blocked_account_states_are_explicit(change: dict[str, object], reason: str) -> None:
    data = responses()
    data.update(change)
    result = backend(data, []).doctor()
    assert not result.preflight_ok and not result.ready
    assert result.reason == reason


@pytest.mark.parametrize("unlimited,ok", [(["maxMachines"], True), ([], False)])
def test_zero_limits_follow_documented_unlimited_flag(unlimited: list[str], ok: bool) -> None:
    data = responses()
    data["/v1/usage"] = {"machines": 4, "limits": {"maxMachines": 0, "unlimited": unlimited}}
    assert backend(data, []).doctor().preflight_ok is ok


def test_no_key_fails_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("INSTABOX_API_KEY", raising=False)
    status = InstaboxBackend().doctor()
    assert status.reason == "MISSING_API_KEY" and not status.preflight_ok


def test_cloud_execution_never_reads_key_or_contacts_api(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: object) -> InstaboxConfig:
        pytest.fail("Cloud execution loaded credentials")

    monkeypatch.setattr(InstaboxConfig, "from_environment", forbidden)
    with snapshot(repo) as source:
        with pytest.raises(BackendUnavailable, match="not implemented"):
            get_backend("instabox").execute(read_steps(source.path)[0], source, DEFAULT_IMAGE, 1)


def test_unknown_backend_is_not_an_implicit_docker_fallback() -> None:
    with pytest.raises(BackendUnavailable):
        get_backend("unknown")


@pytest.mark.parametrize(
    "template",
    [
        {"id": "ci", "arch": "x86_64", "creatable": "true"},
        {"id": "ci", "arch": "x86_64", "hidden": "false"},
        {"id": "ci", "arch": "aarch64", "creatable": True},
        {"id": "ci", "arch": "x86_64"},
    ],
)
def test_unknown_or_malformed_templates_do_not_pass(template: dict[str, object]) -> None:
    data = responses()
    data["/v1/templates"] = {"templates": [template]}
    assert not backend(data, []).doctor().preflight_ok


def test_documented_legacy_hidden_flag_is_understood() -> None:
    data = responses()
    data["/v1/templates"] = {"templates": [{"id": "ci", "arch": "x86_64", "hidden": False}]}
    assert backend(data, []).doctor().preflight_ok


@pytest.mark.parametrize(
    "status,reason",
    [
        (401, "AUTHENTICATION_FAILED"),
        (403, "ACCESS_DENIED"),
        (429, "RATE_LIMITED"),
        (503, "SERVICE_UNAVAILABLE"),
    ],
)
def test_readiness_http_failures_are_safe_and_not_retried(status: int, reason: str) -> None:
    calls: list[str] = []

    def transport(request: urllib.request.Request, timeout: float, limit: int) -> MetadataResponse:
        calls.append(request.selector)
        return MetadataResponse(status, KEY.encode())

    result = InstaboxBackend(InstaboxConfig(KEY), transport).doctor()
    assert result.reason == reason and not result.preflight_ok
    assert KEY not in json.dumps(result.to_dict())
    assert calls == ["/v1/me"]
