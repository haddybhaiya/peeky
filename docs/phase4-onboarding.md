# Phase 4: authenticated passports and restricted onboarding trials

`passport.py` accepts only locally authenticated, completed single-command PASS evidence for the current committed source, policy and plan. It requires the exact successful container state, command hash, image ID and container ID. The candidate Markdown carries a `passport-1` HMAC certificate binding its guidance bytes, full source identity, run ID, image, canonical evidence hash and original evidence-file hash. Changed source or guidance invalidates it. HMAC proves local controller integrity, not public execution attestation. The CLI writes exclusively to `AGENTS.generated.md`; existing files and upstream `AGENTS.md` are preserved.

## Trial protocol

`peeky trial REPO --evidence AUDIT.json --expected-command "python smoke.py" --expected-stdout "HELLO_FROM_GOOD_FIXTURE" --approve --model-consent --env-file .env`

This is opt-in BYOK using the existing Google OpenAI-compatible endpoint and `gemma-4-31b-it`. The checkpoint is open-weight and code-capable, but general-purpose; hosted exact weight revision is unknown. The command uses an already successful audit from the same source/image and reserves a single pair before disclosure. No automatic retries or installation are supported. `scripts/validate_phase4.py --live --env-file .env` first audits the reviewed good fixture, then runs one pair. A report file existing, or CLI exit zero after reporting negative outcomes, does not mean target PASS.

Each arm starts a new remote model conversation and independently captures the same source. It receives identical task, system prompt, manifest and README. Only the passport arm additionally receives authenticated candidate guidance. Freeze source commit/tree/manifest/hash, policy, image digest and resolved ID, requested model/checkpoint/endpoint, prompt/tool schema hash, temperature zero, task, operator command/marker oracle, order and budgets. No seed is promised by this endpoint. Each call records the actual served model when available; missing or substituted identities prevent a comparable-pair claim.

The capability boundary is a remote model plus a trusted local dispatcher, not a separate local agent worker process. The remote model receives no host shell, credentials or direct Docker capability. Native function calls alone may request `read_file` (captured manifest, safe relative path, maximum 2,048 bytes) or `run_smoke` (only controller-owned `step-001`, no command override). Repository instructions and model/log text remain data. The dispatcher invokes the existing strict fresh offline Docker runner; no target execution occurs on the host. Baseline and treatment have independent conversations, exports and containers. There is no autonomous framework, filesystem write tool, dependency fetch, GitHub write or release path.

Budgets per arm: two model calls, two tool calls, one execution, 120 seconds, 32,768 token budget, 512 output tokens per call and 12,000 serialized input characters. HTTP timeout is at most 45 seconds within remaining wall budget; response limit is 65,536 bytes. Missing actual usage charges a conservative UTF-8 byte reservation plus output allowance against the budget. This reservation is explicitly not measured token usage or billing. An execution ends the trial; no model follow-up verdict is requested. The controller records the exact command/exit and independently requires runtime verification, matching image and frozen marker within the deadline. Text saying PASS never counts.

## Evidence and reporting

Actual redacted requests/responses, native tool calls/results, source identities, Docker observations, errors, timing and available usage are retained in authenticated exclusive per-arm records, then a paired record. Credentials/authorization headers are not stored. Pattern redaction is bounded and cannot guarantee removal of every form of personal information. Preserve these local artifacts and the private controller key separately; local HMAC records are not portable public attestations.

Every attempted arm stays in its denominator, including provider errors, text-only answers and budget exhaustion. Report PASS/FAIL/BLOCKED/INCONCLUSIVE separately, actual usage or unknown, budget charge, calls and elapsed time. A comparative estimate requires matching controls plus observed source/model identity in both arms. `write_study` accepts at most two authenticated pairs and binds all pair hashes and the final Markdown hash. It retains negative outcomes and discloses adaptive sample selection and fixed ordering. Small samples, hosted load, cache effects and unknown hosted weight revision preclude generalized causal claims.

## Actual local live result, 2026-10-27

Two complete pairs were attempted under identical frozen controls. The second was explicitly added after the first baseline provider error; sample count was not preregistered. No arm was selectively retried. Baseline: **0/2 PASS, 2 INCONCLUSIVE**. Passport: **1/2 PASS, 1 INCONCLUSIVE**. Three Google HTTP 500 responses have no observed model/usage; one genuine Gemma response called native `run_smoke`, and the fresh restricted container passed the frozen independent marker. **Comparable pairs: 0/2. Comparative gate: INCONCLUSIVE. No improvement estimate is claimed.** Total calls: four; no additional calls planned.

Retained local artifacts (ignored, not public fixtures):

- Audit: `.peeky/phase4-validation/audit/a626e83734c040b48d7255bb93e8c3c5.json`.
- First pair: `.peeky/phase4-validation/pair/pairs/8c2e5660a7c948e1a57d2b0ddd594e31.json`.
- Second pair: `.peeky/phase4-validation/pair2/pairs/4aefd888d8b7441995a41335e0f02527.json`.
- Combined authenticated study: `.peeky/phase4-validation/study-final/records/6833697008c3402c9a28886ff692b4bf.json`.
- Human-readable report: `.peeky/phase4-validation/study-final/paired-report.md`.

Shared controls digest: `sha256:7720e0ba28be2f3cb1821aa649cd2c79e6a139ac63ef1da46634c877b2956afa`. Aggregate actual tokens and billing remain unknown because three responses lack usage. The successful response reported 1,871 total tokens. Baseline/passport budget charges are 4,794/7,108 respectively; these are not cost measurements. All original logs remain preserved after redaction. Implementation protocol tests and a real Docker pair with explicitly mocked provider responses are separate from genuine live results.

The initial aggregate study at `study/records/21201cbbb9e74387844fd51587c0320a.json` and its Markdown remain preserved: final checking found Windows CRLF translation made its byte hash inconsistent. The corrected `study-final` record reaggregates the exact same authenticated pairs with LF byte-exact output and zero new requests. The regression test checks actual file bytes. No trial conditions or outcomes changed.
