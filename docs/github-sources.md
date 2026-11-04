# Public GitHub URL inspection and audits

Owner-authorized post-MVP PR 1 added URL resolution and inspection under
GH-001..GH-008. PR 2 adds approved local Docker audits under GHA-001..GHA-008.
Inspect produces a plan; only an actual completed permitted Docker check can
produce audit PASS evidence.

## Commands

```bash
peeky inspect https://github.com/OWNER/REPO
peeky inspect https://github.com/OWNER/REPO.git --ref main --json
peeky inspect https://github.com/OWNER/REPO --ref refs/tags/v1.0
peeky inspect https://github.com/OWNER/REPO --ref FULL_40_CHARACTER_COMMIT_SHA
```

Local directory inspection keeps its existing behavior and JSON shape. `--ref`
applies only to URL inputs for inspect/audit. Public repository roots on literal
`https://github.com` are accepted, with optional `.git` and trailing slash.
Credentials, ports, queries, fragments, SSH/file URLs, other hosts, GitHub Enterprise,
subdirectory/tree/blob links and private repositories are unsupported. Renamed or
transferred URLs that redirect must be replaced with their current canonical URL.

The default branch is selected when `--ref` is omitted; `HEAD` also selects the
remote HEAD. Named branches/tags and full commit SHAs are supported, not revision
expressions or abbreviated SHAs. When a branch and tag share a name, qualify it
with `refs/heads/NAME` or `refs/tags/NAME`. Annotated tags are peeled to commits;
tags pointing to non-commit objects cannot be inspected.
Git's ref query also returns suffix matches, so Peeky filters records to exact
requested names. A branch such as `topic/HEAD` or a tag named `HEAD` therefore
does not interfere with default-branch inspection.

Exit codes: 0 means a valid nonempty inspection plan, 2 means no opted-in commands,
and 3 means an invalid/unsupported source, command-policy or infrastructure error.
Neither 0 nor 2 establishes target execution or reproducibility. A README still
needs explicit `bash peeky` fences. Inspect does not infer executable setup steps.

## Audit commands and lifecycle

```bash
peeky inspect https://github.com/OWNER/REPO --ref main --json
peeky audit https://github.com/OWNER/REPO --ref FULL_RESOLVED_COMMIT_SHA --approve
peeky report --evidence .peeky/runs/RUN_ID.json --output .peeky/review
```

`--approve` is required before any audit fetch, capture or Docker check. `--ref`
supports the same default/branch/tag/SHA selection as inspect. Every invocation
captures its own immutable revision; use inspect's full commit SHA to run exactly
the source you reviewed across invocations. A moving named ref is resolved once
per invocation, never silently followed during execution.

After acquisition the existing controller validates the image and exactly one
opted-in command, then runs the verified export in fresh local Docker. The target
has no network, credentials, Git metadata or writable source. Existing image,
resource, environment, timeout, log, independent verdict and owned-container
cleanup rules apply unchanged. The approved image must be prepared separately;
the audit never pulls it or installs dependencies.

Exit 0 means observed smoke PASS; 1 means observed target FAIL; 2 means missing
approval or a captured policy/no-op block; 3 means source/infrastructure failure
or uncertain execution. Missing Docker, timeouts and unverified container cleanup
never establish a target PASS. After successful source capture, blocked and
observed attempts preserve authenticated evidence. A failure before capture
returns 3 with a diagnostic and no invented source/plan record.

The final record is published only after both temporary Git storage and source
exports close successfully. Controller interruption or source cleanup failure
does not publish a finalized record. This is normal-return/exception cleanup,
not durable crash journaling. Original runtime provenance can retain temporary
mount paths as observations; those paths are not the durable repository identity.

## Fetch and capture

The controller creates an empty temporary Git repository using an empty template.
It resolves a named ref once, then shallow-fetches that exact commit with no tags,
submodule recursion, checkout or automatic maintenance. HEAD is set to the verified
fetched commit. A moving branch cannot silently replace the chosen revision;
if the server no longer serves that commit, inspection fails.

Only public HTTPS Git transport is enabled. Global/system Git config, inherited
`GIT_*` overrides, credential helpers, askpass, hooks, fsmonitor, redirects and
lazy fetching are disabled. TLS verification stays enabled. Platform PATH, proxy
and CA environment settings are retained; unrelated controller credentials are
not forwarded. Git and its HTTPS helper installation remain trusted host software.
Untrusted repository code, README instructions and Git hooks never execute.

The internal metadata-only capture path requires a root containing only `.git`.
It reuses raw Git commit/tree/blob hash verification, source path/type/credential
checks and the existing source budgets. No worktree or index is created or checked
for this private temporary repository. Local inputs retain their full clean
worktree/index checks. Both paths use the same read-only export implementation.

Temporary Git metadata and source exports are removed on normal return, errors and
Python exception unwinding, including Ctrl-C. POSIX fetches own a process group so
Git's helper children can also be terminated. Windows cleanup uses the installed
`taskkill` tree operation when available; Windows/macOS have not been validated for
this increment. Hard controller termination or host failure can leave temporary
data; no persistent recovery journal is added here.

## Limits

Every fetch/metadata subprocess has a 60-second deadline. Git diagnostic output
has a 128 KiB threshold per stream and temporary Git files have a 64 MiB threshold,
checked roughly every 20 ms and again at completion. These are monitored abort
thresholds, not filesystem quotas or a hard network-transfer cap; bursts can
overshoot between observations, and Git process memory is not independently capped.
Server diagnostics are discarded rather than copied into user-facing errors.

Existing capture limits still apply: 2,000 entries, 4 MiB per file, 32 MiB total,
128,000-byte README, 1 MiB per metadata response and depth 32. Symlinks, submodules,
known credential paths and unsafe/colliding paths are denied before export.
Dependencies and Git LFS objects are not installed or expanded.

## Inspection provenance and compatibility

URL inspection adds `remote` to the existing schema 1.1 inspection JSON:

```json
{
  "url": "https://github.com/OWNER/REPO",
  "requested_ref": "main",
  "resolved_ref": "refs/heads/main",
  "git_commit": "FULL_RESOLVED_COMMIT_SHA"
}
```

The field is absent for local inputs. A full-SHA request has `resolved_ref: null`;
default-branch requests have `requested_ref: null`. SHA inputs are normalized to
lowercase. The existing `source`, policy and plan identities remain unchanged:
identical local and remote commits produce identical source and plan identities.
The URL describes where bytes were obtained; it is not a public attestation or a
claim that a repository is trustworthy. Inspection JSON is not authenticated audit
evidence and is not accepted as a passport input.

URL audits retain schema 1.2 with additive `remote` provenance and `repo` equal to
the canonical HTTPS repository URL. Local audit JSON keeps its existing path and
has no `remote` field. URL/ref/commit/scope consistency is checked before storage;
the HMAC covers the origin fields together with source, plan, policy and observed
runtime results. Evidence remains readable after temporary source deletion.

`report` validates the recorded origin against the captured root commit and
preserves it in JSON/Markdown while omitting runtime host paths. Tampering fails
authentication; inconsistent signed origin fields are rejected. No source is
refetched or executed during reporting. Origin identifies where source was
obtained; local HMAC remains neither a public signature nor GitHub attestation.

Secret redaction also applies to ref names. For example, a valid branch named
`api_key=demo` is stored as `api_key=[REDACTED]`. Live selection still validates the
original Git ref before fetching/storage. A stored label containing the exact
redaction marker is read as display-only metadata, not another executable ref.
Authentication, canonical URL, root scope and exact commit binding remain required;
unredacted records retain full ref consistency checks. Masked names cannot be
reconstructed or independently compared after their hidden characters are removed.

JSON summaries label affected records `remote_ref_status: redacted-display-only`;
Markdown tells the reader to use `git_commit` for the audited revision. Existing
authenticated records with masked ref labels can be exported without rewriting
them or retaining an unredacted copy. Fully masked labels work even after the
secret environment used during storage is removed. No redacted label is reused
for Git resolution, and URL/commit identities that cannot be validated still fail.

Passport, diagnose, recheck and trial still require local source arguments.
Passports explicitly reject URL audit evidence, preserving the existing local
repository-binding contract. URL source refresh for those workflows, private
GitHub authentication, dependency setup and InstaBox are separate work.

## Acceptance checks

| ID | Required behavior | Coverage |
|---|---|---|
| GH-001 | Strict public repository-root URLs; reject credentials, alternate hosts and links into trees | `tests/unit/test_github.py`, CLI smoke |
| GH-002 | Resolve default/branch/tag/full-SHA inputs; reject missing/ambiguous/unsafe refs | Unit advertisements and real Git ref integration |
| GH-003 | Fetch the resolved commit even if its branch moves | Real Git moving-ref integration; mismatch unit test |
| GH-004 | No checkout, target execution, hooks or credential helpers | Metadata-only Git integration, CLI execution-denial checks, transport configuration tests |
| GH-005 | Reuse source identity and path/type/size restrictions | Local/remote identity equality; symlink/submodule/credential/oversized-source integration |
| GH-006 | Bound fetch duration/output/storage and clean up on errors/cancellation | Subprocess limit/cancellation tests and context cleanup integration |
| GH-007 | Preserve local inspection; emit remote provenance and honest empty plans | Local regressions, remote JSON/readable CLI integration |
| GH-008 | Ship URL support in the wheel and deterministic CI gate | Installed artifact smoke; core integration selection |

Deterministic integration uses real Git processes and synthetic local repositories,
substituting only the network transport in the test. Production transport remains
HTTPS-only. No model credentials or live GitHub service are required by CI.

## URL audit acceptance checks

| ID | Required behavior | Coverage |
|---|---|---|
| GHA-001 | No approval means no fetch/source/Docker activity | CLI smoke; installed-wheel approval gate |
| GHA-002 | Default/branch/tag/SHA selection uses canonical immutable source identity | Real Git named-selection tests; inspect/audit source and plan equality in Docker |
| GHA-003 | Actual restricted Docker execution establishes PASS/FAIL | `test_github_audit_docker.py` default/pinned pass/fail cases |
| GHA-004 | Missing prerequisites, denied plans and uncertain runtime cannot PASS | Real Git policy/missing-Docker tests; actual timeout/daemon-loss checks and simulated lost cleanup acknowledgement |
| GHA-005 | Temporary sources and owned containers are cleaned before finalization | Normal/error/cancellation Git tests; source-finalization ordering; independent Docker absence probes |
| GHA-006 | HMAC-bound origin survives cleanup and is reportable | Evidence/unit summary/tamper tests; actual Docker record/report round trip |
| GHA-007 | Local workflows remain compatible; unsupported remote workflows fail clearly | Existing local/evidence/passport regressions; URL command guards |
| GHA-008 | Installed artifact exposes URL audit/ref and enforces approval | Installed help and no-fetch approval smoke; existing core/sandbox CI selectors |
