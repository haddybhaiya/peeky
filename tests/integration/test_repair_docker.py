"""T-022: real baseline/candidate containers, with an explicitly mocked model only."""

from __future__ import annotations

import difflib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from peeky.evidence import write_report
from peeky.providers.openai_compatible import BASE_URL, MODEL, ProviderConfig
from peeky.repair import FrozenOracle, RepairError, diagnose, load_record, recheck, run_snapshot
from peeky.sources import snapshot

pytestmark = [pytest.mark.integration, pytest.mark.docker]


@pytest.mark.parametrize(
    "marker,expected", [("PEEKY_RECHECK_OK", "VERIFIED"), ("MARKER_NEVER_EMITTED", "INCONCLUSIVE")]
)
def test_T022_real_fresh_recheck_requires_frozen_oracle(
    repo: Path, git: Callable[..., bytes], tmp_path: Path, marker: str, expected: str
) -> None:
    original = "# Repair fixture\n\n```bash peeky\npython outdated.py\n```\n"
    (repo / "README.md").write_bytes(original.encode())
    script = b"assert sum((2, 3)) == 5\nprint('PEEKY_RECHECK_OK')\n"
    (repo / "smoke.py").write_bytes(script)
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "reviewed outdated-command fixture")
    with snapshot(repo) as captured:
        baseline = run_snapshot(captured)
    assert baseline["verdict"] == "FAIL", "Real baseline Docker execution must fail"
    evidence = write_report(baseline, tmp_path / "audit")
    patch = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            original.replace("python outdated.py", "python smoke.py").splitlines(keepends=True),
            fromfile="a/README.md",
            tofile="b/README.md",
        )
    )

    def mock_model(*args: Any) -> bytes:
        return json.dumps(
            {
                "id": "synthetic-model-real-docker",
                "model": MODEL,
                "usage": {"prompt_tokens": 10, "completion_tokens": 10},
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": json.dumps(
                                {
                                    "reason": "Outdated README command",
                                    "assumptions": [],
                                    "candidate_diff": patch,
                                    "confidence": 0.7,
                                    "source_refs": ["README.md"],
                                }
                            )
                        },
                    }
                ],
            }
        ).encode()

    state = tmp_path / "attempts"
    proposal_path = diagnose(
        repo,
        evidence,
        FrozenOracle("python smoke.py", marker),
        ProviderConfig(BASE_URL, MODEL, "synthetic-offline-key"),
        tmp_path / "proposals",
        state,
        consent=True,
        transport=mock_model,
    )
    proposal = load_record(proposal_path)
    assert proposal["status"] == "PROPOSED"
    with pytest.raises(RepairError, match="budget"):
        diagnose(
            repo,
            evidence,
            FrozenOracle("python smoke.py", marker),
            ProviderConfig(BASE_URL, MODEL, "synthetic-offline-key"),
            tmp_path / "proposals",
            state,
            consent=True,
            transport=mock_model,
        )
    # A real source revision change invalidates the approved proposal before another container.
    old_head = git(repo, "rev-parse", "HEAD").decode().strip()
    git(repo, "commit", "--allow-empty", "-qm", "new source revision")
    with pytest.raises(RepairError, match="Source revision"):
        recheck(repo, proposal_path, proposal["approval_digest"], tmp_path / "rechecks", state)
    git(repo, "update-ref", "HEAD", old_head)  # Synthetic fixture only; byte/index state unchanged.
    output = recheck(repo, proposal_path, proposal["approval_digest"], tmp_path / "rechecks", state)
    result = load_record(output)
    assert result["status"] == expected
    assert result["oracle_matched"] is (expected == "VERIFIED")
    before, after = result["baseline"], result["candidate"]
    assert before["verdict"] == "FAIL" and after["verdict"] == "PASS"
    bp, ap = before["results"][0]["provenance"], after["results"][0]["provenance"]
    assert bp["container_id"] != ap["container_id"]
    assert bp["image_id"] == ap["image_id"]
    assert bp["cleanup_verified"] and ap["cleanup_verified"]
    assert (repo / "smoke.py").read_bytes() == script
    assert (repo / "README.md").read_bytes() == original.encode()
    with pytest.raises(RepairError, match="budget"):
        recheck(repo, proposal_path, proposal["approval_digest"], tmp_path / "rechecks", state)
