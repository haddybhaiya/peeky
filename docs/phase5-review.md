# Phase 5: local final review and submission preparation

Phase 5 includes FS-009/010 and T-033..T-037: reporting, packaging, setup/limitations review and an actual captioned demo. This is more than a code review. Local preparation does not close external submission or the missing video gate. Phase 4's local protocol passed; its live comparison remains INCONCLUSIVE (0/2 comparable pairs). The owner explicitly authorized this final preparation despite that availability limitation; it is not relabeled a successful comparison.

## Evidence summary export

```powershell
uv run --locked peeky report --evidence PATH_TO_AUDIT.json --evidence PATH_TO_STUDY.json --output .peeky/review-export
```

Select one to sixteen explicit authenticated audit, pair or study JSON files. The command performs bounded regular-file reads and verifies local HMAC before writing a new exclusive output directory. It produces a signed JSON summary under `records/`, `summary.md` with an exact bytes hash, and a convenience `index.json`. It never executes a target, calls a model or refreshes source verification. An incomplete recorded audit PASS is downgraded to INCONCLUSIVE. Missing usage remains unknown, and study attempt denominators and negative outcomes remain visible. Study summaries preserve authenticated aggregates without automatically following private dependency paths; independent verification of the original traces is a separate review operation.

Exports omit raw streams, provider prompts, API headers, absolute host paths and the private controller key. Original redacted logs stay in ignored local evidence. Summary provenance identifies canonical input record hashes, selected source/image/policy identities and exact Markdown bytes. Local HMAC is not public attestation; do not share the private key. Pattern redaction is not a guarantee against every possible secret encoding. Review any bundle before publishing.

## Acceptance review

| ID | Local review | Remaining boundary |
|---|---|---|
| T-033 | Missing execution cannot become PASS; tampering rejected; byte-exact JSON/Markdown link; actual study preserves all negatives | Reports summarize recorded observations, not new verification |
| T-034 | Build final wheel, install without index/dependencies into a clean temporary venv, run module/console/inspect smoke | One Windows host, not independent two-machine reproduction |
| T-035 | CI inspected: pinned checkout/setup actions, locked dependencies, deterministic tests and pre-reviewed Docker image; no model key, env file, secret interpolation or live provider step | No Phase 4/5 remote CI run is inferred from local changes |
| T-036 | Required docs, setup, model attribution, architecture, limitations, source references and public manifest reviewed | Actual published branch/repository must be reviewed by owner |
| T-037 | Caption plan and screenshot-ready retained evidence prepared; all quoted values come from authenticated records | Actual 90–120 second screen recording and human review remain NOT DONE |

## Findings resolved during review

The README lead still described Phase 4 as planned and Phase 3 CI as pending despite later ledger entries. Corrected it to the current implemented harness and inconclusive live outcome. Kept historical work-review entries intact. The report exporter explicitly labels SUMMARY_ONLY rather than advertising another verification. The earlier Windows report newline defect is fixed and its failed and corrected artifacts remain preserved.

## Deadline and eligibility review

Checked the organizer's [OpenFire page](https://luma.com/2k6cxr0n) on 2026-10-27: build ends October 27 at 8 PM IST; submission form closes at 10 PM IST. It requests an X post with a 1–3 minute demo, a working link and public open-source GitHub repository. The local stricter 90–120 second demo plan fits that range.

The current public rules state **Alan + open models**. Earlier repository notes said Alan optional based on Town Hall context, which is not independently available here. This project uses Google-hosted Gemma; Alan integration/use is not evidenced by this implementation. Organizer confirmation is required to resolve that conflict; do not claim eligibility as verified or add an unrequested integration under deadline pressure. Nothing was posted, submitted or published by the controller.

## Actual results and limits

Retained Phase 3: genuine Gemma proposal, exact owner approval and fresh original FAIL/candidate PASS under frozen marker; not a new Phase 5 model request. Retained Phase 4: baseline 0/2 PASS, passport 1/2 PASS, three HTTP 500 responses, 0/2 comparable pairs. All original records remain private and immutable. No onboarding improvement claim, measured free billing claim or exact hosted weights attestation. Updated target commit identities after the ten Phase 4 commits belong to fresh Phase 5 audits; they must not be silently substituted into the older Phase 4 controls.

The final work-review entry records observed test counts, fresh three-fixture outcomes, report/package hashes and evidence paths. The complete phase remains OPEN at the actual-video and organizer eligibility gates. A second machine is desirable but has not been tested. Local source artifacts and summaries are prepared; no remote CI success, video, X post, form submission or release is invented.

Final local gate: **204 passed, 1 live deselected, 0 skips in 400.68s**. Lint/format (48 files), mypy (43), docs (19), built/installed wheel and fresh three-fixture gate passed. Actual JSON/Markdown: `.peeky/phase5-validation/summary/`; CLI export: `cli-report/`; private hash-indexed bundle: `private-review-evidence.zip`; prepared display/captions: `demo.html`, `demo-captions.srt`. The actual video is absent. Phase 4 commits were pushed at bfa78de; Phase 5 edits remain uncommitted/unpushed.
