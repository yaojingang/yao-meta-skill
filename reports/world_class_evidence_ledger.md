# World-Class Evidence Ledger

Generated at: `2026-06-13`

## Summary

- decision: `evidence-pending`
- ready to claim world-class: `false`
- entries: `4`
- source accepted: `0`
- source checks: `7` pass / `13` total
- source blocked: `6`
- accepted: `0`
- pending: `4`
- human pending: `1`
- external pending: `3`
- submitted entries: `0`
- reviewer approved submissions: `0`
- submitted but pending: `0`
- source accepted without valid submission: `0`
- invalid submissions: `0`
- overclaim guard active: `true`

This ledger records the current evidence state. It requires both passing source evidence and a validated intake submission with artifact SHA-256 checks before accepting an item. It does not treat planned work, metadata fallback, pending review, or local command-runner output as world-class completion evidence.

## Ledger

| Evidence | Status | Submission | Category | Current | Next action |
| --- | --- | --- | --- | --- | --- |
| `provider-holdout` | `pending` | `missing` | `external` | model-executed 0; token-observed 0 | Run provider-backed holdout cases with real credentials and commit only aggregate evidence. |
| `human-adjudication` | `pending` | `missing` | `human` | 0/5 decisions; pending 5 | Record real A/B choices in the decision template, then regenerate adjudication. |
| `native-permission-enforcement` | `pending` | `missing` | `external` | native-enforced targets 0; installer-enforced targets 4 | Integrate a real target-client or external installer runtime guard before claiming native permission enforcement. |
| `native-client-telemetry` | `pending` | `missing` | `external` | external source events 0; adoption samples 1 | Install a real client against the native host and import production metadata-only events. |

## Provider Holdout

- objective: Collect at least one provider-backed output-eval holdout run with model, timing, and token metadata.
- source status: `external_required`
- observed state: `{"model_executed_count": 0, "timing_observed_count": 10, "token_observed_count": 0, "accepted": false}`
- source checks: `1` pass / `3` total
- submission state: `{"status": "missing", "path": "evidence/world_class/submissions/provider-holdout.json", "artifact_ref_count": 0, "attested_real_evidence": false, "privacy_contract_satisfied": false, "ledger_reviewer_approved": false, "ledger_reviewer": "", "ledger_reviewed_at": "", "ledger_counts_as_completion": false}`

### Provenance Requirements

- provider-backed model run
- observed timing
- observed token metadata

### Source Runbook

- Set OPENAI_API_KEY in the operator shell before running provider evidence; never commit or print the value.
- `export YAO_OUTPUT_EVAL_MODEL=${YAO_OUTPUT_EVAL_MODEL:-gpt-4.1-mini}`
- `python3 scripts/yao.py output-exec --provider-runner openai --timeout-seconds 60`
- `python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD>`
- Copy evidence/world_class/templates/provider-holdout.intake.json to evidence/world_class/submissions/provider-holdout.json and fill only real evidence fields.
- `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions`

### Source Evidence Checks

| Check | Current | Expected | Status |
| --- | --- | --- | --- |
| Provider model run | `0` | `>0` | `blocked` |
| Timing observed | `10` | `>0` | `pass` |
| Token usage observed | `0` | `>0` | `blocked` |

### Completion Assertions

- reports/output_execution_runs.json summary.model_executed_count > 0
- reports/output_execution_runs.json summary.timing_observed_count > 0
- reports/output_execution_runs.json summary.token_observed_count > 0
- reports/skill_os2_audit.json item provider-holdout status becomes pass

### Privacy Contract

- Do not commit provider credentials or environment dumps.
- The output execution report records output hashes and aggregate run metadata, not raw provider prompts.

## Human Adjudication

- objective: Record real blind A/B reviewer decisions before claiming human output review completion.
- source status: `human_required`
- observed state: `{"pair_count": 5, "judgment_count": 0, "pending_count": 5, "invalid_decision_count": 0, "answer_revealed_count": 0, "accepted": false}`
- source checks: `2` pass / `4` total
- submission state: `{"status": "missing", "path": "evidence/world_class/submissions/human-adjudication.json", "artifact_ref_count": 0, "attested_real_evidence": false, "privacy_contract_satisfied": false, "ledger_reviewer_approved": false, "ledger_reviewer": "", "ledger_reviewed_at": "", "ledger_counts_as_completion": false}`

### Provenance Requirements

- real reviewer identity
- blind A/B decisions
- answer key unopened until decisions exist

### Source Runbook

- `python3 scripts/yao.py output-review-kit --write-template`
- Open reports/output_review_kit.md and choose A or B for each pair without opening the answer key.
- `python3 scripts/adjudicate_output_review.py --write-template`
- Record reviewer choices in a separate JSON, JSONL, or CSV decision source with case_id, winner_variant, confidence, and reason only.
- `python3 scripts/yao.py output-review-import --input <reviewer-decisions.json> --run-adjudication`
- `python3 scripts/yao.py output-review`
- `python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD>`
- Copy evidence/world_class/templates/human-adjudication.intake.json to evidence/world_class/submissions/human-adjudication.json and fill only real evidence fields.
- `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions`

### Source Evidence Checks

| Check | Current | Expected | Status |
| --- | --- | --- | --- |
| Review pairs exist | `5` | `>0` | `pass` |
| No pending decisions | `5` | `==0` | `blocked` |
| Judgments complete | `0` | `==pair_count` | `blocked` |
| No invalid decisions | `0` | `==0` | `pass` |

### Completion Assertions

- reports/output_review_adjudication.json summary.pending_count == 0
- reports/output_review_adjudication.json summary.judgment_count == summary.pair_count
- reports/output_review_adjudication.json summary.invalid_decision_count == 0
- reports/skill_os2_audit.json item human-adjudication status becomes pass

### Privacy Contract

- Reviewer decisions should not include raw user data or private customer detail.
- The decision importer rejects raw prompt, output, transcript, message, and answer-key fields.
- Keep the answer key separate until after decisions are recorded.

## Native Permission Enforcement

- objective: Prove at least one real target client or external installer runtime guard enforces approved high-permission capabilities.
- source status: `external_required`
- observed state: `{"native_enforcement_count": 0, "metadata_fallback_count": 4, "installer_enforcement_pass_count": 4, "installer_permission_failure_count": 0, "installer_enforcement_ready": true, "residual_risk_count": 4, "failure_count": 0, "accepted": false}`
- source checks: `2` pass / `3` total
- submission state: `{"status": "missing", "path": "evidence/world_class/submissions/native-permission-enforcement.json", "artifact_ref_count": 0, "attested_real_evidence": false, "privacy_contract_satisfied": false, "ledger_reviewer_approved": false, "ledger_reviewer": "", "ledger_reviewed_at": "", "ledger_counts_as_completion": false}`

### Provenance Requirements

- real target client or external installer runtime guard
- native enforcement flag or externally accepted guard proof
- residual risk retained for fallback targets

### Source Runbook

- Implement or connect a real target client or external installer runtime guard that blocks undeclared network, file_write, or subprocess capabilities.
- Update the generated target adapter only when the guard is actually enforced by that target.
- `python3 scripts/yao.py package . --platform openai --platform claude --platform generic --platform vscode --output-dir dist --zip`
- `python3 scripts/yao.py install-simulate . --package-dir dist --install-root dist/install-simulation`
- `python3 scripts/yao.py runtime-permissions . --package-dir dist`
- `python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD>`
- Copy evidence/world_class/templates/native-permission-enforcement.intake.json to evidence/world_class/submissions/native-permission-enforcement.json and fill only real evidence fields.
- `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions`

### Source Evidence Checks

| Check | Current | Expected | Status |
| --- | --- | --- | --- |
| Native enforcement | `0` | `>0` | `blocked` |
| Probe failures | `0` | `==0` | `pass` |
| Installer support | `True` | `true` | `pass` |

### Completion Assertions

- reports/runtime_permission_probes.json summary.native_enforcement_count > 0
- reports/runtime_permission_probes.json summary.failure_count == 0
- reports/runtime_permission_probes.json summary.installer_enforcement_pass_count records local installer enforcement but does not replace native evidence
- reports/skill_os2_audit.json item native-permission-enforcement status becomes pass

### Privacy Contract

- Do not mark native_enforcement true for metadata-only fallbacks.
- Keep residual risks visible for targets that still rely on operator enforcement.

## Native Client Telemetry

- objective: Import production metadata-only events from a real external client into the local drift loop.
- source status: `external_required`
- observed state: `{"external_source_events": 0, "adoption_sample_count": 1, "raw_content_allowed": false, "risk_band": "low", "accepted": false}`
- source checks: `2` pass / `3` total
- submission state: `{"status": "missing", "path": "evidence/world_class/submissions/native-client-telemetry.json", "artifact_ref_count": 0, "attested_real_evidence": false, "privacy_contract_satisfied": false, "ledger_reviewer_approved": false, "ledger_reviewer": "", "ledger_reviewed_at": "", "ledger_counts_as_completion": false}`

### Provenance Requirements

- real external client source
- metadata-only event
- local-first import path

### Source Runbook

- `python3 scripts/telemetry_native_host.py . --write-launcher /tmp/yao-telemetry-host.sh --write-manifest /tmp/yao-telemetry-host.json --allowed-origin chrome-extension://<extension-id>/`
- Install the generated native messaging manifest for the real client and send at least one accepted skill_activation or skill_output event.
- `python3 scripts/yao.py telemetry-import . --input-jsonl .yao/telemetry_spool/external_events.jsonl`
- `python3 scripts/yao.py skill-atlas --workspace-root .`
- `python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD>`
- Copy evidence/world_class/templates/native-client-telemetry.intake.json to evidence/world_class/submissions/native-client-telemetry.json and fill only real evidence fields.
- `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions`

### Source Evidence Checks

| Check | Current | Expected | Status |
| --- | --- | --- | --- |
| External events | `0` | `>0` | `blocked` |
| Adoption sample | `1` | `>0` | `pass` |
| Raw content blocked | `False` | `false` | `pass` |

### Completion Assertions

- reports/adoption_drift_report.json summary.source_types.external > 0
- reports/adoption_drift_report.json summary.adoption_sample_count > 0
- reports/skill_os2_audit.json item native-client-telemetry status becomes pass

### Privacy Contract

- Telemetry must remain metadata-only and local-first.
- Do not package reports/telemetry_events.jsonl or any raw prompt, output, transcript, note, or message field.
