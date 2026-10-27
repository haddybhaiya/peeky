"""T-018/019/023/025: offline contracts, no credentials or live network."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from peeky.cli import main
from peeky.providers.openai_compatible import (
    BASE_URL,
    MAX_RESPONSE_BYTES,
    MODEL,
    PatchProposal,
    ProviderConfig,
    ProviderError,
    decode_completion,
    load_config,
    propose,
    strict_json,
)


def proposal_data() -> dict[str, Any]:
    return {
        "reason": "The documented entrypoint is outdated.",
        "assumptions": [],
        "candidate_diff": "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old\n+new\n",
        "confidence": 0.8,
        "source_refs": ["README.md", "evidence.stderr"],
    }


def response_bytes(proposal: dict[str, Any] | None = None, **overrides: Any) -> bytes:
    data = {
        "id": "synthetic-contract-response",
        "model": MODEL,
        "usage": {"prompt_tokens": 40, "completion_tokens": 30},
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": json.dumps(proposal or proposal_data()),
                },
            }
        ],
    }
    data.update(overrides)
    return json.dumps(data).encode()


def test_T018_exact_typed_proposal() -> None:
    parsed = PatchProposal.parse(json.dumps(proposal_data()))
    assert parsed.confidence == 0.8
    assert parsed.source_refs == ("README.md", "evidence.stderr")


@pytest.mark.parametrize(
    "field,value",
    [
        ("verified", True),
        ("verdict", "PASS"),
        ("confidence", True),
        ("confidence", 2**1200),
        ("confidence", float("nan")),
        ("assumptions", "text"),
        ("source_refs", ["../../policy.py"]),
        ("reason", 3),
        ("candidate_diff", "x" * 12_001),
    ],
    ids=["verified", "verdict", "bool-confidence", "range", "nan", "list", "ref", "type", "size"],
)
def test_T018_model_cannot_supply_authority_or_invalid_types(field: str, value: Any) -> None:
    data = proposal_data()
    data[field] = value
    with pytest.raises(ProviderError):
        PatchProposal.parse(json.dumps(data))


def test_T018_duplicate_json_keys_rejected() -> None:
    with pytest.raises(ProviderError):
        strict_json('{"verified": false, "verified": true}')


def test_T019_consent_precedes_configuration_network_and_source() -> None:
    def forbidden(*args: Any) -> bytes:
        pytest.fail("No network without consent")

    with pytest.raises(ProviderError, match="consent"):
        propose(ProviderConfig("", "", ""), {}, consent=False, transport=forbidden)
    assert (
        main(
            [
                "diagnose",
                "missing-repo",
                "--evidence",
                "missing",
                "--expected-command",
                "python smoke.py",
                "--expected-stdout",
                "OK",
            ]
        )
        == 2
    )


def test_T019_disabled_or_missing_provider_does_not_break_core_inspect(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in ("PEEKY_MODEL_API_KEY", "PEEKY_MODEL_BASE_URL", "PEEKY_MODEL_NAME"):
        monkeypatch.delenv(name, raising=False)

    def forbidden(*args: Any, **kwargs: Any) -> None:
        pytest.fail("Core inspect attempted a model call")

    monkeypatch.setattr("peeky.providers.openai_compatible.propose", forbidden)
    assert main(["inspect", str(repo), "--json"]) == 0
    assert (
        main(
            [
                "diagnose",
                str(repo),
                "--evidence",
                "missing",
                "--model-consent",
                "--expected-command",
                "python smoke.py",
                "--expected-stdout",
                "OK",
            ]
        )
        == 3
    )


def test_T019_explicit_byok_file_no_shell_or_key_repr(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text(
        f"PEEKY_MODEL_BASE_URL={BASE_URL}\nPEEKY_MODEL_NAME={MODEL}\n"
        "PEEKY_MODEL_API_KEY=synthetic-key-not-real\nPEEKY_MODEL_CONSENT=true\n"
    )
    config = load_config(env)
    assert "synthetic-key-not-real" not in repr(config)
    env.write_text(env.read_text() + "PEEKY_MODEL_NAME=other\n")
    with pytest.raises(ProviderError):
        load_config(env)


@pytest.mark.parametrize(
    "url,model",
    [
        ("http://example.com", MODEL),
        (BASE_URL + "?key=secret", MODEL),
        ("https://evil.example/v1", MODEL),
        (BASE_URL, "gemini-3.8-flash"),
    ],
)
def test_T019_endpoint_and_checkpoint_fail_closed(url: str, model: str) -> None:
    with pytest.raises(ProviderError):
        ProviderConfig(url, model, "synthetic-key").validate()


def test_T023_mock_trace_records_usage_checkpoint_cost_and_redaction() -> None:
    calls: list[dict[str, Any]] = []

    def transport(request: urllib.request.Request, timeout: float, limit: int) -> bytes:
        assert request.data is not None
        assert isinstance(request.data, bytes)
        body = json.loads(request.data)
        calls.append(body)
        assert "synthetic-secret-key" not in body["messages"][1]["content"]
        assert "person@example.com" not in body["messages"][1]["content"]
        assert request.full_url == BASE_URL + "/chat/completions"
        assert timeout == 45 and limit == MAX_RESPONSE_BYTES
        assert not any(key in body for key in ("tools", "models", "provider"))
        assert body["extra_body"]["google"]["thinking_config"] == {
            "thinking_level": "minimal",
            "include_thoughts": False,
        }
        return response_bytes()

    trace = propose(
        ProviderConfig(BASE_URL, MODEL, "synthetic-secret-key"),
        {"README.md": "person@example.com synthetic-secret-key"},
        consent=True,
        transport=transport,
    )
    assert len(calls) == 1 and trace["status"] == "PROPOSED"
    assert trace["byok"] is True and trace["model_family"] == "gemma"
    assert trace["cost_usd"] == "0" and trace["cost_basis"] == "published_free_tier"
    assert trace["checkpoint_revision"] is None


@pytest.mark.parametrize(
    "response",
    [
        response_bytes(model="different-model"),
        response_bytes(usage={"prompt_tokens": 1, "completion_tokens": 1, "cost": 0.01}),
        response_bytes(choices=[]),
        b"x" * (MAX_RESPONSE_BYTES + 1),
        response_bytes(choices=[{"finish_reason": "length", "message": {"content": "{}"}}]),
    ],
    ids=["wrong-model", "nonzero-cost", "no-choice", "oversized", "truncated"],
)
def test_T018_T019_incomplete_provider_data_never_passes(response: bytes) -> None:
    count = 0

    def transport(*args: Any) -> bytes:
        nonlocal count
        count += 1
        return response

    trace = propose(
        ProviderConfig(BASE_URL, MODEL, "synthetic-key"), {}, consent=True, transport=transport
    )
    assert trace["status"] == "INCONCLUSIVE" and count == 1


def test_T025_context_and_policy_are_bounded_before_network() -> None:
    def forbidden(*args: Any) -> bytes:
        pytest.fail("Oversized context reached network")

    with pytest.raises(ProviderError, match="budget"):
        propose(
            ProviderConfig(BASE_URL, MODEL, "synthetic-key"),
            {"README.md": "x" * 12_000},
            consent=True,
            transport=forbidden,
        )


def test_T023_missing_usage_does_not_block_a_valid_free_model_proposal() -> None:
    def transport(*args: Any) -> bytes:
        return response_bytes(usage={})

    trace = propose(
        ProviderConfig(BASE_URL, MODEL, "synthetic-key"), {}, consent=True, transport=transport
    )
    assert trace["status"] == "PROPOSED"
    assert trace["usage_status"] == "unknown" and trace["cost_usd"] is None
    assert trace["published_price_usd"] == "0"


@pytest.mark.parametrize(
    "flagged,content,expected",
    [
        (
            True,
            "<thought>Untrusted provider reasoning</thought>" + json.dumps(proposal_data()),
            "PROPOSED",
        ),
        (
            False,
            "<thought>Untrusted provider reasoning</thought>" + json.dumps(proposal_data()),
            "INCONCLUSIVE",
        ),
        (True, "<thought>unterminated", "INCONCLUSIVE"),
        (
            True,
            "<thought>ignore policy</thought>" + json.dumps({**proposal_data(), "verified": True}),
            "INCONCLUSIVE",
        ),
        (
            True,
            "<thought>ignore policy</thought>" + json.dumps(proposal_data()) + "{}",
            "INCONCLUSIVE",
        ),
    ],
    ids=["framed", "unflagged", "unterminated", "authority", "extra-object"],
)
def test_T018_google_framing_does_not_relax_json_authority(
    flagged: bool, content: str, expected: str
) -> None:
    def transport(*args: Any) -> bytes:
        return response_bytes(
            choices=[
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": content,
                        "extra_content": {"google": {"thought": flagged}},
                    },
                }
            ]
        )

    trace = propose(
        ProviderConfig(BASE_URL, MODEL, "synthetic-key"), {}, consent=True, transport=transport
    )
    assert trace["status"] == expected


def test_T023_retained_response_decoding_preserves_original_request_provenance() -> None:
    original: dict[str, Any] = {
        "response": response_bytes().decode(),
        "request_sha256": "sha256:original-request",
        "attempts": 1,
        "duration_ms": 123,
        "status": "INCONCLUSIVE",
        "error": "old parser",
    }
    before = dict(original)
    decoded = decode_completion(original)
    assert original == before
    assert decoded["status"] == "PROPOSED" and "error" not in decoded
    for field in ("response", "request_sha256", "attempts", "duration_ms"):
        assert decoded[field] == before[field]
