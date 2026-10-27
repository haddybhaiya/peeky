# Open models and Alan/Orcha decision (OpenFire)

The organizer's Town Hall: **"Alan integration isn't mandatory. Open models are preferred."** The public Luma rules still advertise "Alan + open models"; confirm organizer interpretation. For the product choose transparent, openly licensed model weights whenever possible, disclose exact checkpoints and inference provider. Open-source **application code** does not make a proprietary hosted LLM open source.

## Implemented Phase 3 selection: BYOK Gemma

The owner selected **Gemma** and supplied their own Google AI Studio key. The single adapter uses the reviewed OpenAI-compatible endpoint with exactly `gemma-4-31b-it`; Google's authenticated model list confirmed availability. Gemma 4 31B instruction-tuned is an open-weight general-purpose checkpoint with coding capabilities (Apache 2.0 per Google's card), not a dedicated Qwen/CodeGemma checkpoint. No proprietary Gemini fallback is permitted. Hosted model/version and usage are recorded; the service does not attest an exact weights revision. A successful live gate requires separate evidence, not availability or mock results.

This is BYOK: the user owns the key, provider account and quota. Current published Gemma 4 pricing is free; evidence labels that pricing-derived zero separately from returned billing. Missing response/usage/cost remains unknown. See `phase3-repair.md` and `work_review.md` for actual calls, results and limits.

Official sources: [model card](https://ai.google.dev/gemma/docs/core/model_card_4), [Gemma API](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api), [protocol](https://ai.google.dev/gemini-api/docs/openai/), [pricing](https://ai.google.dev/gemini-api/docs/pricing#gemma-4).

## Earlier planning recommendation (not implemented)

**Qwen2.5-Coder-7B-Instruct** (Apache 2.0 model weights; confirm exact distribution/license) via a local endpoint or an opted-in provider hosting the open weights. Role: reason about setup logs and generate bounded README-only patch proposals. Do not add a frontier closed model as an undisclosed shortcut. OpenAI-compatible API is a *protocol*, not evidence that the underlying model is open.

## Is Laya usable?

**Yes, for an optional classifier/triage stage, not code or README rewriting.** Laya from `NandhaKishorM/laya` / `convaiinnovations/laya` is a distinct open-source decision model (Apache-2.0 checkpoint). It responds to fixed-choice / scoring / yes-no questions with probabilities; it does **not** generate arbitrary natural language, instructions or source code. It is not TypeSafe's hosted **Jev** (closed model). A possible useful stage is categorizing failure logs as `DEPENDENCY`, `ENTRYPOINT`, `ENVIRONMENT`, `PERMISSION`, `UNKNOWN` before the open coding model reasons. But categorization may be unnecessary for a one-day MVP; heuristic routing is enough until measured model value is demonstrated.

## Orcha?

`open-orcha/orcha` is a multi-agent orchestration framework, **not an open-weight language model**. The term Orcha is overloaded across several unrelated GitHub projects; only choose a specific repo for an explicit orchestration need. OpenFire does not require Orcha. Do not build our app around an unrelated orchestration layer merely to satisfy "open-source AI".

## Responsible provider config

No secrets committed; pass endpoint/model/key via environment; opt-in before remote repo content leaves machine; bound 12k input characters; redact tokens and personal data; record checkpoint/provider and costs; mock deterministic tests, one genuine live test only if enabled. Model output is untrusted, strict schema, patch lint, independent verify.

Sources: https://github.com/NandhaKishorM/laya ; https://huggingface.co/convaiinnovations/laya ; https://github.com/open-orcha/orcha ; https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct ; https://luma.com/2k6cxr0n

## Final attribution review (2026-10-27)

The current Google model card identifies Google DeepMind's Gemma 4 as open-weight, Apache 2.0, with coding and native function-calling capabilities; the hosted Gemma API documentation lists `gemma-4-31b-it`. This project uses that managed API, not local inference, a dedicated coding-only checkpoint, or an attested immutable hosted weights digest. Sources: [Google model card](https://ai.google.dev/gemma/docs/core/model_card_4), [hosted API](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api). Current organizer rules at [OpenFire](https://luma.com/2k6cxr0n) say Alan + open models; earlier optional-Alan notes are historical and require clarification.
