# World-Class Evidence Ledger

Generated at: `2026-11-09`

## Summary

- decision: `evidence-pending`
- ready to claim world-class: `false`
- entries: `4`
- source accepted: `2`
- source checks: `11` pass / `14` total
- source blocked: `3`
- accepted: `0`
- pending: `4`
- human pending: `1`
- external pending: `3`
- submitted entries: `0`
- reviewer approved submissions: `0`
- submitted but pending: `0`
- source accepted without valid submission: `2`
- invalid submissions: `0`
- overclaim guard active: `true`

This ledger records the current evidence state. It requires both passing source evidence and a validated intake submission with artifact SHA-256 checks before accepting an item. It does not treat planned work, metadata fallback, pending review, or local command-runner output as world-class completion evidence.

## Ledger

| Evidence | Status | Submission | Category | Current | Next action |
| --- | --- | --- | --- | --- | --- |
| `provider-holdout` | `pending` | `missing` | `external` | phase1 model-executed 40/40; calls 40/40; status completed | Run evidence-build with DEEPSEEK_API_KEY and keep raw outputs in the isolated run directory. |
| `human-adjudication` | `pending` | `missing` | `human` | phase1 reviewers 3/3; pairs 20/20; promotion eligible | Collect three controlled reviewer packets and adjudicate them against the private run answer key. |
| `native-permission-enforcement` | `pending` | `missing` | `external` | native-enforced targets 0; installer-enforced targets 4 | Integrate a real target-client or external installer runtime guard before claiming native permission enforcement. |
| `native-client-telemetry` | `pending` | `missing` | `external` | external source events 0; adoption samples 0 | Install a real client against the native host and import production metadata-only events. |

## Provider Holdout

- objective: Complete the fixed 10-case DeepSeek Flash+Pro matrix with 40 real calls and governed budget evidence.
- source status: `pass`
- observed state: `{"contract_version": "phase1", "call_count": 40, "model_executed_count": 40, "failure_count": 0, "total_tokens": 40938, "accepted": true}`
- source checks: `4` pass / `4` total
- submission state: `{"status": "missing", "path": "evidence/world_class/submissions/provider-holdout.json", "artifact_ref_count": 0, "attested_real_evidence": false, "privacy_contract_satisfied": false, "ledger_reviewer_approved": false, "ledger_reviewer": "", "ledger_reviewed_at": "", "ledger_counts_as_completion": false}`

### Provenance Requirements

- provider-backed model run
- observed timing
- observed token metadata

### Source Runbook

- Set DEEPSEEK_API_KEY in the operator shell; never commit or print the value.
- `python3 scripts/yao.py evidence-build . --run-id <PROVIDER_RUN_ID> --self`
- Keep the generated private answer key and role-neutral review materials inside .yao/runs/<PROVIDER_RUN_ID>.
- `python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD> --self`
- Copy evidence/world_class/templates/provider-holdout.intake.json to evidence/world_class/submissions/provider-holdout.json and fill only real evidence fields.
- `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions --self`

### Source Evidence Checks

| Check | Current | Expected | Status |
| --- | --- | --- | --- |
| Provider calls | `40` | `==40` | `pass` |
| Provider model runs | `40` | `==40` | `pass` |
| Provider failures | `0` | `==0` | `pass` |
| Token budget | `40938` | `<=250000` | `pass` |

### Completion Assertions

- reports/provider_output_evaluation.json summary.call_count == 40
- reports/provider_output_evaluation.json summary.model_executed_count == 40
- reports/provider_output_evaluation.json summary.failure_count == 0
- reports/provider_output_evaluation.json summary.total_tokens <= 250000
- reports/skill_os2_audit.json item provider-holdout status becomes pass

### Privacy Contract

- Do not commit provider credentials or environment dumps.
- The output execution report records output hashes and aggregate run metadata, not raw provider prompts.

## Human Adjudication

- objective: Collect three controlled, independent reviews of the same 20-pair provider blind pack.
- source status: `pass`
- observed state: `{"contract_version": "phase1", "reviewer_count": 3, "pair_count": 20, "failure_count": 0, "blind_pack_bound": true, "accepted": true}`
- source checks: `4` pass / `4` total
- submission state: `{"status": "missing", "path": "evidence/world_class/submissions/human-adjudication.json", "artifact_ref_count": 0, "attested_real_evidence": false, "privacy_contract_satisfied": false, "ledger_reviewer_approved": false, "ledger_reviewer": "", "ledger_reviewed_at": "", "ledger_counts_as_completion": false}`

### Provenance Requirements

- real reviewer identity
- blind A/B decisions
- answer key unopened until decisions exist

### Source Runbook

- Give each registered reviewer an independent copy of the matching provider_review_reviewer-*.json template and the role-neutral blind pack.
- Collect all 20 A/B choices, reasons, controlled submission ids, timestamps, and truthful independent-review attestations.
- Export an access-controlled reviewer registry that binds each reviewer id to the exact packet SHA256.
- `python3 scripts/yao.py evidence-finalize-review . --source-run <PROVIDER_RUN_ID> --decisions <reviewer-a.json> --decisions <reviewer-b.json> --decisions <reviewer-c.json> --reviewer-registry <registry.json> --run-id <FINAL_RUN_ID> --self`
- `python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD> --self`
- Copy evidence/world_class/templates/human-adjudication.intake.json to evidence/world_class/submissions/human-adjudication.json and fill only real evidence fields.
- `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions --self`

### Source Evidence Checks

| Check | Current | Expected | Status |
| --- | --- | --- | --- |
| Registered reviewers | `3` | `==3` | `pass` |
| Blind pairs | `20` | `==20` | `pass` |
| Review failures | `0` | `==0` | `pass` |
| Blind pack binding | `True` | `true` | `pass` |

### Completion Assertions

- reports/provider_output_adjudication.json summary.reviewer_count == 3
- reports/provider_output_adjudication.json summary.pair_count == 20
- reports/provider_output_adjudication.json summary.failure_count == 0
- reports/provider_output_adjudication.json evidence_binding.blind_pack_sha256 matches the source run
- reports/skill_os2_audit.json item human-adjudication status becomes pass

### Privacy Contract

- Reviewer packets contain choices, reasons, hashes, and controlled submission metadata without raw prompts or answer-key roles.
- The private answer key remains under .yao/runs and is opened by the finalizer after all controlled packets are fixed.
- The adjudication and lineage artifacts preserve blind_pack_sha256 and answer_key_sha256 commitments.

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
- `python3 scripts/yao.py package . --platform openai --platform claude --platform generic --platform vscode --output-dir dist --zip --self`
- `python3 scripts/yao.py install-simulate . --package-dir dist --install-root dist/install-simulation --self`
- `python3 scripts/yao.py runtime-permissions . --package-dir dist --self`
- `python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD> --self`
- Copy evidence/world_class/templates/native-permission-enforcement.intake.json to evidence/world_class/submissions/native-permission-enforcement.json and fill only real evidence fields.
- `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions --self`

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
- observed state: `{"external_source_events": 0, "adoption_sample_count": 0, "raw_content_allowed": false, "risk_band": "no-data", "accepted": false}`
- source checks: `1` pass / `3` total
- submission state: `{"status": "missing", "path": "evidence/world_class/submissions/native-client-telemetry.json", "artifact_ref_count": 0, "attested_real_evidence": false, "privacy_contract_satisfied": false, "ledger_reviewer_approved": false, "ledger_reviewer": "", "ledger_reviewed_at": "", "ledger_counts_as_completion": false}`

### Provenance Requirements

- real external client source
- metadata-only event
- local-first import path

### Source Runbook

- `python3 scripts/telemetry_native_host.py . --write-launcher /tmp/yao-telemetry-host.sh --write-manifest /tmp/yao-telemetry-host.json --allowed-origin chrome-extension://<extension-id>/`
- Install the generated native messaging manifest for the real client and send at least one accepted skill_activation or skill_output event.
- `python3 scripts/yao.py telemetry-import . --input-jsonl .yao/telemetry_spool/external_events.jsonl --self`
- `python3 scripts/yao.py skill-atlas --workspace-root . --self`
- `python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD> --self`
- Copy evidence/world_class/templates/native-client-telemetry.intake.json to evidence/world_class/submissions/native-client-telemetry.json and fill only real evidence fields.
- `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions --self`

### Source Evidence Checks

| Check | Current | Expected | Status |
| --- | --- | --- | --- |
| External events | `0` | `>0` | `blocked` |
| Adoption sample | `0` | `>0` | `blocked` |
| Raw content blocked | `False` | `false` | `pass` |

### Completion Assertions

- reports/adoption_drift_report.json summary.source_types.external > 0
- reports/adoption_drift_report.json summary.adoption_sample_count > 0
- reports/skill_os2_audit.json item native-client-telemetry status becomes pass

### Privacy Contract

- Telemetry must remain metadata-only and local-first.
- Do not package reports/telemetry_events.jsonl or any raw prompt, output, transcript, note, or message field.
