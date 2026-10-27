"""Build/install the produced wheel in a clean venv and run CLI smoke."""
import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    wheels = sorted((ROOT / "dist").glob("peeky-*.whl"))
    if not wheels:
        print("No wheel in dist; run `uv build --wheel` first", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        venv_dir = Path(tmp) / "venv"
        venv.EnvBuilder(with_pip=True).create(venv_dir)
        bindir = "Scripts" if os.name == "nt" else "bin"
        python = str(venv_dir / bindir / ("python.exe" if os.name == "nt" else "python"))
        subprocess.run([python, "-m", "pip", "install", "--no-deps", str(wheels[-1])], check=True,
                       stdout=subprocess.DEVNULL)
        subprocess.run([python, "-m", "peeky", "--version"], check=True)
        subprocess.run([python, "-m", "peeky", "inspect", str(ROOT/"tests/fixtures/good_repo")], check=True)
    print("Wheel smoke passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
