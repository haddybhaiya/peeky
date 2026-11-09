"""Bounded InstaBox client for account preflight and cloud sandbox execution."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from http.client import HTTPException
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..sources import SourceSnapshot

API_URL = "https://api.instabox.sh"
READ_ONLY_PATHS = frozenset({"/v1/me", "/v1/templates", "/v1/usage"})
REQUEST_TIMEOUT = 5.0
MAX_METADATA_BYTES = 256 * 1024


class InstaboxError(ValueError):
    def __init__(self, code: str, message: str, *, http_status: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.http_status = http_status


@dataclass(frozen=True)
class InstaboxConfig:
    api_key: str = field(repr=False)
    api_url: str = API_URL
    template_id: str = "ci"

    def validate(self) -> None:
        if not self.api_key:
            raise InstaboxError("MISSING_API_KEY", "Set INSTABOX_API_KEY to your InstaBox API key")
        if not re.fullmatch(r"ibk_[A-Za-z0-9_-]{48}", self.api_key):
            raise InstaboxError(
                "INVALID_API_KEY", "INSTABOX_API_KEY must be a 52-character ibk_ API key"
            )
        if self.api_url != API_URL:
            raise InstaboxError(
                "INVALID_API_URL", "This backend supports only https://api.instabox.sh"
            )
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", self.template_id):
            raise InstaboxError("INVALID_TEMPLATE", "PEEKY_INSTABOX_TEMPLATE must be a template ID")

    @classmethod
    def from_environment(cls) -> InstaboxConfig:
        result = cls(
            api_key=os.environ.get("INSTABOX_API_KEY", ""),
            api_url=os.environ.get("INSTABOX_API_URL", API_URL),
            template_id=os.environ.get("PEEKY_INSTABOX_TEMPLATE", "ci"),
        )
        result.validate()
        return result


@dataclass(frozen=True)
class MetadataResponse:
    status: int
    body: bytes = field(repr=False)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> None:
        return None


def _read_metadata(response: Any, deadline: float, limit: int) -> bytes:
    chunks: list[bytes] = []
    size = 0
    while size <= limit:
        if time.monotonic() >= deadline:
            raise InstaboxError("REQUEST_TIMEOUT", "InstaBox metadata read deadline exceeded")
        chunk = response.read1(min(8192, limit + 1 - size))
        if not chunk:
            break
        chunks.append(chunk)
        size += len(chunk)
    if size > limit:
        raise InstaboxError("RESPONSE_LIMIT", "InstaBox metadata exceeds the response budget")
    return b"".join(chunks)


def metadata_transport(
    request: urllib.request.Request, timeout: float, limit: int
) -> MetadataResponse:
    # Keep configured proxy/CA trust and TLS verification; never follow redirects
    # carrying the account key. No response body or exception text reaches output.
    opener = urllib.request.build_opener(_NoRedirect())
    deadline = time.monotonic() + timeout
    try:
        try:
            response = opener.open(request, timeout=timeout)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            if response.code not in (200, 201, 204):
                return MetadataResponse(response.code, b"")
            if response.code == 204:
                return MetadataResponse(204, b"")
            return MetadataResponse(response.code, _read_metadata(response, deadline, limit))
    except InstaboxError:
        raise
    except (OSError, urllib.error.URLError, HTTPException) as error:
        timed_out = isinstance(error, TimeoutError) or isinstance(
            getattr(error, "reason", None), TimeoutError
        )
        code = "REQUEST_TIMEOUT" if timed_out else "CONNECTION_FAILED"
        raise InstaboxError(
            code, "Could not communicate with InstaBox; check connectivity and TLS setup"
        ) from None


MetadataTransport = Callable[[urllib.request.Request, float, int], MetadataResponse]


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("Duplicate metadata field")
        result[name] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ValueError("Non-finite metadata number")


class InstaboxClient:
    def __init__(
        self, config: InstaboxConfig, transport: MetadataTransport = metadata_transport
    ) -> None:
        config.validate()
        self.config = config
        self._transport = transport

    def get(self, path: str) -> dict[str, Any]:
        if path not in READ_ONLY_PATHS:
            raise InstaboxError(
                "UNSUPPORTED_OPERATION",
                "Only InstaBox identity, templates and usage reads are permitted",
            )
        request = urllib.request.Request(
            self.config.api_url + path,
            method="GET",
            headers={"X-API-Key": self.config.api_key, "Accept": "application/json"},
        )
        try:
            response = self._transport(request, REQUEST_TIMEOUT, MAX_METADATA_BYTES)
        except InstaboxError:
            raise
        except (OSError, ValueError):
            raise InstaboxError(
                "CONNECTION_FAILED", "Could not read InstaBox account metadata"
            ) from None
        status = response.status
        if status != 200:
            code, message = {
                401: (
                    "AUTHENTICATION_FAILED",
                    "InstaBox rejected the API key; check whether it is invalid, expired or revoked",
                ),
                402: (
                    "ACCOUNT_UNAVAILABLE",
                    "InstaBox account access requires attention in the dashboard",
                ),
                403: (
                    "ACCESS_DENIED",
                    "InstaBox denied this read; check key scopes and account activation",
                ),
                404: ("UNSUPPORTED_API", "InstaBox did not expose the documented account endpoint"),
                429: ("RATE_LIMITED", "InstaBox rate limited the check; retry later"),
            }.get(
                status,
                ("REDIRECT_REJECTED", "InstaBox redirects are not followed")
                if 300 <= status < 400
                else ("SERVICE_UNAVAILABLE", "InstaBox account service is unavailable"),
            )
            raise InstaboxError(code, message, http_status=status)
        if len(response.body) > MAX_METADATA_BYTES:
            raise InstaboxError("RESPONSE_LIMIT", "InstaBox metadata exceeds the response budget")
        try:
            data = json.loads(
                response.body.decode("utf-8"),
                object_pairs_hook=_unique_object,
                parse_constant=_invalid_constant,
            )
            if not isinstance(data, dict):
                raise ValueError("Expected metadata object")
            return data
        except (ValueError, UnicodeError, RecursionError):
            raise InstaboxError(
                "INVALID_RESPONSE", "InstaBox returned invalid account metadata"
            ) from None

    @staticmethod
    def _validate_machine_id(machine_id: str) -> None:
        if not isinstance(machine_id, str) or not re.fullmatch(
            r"m_[A-Za-z0-9_-]{8,64}", machine_id
        ):
            raise InstaboxError("INVALID_MACHINE_ID", "Invalid InstaBox machine ID")

    @staticmethod
    def _parse_json(body: bytes) -> dict[str, Any]:
        if len(body) > MAX_METADATA_BYTES:
            raise InstaboxError("RESPONSE_LIMIT", "InstaBox response exceeds the byte budget")
        try:
            data = json.loads(
                body.decode("utf-8"),
                object_pairs_hook=_unique_object,
                parse_constant=_invalid_constant,
            )
            if not isinstance(data, dict):
                raise ValueError("Expected JSON object")
            return data
        except (ValueError, UnicodeError, RecursionError):
            raise InstaboxError(
                "INVALID_RESPONSE", "InstaBox returned invalid JSON response"
            ) from None

    @staticmethod
    def _map_http_error(status: int, action: str = "operation") -> None:
        code, message = {
            401: (
                "AUTHENTICATION_FAILED",
                "InstaBox rejected the API key; check whether it is invalid, expired or revoked",
            ),
            402: (
                "ACCOUNT_UNAVAILABLE",
                "InstaBox account access requires attention in the dashboard",
            ),
            403: (
                "ACCESS_DENIED",
                f"InstaBox denied this {action}; check key scopes and permissions",
            ),
            404: ("RESOURCE_NOT_FOUND", f"InstaBox resource not found for {action}"),
            429: ("RATE_LIMITED", f"InstaBox rate limited {action}; retry later"),
        }.get(
            status,
            ("REDIRECT_REJECTED", "InstaBox redirects are not followed")
            if 300 <= status < 400
            else ("SERVICE_UNAVAILABLE", f"InstaBox service is unavailable during {action}"),
        )
        raise InstaboxError(code, message, http_status=status)

    def create_machine(
        self,
        template: str,
        metadata: dict[str, str] | None = None,
        auto_destroy_seconds: int = 300,
    ) -> str:
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", template):
            raise InstaboxError("INVALID_TEMPLATE", "Invalid template identifier")
        idempotency_key = str(uuid.uuid4())
        payload = {
            "template": template,
            "metadata": metadata or {},
            "auto_destroy": auto_destroy_seconds,
        }
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.config.api_url}/v1/machines",
            data=body,
            headers={
                "X-API-Key": self.config.api_key,
                "Idempotency-Key": idempotency_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            res = self._transport(req, REQUEST_TIMEOUT, MAX_METADATA_BYTES)
        except InstaboxError:
            raise
        except (OSError, ValueError):
            raise InstaboxError("CONNECTION_FAILED", "Failed to create InstaBox machine") from None
        if res.status not in (200, 201):
            self._map_http_error(res.status, "create machine")
        data = self._parse_json(res.body)
        machine_id = data.get("id")
        if not isinstance(machine_id, str) or not re.fullmatch(
            r"m_[A-Za-z0-9_-]{8,64}", machine_id
        ):
            raise InstaboxError(
                "INVALID_RESPONSE", "InstaBox returned invalid machine creation response"
            )
        return machine_id

    def get_machine(self, machine_id: str) -> dict[str, Any]:
        self._validate_machine_id(machine_id)
        req = urllib.request.Request(
            f"{self.config.api_url}/v1/machines/{machine_id}",
            headers={"X-API-Key": self.config.api_key, "Accept": "application/json"},
            method="GET",
        )
        try:
            res = self._transport(req, REQUEST_TIMEOUT, MAX_METADATA_BYTES)
        except InstaboxError:
            raise
        except (OSError, ValueError):
            raise InstaboxError(
                "CONNECTION_FAILED", "Failed to query InstaBox machine status"
            ) from None
        if res.status != 200:
            self._map_http_error(res.status, "query machine")
        return self._parse_json(res.body)

    def put_file(self, machine_id: str, remote_path: str, content: bytes) -> None:
        self._validate_machine_id(machine_id)
        clean_path = remote_path.strip("/").replace("\\", "/")
        parts = clean_path.split("/")
        if any(part in ("", "..", ".") for part in parts):
            raise InstaboxError("INVALID_PATH", "Directory traversal in remote path is forbidden")
        quoted_path = "/".join(urllib.parse.quote(part, safe="") for part in parts)
        req = urllib.request.Request(
            f"{self.config.api_url}/v1/machines/{machine_id}/files/{quoted_path}",
            data=content,
            headers={
                "X-API-Key": self.config.api_key,
                "Content-Type": "application/octet-stream",
            },
            method="PUT",
        )
        try:
            res = self._transport(req, REQUEST_TIMEOUT, MAX_METADATA_BYTES)
        except InstaboxError:
            raise
        except (OSError, ValueError):
            raise InstaboxError(
                "CONNECTION_FAILED", "Failed to upload file to InstaBox machine"
            ) from None
        if res.status not in (200, 201, 204):
            self._map_http_error(res.status, "upload file")

    def upload_snapshot(
        self, machine_id: str, snapshot: SourceSnapshot, target_dir: str = "workspace"
    ) -> None:
        self._validate_machine_id(machine_id)
        for item in snapshot.identity.files:
            file_path = snapshot.path / item.path
            if not file_path.is_file():
                continue
            data = file_path.read_bytes()
            clean_rel = item.path.strip("/").replace("\\", "/")
            remote_path = f"{target_dir.strip('/')}/{clean_rel}"
            self.put_file(machine_id, remote_path, data)

    def exec_step(
        self,
        machine_id: str,
        argv: list[str],
        cwd: str = "/workspace",
        timeout: float = 20.0,
    ) -> dict[str, Any]:
        self._validate_machine_id(machine_id)
        if not argv or not all(isinstance(arg, str) for arg in argv):
            raise InstaboxError("INVALID_ARGV", "Exec argv must be a non-empty list of strings")
        payload = {
            "argv": argv,
            "cwd": cwd,
            "timeout": timeout,
        }
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.config.api_url}/v1/machines/{machine_id}/exec",
            data=body,
            headers={
                "X-API-Key": self.config.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        transport_timeout = timeout + 5.0
        try:
            res = self._transport(req, transport_timeout, MAX_METADATA_BYTES)
        except InstaboxError:
            raise
        except (OSError, ValueError):
            raise InstaboxError(
                "CONNECTION_FAILED", "Failed to execute command in InstaBox machine"
            ) from None
        if res.status != 200:
            self._map_http_error(res.status, "exec command")
        return self._parse_json(res.body)

    def delete_machine(self, machine_id: str, *, timeout: float = 3.0) -> bool:
        self._validate_machine_id(machine_id)
        req = urllib.request.Request(
            f"{self.config.api_url}/v1/machines/{machine_id}",
            headers={"X-API-Key": self.config.api_key, "Accept": "application/json"},
            method="DELETE",
        )
        try:
            res = self._transport(req, REQUEST_TIMEOUT, MAX_METADATA_BYTES)
        except InstaboxError:
            raise
        except (OSError, ValueError):
            raise InstaboxError("CONNECTION_FAILED", "Failed to delete InstaBox machine") from None
        if res.status not in (200, 202, 204, 404):
            self._map_http_error(res.status, "delete machine")
        if res.status in (200, 204, 404):
            return True
        # If 202 Accepted, deletion is pending. Poll until 404 within bounded deadline.
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            time.sleep(0.05)
            try:
                self.get_machine(machine_id)
            except InstaboxError as exc:
                if exc.http_status == 404 or exc.code == "RESOURCE_NOT_FOUND":
                    return True
                raise
        return False
