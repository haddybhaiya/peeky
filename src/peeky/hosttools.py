"""Discover installed host tools without current-directory/target-tree execution."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def host_tool(name: str, avoid: Path | None = None) -> str | None:
    blocked = [Path.cwd().resolve()]
    if avoid is not None:
        blocked.append(avoid.resolve())
    for item in os.get_exec_path():
        directory = Path(item)
        if not item or not directory.is_absolute():
            continue
        directory = directory.resolve()
        if any(directory.is_relative_to(root) for root in blocked):
            continue
        # An explicit directory prevents Windows which() from implicitly searching cwd.
        found = shutil.which(str(directory / name))
        if found is not None and not any(
            Path(found).resolve().is_relative_to(root) for root in blocked
        ):
            return found
    return None
