# Source capture, identity and Phase 1 boundaries

## Supported source and scope

Select a committed local Git repository or a committed subdirectory. The selected directory must contain a committed regular `README.md`. Source capture checks that selected tracked bytes and index entries agree with HEAD and rejects non-ignored untracked files in that scope. Unrelated dirty files outside a selected subdirectory do not affect its export. Bare repos, linked worktrees (`.git` redirection files), submodules, LFS/content-filter checkouts and custom encoding conversions are unsupported.

Input paths containing parent traversal, symlink/reparse ancestors or a non-directory are rejected. Export paths must be relative UTF-8 portable names: no traversal, absolute/drive paths, backslashes, controls, Windows reserved names, trailing spaces/dots or case collisions. Git symlink/submodule modes and filesystem special files are rejected. Known credential paths (`.env*` except examples/templates, `.ssh`, `.aws`, `.azure`, `.gnupg`, private SSH key names) are rejected when tracked. Ignored untracked files and Git metadata are not exported. This is not a complete secret scanner.

## Capture mechanics

The controller resolves HEAD to a full commit ID and reads raw commit, tree and blob objects through Git plumbing. It recomputes each consumed object's Git hash, including SHA-1 or SHA-256 object headers. It does not checkout, run archive filters, initialize submodules, fetch, install or import target material. Git environment overrides and global/system config are excluded, hooks/fsmonitor are disabled, lazy fetching is disabled and protocols are denied. Local Git configuration is not interpreted as controller policy. Git subprocess output and duration are bounded.

Working files are compared directly to committed blobs without running clean/smudge filters. Exact bytes match, or UTF-8 CRLF checkout bytes may normalize to the committed LF bytes; all other differences block. Exports always contain original Git blob bytes. Git index entries and HEAD are checked again before capture returns. Only files in the selected scope contribute to the source manifest, while the containing commit and selected Git tree are also recorded.

Each export uses a fresh temporary directory, regular files with read-only permissions and read-only directory permissions where supported. File-set, symlink and byte integrity are verified before use. CLI audit mounts this export read-only; it does not mount the live input directory. Host-owner access can still change permissions or files, so this is controlled materialization plus integrity checks, not a filesystem security boundary against a hostile concurrent host process. Temporary exports are removed when their context exits.

## Identity, policy and controller state

`SourceIdentity` contains full `git_commit`, selected `git_tree`, relative `scope`, `dirty=false`, and a sorted manifest of file paths, Git modes, sizes and SHA-256 content hashes. `source_sha256` hashes the canonical manifest. Identical bytes/modes can share a source hash across different commits; revision-sensitive comparisons also require commit equality.

The frozen controller `RunPolicy` defines parser, command, capture and runner budgets. Its canonical JSON hash is `policy_sha256`. A plan hash covers the complete source identity, ordered steps and policy hash. A run gets a separate UUID, so independent inspections share source/policy/plan identity while retaining distinct run IDs.

Image input syntax is restricted to `python:TAG` or `python@sha256:` followed by exactly 64 lowercase hexadecimal characters. Registry-shaped names such as `python:5000/other` and malformed digests are rejected. Syntactic acceptance is not verification of a cached image's contents or resolved digest; that remains Phase 2.

The implemented state transitions are `CREATED -> INSPECTED -> APPROVED -> SANDBOX_RUN -> OBSERVED -> FINALIZED`, with terminal BLOCKED exits before observation. Invalid transitions are rejected. Inspect emits an INSPECTED plan without running Docker or target code. Audit writes terminal evidence containing state/history, source and policy. This is not a durable resumable workflow or a signed append-only journal; intermediate/crashed attempts are not independently persisted yet.

## Limits

Default limits: 12 commands; 400 characters per command; 24 arguments of at most 300 characters; README 128,000 bytes; 2,000 source entries; 4 MiB per blob/file; 32 MiB total source; 1 MiB per Git metadata response; 32 nested directories; 15 seconds per Git subprocess. Source names are limited to 255 UTF-8 bytes per component and 1,024 bytes per relative path. The command runner retains its existing 20-second client timeout and offline non-root resource restrictions; Phase 2 must still verify real container behavior and cleanup.

## Evidence and passport compatibility

Schema 1.1 evidence adds source identity, full policy/hash, run state/history and plan hash. The reducer requires result IDs/commands to match the ordered steps and PASS exit codes to be zero. An observed valid failure remains FAIL even when later steps were not executed; incomplete coverage alone cannot become PASS. Missing Docker writes BLOCKED/INCONCLUSIVE with no results.

Passports require matching clean source and commit, matching policy/plan, finalized legal state history, exact README steps and mechanically consistent complete PASS results. Changing a source file or committing a new revision invalidates prior guidance. Schema 1.0 is deliberately rejected. These checks establish internal consistency and source binding, not authenticity of caller-supplied JSON or real execution. Signed provenance, image digest enforcement and independent execution validation remain later gates. No model or release feature is introduced here.
