"""T-033: reporting never promotes incomplete or unauthenticated evidence."""

import hashlib
import json
from pathlib import Path

import pytest

from peeky.evidence import write_report
from peeky.repair import load_record
from peeky.reports import export_summary


def test_T033_incomplete_pass_is_inconclusive_and_bytes_are_bound(
    evidence_file: Path,
    tmp_path: Path,
) -> None:
    data = load_record(evidence_file)
    data["results"] = []
    incomplete = write_report(data, tmp_path / "input")
    path = export_summary([incomplete], tmp_path / "export")
    result = load_record(path)
    assert result["status"] == "SUMMARY_ONLY"
    assert result["records"][0]["outcome"] == "INCONCLUSIVE"
    markdown = (tmp_path / "export/summary.md").read_bytes()
    assert result["markdown_sha256"] == "sha256:" + hashlib.sha256(markdown).hexdigest()
    assert b"INCONCLUSIVE" in markdown
    assert "stdout" not in json.dumps(result)
    with pytest.raises(FileExistsError):
        export_summary([incomplete], tmp_path / "export")


def test_T033_tampered_record_is_rejected_before_export(
    evidence_file: Path,
    tmp_path: Path,
) -> None:
    data = json.loads(evidence_file.read_text())
    data["verdict"] = "INCONCLUSIVE"
    evidence_file.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="integrity"):
        export_summary([evidence_file], tmp_path / "export")
    assert not (tmp_path / "export").exists()


def test_T033_unknown_schema_is_not_invented(tmp_path: Path) -> None:
    record = write_report({"schema_version": "future-unknown"}, tmp_path / "input")
    with pytest.raises(ValueError, match="Unsupported"):
        export_summary([record], tmp_path / "export")
