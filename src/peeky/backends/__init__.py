"""Execution backends; Docker remains the sole audit implementation."""

from .base import BackendUnavailable, SandboxBackend
from .docker import DockerBackend


def get_backend(name: str) -> SandboxBackend:
    if name == "docker":
        return DockerBackend()
    if name == "instabox":
        from .instabox import InstaboxBackend

        return InstaboxBackend()
    raise BackendUnavailable("Unknown sandbox backend; choose docker or instabox")
