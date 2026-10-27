"""Local HMAC integrity, not a public signature or proof against a compromised host."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path

from .sources import read_regular, safe_root

_STATE_HOME = (
    Path(os.environ["LOCALAPPDATA"])
    if os.environ.get("LOCALAPPDATA")
    else Path.home() / ".local/state"
)
DEFAULT_KEY_FILE = _STATE_HOME / "Peeky/controller.key"


def _key(create: bool) -> bytes:
    path = DEFAULT_KEY_FILE
    if create:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        safe_root(path.parent)
        try:
            with os.fdopen(
                os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "wb"
            ) as stream:
                stream.write(os.urandom(32))
        except FileExistsError:
            pass
    data = read_regular(safe_root(path.parent), path.name, 32)
    if len(data) != 32:
        raise ValueError("Invalid controller evidence key")
    return data


def _bytes(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def authenticate(payload: dict[str, object]) -> dict[str, object]:
    data = {key: value for key, value in payload.items() if key != "integrity"}
    encoded = _bytes(data)
    key = _key(create=True)
    return {
        **data,
        "integrity": {
            "algorithm": "hmac-sha256",
            "key_id": hashlib.sha256(key).hexdigest(),
            "payload_sha256": hashlib.sha256(encoded).hexdigest(),
            "signature": hmac.new(key, encoded, hashlib.sha256).hexdigest(),
        },
    }


def verify(payload: dict[str, object]) -> None:
    integrity = payload.get("integrity")
    if not isinstance(integrity, dict) or integrity.get("algorithm") != "hmac-sha256":
        raise ValueError("Missing controller evidence authentication")
    data = _bytes({key: value for key, value in payload.items() if key != "integrity"})
    key = _key(create=False)
    expected = hmac.new(key, data, hashlib.sha256).hexdigest()
    if not (
        hmac.compare_digest(str(integrity.get("signature")), expected)
        and integrity.get("key_id") == hashlib.sha256(key).hexdigest()
        and integrity.get("payload_sha256") == hashlib.sha256(data).hexdigest()
    ):
        raise ValueError("Controller evidence integrity check failed")
