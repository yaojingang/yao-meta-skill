# World-Class Evidence Intake

Generated at: `2026-11-09`

## Summary

- decision: `awaiting-submissions`
- schema present: `true`
- templates: `4` / `4`
- submissions: `0` valid / `0` total
- invalid submissions: `0`
- valid packet but source incomplete: `0`
- operator checklist: `0` ready / `4` total
- ready for external collection: `true`
- ready for ledger review: `false`
- ready to claim world-class: `false`
- overclaim guard active: `true`

This report validates the intake contract for human and external evidence. A valid intake packet means the evidence is ready for ledger review; it does not by itself make a world-class claim true.

## Templates

| Evidence | Status | Path | Artifacts | Errors |
| --- | --- | --- | --- | --- |
| `provider-holdout` | `pass` | `evidence/world_class/templates/provider-holdout.intake.json` | 0 existing / 0 sha256 verified / 0 required verified / 1 refs | none |
| `human-adjudication` | `pass` | `evidence/world_class/templates/human-adjudication.intake.json` | 0 existing / 0 sha256 verified / 0 required verified / 2 refs | none |
| `native-permission-enforcement` | `pass` | `evidence/world_class/templates/native-permission-enforcement.intake.json` | 0 existing / 0 sha256 verified / 0 required verified / 3 refs | none |
| `native-client-telemetry` | `pass` | `evidence/world_class/templates/native-client-telemetry.intake.json` | 0 existing / 0 sha256 verified / 0 required verified / 2 refs | none |

## Submissions

| Evidence | Status | Path | Artifacts | Errors |
| --- | --- | --- | --- | --- |
| `none` | `n/a` | none | none | none |

## Operator Checklist

| Evidence | Readiness | Submission | Next action |
| --- | --- | --- | --- |
| `provider-holdout` | `awaiting-submission` | `missing` | Run evidence-build with DEEPSEEK_API_KEY and keep raw outputs in the isolated run directory. |
| `human-adjudication` | `awaiting-submission` | `missing` | Collect three controlled reviewer packets and adjudicate them against the private run answer key. |
| `native-permission-enforcement` | `awaiting-submission` | `missing` | Integrate a real target-client or external installer runtime guard before claiming native permission enforcement. |
| `native-client-telemetry` | `awaiting-submission` | `missing` | Install a real client against the native host and import production metadata-only events. |

### Provider Holdout

- readiness: `awaiting-submission`
- blocking reason: No real evidence submission has been provided yet.
- owner: operator with provider credentials
- template: `evidence/world_class/templates/provider-holdout.intake.json`
- submission: `evidence/world_class/submissions/provider-holdout.json`

#### Commands

- prepare_submission: `python3 scripts/yao.py world-class-submission-kit . --evidence-key provider-holdout --output-dir evidence/world_class/submissions --self`
- validate_intake: `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions --self`
- submission_review: `python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions --self`
- refresh_ledger: `python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions --self`
- guard_claim: `python3 scripts/yao.py world-class-claim-guard . --self`

#### Must Collect

- provenance_requirements:
  - provider-backed model run
  - observed timing
  - observed token metadata
- success_checks:
  - reports/provider_output_evaluation.json summary.call_count == 40
  - reports/provider_output_evaluation.json summary.model_executed_count == 40
  - reports/provider_output_evaluation.json summary.failure_count == 0
  - reports/provider_output_evaluation.json summary.total_tokens <= 250000
  - reports/skill_os2_audit.json item provider-holdout status becomes pass
- evidence_artifacts:
  - evals/output/provider_matrix.json
  - reports/provider_output_evaluation.json
  - reports/provider_output_blind_pack.json
  - reports/provider_output_answer_commitment.json
  - reports/skill_os2_audit.json
  - evidence/world_class/intake.schema.json
  - evidence/world_class/templates/provider-holdout.intake.json
  - reports/world_class_evidence_intake.json
  - reports/world_class_evidence_intake.md
- privacy_contract:
  - Do not commit provider credentials or environment dumps.
  - The output execution report records output hashes and aggregate run metadata, not raw provider prompts.

#### Source Runbook

- Set DEEPSEEK_API_KEY in the operator shell; never commit or print the value.
- `python3 scripts/yao.py evidence-build . --run-id <PROVIDER_RUN_ID> --self`
- Keep the generated private answer key and role-neutral review materials inside .yao/runs/<PROVIDER_RUN_ID>.
- `python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD> --self`
- Copy evidence/world_class/templates/provider-holdout.intake.json to evidence/world_class/submissions/provider-holdout.json and fill only real evidence fields.
- `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions --self`

### Human Adjudication

- readiness: `awaiting-submission`
- blocking reason: No real evidence submission has been provided yet.
- owner: human reviewer
- template: `evidence/world_class/templates/human-adjudication.intake.json`
- submission: `evidence/world_class/submissions/human-adjudication.json`

#### Commands

- prepare_submission: `python3 scripts/yao.py world-class-submission-kit . --evidence-key human-adjudication --output-dir evidence/world_class/submissions --self`
- validate_intake: `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions --self`
- submission_review: `python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions --self`
- refresh_ledger: `python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions --self`
- guard_claim: `python3 scripts/yao.py world-class-claim-guard . --self`

#### Must Collect

- provenance_requirements:
  - real reviewer identity
  - blind A/B decisions
  - answer key unopened until decisions exist
- success_checks:
  - reports/provider_output_adjudication.json summary.reviewer_count == 3
  - reports/provider_output_adjudication.json summary.pair_count == 20
  - reports/provider_output_adjudication.json summary.failure_count == 0
  - reports/provider_output_adjudication.json evidence_binding.blind_pack_sha256 matches the source run
  - reports/skill_os2_audit.json item human-adjudication status becomes pass
- evidence_artifacts:
  - reports/provider_output_blind_pack.json
  - reports/provider_reviewer_registry.json
  - reports/provider_output_adjudication.json
  - reports/provider_review_lineage.json
  - scripts/adjudicate_multi_reviewer.py
  - scripts/finalize_provider_review.py
  - evidence/world_class/intake.schema.json
  - evidence/world_class/templates/human-adjudication.intake.json
  - reports/world_class_evidence_intake.json
  - reports/world_class_evidence_intake.md
- privacy_contract:
  - Reviewer packets contain choices, reasons, hashes, and controlled submission metadata without raw prompts or answer-key roles.
  - The private answer key remains under .yao/runs and is opened by the finalizer after all controlled packets are fixed.
  - The adjudication and lineage artifacts preserve blind_pack_sha256 and answer_key_sha256 commitments.

#### Source Runbook

- Give each registered reviewer an independent copy of the matching provider_review_reviewer-*.json template and the role-neutral blind pack.
- Collect all 20 A/B choices, reasons, controlled submission ids, timestamps, and truthful independent-review attestations.
- Export an access-controlled reviewer registry that binds each reviewer id to the exact packet SHA256.
- `python3 scripts/yao.py evidence-finalize-review . --source-run <PROVIDER_RUN_ID> --decisions <reviewer-a.json> --decisions <reviewer-b.json> --decisions <reviewer-c.json> --reviewer-registry <registry.json> --run-id <FINAL_RUN_ID> --self`
- `python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD> --self`
- Copy evidence/world_class/templates/human-adjudication.intake.json to evidence/world_class/submissions/human-adjudication.json and fill only real evidence fields.
- `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions --self`

### Native Permission Enforcement

- readiness: `awaiting-submission`
- blocking reason: No real evidence submission has been provided yet.
- owner: target client or installer integrator
- template: `evidence/world_class/templates/native-permission-enforcement.intake.json`
- submission: `evidence/world_class/submissions/native-permission-enforcement.json`

#### Commands

- prepare_submission: `python3 scripts/yao.py world-class-submission-kit . --evidence-key native-permission-enforcement --output-dir evidence/world_class/submissions --self`
- validate_intake: `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions --self`
- submission_review: `python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions --self`
- refresh_ledger: `python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions --self`
- guard_claim: `python3 scripts/yao.py world-class-claim-guard . --self`

#### Must Collect

- provenance_requirements:
  - real target client or external installer runtime guard
  - native enforcement flag or externally accepted guard proof
  - residual risk retained for fallback targets
- success_checks:
  - reports/runtime_permission_probes.json summary.native_enforcement_count > 0
  - reports/runtime_permission_probes.json summary.failure_count == 0
  - reports/runtime_permission_probes.json summary.installer_enforcement_pass_count records local installer enforcement but does not replace native evidence
  - reports/skill_os2_audit.json item native-permission-enforcement status becomes pass
- evidence_artifacts:
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
- privacy_contract:
  - Do not mark native_enforcement true for metadata-only fallbacks.
  - Keep residual risks visible for targets that still rely on operator enforcement.

#### Source Runbook

- Implement or connect a real target client or external installer runtime guard that blocks undeclared network, file_write, or subprocess capabilities.
- Update the generated target adapter only when the guard is actually enforced by that target.
- `python3 scripts/yao.py package . --platform openai --platform claude --platform generic --platform vscode --output-dir dist --zip --self`
- `python3 scripts/yao.py install-simulate . --package-dir dist --install-root dist/install-simulation --self`
- `python3 scripts/yao.py runtime-permissions . --package-dir dist --self`
- `python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD> --self`
- Copy evidence/world_class/templates/native-permission-enforcement.intake.json to evidence/world_class/submissions/native-permission-enforcement.json and fill only real evidence fields.
- `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions --self`

### Native Client Telemetry

- readiness: `awaiting-submission`
- blocking reason: No real evidence submission has been provided yet.
- owner: Browser/Chrome/IDE/provider client integrator
- template: `evidence/world_class/templates/native-client-telemetry.intake.json`
- submission: `evidence/world_class/submissions/native-client-telemetry.json`

#### Commands

- prepare_submission: `python3 scripts/yao.py world-class-submission-kit . --evidence-key native-client-telemetry --output-dir evidence/world_class/submissions --self`
- validate_intake: `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions --self`
- submission_review: `python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions --self`
- refresh_ledger: `python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions --self`
- guard_claim: `python3 scripts/yao.py world-class-claim-guard . --self`

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

#### Source Runbook

- `python3 scripts/telemetry_native_host.py . --write-launcher /tmp/yao-telemetry-host.sh --write-manifest /tmp/yao-telemetry-host.json --allowed-origin chrome-extension://<extension-id>/`
- Install the generated native messaging manifest for the real client and send at least one accepted skill_activation or skill_output event.
- `python3 scripts/yao.py telemetry-import . --input-jsonl .yao/telemetry_spool/external_events.jsonl --self`
- `python3 scripts/yao.py skill-atlas --workspace-root . --self`
- `python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD> --self`
- Copy evidence/world_class/templates/native-client-telemetry.intake.json to evidence/world_class/submissions/native-client-telemetry.json and fill only real evidence fields.
- `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions --self`

## Boundary

- Templates and planned work do not count as accepted evidence.
- Real submissions must include the evidence-key critical artifact paths with verified SHA-256 digests.
- Real submissions must replace template submitter, date, and provenance placeholders with concrete evidence metadata.
- Local command-runner output does not count as provider-backed model evidence.
- Metadata fallback does not count as native permission enforcement.
- Pending reviewer work does not count as human adjudication.
