"""Pre-execution policy. Never interpret README text as controller policy."""

from __future__ import annotations

import re
import shlex

from .domain import DEFAULT_POLICY, RunPolicy


class PolicyError(ValueError):
    pass


def safe_argv(command: str, policy: RunPolicy = DEFAULT_POLICY) -> list[str]:
    if len(command) > policy.max_command_chars:
        raise PolicyError("Command exceeds length limit")
    if any(
        ord(char) < 32 or ord(char) == 127 or char in policy.forbidden_shell_chars
        for char in command
    ):
        raise PolicyError("Shell composition, expansion or redirection is disallowed")
    try:
        args = shlex.split(command)
    except ValueError as exc:
        raise PolicyError(f"Unparseable command: {exc}") from exc
    if not args or args[0] not in policy.allowed_binaries:
        raise PolicyError("Only directly invoked python/python3/pytest are allowed in scaffold")
    if len(args) > policy.max_arguments or any(
        len(arg) > policy.max_argument_chars for arg in args
    ):
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
    if not (
        re.fullmatch(r"python:[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}", image)
        or re.fullmatch(r"python@sha256:[a-f0-9]{64}", image)
    ):
        raise PolicyError("Only python:TAG or python@sha256:FULL_DIGEST is accepted")
    return image
