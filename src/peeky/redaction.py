"""Redact at the collection/storage boundary; never persist raw credential streams."""

from __future__ import annotations

import os
import re

MASK = "[REDACTED]"
_ANSI = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07\x1b]*(?:\x07|\x1b\\))")
_QUERY = re.compile(r"(https?://[^\s?#]+)\?[^\s\"'<>]*", re.IGNORECASE)
_URL_AUTH = re.compile(r"(https?://)[^\s/@]+@", re.IGNORECASE)
_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_.-]*")
_AUTH = re.compile(r"(?i)\b(authorization\s*[:=]\s*(?:bearer\s+|basic\s+)?)[^\r\n]+")
_ASSIGN = re.compile(
    r"(?i)(\b(?:[A-Za-z_][A-Za-z0-9_-]*_)?(?:api[_-]?key|access[_-]?key|secret|token|password|passwd|credential)"
    r"\s*[=:]\s*)(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)"
)
_TOKEN = re.compile(
    r"\b(?:gh[pousr]_[A-Za-z0-9_]{12,}|github_pat_[A-Za-z0-9_]{12,}"
    r"|sk-[A-Za-z0-9_-]{12,}|AKIA[A-Z0-9]{16})\b"
)
_PRIVATE = re.compile(
    r"-----BEGIN [^-]*PRIVATE KEY-----.*?(?:-----END [^-]*PRIVATE KEY-----|\Z)", re.DOTALL
)
_SECRET_NAME = re.compile(
    r"TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|API.?KEY|ACCESS.?KEY|PRIVATE.?KEY", re.IGNORECASE
)


def redact(text: str) -> str:
    text = _ANSI.sub("", text)
    for name, value in os.environ.items():
        if _SECRET_NAME.search(name) and len(value) >= 6:
            text = text.replace(value, MASK)
    text = _PRIVATE.sub(MASK, text)
    text = _URL_AUTH.sub(lambda m: m[1] + MASK + "@", text)
    text = _JWT.sub(MASK, text)
    text = _QUERY.sub(lambda m: m[1] + "?" + MASK, text)
    text = _AUTH.sub(lambda m: m[1] + MASK, text)
    text = _ASSIGN.sub(lambda m: m[1] + MASK, text)
    text = _TOKEN.sub(MASK, text)
    return "".join(c for c in text if c in "\n\t" or ord(c) >= 32 and ord(c) != 127)


def sanitized(value: object) -> object:
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, dict):
        return {str(key): sanitized(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitized(item) for item in value]
    return value
