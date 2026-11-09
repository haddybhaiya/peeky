"""InstaBox backend for account preflight and cloud sandbox execution."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any

from ..domain import CloudPolicy
from ..models import Step, StepResult
from ..policy import PolicyError, safe_argv, validate_image
from ..redaction import redact
from ..sources import SourceSnapshot
from .base import BackendReadiness
from .instabox_api import InstaboxClient, InstaboxConfig, InstaboxError, MetadataTransport


def _require(condition: bool) -> None:
    if not condition:
        raise InstaboxError(
            "INVALID_RESPONSE", "InstaBox returned incomplete or invalid account metadata"
        )


def _count(value: object) -> int:
    if type(value) is not int or value < 0:
        raise InstaboxError("INVALID_RESPONSE", "InstaBox returned invalid account counts")
    return value


def _template_available(data: dict[str, Any], template_id: str) -> bool:
    templates = data.get("templates")
    _require(isinstance(templates, list))
    if not isinstance(templates, list):
        return False
    for item in templates:
        _require(isinstance(item, dict))
        if not isinstance(item, dict) or item.get("id") != template_id:
            continue
        creatable = item.get("creatable")
        hidden = item.get("hidden")
        if creatable is not None:
            _require(type(creatable) is bool)
        if hidden is not None:
            _require(type(hidden) is bool)
        # Official older servers use !hidden; absence of both is unknown.
        offered = (
            creatable if creatable is not None else (not hidden if type(hidden) is bool else False)
        )
        if offered and hidden is not True and item.get("arch") == "x86_64":
            return True
    return False


class InstaboxBackend:
    name = "instabox"
    execution_supported = True

    def __init__(
        self, config: InstaboxConfig | None = None, transport: MetadataTransport | None = None
    ) -> None:
        self._config = config
        self._transport = transport

    def doctor(self, avoid: Path | None = None) -> BackendReadiness:
        checks = {
            "configuration": "not_checked",
            "authentication": "not_checked",
            "account_activation": "not_checked",
            "template_catalog": "not_checked",
            "machine_quota": "not_checked",
            "create_delete_permissions": "not_verified",
            "template_plan_access": "not_verified",
            "provider_capacity": "not_verified",
            "execution": "not_implemented",
        }
        details: dict[str, object] = {"read_only": True}

        def result(ok: bool, reason: str, message: str) -> BackendReadiness:
            return BackendReadiness(
                self.name, ok, self.execution_supported, reason, message, checks, details
            )

        try:
            config = self._config if self._config is not None else InstaboxConfig.from_environment()
            config.validate()
            checks["configuration"] = "passed"
            details["template_id"] = config.template_id
            client = (
                InstaboxClient(config)
                if self._transport is None
                else InstaboxClient(config, self._transport)
            )
            account = client.get("/v1/me")
            _require(type(account.get("userId")) is int and account["userId"] > 0)
            _require(isinstance(account.get("login"), str) and bool(account["login"]))
            checks["authentication"] = "passed"
            details["account_id"] = account["userId"]
            for field in ("inviteRequired", "activated"):
                if field in account:
                    _require(type(account[field]) is bool)
            if account.get("inviteRequired") is True and account.get("activated") is not True:
                checks["account_activation"] = "failed"
                return result(
                    False, "INVITE_REQUIRED", "Activate this InstaBox account in the dashboard"
                )
            checks["account_activation"] = (
                "passed" if account.get("activated") is True else "not_reported"
            )
            if not _template_available(client.get("/v1/templates"), config.template_id):
                checks["template_catalog"] = "failed"
                return result(
                    False,
                    "TEMPLATE_UNAVAILABLE",
                    "The selected x86_64 template is not offered in the current catalog",
                )
            checks["template_catalog"] = "passed"
            usage = client.get("/v1/usage")
            machines = _count(usage.get("machines"))
            limits = usage.get("limits")
            _require(isinstance(limits, dict))
            if not isinstance(limits, dict):
                return result(False, "INVALID_RESPONSE", "InstaBox did not report account limits")
            maximum = _count(limits.get("maxMachines"))
            unlimited = limits.get("unlimited")
            _require(
                unlimited is None
                or (isinstance(unlimited, list) and all(type(v) is str for v in unlimited))
            )
            details.update(machines=machines, max_machines=maximum)
            if maximum == 0 and unlimited is None:
                checks["machine_quota"] = "unknown"
                return result(
                    False, "LIMIT_UNKNOWN", "The provider did not disambiguate a zero machine limit"
                )
            no_limit = maximum == 0 and isinstance(unlimited, list) and "maxMachines" in unlimited
            details["machine_limit_unlimited"] = no_limit
            if not no_limit and machines >= maximum:
                checks["machine_quota"] = "failed"
                return result(
                    False,
                    "MACHINE_LIMIT_REACHED",
                    "No machine slot is available in this account; review it in the dashboard",
                )
            checks["machine_quota"] = "passed"
            checks["execution"] = "supported"
            details["execution_supported"] = True
            return BackendReadiness(
                self.name,
                preflight_ok=True,
                execution_supported=True,
                reason="READY",
                message="InstaBox account and cloud execution readiness confirmed",
                checks=checks,
                details=details,
            )
        except InstaboxError as error:
            if checks["configuration"] != "passed":
                checks["configuration"] = "failed"
            elif error.code == "AUTHENTICATION_FAILED":
                checks["authentication"] = "failed"
            if error.http_status is not None:
                details["http_status"] = error.http_status
            return result(False, error.code, str(error))

    def execute(self, step: Step, source: SourceSnapshot, image: str, timeout: float) -> StepResult:
        config = self._config if self._config is not None else InstaboxConfig.from_environment()
        config.validate()
        cloud_policy = CloudPolicy(template_id=config.template_id)
        try:
            if not (image == config.template_id or image == f"template:{config.template_id}"):
                validate_image(image)
        except PolicyError as err:
            return StepResult(
                id=step.id,
                command=step.command,
                exit_code=None,
                stdout="",
                stderr="",
                outcome="INCONCLUSIVE",
                duration_ms=0,
                reason=f"Requested image '{image}' not supported: {err}",
                provenance={
                    "backend": "instabox",
                    "template_id": config.template_id,
                    "policy_sha256": cloud_policy.sha256,
                    "cleanup_verified": True,
                    "logs_complete": True,
                },
            )

        client = (
            InstaboxClient(config)
            if self._transport is None
            else InstaboxClient(config, self._transport)
        )
        argv = safe_argv(step.command)
        machine_id = client.create_machine(
            template=config.template_id,
            metadata={"creator": "peeky", "step_id": step.id},
            auto_destroy_seconds=cloud_policy.auto_destroy_seconds,
        )
        cleanup_verified = False
        duration_ms = 0
        stdout = ""
        stderr = ""
        exit_code: int | None = None
        outcome = "INCONCLUSIVE"
        reason = ""
        logs_complete = False
        target_started = False
        stdout_seen = 0
        stderr_seen = 0
        try:
            client.upload_snapshot(machine_id, source, target_dir="/workspace")
            start = time.monotonic()
            raw_res = client.exec_step(machine_id, argv, cwd="/workspace", timeout=timeout)
            duration_ms = int((time.monotonic() - start) * 1000)
            target_started = True

            raw_stdout = str(raw_res.get("stdout", ""))
            raw_stderr = str(raw_res.get("stderr", ""))
            stdout_bytes = raw_stdout.encode("utf-8")
            stderr_bytes = raw_stderr.encode("utf-8")
            stdout_seen = len(stdout_bytes)
            stderr_seen = len(stderr_bytes)

            log_limit = cloud_policy.log_bytes_per_stream
            limited = stdout_seen > log_limit or stderr_seen > log_limit

            # Redact complete returned strings before truncating retained text
            redacted_stdout = redact(raw_stdout)
            redacted_stderr = redact(raw_stderr)
            redacted_stdout_bytes = redacted_stdout.encode("utf-8")
            redacted_stderr_bytes = redacted_stderr.encode("utf-8")

            if len(redacted_stdout_bytes) > log_limit:
                stdout = redacted_stdout_bytes[:log_limit].decode("utf-8", errors="replace")
            else:
                stdout = redacted_stdout

            if len(redacted_stderr_bytes) > log_limit:
                stderr = redacted_stderr_bytes[:log_limit].decode("utf-8", errors="replace")
            else:
                stderr = redacted_stderr
            exit_code = raw_res.get("exitCode")
            timed_out = bool(raw_res.get("timedOut", False))
            logs_complete = not (limited or timed_out)

            if limited:
                outcome = "INCONCLUSIVE"
                reason = "LOG_LIMIT"
            elif timed_out:
                outcome = "TIMEOUT"
                reason = "Command timed out in cloud sandbox"
            elif exit_code == 0:
                outcome = "PASS"
                reason = ""
            elif exit_code is not None:
                outcome = "FAIL"
                reason = f"Command failed with exit code {exit_code}"
            else:
                outcome = "INCONCLUSIVE"
                reason = "Unknown execution outcome from InstaBox"
        except InstaboxError as exc:
            outcome = "INCONCLUSIVE"
            reason = f"CLOUD_ERROR: {exc.code}"
        except Exception as exc:
            outcome = "INCONCLUSIVE"
            reason = f"CLOUD_ERROR: {type(exc).__name__}"
        finally:
            try:
                cleanup_verified = client.delete_machine(machine_id)
            except Exception:
                cleanup_verified = False

        provenance = {
            "backend": "instabox",
            "machine_id": machine_id,
            "template_id": config.template_id,
            "image": f"template:{config.template_id}",
            "image_digest": f"template:{config.template_id}",
            "requested_image": image,
            "cloud": True,
            "source_sha256": source.identity.source_sha256,
            "policy_sha256": cloud_policy.sha256,
            "target_started": target_started,
            "logs_complete": logs_complete,
            "cleanup_verified": cleanup_verified,
            "duration_ms": duration_ms,
            "stdout_bytes_seen": stdout_seen,
            "stderr_bytes_seen": stderr_seen,
            "stdout_sha256": hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
            "stderr_sha256": hashlib.sha256(stderr.encode("utf-8")).hexdigest(),
        }
        return StepResult(
            id=step.id,
            command=step.command,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            outcome=outcome,
            duration_ms=duration_ms,
            reason=reason,
            provenance=provenance,
        )
