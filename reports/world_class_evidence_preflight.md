# World-Class Evidence Preflight

Generated at: `2026-06-13`

## Summary

- decision: `collection-preflight-blocked`
- ready to claim world-class: `false`
- preflight counts as evidence: `false`
- credential value exposed: `false`
- collection ready: `1`
- collection blocked: `3`
- source checks: `10` pass / `19` total
- repair rows: `13` blocked / `13` total

This preflight report checks whether an operator can start collecting the remaining external or human evidence. It never accepts evidence, prints secret values, or changes the world-class ledger.

## Submission Kit Handoff

- submissions directory: `evidence/world_class/submissions`
- prepare drafts: `python3 scripts/yao.py world-class-submission-kit . --output-dir evidence/world_class/submissions`
- prepare drafts with artifact SHA prefill: `python3 scripts/yao.py world-class-submission-kit . --output-dir evidence/world_class/submissions --prefill-artifacts`
- validate intake: `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions`
- review queue: `python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions`
- refresh ledger: `python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions`
- guard claims: `python3 scripts/yao.py world-class-claim-guard .`
- drafts count as evidence: `false`
- artifact prefill counts as evidence: `false`
- submission refs ready: `7` / `7`
- supporting evidence ready: `31` / `31`

Generate the submission kit after the real provider, human, native-permission, or native-client work exists. The generated JSON drafts remain `template_only: true` until an operator edits them with real aggregate artifact references and matching SHA-256 digests. The prefill command only inserts local artifact SHA-256 digests; it does not make a draft count as evidence.

| Role | Copy to artifact_refs | Ready | Meaning |
| --- | --- | --- | --- |
| `submission-ref` | `true` | `7 / 7` | Rows marked submission-ref are the aggregate paths expected in artifact_refs. |
| `supporting-evidence` | `false` | `31 / 31` | Supporting-evidence rows help reviewers audit the packet but do not all need to be copied into artifact_refs. |

`submission-ref` rows are the only checklist rows expected in `artifact_refs`; `supporting-evidence` rows stay available for audit context and reviewer traceability.

## Evidence Items

| Evidence | Status | Intake | Review | Next action |
| --- | --- | --- | --- | --- |
| `provider-holdout` | `blocked` | `awaiting-submission` | `awaiting-submission` | Set OPENAI_API_KEY in the operator shell; never commit or print the value. |
| `human-adjudication` | `ready-for-human-review` | `awaiting-submission` | `awaiting-submission` | Assign a real reviewer identity before claiming human adjudication. |
| `native-permission-enforcement` | `blocked` | `awaiting-submission` | `awaiting-submission` | Attach a real target-client or external installer runtime guard; metadata fallback is not enough. |
| `native-client-telemetry` | `blocked` | `awaiting-submission` | `awaiting-submission` | Install a real Browser, Chrome, IDE, or provider client that emits metadata-only events. |

## Repair Checklist

Repair rows convert preflight and source blockers into concrete operator actions. They are guidance only and do not count as completion evidence.

| Evidence | Type | Target | Status | Next action |
| --- | --- | --- | --- | --- |
| `provider-holdout` | `precheck` | `openai-api-key` | `blocked` | Set OPENAI_API_KEY in the operator shell; never commit or print the value. |
| `provider-holdout` | `source-check` | `model_executed_count` | `blocked` | Run provider-backed output-exec with real credentials. |
| `provider-holdout` | `source-check` | `token_observed_count` | `blocked` | Provider execution should return non-estimated token usage. |
| `human-adjudication` | `precheck` | `human-reviewer` | `blocked` | Assign a real reviewer identity before claiming human adjudication. |
| `human-adjudication` | `source-check` | `pending_count` | `blocked` | Record a reviewer choice and reason for every pair. |
| `human-adjudication` | `source-check` | `judgment_count` | `blocked` | Every pair needs one valid human judgment. |
| `human-adjudication` | `source-check` | `reviewer_metadata_present` | `blocked` | Record reviewer and reviewed_at before adjudication can count. |
| `human-adjudication` | `source-check` | `blind_review_attested` | `blocked` | Set reviewer_attestation only after choices are completed before opening the answer key. |
| `human-adjudication` | `source-check` | `ready_for_human_evidence` | `blocked` | Complete all reviewer decisions with metadata and rationale, plus blind-review attestation and integrity fingerprints. |
| `native-permission-enforcement` | `precheck` | `native-guard` | `blocked` | Attach a real target-client or external installer runtime guard; metadata fallback is not enough. |
| `native-permission-enforcement` | `source-check` | `native_enforcement_count` | `blocked` | Collect real target-client or external runtime guard proof. |
| `native-client-telemetry` | `precheck` | `external-client` | `blocked` | Install a real Browser, Chrome, IDE, or provider client that emits metadata-only events. |
| `native-client-telemetry` | `source-check` | `external_source_events` | `blocked` | Import at least one metadata-only event from a real client. |

## Provider Holdout

- status: `blocked`
- ledger: `pending`
- submission: `evidence/world_class/submissions/provider-holdout.json`
- prepare draft: `python3 scripts/yao.py world-class-submission-kit . --evidence-key provider-holdout --output-dir evidence/world_class/submissions`
- prepare draft with artifact SHA prefill: `python3 scripts/yao.py world-class-submission-kit . --evidence-key provider-holdout --output-dir evidence/world_class/submissions --prefill-artifacts`
- submission refs ready: `1` / `1`
- supporting evidence ready: `6` / `6`

### Prechecks

| Check | Kind | Current | Status | Next action |
| --- | --- | --- | --- | --- |
| Output eval cases | `file` | `present` | `pass` | Keep output holdout cases available before provider execution. |
| Provider runner | `file` | `present` | `pass` | Use the provider runner instead of the local command runner for model-backed evidence. |
| Provider credential | `env` | `not-set` | `missing` | Set OPENAI_API_KEY in the operator shell; never commit or print the value. |
| Provider model | `env` | `not-set` | `optional` | Optionally set YAO_OUTPUT_EVAL_MODEL; the runbook defaults to gpt-4.1-mini. |

### Source Checks

| Check | Current | Expected | Status | Next action |
| --- | --- | --- | --- | --- |
| Provider model run | `0` | `>0` | `blocked` | Run provider-backed output-exec with real credentials. |
| Timing observed | `10` | `>0` | `pass` | Provider execution should record timing metadata. |
| Token usage observed | `0` | `>0` | `blocked` | Provider execution should return non-estimated token usage. |

## Human Adjudication

- status: `ready-for-human-review`
- ledger: `pending`
- submission: `evidence/world_class/submissions/human-adjudication.json`
- prepare draft: `python3 scripts/yao.py world-class-submission-kit . --evidence-key human-adjudication --output-dir evidence/world_class/submissions`
- prepare draft with artifact SHA prefill: `python3 scripts/yao.py world-class-submission-kit . --evidence-key human-adjudication --output-dir evidence/world_class/submissions --prefill-artifacts`
- submission refs ready: `2` / `2`
- supporting evidence ready: `8` / `8`

### Prechecks

| Check | Kind | Current | Status | Next action |
| --- | --- | --- | --- | --- |
| Blind review kit | `file` | `present` | `pass` | Open the blind review kit and record real reviewer choices with required rationale. |
| Decision template | `file` | `present` | `pass` | Import real A/B decisions with reviewer, reviewed_at, winner_variant, confidence, reason, and truthful blind-review attestation via `python3 scripts/yao.py output-review-import --input <reviewer-decisions.json> --blind-review-attested --run-adjudication`. |
| Decision importer | `file` | `present` | `pass` | Use the importer to reject raw content fields and normalize reviewer decisions before adjudication. |
| Human reviewer | `human` | `external-human-action` | `human-required` | Assign a real reviewer identity before claiming human adjudication. |

### Source Checks

| Check | Current | Expected | Status | Next action |
| --- | --- | --- | --- | --- |
| Review pairs exist | `5` | `>0` | `pass` | Generate the blind A/B review pack. |
| No pending decisions | `5` | `==0` | `blocked` | Record a reviewer choice and reason for every pair. |
| Judgments complete | `0` | `==pair_count` | `blocked` | Every pair needs one valid human judgment. |
| No invalid decisions | `0` | `==0` | `pass` | Fix malformed winner/confidence entries. |
| Reviewer metadata | `False` | `true` | `blocked` | Record reviewer and reviewed_at before adjudication can count. |
| Reason required | `True` | `true` | `pass` | Keep reason mandatory for every imported or direct reviewer decision. |
| Blind review attested | `False` | `true` | `blocked` | Set reviewer_attestation only after choices are completed before opening the answer key. |
| Raw content attested | `True` | `true` | `pass` | Attest that reviewer decisions exclude raw prompts, outputs, transcripts, messages, and private user content. |
| Raw content blocked | `False` | `false` | `pass` | Adjudication evidence should store prompt hashes and reviewer metadata, not raw prompts, outputs, transcripts, or messages. |
| Human evidence ready | `False` | `true` | `blocked` | Complete all reviewer decisions with metadata and rationale, plus blind-review attestation and integrity fingerprints. |

## Native Permission Enforcement

- status: `blocked`
- ledger: `pending`
- submission: `evidence/world_class/submissions/native-permission-enforcement.json`
- prepare draft: `python3 scripts/yao.py world-class-submission-kit . --evidence-key native-permission-enforcement --output-dir evidence/world_class/submissions`
- prepare draft with artifact SHA prefill: `python3 scripts/yao.py world-class-submission-kit . --evidence-key native-permission-enforcement --output-dir evidence/world_class/submissions --prefill-artifacts`
- submission refs ready: `2` / `2`
- supporting evidence ready: `11` / `11`

### Prechecks

| Check | Kind | Current | Status | Next action |
| --- | --- | --- | --- | --- |
| Permission policy | `file` | `present` | `pass` | Keep approved high-permission capabilities explicit. |
| Runtime probes | `file` | `present` | `pass` | Refresh runtime permission probes after packaging changes. |
| Native guard | `external` | `external-integration-required` | `external-required` | Attach a real target-client or external installer runtime guard; metadata fallback is not enough. |

### Source Checks

| Check | Current | Expected | Status | Next action |
| --- | --- | --- | --- | --- |
| Native enforcement | `0` | `>0` | `blocked` | Collect real target-client or external runtime guard proof. |
| Probe failures | `0` | `==0` | `pass` | Runtime permission probes must stay clean. |
| Installer support | `True` | `true` | `pass` | Installer enforcement is supporting evidence, not native proof. |

## Native Client Telemetry

- status: `blocked`
- ledger: `pending`
- submission: `evidence/world_class/submissions/native-client-telemetry.json`
- prepare draft: `python3 scripts/yao.py world-class-submission-kit . --evidence-key native-client-telemetry --output-dir evidence/world_class/submissions`
- prepare draft with artifact SHA prefill: `python3 scripts/yao.py world-class-submission-kit . --evidence-key native-client-telemetry --output-dir evidence/world_class/submissions --prefill-artifacts`
- submission refs ready: `2` / `2`
- supporting evidence ready: `6` / `6`

### Prechecks

| Check | Kind | Current | Status | Next action |
| --- | --- | --- | --- | --- |
| Native telemetry host | `file` | `present` | `pass` | Use the native host to receive metadata-only client events. |
| Hook recipes | `file` | `present` | `pass` | Refresh telemetry hook recipes before external client installation. |
| External client | `external` | `external-integration-required` | `external-required` | Install a real Browser, Chrome, IDE, or provider client that emits metadata-only events. |

### Source Checks

| Check | Current | Expected | Status | Next action |
| --- | --- | --- | --- | --- |
| External events | `0` | `>0` | `blocked` | Import at least one metadata-only event from a real client. |
| Adoption sample | `1` | `>0` | `pass` | Telemetry must include adoption outcome evidence. |
| Raw content blocked | `False` | `false` | `pass` | Telemetry must stay metadata-only. |

## Boundary

- Environment variables are reported only as `set` or `not-set`; values are never printed.
- Human-required and external-required states are operator actions, not accepted evidence.
- The world-class ledger remains the source of truth for `ready_to_claim_world_class`.
