# World-Class Evidence Intake

Generated at: `2026-06-13`

## Summary

- decision: `awaiting-submissions`
- schema present: `true`
- templates: `4` / `4`
- submissions: `0` valid / `0` total
- invalid submissions: `0`
- operator checklist: `0` ready / `4` total
- ready for external collection: `true`
- ready for ledger review: `false`
- ready to claim world-class: `false`
- overclaim guard active: `true`

This report validates the intake contract for human and external evidence. A valid intake packet means the evidence is ready for ledger review; it does not by itself make a world-class claim true.

## Templates

| Evidence | Status | Path | Errors |
| --- | --- | --- | --- |
| `provider-holdout` | `pass` | `evidence/world_class/templates/provider-holdout.intake.json` | none |
| `human-adjudication` | `pass` | `evidence/world_class/templates/human-adjudication.intake.json` | none |
| `native-permission-enforcement` | `pass` | `evidence/world_class/templates/native-permission-enforcement.intake.json` | none |
| `native-client-telemetry` | `pass` | `evidence/world_class/templates/native-client-telemetry.intake.json` | none |

## Submissions

| Evidence | Status | Path | Errors |
| --- | --- | --- | --- |
| `none` | `n/a` | none | none |

## Operator Checklist

| Evidence | Readiness | Submission | Next action |
| --- | --- | --- | --- |
| `provider-holdout` | `awaiting-submission` | `missing` | Run provider-backed holdout cases with real credentials and commit only aggregate evidence. |
| `human-adjudication` | `awaiting-submission` | `missing` | Record real A/B choices in the decision template, then regenerate adjudication. |
| `native-permission-enforcement` | `awaiting-submission` | `missing` | Integrate a real client or installer runtime guard before claiming native permission enforcement. |
| `native-client-telemetry` | `awaiting-submission` | `missing` | Install a real client against the native host and import production metadata-only events. |

### Provider Holdout

- readiness: `awaiting-submission`
- blocking reason: No real evidence submission has been provided yet.
- owner: operator with provider credentials
- template: `evidence/world_class/templates/provider-holdout.intake.json`
- submission: `evidence/world_class/submissions/provider-holdout.json`

#### Commands

- prepare_submission: `python3 scripts/yao.py world-class-submission-kit . --evidence-key provider-holdout --output-dir evidence/world_class/submissions`
- validate_intake: `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions`
- refresh_ledger: `python3 scripts/yao.py world-class-ledger .`
- guard_claim: `python3 scripts/yao.py world-class-claim-guard .`

#### Must Collect

- provenance_requirements:
  - provider-backed model run
  - observed timing
  - observed token metadata
- success_checks:
  - reports/output_execution_runs.json summary.model_executed_count > 0
  - reports/output_execution_runs.json summary.timing_observed_count > 0
  - reports/output_execution_runs.json summary.token_observed_count > 0
  - reports/skill_os2_audit.json item provider-holdout status becomes pass
- evidence_artifacts:
  - reports/output_execution_runs.json
  - reports/output_execution_runs.md
  - reports/skill_os2_audit.json
  - evidence/world_class/intake.schema.json
  - evidence/world_class/templates/provider-holdout.intake.json
  - reports/world_class_evidence_intake.json
  - reports/world_class_evidence_intake.md
- privacy_contract:
  - Do not commit provider credentials or environment dumps.
  - The output execution report records output hashes and aggregate run metadata, not raw provider prompts.

### Human Adjudication

- readiness: `awaiting-submission`
- blocking reason: No real evidence submission has been provided yet.
- owner: human reviewer
- template: `evidence/world_class/templates/human-adjudication.intake.json`
- submission: `evidence/world_class/submissions/human-adjudication.json`

#### Commands

- prepare_submission: `python3 scripts/yao.py world-class-submission-kit . --evidence-key human-adjudication --output-dir evidence/world_class/submissions`
- validate_intake: `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions`
- refresh_ledger: `python3 scripts/yao.py world-class-ledger .`
- guard_claim: `python3 scripts/yao.py world-class-claim-guard .`

#### Must Collect

- provenance_requirements:
  - real reviewer identity
  - blind A/B decisions
  - answer key unopened until decisions exist
- success_checks:
  - reports/output_review_adjudication.json summary.pending_count == 0
  - reports/output_review_adjudication.json summary.judgment_count == summary.pair_count
  - reports/output_review_adjudication.json summary.invalid_decision_count == 0
  - reports/skill_os2_audit.json item human-adjudication status becomes pass
- evidence_artifacts:
  - reports/output_blind_review_pack.md
  - reports/output_review_decisions.json
  - reports/output_review_adjudication.json
  - reports/output_review_adjudication.md
  - evidence/world_class/intake.schema.json
  - evidence/world_class/templates/human-adjudication.intake.json
  - reports/world_class_evidence_intake.json
  - reports/world_class_evidence_intake.md
- privacy_contract:
  - Reviewer decisions should not include raw user data or private customer detail.
  - Keep the answer key separate until after decisions are recorded.

### Native Permission Enforcement

- readiness: `awaiting-submission`
- blocking reason: No real evidence submission has been provided yet.
- owner: target client or installer integrator
- template: `evidence/world_class/templates/native-permission-enforcement.intake.json`
- submission: `evidence/world_class/submissions/native-permission-enforcement.json`

#### Commands

- prepare_submission: `python3 scripts/yao.py world-class-submission-kit . --evidence-key native-permission-enforcement --output-dir evidence/world_class/submissions`
- validate_intake: `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions`
- refresh_ledger: `python3 scripts/yao.py world-class-ledger .`
- guard_claim: `python3 scripts/yao.py world-class-claim-guard .`

#### Must Collect

- provenance_requirements:
  - real target or installer guard
  - native enforcement flag
  - residual risk retained for fallback targets
- success_checks:
  - reports/runtime_permission_probes.json summary.native_enforcement_count > 0
  - reports/runtime_permission_probes.json summary.failure_count == 0
  - reports/skill_os2_audit.json item native-permission-enforcement status becomes pass
- evidence_artifacts:
  - dist/targets/*/adapter.json
  - reports/runtime_permission_probes.json
  - reports/runtime_permission_probes.md
  - security/permission_policy.json
  - evidence/world_class/intake.schema.json
  - evidence/world_class/templates/native-permission-enforcement.intake.json
  - reports/world_class_evidence_intake.json
  - reports/world_class_evidence_intake.md
- privacy_contract:
  - Do not mark native_enforcement true for metadata-only fallbacks.
  - Keep residual risks visible for targets that still rely on operator enforcement.

### Native Client Telemetry

- readiness: `awaiting-submission`
- blocking reason: No real evidence submission has been provided yet.
- owner: Browser/Chrome/IDE/provider client integrator
- template: `evidence/world_class/templates/native-client-telemetry.intake.json`
- submission: `evidence/world_class/submissions/native-client-telemetry.json`

#### Commands

- prepare_submission: `python3 scripts/yao.py world-class-submission-kit . --evidence-key native-client-telemetry --output-dir evidence/world_class/submissions`
- validate_intake: `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions`
- refresh_ledger: `python3 scripts/yao.py world-class-ledger .`
- guard_claim: `python3 scripts/yao.py world-class-claim-guard .`

#### Must Collect

- provenance_requirements:
  - real external client source
  - metadata-only event
  - local-first import path
- success_checks:
  - reports/adoption_drift_report.json summary.source_types.external > 0
  - reports/adoption_drift_report.json summary.adoption_sample_count > 0
  - reports/skill_os2_audit.json item native-client-telemetry status becomes pass
- evidence_artifacts:
  - reports/adoption_drift_report.json
  - reports/adoption_drift_report.md
  - reports/telemetry_hook_recipes.json
  - scripts/telemetry_native_host.py
  - evidence/world_class/intake.schema.json
  - evidence/world_class/templates/native-client-telemetry.intake.json
  - reports/world_class_evidence_intake.json
  - reports/world_class_evidence_intake.md
- privacy_contract:
  - Telemetry must remain metadata-only and local-first.
  - Do not package reports/telemetry_events.jsonl or any raw prompt, output, transcript, note, or message field.

## Boundary

- Templates and planned work do not count as accepted evidence.
- Local command-runner output does not count as provider-backed model evidence.
- Metadata fallback does not count as native permission enforcement.
- Pending reviewer work does not count as human adjudication.
