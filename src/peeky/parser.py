"""Extract *explicitly opted-in* single-command fenced README blocks."""
from __future__ import annotations

import re
from pathlib import Path

from .models import Step

_START = re.compile(r"^\s*```(?:bash|sh)\s+peeky\s*$", re.IGNORECASE)
_END = re.compile(r"^\s*```\s*$")


class ParseError(ValueError):
    pass


def extract_steps(content: str) -> list[Step]:
    steps: list[Step] = []
    fenced = False
    for number, line in enumerate(content.splitlines(), start=1):
        if not fenced and _START.fullmatch(line):
            fenced = True
            continue
        if fenced and _END.fullmatch(line):
            fenced = False
            continue
        if fenced:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                if len(stripped) > 400:
                    raise ParseError(f"Command over length limit on line {number}")
                steps.append(Step(f"step-{len(steps)+1:03d}", stripped, number))
                if len(steps) > 12:
                    raise ParseError("More than 12 annotated commands")
    if fenced:
        raise ParseError("Unterminated fenced `bash peeky` block")
    return steps


def read_steps(repo: Path) -> list[Step]:
    root = repo.resolve(strict=True)
    readme = root / "README.md"
    if readme.is_symlink() or not readme.is_file():
        raise ParseError("Expected a regular non-symlink README.md")
    if readme.stat().st_size > 128_000:
        raise ParseError("README over 128 KiB limit")
    return extract_steps(readme.read_text(encoding="utf-8"))
