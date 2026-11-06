import io
import time
import urllib.error
import urllib.request
from http.client import HTTPMessage, IncompleteRead
from types import SimpleNamespace

import pytest

from peeky.backends import instabox_api
from peeky.backends.instabox import InstaboxBackend

KEY = "ibk_" + "a" * 48


class Response(io.BytesIO):
    code = 200


def request() -> urllib.request.Request:
    return urllib.request.Request(
        instabox_api.API_URL + "/v1/me", headers={"X-API-Key": KEY}, method="GET"
    )


def test_production_transport_rejects_credential_redirect_without_following(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    error = urllib.error.HTTPError(
        instabox_api.API_URL + "/v1/me", 302, "Found", HTTPMessage(), io.BytesIO(KEY.encode())
    )

    def build(*handlers: object) -> SimpleNamespace:
        redirect: urllib.request.HTTPRedirectHandler = next(
            h for h in handlers if isinstance(h, instabox_api._NoRedirect)
        )
        assert (
            redirect.redirect_request(
                request(), io.BytesIO(), 302, "Found", HTTPMessage(), "https://evil.example"
            )
            is None
        )

        def open_request(req: urllib.request.Request, timeout: float) -> object:
            calls.append(req.full_url)
            raise error

        return SimpleNamespace(open=open_request)

    monkeypatch.setattr(urllib.request, "build_opener", build)
    client = instabox_api.InstaboxClient(instabox_api.InstaboxConfig(KEY))
    with pytest.raises(instabox_api.InstaboxError) as caught:
        client.get("/v1/me")
    assert caught.value.code == "REDIRECT_REJECTED" and KEY not in str(caught.value)
    assert calls == [instabox_api.API_URL + "/v1/me"]
    assert error.closed


def test_production_transport_closes_oversized_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    response = Response(b"x" * 20)
    monkeypatch.setattr(
        urllib.request,
        "build_opener",
        lambda *args: SimpleNamespace(open=lambda *args, **kwargs: response),
    )
    with pytest.raises(instabox_api.InstaboxError) as caught:
        instabox_api.metadata_transport(request(), 5.0, 8)
    assert caught.value.code == "RESPONSE_LIMIT" and response.closed


@pytest.mark.parametrize(
    ("status", "reason"),
    [(401, "AUTHENTICATION_FAILED"), (403, "ACCESS_DENIED"), (429, "RATE_LIMITED")],
)
@pytest.mark.parametrize("body_mode", ["oversized", "stalled"])
@pytest.mark.parametrize("raised_http_error", [False, True])
def test_known_http_failure_preserves_status_without_reading_body(
    monkeypatch: pytest.MonkeyPatch,
    status: int,
    reason: str,
    body_mode: str,
    raised_http_error: bool,
) -> None:
    class ErrorBody(io.BytesIO):
        read_calls = 0
        code = status

        def read1(self, size: int | None = -1) -> bytes:
            self.read_calls += 1
            if body_mode == "stalled":
                raise TimeoutError(KEY)
            return super().read1(size)

    body = ErrorBody(KEY.encode() + b"x" * instabox_api.MAX_METADATA_BYTES)
    error = urllib.error.HTTPError(
        instabox_api.API_URL + "/v1/me", status, "test", HTTPMessage(), body
    )
    requests: list[str] = []

    def open_response(req: urllib.request.Request, timeout: float) -> object:
        requests.append(req.full_url)
        if raised_http_error:
            raise error
        return body

    monkeypatch.setattr(
        urllib.request,
        "build_opener",
        lambda *args: SimpleNamespace(open=open_response),
    )
    result = InstaboxBackend(instabox_api.InstaboxConfig(KEY)).doctor()
    assert result.reason == reason
    assert result.details["http_status"] == status
    assert result.preflight_ok is False and result.ready is False
    assert KEY not in str(result.to_dict())
    assert requests == [instabox_api.API_URL + "/v1/me"]
    assert body.read_calls == 0 and body.closed


def test_production_transport_checks_elapsed_budget_between_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = Response(b"{}")
    clock = iter([0.0, 0.0, 6.0])
    monkeypatch.setattr(time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(
        urllib.request,
        "build_opener",
        lambda *args: SimpleNamespace(open=lambda *args, **kwargs: response),
    )
    with pytest.raises(instabox_api.InstaboxError) as caught:
        instabox_api.metadata_transport(request(), 5.0, 32)
    assert caught.value.code == "REQUEST_TIMEOUT" and response.closed


@pytest.mark.parametrize(
    ("failure", "code"),
    [
        (TimeoutError(KEY), "REQUEST_TIMEOUT"),
        (urllib.error.URLError(TimeoutError(KEY)), "REQUEST_TIMEOUT"),
        (IncompleteRead(KEY.encode()), "CONNECTION_FAILED"),
    ],
)
def test_transport_failures_cannot_echo_credentials(
    monkeypatch: pytest.MonkeyPatch, failure: Exception, code: str
) -> None:
    def open_request(*args: object, **kwargs: object) -> object:
        raise failure

    monkeypatch.setattr(
        urllib.request,
        "build_opener",
        lambda *args: SimpleNamespace(open=open_request),
    )
    with pytest.raises(instabox_api.InstaboxError) as caught:
        instabox_api.metadata_transport(request(), 5.0, 32)
    assert caught.value.code == code and KEY not in str(caught.value)
