"""T-029/030/032: real paired Docker executions, explicitly mocked remote model."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from peeky.benchmark import run_pair
from peeky.cli import main
from peeky.providers.openai_compatible import BASE_URL, MODEL, ProviderConfig
from peeky.repair import FrozenOracle, load_record

pytestmark = [pytest.mark.docker, pytest.mark.integration]


def test_T029_T030_T032_native_tool_pair_has_independent_fresh_runtime_outcomes(
    tmp_path: Path,
) -> None:
    repo = Path("tests/fixtures/good_repo").resolve()
    audit = tmp_path / "audit"
    assert main(["audit", str(repo), "--approve", "--output", str(audit)]) == 0
    requests: list[dict[str, Any]] = []

    def model(request: Any, *args: Any) -> bytes:
        body = json.loads(request.data)
        requests.append(body)
        assert len(body["messages"]) == 2, "Each arm must start with a fresh conversation"
        return json.dumps(
            {
                "model": MODEL,
                "id": "synthetic-model-real-docker",
                "usage": {"total_tokens": 10},
                "choices": [
                    {
                        "finish_reason": "tool_calls",
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "type": "function",
                                    "id": "1",
                                    "function": {
                                        "name": "run_smoke",
                                        "arguments": '{"command_id":"step-001"}',
                                    },
                                }
                            ],
                        },
                    }
                ],
            }
        ).encode()

    path = run_pair(
        repo,
        next(audit.glob("*.json")),
        FrozenOracle("python smoke.py", "HELLO_FROM_GOOD_FIXTURE"),
        ProviderConfig(BASE_URL, MODEL, "synthetic-key"),
        tmp_path / "pair",
        consent=True,
        approve=True,
        transport=model,
    )
    record = load_record(path)
    before, after = record["trials"]
    assert before["controls_sha256"] == after["controls_sha256"]
    assert before["outcome"] == after["outcome"] == "PASS"
    assert record["summary"]["comparable_pairs"] == 1
    bp = before["executions"][0]["result"]["provenance"]
    ap = after["executions"][0]["result"]["provenance"]
    assert bp["container_id"] != ap["container_id"] and bp["image_id"] == ap["image_id"]
    assert bp["cleanup_verified"] and ap["cleanup_verified"]
    assert (
        requests[0]["model"] == requests[1]["model"]
        and requests[0]["tools"] == requests[1]["tools"]
    )
