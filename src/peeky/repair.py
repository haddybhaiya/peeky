"""README-only proposals and human-approved fresh Docker rechecks, never a model loop."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .domain import DEFAULT_POLICY, RunRecord, RunState, canonical_hash, plan_hash, valid_history
from .evidence import report, runtime_verified, verdict, write_report
from .hosttools import host_tool
from .images import DEFAULT_IMAGE
from .models import StepResult
from .parser import extract_steps, read_steps
from .policy import safe_argv
from .provenance import verify
from .providers.openai_compatible import (
    PatchProposal,
    ProviderConfig,
    ProviderError,
    Transport,
    http_transport,
    propose,
)
from .runner import execute
from .sources import SourceSnapshot, read_regular, safe_relative, safe_root, snapshot


class RepairError(ValueError):
    pass


@dataclass(frozen=True)
class FrozenOracle:
    expected_command: str
    stdout_line: str

    def validate(self, captured: SourceSnapshot) -> None:
        argv = safe_argv(self.expected_command)
        if len(argv) != 2 or argv[0] not in {"python", "python3"} or not argv[1].endswith(".py"):
            raise RepairError(
                "Repair oracle requires python/python3 and one existing .py file, no flags"
            )
        safe_relative(argv[1])
        if argv[1] not in {f.path for f in captured.identity.files}:
            raise RepairError("Oracle entrypoint must exist in the frozen source")
        if not re.fullmatch(r"[A-Za-z0-9_.: -]{1,160}", self.stdout_line):
            raise RepairError("Oracle requires a bounded exact stdout marker line")


def load_record(path: Path) -> dict[str, Any]:
    data = json.loads(read_regular(safe_root(path.parent), path.name, 2 * 1024 * 1024))
    if not isinstance(data, dict):
        raise RepairError("Expected an authenticated record object")
    verify(data)
    return data


def claim_attempt(state: Path, kind: str, identity: str) -> None:
    directory = state / kind
    directory.mkdir(parents=True, exist_ok=True)
    safe_root(directory)
    path = directory / (hashlib.sha256(identity.encode()).hexdigest() + ".claim")
    try:
        # Reserve before the action, including crashes/failures; no automatic retry.
        with path.open("x", encoding="utf-8") as stream:
            stream.write("one controller attempt reserved\n")
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        raise RepairError(
            "Repair attempt budget exhausted; explicit operator review required"
        ) from None


def validate_baseline(captured: SourceSnapshot, record: dict[str, Any]) -> None:
    steps = read_steps(captured.path)
    results = [StepResult(**item) for item in record.get("results", [])]
    run = record.get("run", {})
    if (
        record.get("schema_version") != "1.2"
        or record.get("execution") != "offline-docker-single-command"
        or canonical_hash(record.get("source")) != canonical_hash(asdict(captured.identity))
        or canonical_hash(record.get("policy")) != DEFAULT_POLICY.sha256
        or record.get("policy_sha256") != DEFAULT_POLICY.sha256
        or record.get("image") != DEFAULT_IMAGE
        or record.get("steps") != [asdict(step) for step in steps]
        or len(steps) != 1
        or len(results) != 1
        or record.get("verdict") != "FAIL"
        or verdict(steps, results) != "FAIL"
        or not runtime_verified(results[0], captured.identity, DEFAULT_IMAGE)
        or run.get("state") != RunState.FINALIZED
        or not valid_history(run.get("history"), RunState.FINALIZED)
        or run.get("plan_sha256") != plan_hash(captured.identity, tuple(steps), DEFAULT_POLICY)
    ):
        raise RepairError("Diagnosis requires complete matching authenticated target FAIL evidence")


def validate_diff(original: bytes, diff: str, oracle: FrozenOracle) -> bytes:
    """Exact-context single-file unified diff; no fuzzy patching, shell, git apply or hooks."""
    if len(diff.encode()) > 12_000 or not diff.endswith("\n"):
        raise RepairError("Diff exceeds budget or lacks final newline")
    text = original.decode("utf-8")
    if "\r" in text or not text.endswith("\n"):
        raise RepairError("Phase 3 README repair requires UTF-8 LF text with a final newline")
    steps = extract_steps(text)
    if len(steps) != 1:
        raise RepairError("Repair requires exactly one original annotated command")
    lines = text.splitlines(keepends=True)
    patch = diff.splitlines(keepends=True)
    if len(patch) < 4 or patch[:2] != ["--- a/README.md\n", "+++ b/README.md\n"]:
        raise RepairError("Only the exact README.md path is allowed; no metadata/renames")
    header = re.fullmatch(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@\n", patch[2])
    if header is None:
        raise RepairError("Exactly one well-formed diff hunk is required")
    old_start, old_count, new_start, new_count = (
        int(header[1]),
        int(header[2] or 1),
        int(header[3]),
        int(header[4] or 1),
    )
    old: list[str] = []
    new: list[str] = []
    for line in patch[3:]:
        if not line or line[0] not in " +-":
            raise RepairError("Diff contains unsupported or additional file metadata")
        if line[0] in " -":
            old.append(line[1:])
        if line[0] in " +":
            new.append(line[1:])
    if (
        old_start < 1
        or new_start != old_start
        or len(old) != old_count
        or len(new) != new_count
        or lines[old_start - 1 : old_start - 1 + old_count] != old
    ):
        raise RepairError("Diff does not match exact frozen README context")
    candidate = lines[: old_start - 1] + new + lines[old_start - 1 + old_count :]
    expected = list(lines)
    index = steps[0].line - 1
    prefix = lines[index][: len(lines[index]) - len(lines[index].lstrip(" "))]
    expected[index] = prefix + oracle.expected_command + "\n"
    if candidate != expected or candidate == lines:
        raise RepairError("Only the frozen expected command line may change; no test weakening")
    actual_steps = extract_steps("".join(candidate))
    if len(actual_steps) != 1 or actual_steps[0].command != oracle.expected_command:
        raise RepairError("Candidate does not preserve the frozen command oracle")
    return "".join(candidate).encode()


def proposal_digest(record: dict[str, Any]) -> str:
    return canonical_hash(
        {k: v for k, v in record.items() if k not in {"integrity", "approval_digest"}}
    )


def diagnose(
    repo: Path,
    evidence: Path,
    oracle: FrozenOracle,
    config: ProviderConfig,
    output: Path,
    state: Path,
    *,
    consent: bool,
    transport: Transport = http_transport,
) -> Path:
    if not consent:
        raise ProviderError("Model consent required; no source capture or model call")
    config.validate()
    baseline = load_record(evidence)
    with snapshot(repo) as captured:
        validate_baseline(captured, baseline)
        oracle.validate(captured)
        original = read_regular(captured.path, "README.md", DEFAULT_POLICY.max_readme_bytes)
        context = {
            "README.md": original.decode("utf-8"),
            "source.manifest": [f.path for f in captured.identity.files],
            "evidence.stdout": baseline["results"][0]["stdout"],
            "evidence.stderr": baseline["results"][0]["stderr"],
            "expected_command": oracle.expected_command,
            "instruction": "Propose only the command-line correction; never an execution verdict.",
        }
        claim_attempt(state, "diagnosis", canonical_hash(baseline))
        trace = propose(config, context, consent=True, transport=transport)
        data: dict[str, Any] = {
            "schema_version": "repair-proposal-1",
            "status": trace["status"],
            "source": asdict(captured.identity),
            "policy_sha256": DEFAULT_POLICY.sha256,
            "image": DEFAULT_IMAGE,
            "oracle": asdict(oracle),
            "baseline_sha256": canonical_hash(baseline),
            "baseline": baseline,
            "provider_trace": trace,
        }
        if trace["status"] == "PROPOSED":
            try:
                proposal = PatchProposal.parse(json.dumps(trace["proposal"]))
                candidate = validate_diff(original, proposal.candidate_diff, oracle)
                data.update(
                    {
                        "proposal": asdict(proposal),
                        "candidate_readme_sha256": "sha256:"
                        + hashlib.sha256(candidate).hexdigest(),
                    }
                )
            except ValueError as exc:
                data.update({"status": "REJECTED", "error": str(exc)})
        # Hash the same sanitized bytes that will be stored; the model never supplies approval.
        from .redaction import sanitized

        clean = sanitized(data)
        assert isinstance(clean, dict)
        clean["approval_digest"] = proposal_digest(clean)
        return write_report(clean, output)


@contextmanager
def candidate_snapshot(base: SourceSnapshot, readme: bytes) -> Iterator[SourceSnapshot]:
    """Make an isolated clean Git revision from frozen bytes; never checkout/apply in target."""
    base.verify()
    binary = host_tool("git", avoid=base._origin)
    if binary is None:
        raise RepairError("Trusted Git unavailable for candidate capture")
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_ATTR_NOSYSTEM="1",
        GIT_TERMINAL_PROMPT="0",
        GIT_NO_LAZY_FETCH="1",
        GIT_AUTHOR_NAME="Peeky candidate",
        GIT_AUTHOR_EMAIL="candidate@example.invalid",
        GIT_COMMITTER_NAME="Peeky candidate",
        GIT_COMMITTER_EMAIL="candidate@example.invalid",
    )
    with tempfile.TemporaryDirectory(prefix="peeky-candidate-") as temp:
        root = Path(temp)

        def git(*args: str) -> None:
            subprocess.run(
                [
                    binary,
                    "-c",
                    f"core.hooksPath={os.devnull}",
                    "-c",
                    "commit.gpgSign=false",
                    "-c",
                    "core.autocrlf=false",
                    "-c",
                    "protocol.allow=never",
                    *args,
                ],
                cwd=root,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=DEFAULT_POLICY.git_timeout_seconds,
                check=True,
            )

        for item in base.identity.files:
            target = root / item.path
            target.parent.mkdir(parents=True, exist_ok=True)
            content = (
                readme
                if item.path == "README.md"
                else read_regular(base.path, item.path, DEFAULT_POLICY.max_file_bytes)
            )
            target.write_bytes(content)
            target.chmod(0o755 if item.mode == "100755" else 0o644)
        git("init", "--template=", "-q")
        git("add", "--force", "--", ".")
        for item in base.identity.files:
            git(
                "update-index",
                "--chmod=" + ("+x" if item.mode == "100755" else "-x"),
                "--",
                item.path,
            )
        git("commit", "-qm", "Controller README-only candidate; not a target checkout")
        with snapshot(root) as captured:
            original_files = {f.path: f for f in base.identity.files if f.path != "README.md"}
            candidate_files = {f.path: f for f in captured.identity.files if f.path != "README.md"}
            if candidate_files != original_files:
                raise RepairError("Candidate changed executable source, tests or file modes")
            yield captured
        base.verify()


def run_snapshot(captured: SourceSnapshot) -> dict[str, Any]:
    steps = read_steps(captured.path)
    if len(steps) != 1:
        raise RepairError("Recheck requires one annotated command")
    run = RunRecord(captured.identity, tuple(steps))
    for stage in (RunState.INSPECTED, RunState.APPROVED, RunState.SANDBOX_RUN):
        run.advance(stage)
    result = execute(steps[0], captured, DEFAULT_IMAGE)
    captured.verify()
    run.advance(RunState.OBSERVED)
    run.advance(RunState.FINALIZED)
    return report(
        captured.path, DEFAULT_IMAGE, steps, [result], captured.identity, run, DEFAULT_POLICY
    )


def recheck(repo: Path, proposal_file: Path, approval: str, output: Path, state: Path) -> Path:
    if not approval:
        raise RepairError("Human approval of the exact proposal digest is required")
    record = load_record(proposal_file)
    digest = proposal_digest(record)
    if record.get("approval_digest") != digest or approval != digest:
        raise RepairError("Approval does not match this exact source/patch/oracle proposal")
    if record.get("schema_version") != "repair-proposal-1" or record.get("status") != "PROPOSED":
        raise RepairError("Only a controller-validated proposal can be approved")
    if record.get("policy_sha256") != DEFAULT_POLICY.sha256 or record.get("image") != DEFAULT_IMAGE:
        raise RepairError("Recheck policy/image changed")
    proposal = PatchProposal.parse(json.dumps(record["proposal"]))
    oracle = FrozenOracle(**record["oracle"])
    with snapshot(repo) as base:
        if canonical_hash(record.get("source")) != canonical_hash(asdict(base.identity)):
            raise RepairError("Source revision or bytes changed after review")
        baseline_record = record["baseline"]
        verify(baseline_record)
        validate_baseline(base, baseline_record)
        if record["baseline_sha256"] != canonical_hash(baseline_record):
            raise RepairError("Baseline evidence identity changed")
        oracle.validate(base)
        candidate = validate_diff(
            read_regular(base.path, "README.md", DEFAULT_POLICY.max_readme_bytes),
            proposal.candidate_diff,
            oracle,
        )
        if record["candidate_readme_sha256"] != "sha256:" + hashlib.sha256(candidate).hexdigest():
            raise RepairError("Candidate README identity changed")
        claim_attempt(state, "recheck", digest)
        before = run_snapshot(base)
        before_path = write_report(before, output / "baseline")
        with candidate_snapshot(base, candidate) as derived:
            after = run_snapshot(derived)
            after_path = write_report(after, output / "candidate")
        b = before["results"][0]["provenance"]
        a = after["results"][0]["provenance"]
        matched = (
            before["verdict"] == "FAIL"
            and after["verdict"] == "PASS"
            and b.get("image_id") == a.get("image_id")
            and bool(a.get("image_id"))
            and b.get("container_id") != a.get("container_id")
            and b.get("cleanup_verified") is True
            and a.get("cleanup_verified") is True
            and after["steps"][0]["command"] == oracle.expected_command
            and oracle.stdout_line in after["results"][0]["stdout"].splitlines()
        )
        data = {
            "schema_version": "repair-recheck-1",
            "approval_digest": digest,
            "status": "VERIFIED" if matched else "INCONCLUSIVE",
            "oracle": asdict(oracle),
            "oracle_matched": matched,
            "source": record["source"],
            "proposal_sha256": canonical_hash(record),
            "baseline_evidence": str(before_path.resolve()),
            "candidate_evidence": str(after_path.resolve()),
            "baseline": before,
            "candidate": after,
            "limitations": [
                "Only the frozen README command and exact marker were verified",
                "Candidate is an isolated temporary Git revision; target is never modified",
                "No model statement decides verified status",
            ],
        }
        return write_report(data, output)
