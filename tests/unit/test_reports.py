"""T-033: reporting never promotes incomplete or unauthenticated evidence."""

import hashlib
import json
from pathlib import Path

import pytest

from peeky.evidence import write_report
from peeky.passport import PassportError, make_passport
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


def test_url_summary_preserves_origin_after_capture_is_gone(
    evidence_file: Path, repo: Path, tmp_path: Path
) -> None:
    data = load_record(evidence_file)
    # Reuse a synthetic authenticated result to test serialization, not execution.
    data["repo"] = "https://github.com/fixture/project"
    data["remote"] = {
        "url": data["repo"],
        "requested_ref": "main",
        "resolved_ref": "refs/heads/main",
        "git_commit": data["source"]["git_commit"],
    }
    record = write_report(data, tmp_path / "url-evidence")
    summary = load_record(export_summary([record], tmp_path / "url-summary"))
    assert summary["records"][0]["remote"] == data["remote"]
    markdown = (tmp_path / "url-summary/summary.md").read_text()
    assert data["repo"] in markdown and "refs/heads/main" in markdown
    with pytest.raises(PassportError, match="URL passports"):
        make_passport(repo, record)


@pytest.mark.parametrize("mismatch", ["commit", "repository", "ref"])
def test_url_summary_rejects_inconsistent_origin(
    evidence_file: Path, tmp_path: Path, mismatch: str
) -> None:
    data = load_record(evidence_file)
    data["repo"] = "https://github.com/fixture/project"
    data["remote"] = {
        "url": data["repo"],
        "requested_ref": "main",
        "resolved_ref": "refs/heads/main",
        "git_commit": data["source"]["git_commit"],
    }
    if mismatch == "commit":
        data["remote"]["git_commit"] = "0" * 40
    elif mismatch == "repository":
        data["repo"] = "https://github.com/fixture/other"
    else:
        data["remote"]["resolved_ref"] = "refs/heads/other"
    record = write_report(data, tmp_path / "bad-origin")
    with pytest.raises(ValueError):
        export_summary([record], tmp_path / "bad-summary")
    assert not (tmp_path / "bad-summary").exists()


@pytest.mark.parametrize("selector", ["short", "qualified", "default"])
def test_redacted_ref_summary_preserves_labels_and_exact_revision(
    evidence_file: Path, tmp_path: Path, selector: str
) -> None:
    data = load_record(evidence_file)  # Synthetic result: serialization, not execution evidence.
    data["repo"] = "https://github.com/fixture/project"
    requested = {"short": "api_key=demo", "qualified": "refs/heads/api_key=demo", "default": None}[
        selector
    ]
    data["remote"] = {
        "url": data["repo"],
        "requested_ref": requested,
        "resolved_ref": "refs/heads/api_key=demo",
        "git_commit": data["source"]["git_commit"],
    }
    artifact = write_report(data, tmp_path / "redacted-input")
    saved = load_record(artifact)
    assert "api_key=demo" not in artifact.read_text()
    assert saved["remote"]["resolved_ref"] == "refs/heads/api_key=[REDACTED]"
    # This is the existing stored shape: no migration or unredacted copy is needed.
    assert set(saved["remote"]) == {"url", "requested_ref", "resolved_ref", "git_commit"}
    summary = load_record(export_summary([artifact], tmp_path / "redacted-summary"))
    row = summary["records"][0]
    assert row["remote"] == saved["remote"]
    assert row["git_commit"] == saved["source"]["git_commit"]
    assert row["remote_ref_status"] == "redacted-display-only"
    markdown = (tmp_path / "redacted-summary/summary.md").read_text()
    assert "api_key=demo" not in markdown
    assert "[REDACTED]" in markdown and "use git_commit" in markdown


def test_fully_redacted_ref_exports_without_original_secret_environment(
    evidence_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = load_record(evidence_file)
    ref = "refs/heads/confidential-name"
    data["repo"] = "https://github.com/fixture/project"
    data["remote"] = {
        "url": data["repo"],
        "requested_ref": ref,
        "resolved_ref": ref,
        "git_commit": data["source"]["git_commit"],
    }
    with monkeypatch.context() as configured:
        configured.setenv("PEEKY_TEST_API_KEY", ref)
        artifact = write_report(data, tmp_path / "secret-ref")
    saved = load_record(artifact)
    assert saved["remote"]["requested_ref"] == saved["remote"]["resolved_ref"] == "[REDACTED]"
    assert ref not in artifact.read_text()
    result = load_record(export_summary([artifact], tmp_path / "secret-ref-summary"))
    assert result["records"][0]["remote_ref_status"] == "redacted-display-only"


@pytest.mark.parametrize("mismatch", ["commit", "repository"])
def test_redacted_ref_does_not_relax_signed_identity_checks(
    evidence_file: Path, tmp_path: Path, mismatch: str
) -> None:
    data = load_record(evidence_file)
    data["repo"] = "https://github.com/fixture/project"
    data["remote"] = {
        "url": data["repo"],
        "requested_ref": "api_key=demo",
        "resolved_ref": "refs/heads/api_key=demo",
        "git_commit": data["source"]["git_commit"],
    }
    if mismatch == "commit":
        data["remote"]["git_commit"] = "0" * 40
    else:
        data["repo"] = "https://github.com/fixture/other"
    artifact = write_report(data, tmp_path / "bad-redacted-origin")
    with pytest.raises(ValueError):
        export_summary([artifact], tmp_path / "bad-redacted-summary")


def test_redacted_ref_tampering_still_fails_authentication(
    evidence_file: Path, tmp_path: Path
) -> None:
    data = load_record(evidence_file)
    data["repo"] = "https://github.com/fixture/project"
    data["remote"] = {
        "url": data["repo"],
        "requested_ref": "api_key=demo",
        "resolved_ref": "refs/heads/api_key=demo",
        "git_commit": data["source"]["git_commit"],
    }
    artifact = write_report(data, tmp_path / "tampered-redacted-origin")
    saved = load_record(artifact)
    saved["remote"]["requested_ref"] = "other=[REDACTED]"
    artifact.write_text(json.dumps(saved))
    with pytest.raises(ValueError, match="integrity"):
        export_summary([artifact], tmp_path / "tampered-redacted-summary")
