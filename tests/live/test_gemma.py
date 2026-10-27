"""T-023: inspect retained evidence of the separately authorized live request; never retry it."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from peeky.provenance import DEFAULT_KEY_FILE
from peeky.providers.openai_compatible import MODEL
from peeky.repair import load_record

HOST_KEY_FILE = DEFAULT_KEY_FILE
pytestmark = pytest.mark.live


def test_T023_authorized_gemma_trace_records_model_version_usage_and_cost(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = os.environ.get("PEEKY_LIVE_EVIDENCE")
    assert evidence, "Run the separately authorized scripts/validate_phase3.py --live first"
    monkeypatch.setattr("peeky.provenance.DEFAULT_KEY_FILE", HOST_KEY_FILE)
    record = load_record(Path(evidence))
    trace = record["provider_trace"]
    assert trace["status"] == "PROPOSED", trace.get("error", "Missing real completion")
    assert record["status"] == "PROPOSED", record.get("error", "Rejected real proposal")
    assert trace["requested_model"] == MODEL
    assert trace["observed_model"] in (MODEL, "models/" + MODEL)
    assert trace["model_family"] == "gemma" and trace["byok"] is True
    assert trace["model_version"] and trace["checkpoint"] and trace["request_id"]
    if trace["usage_status"] == "reported":
        assert trace["usage"]["prompt_tokens"] > 0 and trace["usage"]["completion_tokens"] > 0
    else:
        assert trace["usage_status"] == "unknown" and trace["cost_usd"] is None
    assert trace["cost_usd"] in (None, "0") and trace["pricing_source"]
    assert trace["cost_basis"] in {"provider_reported", "published_free_tier"}
    assert trace["attempts"] == 1
