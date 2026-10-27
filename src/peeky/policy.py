"""Pre-execution policy. Never interpret README text as controller policy."""

from __future__ import annotations

import re
import shlex


class PolicyError(ValueError):
    pass


_ALLOWED_BINARIES = {"python", "python3", "pytest"}


def safe_argv(command: str) -> list[str]:
    if any(char in command for char in "\n\r;&|<>`$\\"):
        raise PolicyError("Shell composition, expansion or redirection is disallowed")
    try:
        args = shlex.split(command)
    except ValueError as exc:
        raise PolicyError(f"Unparseable command: {exc}") from exc
    if not args or args[0] not in _ALLOWED_BINARIES:
        raise PolicyError("Only directly invoked python/python3/pytest are allowed in scaffold")
    if len(args) > 24 or any(len(arg) > 300 for arg in args):
        raise PolicyError("Arguments exceed limits")
    if any(a.startswith("-") and a in {"-i", "--interactive"} for a in args):
        raise PolicyError("Interactive commands are forbidden")
    return args


def validate_image(image: str) -> str:
    # Do not allow executable or malformed Docker argument injection.
    if not image or image.startswith("-") or len(image) > 200:
        raise PolicyError("Invalid image identifier")
    if not re.fullmatch(r"[a-zA-Z0-9./:_@-]+", image):
        raise PolicyError("Invalid image identifier characters")
    if not image.startswith("python:") and not image.startswith("python@sha256:"):
        raise PolicyError("Scaffold runner supports the Python official image only")
    return image
