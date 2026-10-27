"""Phase 4 controller contracts. Mock provider data never establishes a live outcome."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest

from peeky.benchmark import (
    BUDGET,
    dispatch_tool,
    render_report,
    run_trial,
    summarize,
    validate_tool,
    write_study,
)
from peeky.cli import main
from peeky.domain import DEFAULT_POLICY, canonical_hash
from peeky.passport import PassportError, make_passport, validate_passport_snapshot
from peeky.provenance import authenticate
from peeky.providers.openai_compatible import BASE_URL, MODEL, ProviderConfig
from peeky.sources import fingerprint, snapshot


def test_T026_passport_binds_exact_evidence_and_image(repo: Path, evidence_file: Path) -> None:
    text = make_passport(repo, evidence_file)
    with snapshot(repo) as source:
        certificate = validate_passport_snapshot(source, text)
    assert certificate["image_id"] == "sha256:" + "a" * 64
    assert certificate["evidence_sha256"] == canonical_hash(json.loads(evidence_file.read_text()))
    assert certificate["evidence_file_sha256"] and certificate["run_id"]


@pytest.mark.parametrize("field", ["command_sha256", "container_id", "image_id", "container_state"])
def test_T026_incomplete_runtime_provenance_is_denied(
    repo: Path, evidence_file: Path, field: str
) -> None:
    record = json.loads(evidence_file.read_text())
    record["results"][0]["provenance"].pop(field)
    evidence_file.write_text(json.dumps(authenticate(record)))
    with pytest.raises(PassportError):
        make_passport(repo, evidence_file)


def test_T027_guidance_tampering_and_source_change_invalidate_certificate(
    repo: Path, evidence_file: Path
) -> None:
    text = make_passport(repo, evidence_file)
    with snapshot(repo) as source:
        with pytest.raises(PassportError):
            validate_passport_snapshot(source, text.replace("python smoke.py", "python other.py"))
    (repo / "smoke.py").write_bytes(b"changed\n")
    with pytest.raises(ValueError):
        with snapshot(repo) as source:
            validate_passport_snapshot(source, text)


def test_T028_existing_agent_files_never_overwritten(
    repo: Path, evidence_file: Path, tmp_path: Path
) -> None:
    agents = tmp_path / "AGENTS.md"
    generated = tmp_path / "AGENTS.generated.md"
    agents.write_text("owner instructions")
    generated.write_text("previous generated artifact")
    assert (
        main(["passport", str(repo), "--evidence", str(evidence_file), "--output", str(agents)])
        == 3
    )
    assert (
        main(["passport", str(repo), "--evidence", str(evidence_file), "--output", str(generated)])
        == 3
    )
    assert (
        agents.read_text() == "owner instructions"
        and generated.read_text() == "previous generated artifact"
    )


def controls(repo: Path) -> dict[str, Any]:
    return {
        "source": asdict(fingerprint(repo)),
        "budget": asdict(BUDGET),
        "policy_sha256": DEFAULT_POLICY.sha256,
        "image_id": "sha256:" + "a" * 64,
        "oracle": {"expected_command": "python smoke.py", "stdout_line": "OK"},
    }


def response(message: dict[str, Any]) -> bytes:
    return json.dumps(
        {
            "model": MODEL,
            "id": "synthetic-tool-response",
            "usage": {"total_tokens": 10},
            "choices": [{"finish_reason": "stop", "message": message}],
        }
    ).encode()


def test_T029_text_only_success_claim_never_executes_or_passes(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: Any) -> None:
        pytest.fail("Text-only model output reached executor")

    monkeypatch.setattr("peeky.benchmark.dispatch_tool", forbidden)
    trial = run_trial(
        repo,
        "baseline",
        "",
        controls(repo),
        ProviderConfig(BASE_URL, MODEL, "fake-key"),
        transport=lambda *args: response(
            {"role": "assistant", "content": "PASS, verified, exit 0"}
        ),
    )
    assert trial["outcome"] == "INCONCLUSIVE" and trial["reason"] == "TEXT_ONLY_NO_EXECUTION"
    assert trial["executions"] == [] and len(trial["calls"]) == 1


@pytest.mark.parametrize(
    "name,args",
    [
        ("host_shell", {"command": "whoami"}),
        ("run_smoke", {"command_id": "step-001", "command": "python evil.py"}),
        ("run_smoke", {"command_id": "step-999"}),
        ("read_file", {"path": "../.env"}),
        ("read_file", {"path": ".git/config"}),
    ],
)
def test_T029_tools_cannot_expand_permissions(repo: Path, name: str, args: dict[str, Any]) -> None:
    with snapshot(repo) as source:
        with pytest.raises(ValueError):
            dispatch_tool(source, name, args)


def test_T031_native_tool_loop_is_bounded_and_uses_real_reads(repo: Path) -> None:
    count = 0

    def transport(*args: Any) -> bytes:
        nonlocal count
        count += 1
        return response(
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": str(count),
                        "type": "function",
                        "function": {"name": "read_file", "arguments": '{"path":"README.md"}'},
                    }
                ],
            }
        )

    trial = run_trial(
        repo,
        "baseline",
        "",
        controls(repo),
        ProviderConfig(BASE_URL, MODEL, "fake-key"),
        transport=transport,
    )
    assert count == BUDGET.model_calls == 2 and len(trial["tools"]) == 2
    assert trial["outcome"] == "INCONCLUSIVE" and trial["reason"] == "MODEL_CALL_BUDGET"
    assert trial["tools"][0]["result"]["content"].startswith("# Fixture")


def pair_rows(repo: Path) -> list[dict[str, Any]]:
    fixed = controls(repo)
    return [
        {
            "arm": arm,
            "controls": fixed,
            "controls_sha256": canonical_hash(fixed),
            "observed_source": fixed["source"],
            "outcome": outcome,
            "calls": [{"observed_model": MODEL, "usage": {"total_tokens": 10}}],
            "tools": [],
            "accounted_tokens": 10,
            "duration_ms": 1,
        }
        for arm, outcome in (("baseline", "INCONCLUSIVE"), ("passport", "PASS"))
    ]


@pytest.mark.parametrize("field", ["source", "budget", "image_id", "model", "task"])
def test_T030_condition_drift_prevents_comparison(repo: Path, field: str) -> None:
    rows = pair_rows(repo)
    rows[1]["controls"] = {**rows[1]["controls"], field: "changed"}
    rows[1]["controls_sha256"] = canonical_hash(rows[1]["controls"])
    report = summarize(rows)
    assert report["comparable_pairs"] == 0 and report["paired_success_difference"] is None
    assert report["attempted_trials"] == 2


def test_T032_negatives_and_missing_provider_stay_in_denominators(repo: Path) -> None:
    rows = pair_rows(repo)
    rows[0]["calls"] = [{"status": "INCONCLUSIVE", "error": "provider unavailable"}]
    report = summarize(rows)
    assert report["attempted_pairs"] == 1 and report["comparable_pairs"] == 0
    assert report["rows"][0]["INCONCLUSIVE"] == 1 and report["rows"][0]["attempted"] == 1
    assert report["rows"][1]["PASS"] == 1 and report["rows"][1]["attempted"] == 1
    assert report["rows"][0]["reported_tokens"] is None
    assert "0/1" in render_report(report) and "1/1" in render_report(report)


def test_T029_native_tool_schema_rejects_duplicate_argument_keys() -> None:
    with pytest.raises(ValueError):
        validate_tool(
            {
                "tool_calls": [
                    {
                        "type": "function",
                        "id": "1",
                        "function": {
                            "name": "run_smoke",
                            "arguments": '{"command_id":"step-001","command_id":"other"}',
                        },
                    }
                ]
            }
        )


def test_T032_study_retains_all_pairs_and_authenticates_report(repo: Path, tmp_path: Path) -> None:
    import hashlib

    from peeky.evidence import write_report
    from peeky.repair import load_record

    rows = pair_rows(repo)
    rows[0]["calls"] = [{"error": "HTTP 500"}]
    data: dict[str, Any] = {
        "schema_version": "onboarding-pair-1",
        "controls": rows[0]["controls"],
        "trials": rows,
    }
    paths = [write_report(data, tmp_path / "pairs") for _ in range(2)]
    path = write_study(paths, tmp_path / "study")
    record = load_record(path)
    summary = record["summary"]
    assert summary["attempted_pairs"] == 2 and summary["attempted_trials"] == 4
    assert summary["comparable_pairs"] == 0
    assert summary["rows"][0]["INCONCLUSIVE"] == 2 and summary["rows"][1]["PASS"] == 2
    markdown = (tmp_path / "study/paired-report.md").read_bytes()
    assert record["report_sha256"] == "sha256:" + hashlib.sha256(markdown).hexdigest()
