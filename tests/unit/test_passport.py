import json
from pathlib import Path

import pytest

from peeky.evidence import sha256_file
from peeky.passport import PassportError, make_passport


@pytest.mark.unit
def test_passport_rejects_failed_and_changed_evidence(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# demo", encoding="utf-8")
    evidence = tmp_path / "evidence.json"
    raw = {"schema_version": "1.0", "verdict": "FAIL", "repo": str(repo.resolve()),
           "readme_sha256": sha256_file(repo / "README.md"),
           "steps": [{"command": "python smoke.py"}], "results": [{"outcome": "PASS"}]}
    evidence.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(PassportError):
        make_passport(repo, evidence)
    raw["verdict"] = "PASS"
    evidence.write_text(json.dumps(raw), encoding="utf-8")
    assert "python smoke.py" in make_passport(repo, evidence)
    (repo / "README.md").write_text("# changed", encoding="utf-8")
    with pytest.raises(PassportError):
        make_passport(repo, evidence)
