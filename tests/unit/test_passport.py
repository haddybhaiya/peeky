import json
from collections.abc import Callable
from pathlib import Path

import pytest

from peeky.passport import PassportError, make_passport

pytestmark = pytest.mark.unit


def test_T008_passport_requires_matching_committed_source(repo: Path, evidence_file: Path) -> None:
    assert "python smoke.py" in make_passport(repo, evidence_file)
    (repo / "smoke.py").write_bytes(b"changed source\n")
    with pytest.raises(PassportError):
        make_passport(repo, evidence_file)


def test_T008_new_commit_invalidates_passport(
    repo: Path, evidence_file: Path, git: Callable[..., bytes]
) -> None:
    git(repo, "commit", "--allow-empty", "-qm", "different revision same bytes")
    with pytest.raises(PassportError, match="revision"):
        make_passport(repo, evidence_file)


def test_T008_readme_mutation_invalidates_passport(repo: Path, evidence_file: Path) -> None:
    (repo / "README.md").write_bytes(b"# changed\n")
    with pytest.raises(PassportError):
        make_passport(repo, evidence_file)


@pytest.mark.parametrize(
    "change",
    [
        "verdict",
        "schema",
        "policy",
        "result",
        "exit_code",
        "steps",
        "state",
        "source",
        "history",
        "execution",
    ],
)
def test_inconsistent_evidence_never_creates_passport(
    repo: Path, evidence_file: Path, change: str
) -> None:
    payload = json.loads(evidence_file.read_text(encoding="utf-8"))
    if change == "verdict":
        payload["verdict"] = "FAIL"
    elif change == "schema":
        payload["schema_version"] = "1.0"
    elif change == "policy":
        payload["policy"]["max_commands"] = 500
    elif change == "result":
        payload["results"][0]["command"] = "python unrelated.py"
    elif change == "exit_code":
        payload["results"][0]["exit_code"] = 1
    elif change == "steps":
        payload["steps"][0]["command"] = "python unexecuted.py"
    elif change == "state":
        payload["run"]["state"] = "APPROVED"
    elif change == "source":
        payload["source"]["source_sha256"] = "sha256:tampered"
    elif change == "execution":
        payload["execution"] = "model-said-so"
    else:
        payload["run"]["history"] = ["CREATED", "FINALIZED"]
    evidence_file.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(PassportError):
        make_passport(repo, evidence_file)
