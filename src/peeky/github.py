"""Public GitHub source inputs; repository contents never become host instructions."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .sources import SourceError


@dataclass(frozen=True)
class GitHubRepository:
    owner: str
    name: str

    @property
    def url(self) -> str:
        return f"https://github.com/{self.owner}/{self.name}"


def parse_url(value: str) -> GitHubRepository:
    """Accept only literal HTTPS repository roots, without credentials or redirects."""
    match = re.fullmatch(
        r"https://github\.com/([A-Za-z0-9][A-Za-z0-9-]{0,38})/([A-Za-z0-9_.-]{1,104})/?",
        value,
    )
    if match is None:
        raise SourceError(
            "Use a public repository root: https://github.com/OWNER/REPO; "
            "subdirectory URLs, credentials, queries and other hosts are unsupported"
        )
    owner, name = match.groups()
    if name.endswith(".git"):
        name = name[:-4]
    if not name or name in {".", ".."} or len(name) > 100 or owner.endswith("-"):
        raise SourceError("Invalid GitHub repository name or owner")
    return GitHubRepository(owner, name)


def validate_ref(value: str | None) -> str | None:
    """Validate a branch/tag/full SHA before constructing any Git argument."""
    if value is None:
        return None
    if re.fullmatch(r"[a-fA-F0-9]{40}", value):
        return value.lower()
    if (
        not value
        or len(value) > 255
        or value == "@"
        or value.startswith(("-", "/"))
        or value.endswith(("/", "."))
        or ".." in value
        or "@{" in value
        or any(ord(c) <= 32 or ord(c) == 127 or c in "~^:?*[\\" for c in value)
        or any(
            not part or part.startswith(".") or part.endswith(".lock") for part in value.split("/")
        )
        or (value.startswith("refs/") and not value.startswith(("refs/heads/", "refs/tags/")))
        or value in {"refs/heads/", "refs/tags/"}
    ):
        raise SourceError("--ref must be a branch, tag or full 40-character commit SHA")
    return value
