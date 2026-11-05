import json
import urllib.request

import pytest

from peeky.backends.instabox_api import (
    API_URL,
    MAX_METADATA_BYTES,
    READ_ONLY_PATHS,
    REQUEST_TIMEOUT,
    InstaboxClient,
    InstaboxConfig,
    InstaboxError,
    MetadataResponse,
)

KEY = "ibk_" + "a" * 48


def test_byok_environment_config_is_secret_and_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INSTABOX_API_KEY", KEY)
    monkeypatch.setenv("INSTABOX_API_URL", API_URL)
    monkeypatch.setenv("PEEKY_INSTABOX_TEMPLATE", "ci")
    config = InstaboxConfig.from_environment()
    assert config.api_key == KEY and config.template_id == "ci"
    assert KEY not in repr(config)


@pytest.mark.parametrize("key", ["", "ibk_short", KEY + "\n", "iba_" + "a" * 48])
def test_invalid_keys_fail_before_network(key: str) -> None:
    with pytest.raises(InstaboxError) as error:
        InstaboxClient(InstaboxConfig(key))
    if key:
        assert key not in str(error.value)


@pytest.mark.parametrize(
    "url",
    [
        "http://api.instabox.sh",
        API_URL + "/",
        "https://evil.test",
        "https://api.instabox.sh@evil.test",
        API_URL + "?key=secret",
    ],
)
def test_only_reviewed_api_origin_receives_credentials(url: str) -> None:
    with pytest.raises(InstaboxError, match="only https"):
        InstaboxClient(InstaboxConfig(KEY, api_url=url))


@pytest.mark.parametrize("path", sorted(READ_ONLY_PATHS))
def test_client_sends_only_documented_authenticated_gets(path: str) -> None:
    def transport(request: urllib.request.Request, timeout: float, limit: int) -> MetadataResponse:
        assert request.full_url == API_URL + path
        assert request.get_method() == "GET" and request.data is None
        assert request.get_header("X-api-key") == KEY
        assert timeout == REQUEST_TIMEOUT and limit == MAX_METADATA_BYTES
        return MetadataResponse(200, json.dumps({"ok": True}).encode())

    assert InstaboxClient(InstaboxConfig(KEY), transport).get(path) == {"ok": True}


@pytest.mark.parametrize(
    "path",
    ["/v1/machines", "/v1/keys", "/v1/me?token=secret", "https://evil.test", "/v1/me/../machines"],
)
def test_client_cannot_address_mutation_or_arbitrary_endpoints(path: str) -> None:
    def forbidden(*args: object) -> MetadataResponse:
        pytest.fail("Unsupported operation reached transport")

    with pytest.raises(InstaboxError, match="Only InstaBox"):
        InstaboxClient(InstaboxConfig(KEY), forbidden).get(path)


@pytest.mark.parametrize("status", [301, 401, 402, 403, 404, 429, 500])
def test_provider_error_bodies_never_reach_errors(status: int) -> None:
    def transport(*args: object) -> MetadataResponse:
        return MetadataResponse(status, ("provider echo: " + KEY).encode())

    with pytest.raises(InstaboxError) as error:
        InstaboxClient(InstaboxConfig(KEY), transport).get("/v1/me")
    assert error.value.http_status == status
    assert KEY not in str(error.value) and "provider echo" not in str(error.value)


@pytest.mark.parametrize(
    "body", [b"[]", b'{"a":1,"a":2}', b'{"a":NaN}', b"\xff", b"x" * (MAX_METADATA_BYTES + 1)]
)
def test_malformed_or_oversized_metadata_cannot_succeed(body: bytes) -> None:
    def transport(*args: object) -> MetadataResponse:
        return MetadataResponse(200, body)

    with pytest.raises(InstaboxError):
        InstaboxClient(InstaboxConfig(KEY), transport).get("/v1/me")
