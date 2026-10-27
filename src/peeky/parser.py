"""Parse designated fences while ignoring examples nested in other Markdown fences."""

from __future__ import annotations

import re
from pathlib import Path

from .domain import DEFAULT_POLICY, RunPolicy
from .models import Step
from .sources import read_regular, safe_root

_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


class ParseError(ValueError):
    pass


def extract_steps(content: str, policy: RunPolicy = DEFAULT_POLICY) -> list[Step]:
    if len(content.encode("utf-8")) > policy.max_readme_bytes:
        raise ParseError("README exceeds byte limit")
    steps: list[Step] = []
    marker = ""
    active = False
    for number, line in enumerate(content.splitlines(), start=1):
        fence = _FENCE.fullmatch(line)
        if marker:
            if fence and fence[1][0] == marker[0] and len(fence[1]) >= len(marker):
                if not fence[2].strip():
                    marker, active = "", False
                    continue
                if active:
                    raise ParseError("Nested or malformed annotated fence")
            if active:
                command = line.strip()
                if command and not command.startswith("#"):
                    if len(command) > policy.max_command_chars:
                        raise ParseError(f"Command over length limit on line {number}")
                    steps.append(Step(f"step-{len(steps) + 1:03d}", command, number))
                    if len(steps) > policy.max_commands:
                        raise ParseError("Annotated command count exceeds limit")
        elif fence:
            marker = fence[1]
            info = fence[2].strip().lower().split()
            if "peeky" in info and info != ["bash", "peeky"] and info != ["sh", "peeky"]:
                raise ParseError("Malformed Peeky fence annotation")
            active = info in (["bash", "peeky"], ["sh", "peeky"])
    if marker and active:
        raise ParseError("Unterminated fenced `bash peeky` block")
    return steps


def read_steps(repo: Path, policy: RunPolicy = DEFAULT_POLICY) -> list[Step]:
    return extract_steps(
        read_regular(safe_root(repo), "README.md", policy.max_readme_bytes).decode("utf-8"), policy
    )
