# World-Class Evidence Plan

Generated at: `2026-06-20`

## Summary

- decision: `collect-external-evidence`
- audit decision: `continue-iteration`
- ready to claim world-class: `false`
- ledger completion required: `true`
- evidence requirements: `4`
- tasks: `4`
- human tasks: `1`
- external tasks: `3`

This report is an execution plan for the remaining world-class evidence gaps. It does not count a plan or source-report pass as completion; the ledger must still validate accepted submissions.

## Task Table

| Task | Status | Category | Owner | Current |
| --- | --- | --- | --- | --- |
| `provider-holdout` | `pass` | `external` | operator with provider credentials | model-executed 10; token-observed 10 |
| `human-adjudication` | `human_required` | `human` | human reviewer | 0/5 decisions; pending 5 |
| `native-permission-enforcement` | `external_required` | `external` | target client or installer integrator | native-enforced targets 0; installer-enforced targets 4 |
| `native-client-telemetry` | `external_required` | `external` | Browser/Chrome/IDE/provider client integrator | external source events 0; adoption samples 1 |

## Provider Holdout

- objective: Collect at least one provider-backed output-eval holdout run with model, timing, and token metadata.
- audit next action: Run provider-backed holdout cases with real credentials and commit only aggregate evidence.

### Runbook

- Set one provider API key in the operator shell, such as OPENAI_API_KEY or DEEPSEEK_API_KEY; never commit or print the value.
- For OpenAI Responses: python3 scripts/yao.py output-exec --provider-runner openai --provider-model ${YAO_OUTPUT_EVAL_MODEL:-gpt-4.1-mini} --timeout-seconds 60
- For DeepSeek Chat Completions: python3 scripts/yao.py output-exec --provider-runner deepseek --provider-model deepseek-v4-flash --provider-api-format chat-completions --provider-thinking disabled --api-key-env DEEPSEEK_API_KEY --timeout-seconds 120
- `python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD>`
- Copy evidence/world_class/templates/provider-holdout.intake.json to evidence/world_class/submissions/provider-holdout.json and fill only real evidence fields.
- `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions`

### Success Checks

- reports/output_execution_runs.json summary.model_executed_count > 0
- reports/output_execution_runs.json summary.timing_observed_count > 0
- reports/output_execution_runs.json summary.token_observed_count > 0
- reports/skill_os2_audit.json item provider-holdout status becomes pass

### Evidence Artifacts

- `reports/output_execution_runs.json`
- `reports/output_execution_runs.md`
- `reports/skill_os2_audit.json`
- `evidence/world_class/intake.schema.json`
- `evidence/world_class/templates/provider-holdout.intake.json`
- `reports/world_class_evidence_intake.json`
- `reports/world_class_evidence_intake.md`

### Privacy Contract

- Do not commit provider credentials or environment dumps.
- The output execution report records output hashes and aggregate run metadata, not raw provider prompts.

## Human Adjudication

- objective: Record real blind A/B reviewer decisions before claiming human output review completion.
- audit next action: Record real A/B choices, reviewer metadata, and blind-review attestation, then regenerate adjudication.

### Runbook

- `python3 scripts/yao.py output-review-kit --write-template`
- Open reports/output_review_kit.md and choose A or B for each pair without opening the answer key.
- `python3 scripts/adjudicate_output_review.py --write-template`
- Record reviewer choices in a separate JSON, JSONL, or CSV decision source with reviewer, reviewed_at, case_id, winner_variant, confidence, required reason, and truthful reviewer_attestation only.
- `python3 scripts/yao.py output-review-import --input <reviewer-decisions.json> --blind-review-attested --run-adjudication`
- `python3 scripts/yao.py output-review`
- `python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD>`
- Copy evidence/world_class/templates/human-adjudication.intake.json to evidence/world_class/submissions/human-adjudication.json and fill only real evidence fields.
- `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions`

### Success Checks

- reports/output_review_adjudication.json summary.pending_count == 0
- reports/output_review_adjudication.json summary.judgment_count == summary.pair_count
- reports/output_review_adjudication.json summary.invalid_decision_count == 0
- reports/output_review_adjudication.json summary.reviewer_metadata_present is true
- reports/output_review_adjudication.json summary.blind_review_attested is true
- reports/output_review_adjudication.json review_integrity.blind_pack_sha256 exists and matches reports/output_review_decisions.json
- reports/output_review_adjudication.json pairs and reviewer_checklist store prompt_sha256, not raw prompt text
- reports/output_review_adjudication.json summary.ready_for_human_evidence is true
- reports/skill_os2_audit.json item human-adjudication status becomes pass

### Evidence Artifacts

- `reports/output_blind_review_pack.md`
- `reports/output_review_kit.md`
- `reports/output_review_decisions.json`
- `reports/output_review_adjudication.json`
- `reports/output_review_adjudication.md`
- `scripts/import_output_review_decisions.py`
- `evidence/world_class/intake.schema.json`
- `evidence/world_class/templates/human-adjudication.intake.json`
- `reports/world_class_evidence_intake.json`
- `reports/world_class_evidence_intake.md`

### Privacy Contract

- Reviewer decisions should not include raw user data or private customer detail.
- Reviewer reasons must be rubric-based and must not include raw user data or private customer detail.
- The decision importer rejects raw prompt, output, transcript, message, and answer-key fields.
- The adjudication evidence stores prompt_sha256 instead of raw prompt text.
- The decision and adjudication artifacts preserve blind_pack_sha256 so reviewers can audit exactly which pack was judged.
- Keep the answer key separate until after decisions are recorded.

## Native Permission Enforcement

- objective: Prove at least one real target client or external installer runtime guard enforces approved high-permission capabilities.
- audit next action: Integrate a real target-client or external installer runtime guard before claiming native permission enforcement.

### Runbook

- Implement or connect a real target client or external installer runtime guard that blocks undeclared network, file_write, or subprocess capabilities.
- Update the generated target adapter only when the guard is actually enforced by that target.
- `python3 scripts/yao.py package . --platform openai --platform claude --platform generic --platform vscode --output-dir dist --zip`
- `python3 scripts/yao.py install-simulate . --package-dir dist --install-root dist/install-simulation`
- `python3 scripts/yao.py runtime-permissions . --package-dir dist`
- `python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD>`
- Copy evidence/world_class/templates/native-permission-enforcement.intake.json to evidence/world_class/submissions/native-permission-enforcement.json and fill only real evidence fields.
- `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions`

### Success Checks

- reports/runtime_permission_probes.json summary.native_enforcement_count > 0
- reports/runtime_permission_probes.json summary.failure_count == 0
- reports/runtime_permission_probes.json summary.installer_enforcement_pass_count records local installer enforcement but does not replace native evidence
- reports/skill_os2_audit.json item native-permission-enforcement status becomes pass

### Evidence Artifacts

- `dist/targets/*/adapter.json`
- `reports/runtime_permission_probes.json`
- `reports/runtime_permission_probes.md`
- `reports/install_simulation.json`
- `reports/install_simulation.md`
- `security/permission_policy.json`
- `evidence/world_class/intake.schema.json`
- `evidence/world_class/templates/native-permission-enforcement.intake.json`
- `reports/world_class_evidence_intake.json`
- `reports/world_class_evidence_intake.md`

### Privacy Contract

- Do not mark native_enforcement true for metadata-only fallbacks.
- Keep residual risks visible for targets that still rely on operator enforcement.

## Native Client Telemetry

- objective: Import production metadata-only events from a real external client into the local drift loop.
- audit next action: Install a real client against the native host and import production metadata-only events.

### Runbook

- `python3 scripts/telemetry_native_host.py . --write-launcher /tmp/yao-telemetry-host.sh --write-manifest /tmp/yao-telemetry-host.json --allowed-origin chrome-extension://<extension-id>/`
- Install the generated native messaging manifest for the real client and send at least one accepted skill_activation or skill_output event.
- `python3 scripts/yao.py telemetry-import . --input-jsonl .yao/telemetry_spool/external_events.jsonl`
- `python3 scripts/yao.py skill-atlas --workspace-root .`
- `python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD>`
- Copy evidence/world_class/templates/native-client-telemetry.intake.json to evidence/world_class/submissions/native-client-telemetry.json and fill only real evidence fields.
- `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions`

### Success Checks

- reports/adoption_drift_report.json summary.source_types.external > 0
- reports/adoption_drift_report.json summary.adoption_sample_count > 0
- reports/skill_os2_audit.json item native-client-telemetry status becomes pass

### Evidence Artifacts

- `reports/adoption_drift_report.json`
- `reports/adoption_drift_report.md`
- `reports/telemetry_hook_recipes.json`
- `scripts/telemetry_native_host.py`
- `evidence/world_class/intake.schema.json`
- `evidence/world_class/templates/native-client-telemetry.intake.json`
- `reports/world_class_evidence_intake.json`
- `reports/world_class_evidence_intake.md`

### Privacy Contract

- Telemetry must remain metadata-only and local-first.
- Do not package reports/telemetry_events.jsonl or any raw prompt, output, transcript, note, or message field.
