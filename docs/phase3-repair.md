# Phase 3: BYOK Gemma proposals and approved README rechecks

The owner selected **Gemma**, replacing the earlier Qwen recommendation. One OpenAI-compatible Chat Completions adapter uses `gemma-4-31b-it` at `https://generativelanguage.googleapis.com/v1beta/openai`. Gemma 4 31B instruction-tuned is an open-weight general-purpose checkpoint with coding capabilities, not a dedicated Qwen/CodeGemma coding checkpoint. Google's model card identifies Apache 2.0 licensing. Hosted responses identify the model but do not attest an exact weights Git revision; evidence explicitly leaves that field unknown.

## BYOK and consent

Bring your own Google AI Studio key. No bundled credentials, managed billing or model download is added. Baseline audit/inspect/doctor never read provider configuration or contact the model. Mock tests need no key.

```dotenv
PEEKY_MODEL_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
PEEKY_MODEL_NAME=gemma-4-31b-it
PEEKY_MODEL_API_KEY=YOUR_GOOGLE_AI_STUDIO_KEY
PEEKY_MODEL_CONSENT=false
```

Set consent true and explicitly pass `--model-consent` after reviewing disclosure. `--env-file .env` reads only four unique literal settings from an explicitly selected bounded regular file; it never sources a shell, expands variables or auto-loads a scanned target's configuration. Keys are excluded from repr and evidence. No provider key/context enters a container. Endpoint/model are allowlisted; no arbitrary routing, paid fallback or redirect is permitted. Ambient HTTP proxies are disabled.

Google currently lists Gemma 4 input/output as free, with no paid tier. When billing is absent from the response, evidence records `cost_basis=published_free_tier`, the pricing source/date and returned token usage. This is not a measured invoice. Missing usage/cost alone does not block a valid proposal under the owner's explicit instruction; it is recorded as unknown, with published free pricing separate. A missing completion still blocks the live gate. API failures are INCONCLUSIVE.

## Frozen inputs and proposals

Diagnosis requires authenticated schema 1.2 target FAIL evidence matching the complete clean source, command, policy, finalized history and runtime provenance. Infrastructure failure, incomplete logs or uncertain cleanup cannot authorize repair. Before contacting Gemma the operator freezes `--expected-command` and an exact `--expected-stdout` marker. The command must be python/python3 plus one existing captured `.py` path without flags. The operator owns this independent oracle; an inappropriate entrypoint or weak marker is not a general correctness proof.

Only redacted README, selected filenames, original stdout/stderr and expected command are sent. System plus context is capped at 12,000 characters without silent truncation. Known secrets, the configured key and context email addresses are removed. Requests have no tools, streaming or automatic retries; output is capped at 1,800 tokens and 65,536 bytes. Network operations use 45-second socket timeouts and a 45-second elapsed read budget checked between chunks; pending I/O may add one socket timeout and DNS remains OS-controlled. The earlier 10-second response wait was too short for observed Gemma generation latency.

Requests use Google's documented minimal thinking level with thought inclusion disabled. If Google nevertheless returns an explicitly flagged, well-delimited thought prefix, the adapter discards only that provider frame; unflagged/unterminated framing is rejected. The remaining output must be one strict JSON object with exactly `reason`, `assumptions`, `candidate_diff`, `confidence`, `source_refs`. Duplicate keys, non-finite/bool confidence, incorrect/unbounded types, unknown references, tool calls, truncation and model substitution fail closed. Model assertions have no verdict authority. Errors retain bounded redacted details and consume the reserved attempt.

The diff parser accepts only `--- a/README.md`, `+++ b/README.md` and one exact-context unified hunk. The only resulting change may replace the original single opted-in command line with the frozen expected command. Other README lines, annotations, scripts, tests, assertions, modes, configuration, evidence and policy remain identical. No fuzzy application, shell patcher, git apply, rename or traversal is supported. This is deliberately narrower than arbitrary README editing.

## Approval and clean recheck

Diagnosis saves a signed PROPOSED artifact and prints its diff and approval digest. It never applies the candidate. A human reviews that exact source/patch/oracle/baseline/provider artifact and supplies the digest to a separate `recheck --approve-proposal sha256:...` command. Artifact/source revision/policy/image drift invalidates approval. The model cannot supply approval fields.

Recheck reruns the unchanged original snapshot in a new restricted container. It then creates a separate temporary Git repository from frozen bytes, changes only the approved README line and captures a real clean derived commit/tree. Hooks, templates, external Git configuration and signing are disabled; no target code runs on the host. Every non-README hash and executable mode must match. The candidate runs in another fresh container using the same image ID and policy. The target worktree/index are never patched or committed.

Only the controller records VERIFIED: fresh baseline FAIL, candidate PASS, matching observed image IDs, distinct containers, confirmed cleanup and the exact frozen stdout marker for the exact expected command. A zero exit without the marker remains INCONCLUSIVE. Both redacted execution records and the signed repair comparison are retained. This verifies one frozen command/marker, not universal installation correctness or model superiority.

## Attempts and tests

Exclusive durable claims reserve one diagnosis per baseline and one recheck per proposal before dispatch. Reinvocation with the same state cannot retry, including after crashes/errors. A trusted operator can deliberately authorize a separate manual attempt. `scripts/validate_phase3.py --live` prepares only the reviewed synthetic fixture, runs its baseline, makes at most one authorized call and stops for human review. Prior attempts remain preserved.

T-018/019: typed provider/consent/BYOK; T-020/021: README-only and anti-weakening; T-022: real fresh Docker comparisons with an explicitly mocked model; T-023: retained separately authorized genuine Gemma trace; T-024: persistent budgets; T-025: injection remains data. Deterministic tests never read the real model key or call Google. The selected live evidence test fails rather than skips missing/incomplete trace. Actual results and live/human blockers belong in `work_review.md`.

References: [OpenAI-compatible protocol](https://ai.google.dev/gemini-api/docs/openai/), [Gemma API](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api), [model card](https://ai.google.dev/gemma/docs/core/model_card_4), [pricing](https://ai.google.dev/gemini-api/docs/pricing#gemma-4).


Retained-response decoding is separate from HTTP dispatch. A controller may revalidate an authenticated original completion after a framing fix, linking its original record hash and preserving the raw response, request hash/ID, original token usage and latency. It records zero new network requests; it cannot invent a model call or rewrite the original evidence. Human approval still applies to the resulting exact proposal. The real fixture completed this path and the approved fresh recheck; see work review for the full chain.
