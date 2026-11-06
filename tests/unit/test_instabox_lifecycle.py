"""Unit tests for InstaBox machine lifecycle, source transfer, and execution."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import pytest

from peeky.backends import instabox_api
from peeky.backends.instabox import InstaboxBackend
from peeky.backends.instabox_api import (
    InstaboxClient,
    InstaboxConfig,
    InstaboxError,
    MetadataResponse,
)
from peeky.models import Step
from peeky.sources import snapshot

KEY = "ibk_" + "a" * 48
MID = "m_testmachine123"


def test_create_machine_sends_idempotency_and_metadata() -> None:
    calls: list[dict[str, object]] = []

    def transport(request: urllib.request.Request, timeout: float, limit: int) -> MetadataResponse:
        assert request.get_method() == "POST"
        assert request.full_url == f"{instabox_api.API_URL}/v1/machines"
        assert request.get_header("X-api-key") == KEY
        assert request.get_header("Idempotency-key") is not None
        assert request.get_header("Content-type") == "application/json"
        raw_data = request.data if isinstance(request.data, bytes) else b""
        body = json.loads(raw_data.decode("utf-8")) if raw_data else {}
        calls.append(body)
        return MetadataResponse(201, json.dumps({"id": MID, "status": "running"}).encode())

    client = InstaboxClient(InstaboxConfig(KEY), transport)
    machine_id = client.create_machine("ci", metadata={"test": "true"}, auto_destroy_seconds=120)
    assert machine_id == MID
    assert len(calls) == 1
    assert calls[0]["template"] == "ci"
    assert calls[0]["auto_destroy"] == 120
    assert calls[0]["metadata"] == {"test": "true"}


def test_create_machine_rejects_invalid_machine_id_response() -> None:
    def transport(request: urllib.request.Request, timeout: float, limit: int) -> MetadataResponse:
        return MetadataResponse(201, json.dumps({"id": "invalid_id"}).encode())

    client = InstaboxClient(InstaboxConfig(KEY), transport)
    with pytest.raises(InstaboxError, match="invalid machine creation response"):
        client.create_machine("ci")


def test_put_file_uploads_binary_contents() -> None:
    calls: list[tuple[str, bytes]] = []

    def transport(request: urllib.request.Request, timeout: float, limit: int) -> MetadataResponse:
        assert request.get_method() == "PUT"
        assert (
            request.full_url == f"{instabox_api.API_URL}/v1/machines/{MID}/files/workspace/app.py"
        )
        assert request.get_header("X-api-key") == KEY
        assert request.get_header("Content-type") == "application/octet-stream"
        data = request.data if isinstance(request.data, bytes) else b""
        calls.append((request.full_url, data))
        return MetadataResponse(204, b"")

    client = InstaboxClient(InstaboxConfig(KEY), transport)
    client.put_file(MID, "workspace/app.py", b"print('hello')")
    assert len(calls) == 1
    assert calls[0][1] == b"print('hello')"


def test_put_file_rejects_directory_traversal() -> None:
    client = InstaboxClient(InstaboxConfig(KEY), lambda *args: MetadataResponse(200, b""))
    with pytest.raises(InstaboxError, match="Directory traversal"):
        client.put_file(MID, "workspace/../../etc/passwd", b"evil")


def test_exec_step_sends_argv_and_cwd() -> None:
    calls: list[dict[str, object]] = []

    def transport(request: urllib.request.Request, timeout: float, limit: int) -> MetadataResponse:
        assert request.get_method() == "POST"
        assert request.full_url == f"{instabox_api.API_URL}/v1/machines/{MID}/exec"
        assert request.get_header("X-api-key") == KEY
        assert request.get_header("Content-type") == "application/json"
        raw_data = request.data if isinstance(request.data, bytes) else b""
        body = json.loads(raw_data.decode("utf-8")) if raw_data else {}
        calls.append(body)
        return MetadataResponse(
            200,
            json.dumps(
                {"exitCode": 0, "stdout": "PASS\n", "stderr": "", "timedOut": False}
            ).encode(),
        )

    client = InstaboxClient(InstaboxConfig(KEY), transport)
    res = client.exec_step(MID, ["python", "smoke.py"], cwd="/workspace", timeout=15.0)
    assert res["exitCode"] == 0
    assert res["stdout"] == "PASS\n"
    assert len(calls) == 1
    assert calls[0]["argv"] == ["python", "smoke.py"]
    assert calls[0]["cwd"] == "/workspace"
    assert calls[0]["timeout"] == 15.0


def test_delete_machine_sends_delete_method() -> None:
    calls: list[str] = []

    def transport(request: urllib.request.Request, timeout: float, limit: int) -> MetadataResponse:
        assert request.get_method() == "DELETE"
        assert request.full_url == f"{instabox_api.API_URL}/v1/machines/{MID}"
        assert request.get_header("X-api-key") == KEY
        calls.append(request.full_url)
        return MetadataResponse(204, b"")

    client = InstaboxClient(InstaboxConfig(KEY), transport)
    client.delete_machine(MID)
    assert len(calls) == 1


def test_backend_execute_lifecycle_pass(tmp_path: Path) -> None:
    created: list[str] = []
    deleted: list[str] = []
    uploaded: list[str] = []
    executed: list[list[str]] = []

    def transport(request: urllib.request.Request, timeout: float, limit: int) -> MetadataResponse:
        method = request.get_method()
        url = request.full_url
        if method == "POST" and url.endswith("/v1/machines"):
            created.append(MID)
            return MetadataResponse(201, json.dumps({"id": MID, "status": "running"}).encode())
        if method == "PUT" and "/files/" in url:
            uploaded.append(url)
            return MetadataResponse(204, b"")
        if method == "POST" and url.endswith(f"/v1/machines/{MID}/exec"):
            raw_data = request.data if isinstance(request.data, bytes) else b""
            body = json.loads(raw_data.decode("utf-8")) if raw_data else {}
            argv = body.get("argv")
            if isinstance(argv, list):
                executed.append([str(x) for x in argv])
            return MetadataResponse(
                200,
                json.dumps(
                    {
                        "exitCode": 0,
                        "stdout": f"All ok with {KEY}\n",
                        "stderr": "",
                        "timedOut": False,
                    }
                ).encode(),
            )
        if method == "DELETE" and url.endswith(f"/v1/machines/{MID}"):
            deleted.append(MID)
            return MetadataResponse(204, b"")
        return MetadataResponse(404, b"")

    with snapshot(Path("tests/fixtures/good_repo")) as snap:
        backend = InstaboxBackend(InstaboxConfig(KEY), transport)
        step = Step(id="S1", command="python smoke.py", line=1)
        res = backend.execute(step, snap, "python:3.12-slim", timeout=10.0)

    assert res.outcome == "PASS"
    assert res.exit_code == 0
    assert KEY not in res.stdout
    assert "[REDACTED]" in res.stdout
    assert res.provenance["backend"] == "instabox"
    assert res.provenance["cloud"] is True
    assert res.provenance["cleanup_verified"] is True
    assert res.provenance["machine_id"] == MID
    assert created == [MID]
    assert deleted == [MID]
    assert executed == [["python", "smoke.py"]]
    assert len(uploaded) >= 2


def test_backend_execute_lifecycle_failure(tmp_path: Path) -> None:
    deleted: list[str] = []

    def transport(request: urllib.request.Request, timeout: float, limit: int) -> MetadataResponse:
        method = request.get_method()
        url = request.full_url
        if method == "POST" and url.endswith("/v1/machines"):
            return MetadataResponse(201, json.dumps({"id": MID, "status": "running"}).encode())
        if method == "PUT" and "/files/" in url:
            return MetadataResponse(204, b"")
        if method == "POST" and url.endswith(f"/v1/machines/{MID}/exec"):
            return MetadataResponse(
                200,
                json.dumps(
                    {
                        "exitCode": 1,
                        "stdout": "",
                        "stderr": "ModuleNotFoundError",
                        "timedOut": False,
                    }
                ).encode(),
            )
        if method == "DELETE" and url.endswith(f"/v1/machines/{MID}"):
            deleted.append(MID)
            return MetadataResponse(204, b"")
        return MetadataResponse(404, b"")

    with snapshot(Path("tests/fixtures/good_repo")) as snap:
        backend = InstaboxBackend(InstaboxConfig(KEY), transport)
        step = Step(id="S1", command="python smoke.py", line=1)
        res = backend.execute(step, snap, "python:3.12-slim", timeout=10.0)

    assert res.outcome == "FAIL"
    assert res.exit_code == 1
    assert "ModuleNotFoundError" in res.stderr
    assert res.provenance["cleanup_verified"] is True
    assert deleted == [MID]


def test_backend_execute_guarantees_cleanup_on_exception(tmp_path: Path) -> None:
    deleted: list[str] = []

    def transport(request: urllib.request.Request, timeout: float, limit: int) -> MetadataResponse:
        method = request.get_method()
        url = request.full_url
        if method == "POST" and url.endswith("/v1/machines"):
            return MetadataResponse(201, json.dumps({"id": MID, "status": "running"}).encode())
        if method == "PUT" and "/files/" in url:
            # Injected failure during file upload
            raise TimeoutError("Upload connection stalled")
        if method == "DELETE" and url.endswith(f"/v1/machines/{MID}"):
            deleted.append(MID)
            return MetadataResponse(204, b"")
        return MetadataResponse(404, b"")

    with snapshot(Path("tests/fixtures/good_repo")) as snap:
        backend = InstaboxBackend(InstaboxConfig(KEY), transport)
        step = Step(id="S1", command="python smoke.py", line=1)
        with pytest.raises(InstaboxError):
            backend.execute(step, snap, "python:3.12-slim", timeout=10.0)

    # Machine must be deleted even if upload failed!
    assert deleted == [MID]
