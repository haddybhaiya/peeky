"""Build/install the produced wheel in a clean venv and run CLI smoke."""

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
        subprocess.run(
            [cli, "inspect", str(ROOT / "tests/fixtures/good_repo")], check=True, cwd=tmp, env=env
        )
    print("Wheel smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
