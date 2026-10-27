"""Real controller/Git integration without Docker or target execution."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def test_two_processes_measure_identical_source_and_policy(repo: Path, tmp_path: Path) -> None:
    def inspect() -> dict[str, object]:
        output = subprocess.run(
            [sys.executable, "-I", "-m", "peeky", "inspect", str(repo), "--json"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        data: dict[str, object] = json.loads(output.stdout)
        return data

    first, second = inspect(), inspect()
    assert first["source"] == second["source"]
    assert first["policy_sha256"] == second["policy_sha256"]
    first_run, second_run = first["run"], second["run"]
    assert isinstance(first_run, dict) and isinstance(second_run, dict)
    assert first_run["plan_sha256"] == second_run["plan_sha256"]
    assert first_run["id"] != second_run["id"]
    (repo / "smoke.py").write_bytes(b"dirty source")
    denied = subprocess.run(
        [sys.executable, "-I", "-m", "peeky", "inspect", str(repo), "--json"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert denied.returncode == 3 and "Dirty" in denied.stderr
    assert denied.stdout == ""
