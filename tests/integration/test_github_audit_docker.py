"""URL acquisition uses a local Git transport; target checks use genuine offline Docker."""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from peeky import cli, runner
from peeky.cli import main
from peeky.images import DEFAULT_IMAGE
from peeky.models import Step, StepResult
from peeky.provenance import verify
from peeky.repair import load_record
from peeky.runner import LABEL, doctor, inspect_image
from peeky.sources import SourceSnapshot, fingerprint

pytestmark = [pytest.mark.integration, pytest.mark.docker]
URL = "https://github.com/fixture/project"


@pytest.fixture(scope="session")
def url_docker() -> str:
    binary = shutil.which("docker")
    assert binary is not None, "URL Docker gate requires the Docker CLI"
    status = doctor()
    assert status["docker_daemon"] and status["linux"], "URL Docker gate requires Linux Docker"
    inspect_image(binary, DEFAULT_IMAGE)
    return binary


def assert_container_and_sources_removed(
    binary: str, record: dict[str, object], roots: list[Path], *, cleanup_verified: bool = True
) -> None:
    # Inspect the retained raw provenance, then independently query the daemon.
    results = record["results"]
    assert isinstance(results, list)
    provenance = results[0]["provenance"]
    assert provenance["cleanup_verified"] is cleanup_verified
    probe = subprocess.run(
        [binary, "ps", "--all", "--quiet", "--filter", f"label={LABEL}={provenance['run_id']}"],
        capture_output=True,
        text=True,
        check=True,
        timeout=8,
    )
    assert not probe.stdout.strip()
    for mount in provenance.get("docker_create_argv", []):
        if mount.startswith("type=bind,"):
            exported = Path(mount.split("source=", 1)[1].split(",target=", 1)[0])
            assert not exported.exists()
    assert roots and all(not root.exists() for root in roots)


@pytest.mark.parametrize("pinned", [False, True])
@pytest.mark.parametrize("target_code", [0, 7])
def test_url_audit_real_pass_fail_and_durable_evidence(
    repo: Path,
    git: Callable[..., bytes],
    local_transport: list[Path],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    url_docker: str,
    pinned: bool,
    target_code: int,
) -> None:
    # UID and source metadata assertions also make accidental host execution fail.
    script = (
        "import os\n"
        "assert os.getuid() == 65534\n"
        "assert not os.path.exists('/repo/.git')\n"
        "assert not os.environ.get('HTTPS_PROXY')\n"
        "assert not os.environ.get('INSTABOX_API_KEY')\n"
        "print('PEEKY_URL_AUDIT_EXECUTED')\n"
        f"raise SystemExit({target_code})\n"
    )
    (repo / "smoke.py").write_text(script)
    git(repo, "add", "smoke.py")
    git(repo, "commit", "-qm", "reviewed URL Docker fixture")
    expected = fingerprint(repo)
    ref_args = ["--ref", expected.git_commit] if pinned else []
    assert main(["inspect", URL, *ref_args, "--json"]) == 0
    plan = json.loads(capsys.readouterr().out)
    output = tmp_path / "url-audit"
    assert main(["audit", URL, *ref_args, "--approve", "--output", str(output)]) == (
        0 if target_code == 0 else 1
    )
    artifact = next(output.glob("*.json"))
    record = load_record(artifact)
    verify(record)
    assert record["repo"] == URL
    assert record["remote"] == plan["remote"]
    assert record["source"] == plan["source"]
    assert record["run"]["plan_sha256"] == plan["run"]["plan_sha256"]
    assert record["source"]["git_commit"] == expected.git_commit
    assert record["verdict"] == ("PASS" if target_code == 0 else "FAIL")
    assert record["results"][0]["exit_code"] == target_code
    assert "PEEKY_URL_AUDIT_EXECUTED" in record["results"][0]["stdout"]
    assert_container_and_sources_removed(url_docker, record, local_transport)
    summary_dir = tmp_path / "summary"
    assert main(["report", "--evidence", str(artifact), "--output", str(summary_dir)]) == 0
    summary = load_record(next((summary_dir / "records").glob("*.json")))
    assert summary["records"][0]["remote"] == record["remote"]
    assert summary["records"][0]["outcome"] == record["verdict"]
    assert "peeky-source-" not in json.dumps(summary)


def test_url_timeout_is_not_a_target_failure(
    repo: Path,
    git: Callable[..., bytes],
    local_transport: list[Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    url_docker: str,
) -> None:
    (repo / "smoke.py").write_text("import time\ntime.sleep(60)\n")
    git(repo, "add", "smoke.py")
    git(repo, "commit", "-qm", "URL timeout fixture")

    def shorter_deadline(
        step: Step, source: SourceSnapshot, image: str, timeout: float
    ) -> StepResult:
        # Exercise the real runner with a lower permitted deadline, not a fake outcome.
        return runner.execute(step, source, image, timeout=0.5)

    monkeypatch.setattr(cli, "execute", shorter_deadline)
    output = tmp_path / "timeout"
    assert main(["audit", URL, "--approve", "--output", str(output)]) == 3
    record = load_record(next(output.glob("*.json")))
    assert record["verdict"] == "INCONCLUSIVE"
    assert record["results"][0]["outcome"] == "TIMEOUT"
    assert record["results"][0]["reason"] == "COMMAND_TIMEOUT"
    assert_container_and_sources_removed(url_docker, record, local_transport)


def test_url_cleanup_acknowledgement_failure_cannot_pass(
    repo: Path,
    git: Callable[..., bytes],
    local_transport: list[Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    url_docker: str,
) -> None:
    (repo / "smoke.py").write_text("print('URL_CLEANUP_FIXTURE')\n")
    git(repo, "add", "smoke.py")
    git(repo, "commit", "-qm", "URL cleanup fixture")
    original = runner._cleanup

    def uncertain(binary: str, name: str, run_id: str) -> bool:
        # Remove the actual owned container, then simulate a lost cleanup acknowledgement.
        assert original(binary, name, run_id)
        return False

    monkeypatch.setattr(runner, "_cleanup", uncertain)
    output = tmp_path / "cleanup"
    assert main(["audit", URL, "--approve", "--output", str(output)]) == 3
    record = load_record(next(output.glob("*.json")))
    assert record["verdict"] == "INCONCLUSIVE"
    assert record["results"][0]["reason"] == "CLEANUP_UNVERIFIED"
    assert_container_and_sources_removed(
        url_docker, record, local_transport, cleanup_verified=False
    )


def test_url_daemon_loss_after_preflight_cannot_run_on_host(
    local_transport: list[Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, url_docker: str
) -> None:
    output = tmp_path / "daemon-loss"
    with monkeypatch.context() as changed:
        # Preflight succeeds, but the real runner subsequently sees an unreachable daemon.
        changed.setattr(cli, "doctor", lambda **kwargs: {"docker_daemon": True, "linux": True})
        changed.delenv("DOCKER_CONTEXT", raising=False)
        changed.setenv("DOCKER_HOST", "tcp://127.0.0.1:1")
        assert main(["audit", URL, "--approve", "--output", str(output)]) == 3
    record = load_record(next(output.glob("*.json")))
    provenance = record["results"][0]["provenance"]
    assert record["verdict"] == "INCONCLUSIVE"
    assert record["results"][0]["reason"] == "DOCKER_UNAVAILABLE"
    assert provenance["target_started"] is False
    assert_container_and_sources_removed(url_docker, record, local_transport)


@pytest.mark.parametrize("selector", ["branch", "tag"])
def test_successful_url_audit_with_secret_like_ref_still_exports(
    repo: Path,
    git: Callable[..., bytes],
    local_transport: list[Path],
    tmp_path: Path,
    url_docker: str,
    selector: str,
) -> None:
    (repo / "smoke.py").write_text(
        "import os\nassert os.getuid() == 65534\nprint('REDACTED_REF_SMOKE_OK')\n"
    )
    git(repo, "add", "smoke.py")
    git(repo, "commit", "-qm", "reviewed ref redaction Docker fixture")
    expected = fingerprint(repo)
    ref = "api_key=demo"
    if selector == "tag":
        git(repo, "tag", "-a", ref, "-m", "redaction Docker tag")
    else:
        git(repo, "branch", ref)
    output = tmp_path / "successful-redacted-ref"
    assert main(["audit", URL, "--ref", ref, "--approve", "--output", str(output)]) == 0
    artifact = next(output.glob("*.json"))
    record = load_record(artifact)
    assert record["verdict"] == "PASS"
    assert record["remote"]["git_commit"] == expected.git_commit
    assert record["remote"]["requested_ref"] == "api_key=[REDACTED]"
    assert ref not in artifact.read_text()
    assert "REDACTED_REF_SMOKE_OK" in record["results"][0]["stdout"]
    assert_container_and_sources_removed(url_docker, record, local_transport)
    summary_dir = tmp_path / "successful-redacted-summary"
    assert main(["report", "--evidence", str(artifact), "--output", str(summary_dir)]) == 0
    result = load_record(next((summary_dir / "records").glob("*.json")))["records"][0]
    assert result["outcome"] == "PASS" and result["git_commit"] == expected.git_commit
    assert result["remote_ref_status"] == "redacted-display-only"
