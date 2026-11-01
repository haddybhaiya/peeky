# Public GitHub URL inspection

This owner-authorized post-MVP increment adds URL resolution and inspection.
It implements GH-001..GH-008 below. URL-based Docker audits are the next increment;
this command produces a plan, never execution evidence or a PASS verdict.

## Commands

```bash
peeky inspect https://github.com/OWNER/REPO
peeky inspect https://github.com/OWNER/REPO.git --ref main --json
peeky inspect https://github.com/OWNER/REPO --ref refs/tags/v1.0
peeky inspect https://github.com/OWNER/REPO --ref FULL_40_CHARACTER_COMMIT_SHA
```

Local directory inspection keeps its existing behavior and JSON shape. `--ref`
applies only to URL inspection. Public repository roots on literal
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
evidence and is not accepted as a passport input. The audit evidence schema stays
1.2. Audit, passport, diagnose, recheck and trial continue to use local sources.

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
