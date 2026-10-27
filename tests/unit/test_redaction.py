import json
import uuid
from pathlib import Path

import pytest

from peeky.evidence import write_report
from peeky.provenance import authenticate, verify
from peeky.redaction import redact

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "text",
    [
        "api_key=synthetic-secret-value",
        "password: synthetic-secret-value",
        "Authorization: Bearer synthetic-secret-value",
        "https://example.invalid/?token=synthetic-secret-value",
    ],
)
def test_T015_known_secret_formats_are_redacted(text: str) -> None:
    assert "synthetic-secret-value" not in redact(text)
    assert "[REDACTED]" in redact(text)


def test_environment_values_and_terminal_controls_are_removed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PEEKY_TEST_API_KEY", "synthetic-environment-secret")
    assert redact("\x1b[31msynthetic-environment-secret\x1b[0m") == "[REDACTED]"


def test_T015_T016_authenticated_evidence_detects_tampering(tmp_path: Path) -> None:
    signed = authenticate({"message": "original"})
    verify(signed)
    signed["message"] = "tampered"
    with pytest.raises(ValueError, match="integrity"):
        verify(signed)
    path = write_report(
        {"verdict": "INCONCLUSIVE", "detail": "api_key=synthetic-secret-value"},
        tmp_path / "records",
    )
    stored = path.read_text(encoding="utf-8")
    assert "synthetic-secret-value" not in stored
    verify(json.loads(stored))


@pytest.mark.parametrize(
    "text",
    [
        "CLIENT_API_KEY=synthetic-secret-value",
        "https://user:synthetic-secret-value@example.invalid/path",
    ],
)
def test_prefixed_keys_and_url_credentials_redacted(text: str) -> None:
    assert "synthetic-secret-value" not in redact(text)


def test_evidence_finalization_is_exclusive_and_leaves_no_partial_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(uuid, "uuid4", lambda: uuid.UUID(int=42))
    output = tmp_path / "records"
    first = write_report({"message": "original"}, output)
    original = first.read_bytes()
    with pytest.raises(FileExistsError):
        write_report({"message": "must not replace original"}, output)
    assert first.read_bytes() == original and not list(output.glob("*.tmp"))
