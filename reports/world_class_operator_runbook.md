# World-Class Operator Runbook

Generated at: `2026-06-14`

## Summary

- decision: `collect-evidence`
- ready to claim world-class: `false`
- runbook counts as completion: `false`
- evidence items: `4`
- pending: `4`
- awaiting submission: `4`
- ready for ledger review: `0`

This runbook coordinates evidence collection only. It does not accept submissions or make world-class completion true.

## Fast Path

1. Run the real external or human work for one evidence item.
2. Generate the matching submission draft.
3. Replace template-only fields with aggregate evidence and provenance.
4. Validate intake, review the queue, refresh the ledger, then run the claim guard.

## Evidence Items

| Evidence | Ledger | Intake | Review | Owner |
| --- | --- | --- | --- | --- |
| `provider-holdout` | `pending` | `awaiting-submission` | `awaiting-submission` | operator with provider credentials |
| `human-adjudication` | `pending` | `awaiting-submission` | `awaiting-submission` | human reviewer |
| `native-permission-enforcement` | `pending` | `awaiting-submission` | `awaiting-submission` | target client or installer integrator |
| `native-client-telemetry` | `pending` | `awaiting-submission` | `awaiting-submission` | Browser/Chrome/IDE/provider client integrator |

## Provider Holdout

- objective: Collect at least one provider-backed output-eval holdout run with model, timing, and token metadata.
- blocking reason: No evidence packet has been submitted for review.
- submission: `evidence/world_class/submissions/provider-holdout.json`
- template: `evidence/world_class/templates/provider-holdout.intake.json`

### Commands

- prepare_submission: `python3 scripts/yao.py world-class-submission-kit . --evidence-key provider-holdout --output-dir evidence/world_class/submissions`
- validate_intake: `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions`
- review_queue: `python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions`
- refresh_ledger: `python3 scripts/yao.py world-class-ledger .`
- guard_claim: `python3 scripts/yao.py world-class-claim-guard .`

### Must Collect

- provider-backed model run
- observed timing
- observed token metadata

### Success Checks

- reports/output_execution_runs.json summary.model_executed_count > 0
- reports/output_execution_runs.json summary.timing_observed_count > 0
- reports/output_execution_runs.json summary.token_observed_count > 0
- reports/skill_os2_audit.json item provider-holdout status becomes pass

### Privacy Contract

- Do not commit provider credentials or environment dumps.
- The output execution report records output hashes and aggregate run metadata, not raw provider prompts.

### Evidence Artifacts

- reports/output_execution_runs.json
- reports/output_execution_runs.md
- reports/skill_os2_audit.json
- evidence/world_class/intake.schema.json
- evidence/world_class/templates/provider-holdout.intake.json
- reports/world_class_evidence_intake.json
- reports/world_class_evidence_intake.md

## Human Adjudication

- objective: Record real blind A/B reviewer decisions before claiming human output review completion.
- blocking reason: No evidence packet has been submitted for review.
- submission: `evidence/world_class/submissions/human-adjudication.json`
- template: `evidence/world_class/templates/human-adjudication.intake.json`

### Commands

- prepare_submission: `python3 scripts/yao.py world-class-submission-kit . --evidence-key human-adjudication --output-dir evidence/world_class/submissions`
- validate_intake: `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions`
- review_queue: `python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions`
- refresh_ledger: `python3 scripts/yao.py world-class-ledger .`
- guard_claim: `python3 scripts/yao.py world-class-claim-guard .`

### Must Collect

- real reviewer identity
- blind A/B decisions
- answer key unopened until decisions exist

### Success Checks

- reports/output_review_adjudication.json summary.pending_count == 0
- reports/output_review_adjudication.json summary.judgment_count == summary.pair_count
- reports/output_review_adjudication.json summary.invalid_decision_count == 0
- reports/skill_os2_audit.json item human-adjudication status becomes pass

### Privacy Contract

- Reviewer decisions should not include raw user data or private customer detail.
- Keep the answer key separate until after decisions are recorded.

### Evidence Artifacts

- reports/output_blind_review_pack.md
- reports/output_review_kit.md
- reports/output_review_decisions.json
- reports/output_review_adjudication.json
- reports/output_review_adjudication.md
- evidence/world_class/intake.schema.json
- evidence/world_class/templates/human-adjudication.intake.json
- reports/world_class_evidence_intake.json
- reports/world_class_evidence_intake.md

## Native Permission Enforcement

- objective: Prove at least one real target client or external installer runtime guard enforces approved high-permission capabilities.
- blocking reason: No evidence packet has been submitted for review.
- submission: `evidence/world_class/submissions/native-permission-enforcement.json`
- template: `evidence/world_class/templates/native-permission-enforcement.intake.json`

### Commands

- prepare_submission: `python3 scripts/yao.py world-class-submission-kit . --evidence-key native-permission-enforcement --output-dir evidence/world_class/submissions`
- validate_intake: `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions`
- review_queue: `python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions`
- refresh_ledger: `python3 scripts/yao.py world-class-ledger .`
- guard_claim: `python3 scripts/yao.py world-class-claim-guard .`

### Must Collect

- real target client or external installer runtime guard
- native enforcement flag or externally accepted guard proof
- residual risk retained for fallback targets

### Success Checks

- reports/runtime_permission_probes.json summary.native_enforcement_count > 0
- reports/runtime_permission_probes.json summary.failure_count == 0
- reports/runtime_permission_probes.json summary.installer_enforcement_pass_count records local installer enforcement but does not replace native evidence
- reports/skill_os2_audit.json item native-permission-enforcement status becomes pass

### Privacy Contract

- Do not mark native_enforcement true for metadata-only fallbacks.
- Keep residual risks visible for targets that still rely on operator enforcement.

### Evidence Artifacts

- dist/targets/*/adapter.json
- reports/runtime_permission_probes.json
- reports/runtime_permission_probes.md
- reports/install_simulation.json
- reports/install_simulation.md
- security/permission_policy.json
- evidence/world_class/intake.schema.json
- evidence/world_class/templates/native-permission-enforcement.intake.json
- reports/world_class_evidence_intake.json
- reports/world_class_evidence_intake.md

## Native Client Telemetry

- objective: Import production metadata-only events from a real external client into the local drift loop.
- blocking reason: No evidence packet has been submitted for review.
- submission: `evidence/world_class/submissions/native-client-telemetry.json`
- template: `evidence/world_class/templates/native-client-telemetry.intake.json`

### Commands

- prepare_submission: `python3 scripts/yao.py world-class-submission-kit . --evidence-key native-client-telemetry --output-dir evidence/world_class/submissions`
- validate_intake: `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions`
- review_queue: `python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions`
- refresh_ledger: `python3 scripts/yao.py world-class-ledger .`
- guard_claim: `python3 scripts/yao.py world-class-claim-guard .`

### Must Collect

- real external client source
- metadata-only event
- local-first import path

### Success Checks

- reports/adoption_drift_report.json summary.source_types.external > 0
- reports/adoption_drift_report.json summary.adoption_sample_count > 0
- reports/skill_os2_audit.json item native-client-telemetry status becomes pass

### Privacy Contract

- Telemetry must remain metadata-only and local-first.
- Do not package reports/telemetry_events.jsonl or any raw prompt, output, transcript, note, or message field.

### Evidence Artifacts

- reports/adoption_drift_report.json
- reports/adoption_drift_report.md
- reports/telemetry_hook_recipes.json
- scripts/telemetry_native_host.py
- evidence/world_class/intake.schema.json
- evidence/world_class/templates/native-client-telemetry.intake.json
- reports/world_class_evidence_intake.json
- reports/world_class_evidence_intake.md

## Boundary

- Planned work, draft packets, metadata fallback, pending human decisions, and local command runners do not count as completion.
- Valid intake means ready for submission review; ledger review still requires passing source evidence.
- The world-class ledger and claim guard remain the source of truth.
