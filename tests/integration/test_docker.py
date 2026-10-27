"""Real offline Docker gates. Selected Docker tests fail rather than skip prerequisites."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from peeky.cli import main
from peeky.domain import DEFAULT_POLICY, RunRecord, RunState
from peeky.evidence import report, write_report
from peeky.images import DEFAULT_IMAGE
from peeky.models import StepResult
from peeky.parser import read_steps
from peeky.provenance import verify
from peeky.runner import LABEL, InfrastructureError, doctor, execute, inspect_image
from peeky.sources import snapshot

pytestmark = [pytest.mark.integration, pytest.mark.docker]


@pytest.fixture(scope="session")
def docker_binary() -> str:
    binary = shutil.which("docker")
    assert binary is not None, "Docker gate requires Docker CLI"
    status = doctor()
    assert status["docker_daemon"] and status["linux"], (
        "Docker gate requires a running Linux daemon"
    )
    inspect_image(binary, DEFAULT_IMAGE)  # Never pull during target execution/tests.
    return binary


@pytest.fixture(autouse=True)
def require_docker(docker_binary: str) -> None:
    pass


@pytest.fixture
def script_repo(repo: Path, git: Callable[..., bytes]) -> Callable[[str, str], Path]:
    def prepare(script: str, command: str = "python smoke.py") -> Path:
        (repo / "smoke.py").write_bytes(script.encode())
        (repo / "README.md").write_bytes(
            f"# Docker fixture\n\n```bash peeky\n{command}\n```\n".encode()
        )
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "reviewed Docker fixture")
        return repo

    return prepare


def run_fixture(path: Path, timeout: float = 20) -> StepResult:
    with snapshot(path) as captured:
        return execute(read_steps(captured.path)[0], captured, DEFAULT_IMAGE, timeout=timeout)


def assert_removed(binary: str, result: StepResult) -> None:
    assert result.provenance["cleanup_verified"] is True
    probe = subprocess.run(
        [
            binary,
            "ps",
            "--all",
            "--quiet",
            "--filter",
            f"label={LABEL}={result.provenance['run_id']}",
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=8,
    )
    assert probe.stdout.strip() == ""


def test_T009_real_good_fixture(docker_binary: str) -> None:
    result = run_fixture(Path("tests/fixtures/good_repo"))
    assert result.outcome == "PASS", result.dict()
    assert "HELLO_FROM_GOOD_FIXTURE" in result.stdout
    assert result.exit_code == 0
    assert_removed(docker_binary, result)


def test_T010_real_bad_fixture(docker_binary: str) -> None:
    result = run_fixture(Path("tests/fixtures/bad_repo"))
    assert result.outcome == "FAIL", result.dict()
    assert result.reason == "COMMAND_EXIT_NONZERO" and result.exit_code != 0
    assert "missing_onboarding_entrypoint" in result.stderr
    assert_removed(docker_binary, result)


@pytest.mark.parametrize("code", [125, 126, 127])
def test_T010_target_reserved_exit_codes_are_failures(
    script_repo: Callable[[str, str], Path], docker_binary: str, code: int
) -> None:
    result = run_fixture(script_repo(f"raise SystemExit({code})\n", "python smoke.py"))
    assert result.outcome == "FAIL" and result.exit_code == code, result.dict()
    assert result.provenance["target_started"] is True
    assert_removed(docker_binary, result)


def test_T011_real_missing_image_is_infrastructure(docker_binary: str) -> None:
    with pytest.raises(InfrastructureError) as caught:
        inspect_image(docker_binary, "python@sha256:" + "0" * 64)
    assert caught.value.reason == "IMAGE_UNAVAILABLE"


def test_T011_unreachable_daemon_never_executes(
    script_repo: Callable[[str, str], Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = script_repo("print('must not run')\n", "python smoke.py")
    monkeypatch.delenv("DOCKER_CONTEXT", raising=False)
    monkeypatch.setenv("DOCKER_HOST", "tcp://127.0.0.1:1")
    result = run_fixture(root)
    assert result.outcome == "INCONCLUSIVE" and result.reason == "DOCKER_UNAVAILABLE"
    assert result.provenance["target_started"] is False and result.stdout == ""


def test_T011_missing_executable_is_not_target_failure(
    script_repo: Callable[[str, str], Path],
    docker_binary: str,
) -> None:
    result = run_fixture(script_repo("# not executed\n", "pytest --version"))
    assert result.outcome == "INCONCLUSIVE" and result.reason == "COMMAND_NOT_STARTED", (
        result.dict()
    )
    assert result.provenance["target_started"] is False
    assert_removed(docker_binary, result)


def test_T012_timeout_kills_and_removes_container(
    script_repo: Callable[[str, str], Path],
    docker_binary: str,
) -> None:
    root = script_repo(
        "import time\nprint('before sleep', flush=True)\ntime.sleep(30)\n", "python smoke.py"
    )
    result = run_fixture(root, timeout=2)
    assert result.outcome == "TIMEOUT" and result.reason == "COMMAND_TIMEOUT", result.dict()
    assert result.exit_code is None
    assert result.provenance["target_started"] is True
    assert_removed(docker_binary, result)


def test_T013_T014_real_filesystem_network_identity_and_kernel_budgets(
    script_repo: Callable[[str, str], Path],
    docker_binary: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PEEKY_SYNTHETIC_HOST_TOKEN", "NEVER_PASS_THIS_TO_CONTAINER")
    monkeypatch.setenv("HTTP_PROXY", "http://user:synthetic-proxy-secret@example.invalid")
    script = """import errno
import json
import os
from pathlib import Path
import socket
for name in ('/repo/forbidden', '/etc/forbidden'):
    try:
        Path(name).write_text('forbidden')
    except OSError as exc:
        assert exc.errno in (errno.EROFS, errno.EACCES, errno.EPERM)
    else:
        raise AssertionError('filesystem was writable')
assert os.getuid() == 65534
assert 'PEEKY_SYNTHETIC_HOST_TOKEN' not in os.environ
assert not os.environ.get('HTTP_PROXY') and not os.environ.get('http_proxy')
status = Path('/proc/self/status').read_text()
assert 'NoNewPrivs:\\t1' in status
assert 'CapEff:\\t0000000000000000' in status
sock = socket.socket()
sock.settimeout(0.2)
assert sock.connect_ex(('203.0.113.1', 9)) != 0
sock.close()
cgroup = Path('/sys/fs/cgroup')
if (cgroup / 'memory.max').exists():
    memory = int((cgroup / 'memory.max').read_text())
    pids = int((cgroup / 'pids.max').read_text())
    quota, period = map(int, (cgroup / 'cpu.max').read_text().split())
else:
    memory = int((cgroup / 'memory/memory.limit_in_bytes').read_text())
    pids = int((cgroup / 'pids/pids.max').read_text())
    quota = int((cgroup / 'cpu/cpu.cfs_quota_us').read_text())
    period = int((cgroup / 'cpu/cpu.cfs_period_us').read_text())
assert memory == 268435456 and pids == 64 and quota == period
print(json.dumps({'uid': os.getuid(), 'memory': memory, 'pids': pids, 'cpu_ratio': quota / period}))
"""
    result = run_fixture(script_repo(script, "python smoke.py"))
    assert result.outcome == "PASS", result.dict()
    observed = json.loads(result.stdout)
    assert observed == {"uid": 65534, "memory": 268435456, "pids": 64, "cpu_ratio": 1.0}
    isolation = result.provenance["isolation"]
    assert isinstance(isolation, dict)
    assert isolation["LogConfig"] == {"Type": "none", "Config": {}}
    assert_removed(docker_binary, result)


def test_T014_real_memory_budget_is_inconclusive(
    script_repo: Callable[[str, str], Path],
    docker_binary: str,
) -> None:
    result = run_fixture(script_repo("data = bytearray(600 * 1024 * 1024)\n", "python smoke.py"))
    assert result.outcome == "INCONCLUSIVE" and result.reason == "MEMORY_LIMIT", json.dumps(
        result.dict(), indent=2, sort_keys=True
    )
    state = result.provenance["container_state"]
    assert isinstance(state, dict) and state["OOMKilled"] is True
    assert_removed(docker_binary, result)


@pytest.mark.parametrize(
    "script",
    [
        "raise SystemExit(137)\n",
        "import os, signal\n"
        "pid = os.fork()\n"
        "if pid == 0:\n"
        "    os.kill(os.getpid(), signal.SIGKILL)\n"
        "    os._exit(99)\n"
        "_, status = os.waitpid(pid, 0)\n"
        "assert os.WIFSIGNALED(status) and os.WTERMSIG(status) == signal.SIGKILL\n"
        "os._exit(128 + os.WTERMSIG(status))\n",
    ],
    ids=["explicit-exit", "propagated-child-sigkill"],
)
def test_T014_unconfirmed_137_is_not_claimed_as_oom_or_target_failure(
    script_repo: Callable[[str, str], Path], docker_binary: str, script: str
) -> None:
    result = run_fixture(script_repo(script, "python smoke.py"))
    assert result.exit_code == 137, result.dict()
    assert result.outcome == "INCONCLUSIVE" and result.reason == "TERMINATION_UNCERTAIN"
    state = result.provenance["container_state"]
    assert isinstance(state, dict) and state["OOMKilled"] is False
    assert_removed(docker_binary, result)


def test_T015_T016_full_redacted_logs_and_authenticated_provenance(
    script_repo: Callable[[str, str], Path],
    tmp_path: Path,
    docker_binary: str,
) -> None:
    secret = "SYNTHETIC_API_SECRET_123456789"
    script = (
        "import sys\nprint('x' * 4090)\n"
        f"print('api_key={secret}')\nprint('https://example.invalid/path?token={secret}')\n"
        f"print('Authorization: Bearer {secret}', file=sys.stderr)\n"
        "print('z' * 9000)\nprint('ORIGINAL_LOG_TAIL')\n"
    )
    root = script_repo(script, "python smoke.py")
    with snapshot(root) as captured:
        steps = read_steps(captured.path)
        result = execute(steps[0], captured, DEFAULT_IMAGE)
        assert result.outcome == "PASS", result.dict()
        assert secret not in result.stdout + result.stderr
        assert "ORIGINAL_LOG_TAIL" in result.stdout and len(result.stdout) > 5000
        assert (
            result.provenance["stdout_sha256"] == hashlib.sha256(result.stdout.encode()).hexdigest()
        )
        assert result.provenance["image_digest"] == DEFAULT_IMAGE
        run = RunRecord(captured.identity, tuple(steps))
        for state in (
            RunState.INSPECTED,
            RunState.APPROVED,
            RunState.SANDBOX_RUN,
            RunState.OBSERVED,
            RunState.FINALIZED,
        ):
            run.advance(state)
        artifact = write_report(
            report(root, DEFAULT_IMAGE, steps, [result], captured.identity, run, DEFAULT_POLICY),
            tmp_path / "evidence",
        )
    stored = artifact.read_text(encoding="utf-8")
    assert secret not in stored and "ORIGINAL_LOG_TAIL" in stored
    payload = json.loads(stored)
    verify(payload)
    assert payload["verdict"] == "PASS" and payload["coverage"]["complete"] is True
    assert_removed(docker_binary, result)


def test_T015_log_budget_stops_flood_and_removes_container(
    script_repo: Callable[[str, str], Path],
    docker_binary: str,
) -> None:
    result = run_fixture(
        script_repo("import sys\nsys.stdout.write('x' * 2000000)\n", "python smoke.py")
    )
    assert result.outcome == "INCONCLUSIVE" and result.reason == "LOG_LIMIT", result.dict()
    assert len(result.stdout) <= DEFAULT_POLICY.log_bytes_per_stream
    assert result.provenance["logs_complete"] is False
    assert_removed(docker_binary, result)


def test_T017_noop_fixture_preserves_inconclusive_evidence(tmp_path: Path) -> None:
    output = tmp_path / "noop"
    assert (
        main(["audit", "tests/fixtures/no_optin_repo", "--approve", "--output", str(output)]) == 2
    )
    payload = json.loads(next(output.glob("*.json")).read_text(encoding="utf-8"))
    verify(payload)
    assert payload["verdict"] == "INCONCLUSIVE" and payload["results"] == []
    assert payload["reason"] == "NO_OPTED_IN_COMMANDS"


def test_T017_multiple_steps_block_before_execution(
    repo: Path,
    git: Callable[..., bytes],
    tmp_path: Path,
) -> None:
    (repo / "README.md").write_bytes(b"```bash peeky\npython smoke.py\npython smoke.py\n```\n")
    git(repo, "add", "README.md")
    git(repo, "commit", "-qm", "multiple steps fixture")
    output = tmp_path / "multi"
    assert main(["audit", str(repo), "--approve", "--output", str(output)]) == 2
    payload = json.loads(next(output.glob("*.json")).read_text(encoding="utf-8"))
    assert payload["reason"] == "MULTI_STEP_UNSUPPORTED" and payload["results"] == []
    assert payload["coverage"] == {"planned": 2, "observed": 0, "complete": False}
