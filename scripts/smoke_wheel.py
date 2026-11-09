"""Build/install the produced wheel in a clean venv and run CLI smoke."""

import json
import os
import subprocess
import sys
import tempfile
import tomllib
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]
    wheels = sorted((ROOT / "dist").glob(f"peeky-{version}-*.whl"))
    if len(wheels) != 1:
        print("Expected one matching wheel in dist; run `uv build --wheel` first", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        venv_dir = Path(tmp) / "venv"
        venv.EnvBuilder(with_pip=True).create(venv_dir)
        bindir = "Scripts" if os.name == "nt" else "bin"
        python = str(venv_dir / bindir / ("python.exe" if os.name == "nt" else "python"))
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
        subprocess.run(
            [
                python,
                "-I",
                "-m",
                "pip",
                "--disable-pip-version-check",
                "install",
                "--no-index",
                "--no-deps",
                str(wheels[0]),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            cwd=tmp,
            env=env,
        )
        subprocess.run([python, "-I", "-m", "peeky", "--version"], check=True, cwd=tmp, env=env)
        cli = str(venv_dir / bindir / ("peeky.exe" if os.name == "nt" else "peeky"))
        subprocess.run([cli, "--version"], check=True, cwd=tmp, env=env)
        for command in ("inspect", "audit"):
            help_text = subprocess.run(
                [cli, command, "--help"],
                check=True,
                cwd=tmp,
                env=env,
                capture_output=True,
                text=True,
            ).stdout
            assert "--ref" in help_text and "GitHub" in help_text
            if command == "audit":
                assert "--backend" in help_text and "instabox" in help_text
        doctor_help = subprocess.run(
            [cli, "doctor", "--help"],
            check=True,
            cwd=tmp,
            env=env,
            capture_output=True,
            text=True,
        ).stdout
        assert "--backend" in doctor_help and "instabox" in doctor_help
        # These installed-package checks must remain offline even on a keyed host.
        cloud_env = env.copy()
        for setting in ("INSTABOX_API_KEY", "INSTABOX_API_URL", "PEEKY_INSTABOX_TEMPLATE"):
            cloud_env.pop(setting, None)
        cloud_check = subprocess.run(
            [cli, "doctor", "--backend", "instabox", "--json"],
            check=False,
            cwd=tmp,
            env=cloud_env,
            capture_output=True,
            text=True,
        )
        readiness = json.loads(cloud_check.stdout)
        assert cloud_check.returncode == 3 and readiness["reason"] == "MISSING_API_KEY"
        assert readiness["ready"] is False and readiness["execution_supported"] is True
        # The instabox backend is  implemented now, so the audit command should not fail with a not-implemented error
        cloud_audit = subprocess.run(
            [
                cli,
                "audit",
                str(ROOT / "tests/fixtures/good_repo"),
                "--backend",
                "instabox",
                "--approve",
            ],
            check=False,
            cwd=tmp,
            env=cloud_env,
            capture_output=True,
            text=True,
        )
        assert cloud_audit.returncode == 3 and "refusing host execution" in cloud_audit.stderr
        unapproved = subprocess.run(
            [cli, "audit", "https://github.com/fixture/project", "--ref", "main"],
            check=False,
            cwd=tmp,
            env=env,
            capture_output=True,
            text=True,
        )
        assert unapproved.returncode == 2 and "not authorized" in unapproved.stderr
        # Import the URL support from the installed artifact, outside the checkout.
        subprocess.run(
            [
                python,
                "-I",
                "-c",
                "from peeky.github import parse_url; from peeky.backends import get_backend; "
                "assert parse_url('https://github.com/o/r.git').url == 'https://github.com/o/r'; "
                "assert get_backend('docker').execution_supported; "
                "assert get_backend('instabox').execution_supported",
            ],
            check=True,
            cwd=tmp,
            env=env,
        )
        subprocess.run(
            [cli, "inspect", str(ROOT / "tests/fixtures/good_repo")], check=True, cwd=tmp, env=env
        )
    print("Wheel smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
