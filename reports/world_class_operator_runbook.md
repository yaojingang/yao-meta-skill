# World-Class Operator Runbook

Generated at: `2026-06-13`

## Summary

- decision: `collect-evidence`
- ready to claim world-class: `false`
- runbook counts as completion: `false`
- evidence items: `4`
- pending: `4`
- awaiting submission: `4`
- ready for ledger review: `0`
- phase queue: `2` blocked / `2` phases
- phase queue rows: `13`
- phase queue counts as completion: `false`

This runbook coordinates evidence collection only. It does not accept submissions or make world-class completion true.

## Fast Path

1. Run the real external or human work for one evidence item.
2. Generate the matching submission draft.
3. Replace template-only fields with aggregate evidence and provenance.
4. Validate intake, review the queue, refresh the ledger, then run the claim guard.

## Phase Queue

| Phase | Status | Rows | Blocked | Owners | Next action | Verify |
| --- | --- | ---: | ---: | --- | --- | --- |
| `unblock-access` | `blocked` | `4` | `4` | Browser/Chrome/IDE/provider client integrator, human reviewer, operator with provider credentials, target client or installer integrator | Assign a real reviewer identity before claiming human adjudication. | `python3 scripts/yao.py world-class-preflight . --submissions-dir evidence/world_class/submissions` |
| `collect-source` | `blocked` | `9` | `9` | Browser/Chrome/IDE/provider client integrator, human reviewer, operator with provider credentials, target client or installer integrator | Set reviewer_attestation only after choices are completed before opening the answer key. | `python3 scripts/yao.py output-review && python3 scripts/yao.py world-class-preflight . --submissions-dir evidence/world_class/submissions` |

## Evidence Items

| Evidence | Ledger | Intake | Review | Blocked checks | Next source action | Owner |
| --- | --- | --- | --- | ---: | --- | --- |
| `provider-holdout` | `pending` | `awaiting-submission` | `awaiting-submission` | `2` | Run provider-backed output-exec with real credentials. | operator with provider credentials |
| `human-adjudication` | `pending` | `awaiting-submission` | `awaiting-submission` | `5` | Record a reviewer choice and reason for every pair. | human reviewer |
| `native-permission-enforcement` | `pending` | `awaiting-submission` | `awaiting-submission` | `1` | Collect real target-client or external runtime guard proof. | target client or installer integrator |
| `native-client-telemetry` | `pending` | `awaiting-submission` | `awaiting-submission` | `1` | Import at least one metadata-only event from a real client. | Browser/Chrome/IDE/provider client integrator |

## Provider Holdout

- objective: Collect at least one provider-backed output-eval holdout run with model, timing, and token metadata.
- blocking reason: No evidence packet has been submitted for review.
- blocked source checks: `2`
- repair rows: `3` blocked
- phase queue: `2` blocked phases
- submission: `evidence/world_class/submissions/provider-holdout.json`
- template: `evidence/world_class/templates/provider-holdout.intake.json`

### Phase Queue

| Phase | Status | Rows | Blocked | Next action |
| --- | --- | ---: | ---: | --- |
| `unblock-access` | `blocked` | `1` | `1` | Set OPENAI_API_KEY in the operator shell; never commit or print the value. |
| `collect-source` | `blocked` | `2` | `2` | Run provider-backed output-exec with real credentials. |

### Source Runbook

- Set OPENAI_API_KEY in the operator shell before running provider evidence; never commit or print the value.
- export YAO_OUTPUT_EVAL_MODEL=${YAO_OUTPUT_EVAL_MODEL:-gpt-4.1-mini}
- python3 scripts/yao.py output-exec --provider-runner openai --timeout-seconds 60
- python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD>
- Copy evidence/world_class/templates/provider-holdout.intake.json to evidence/world_class/submissions/provider-holdout.json and fill only real evidence fields.
- python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions

### Commands

- prepare_submission: `python3 scripts/yao.py world-class-submission-kit . --evidence-key provider-holdout --output-dir evidence/world_class/submissions`
- validate_intake: `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions`
- review_queue: `python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions`
- refresh_ledger: `python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions`
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

### Next Source Actions

- Run provider-backed output-exec with real credentials.
- Provider execution should return non-estimated token usage.

### Source Evidence Snapshot

| Check | Current | Expected | Status | Next action |
| --- | --- | --- | --- | --- |
| Provider model run | `0` | `>0` | `blocked` | Run provider-backed output-exec with real credentials. |
| Timing observed | `10` | `>0` | `pass` | Provider execution should record timing metadata. |
| Token usage observed | `0` | `>0` | `blocked` | Provider execution should return non-estimated token usage. |

## Human Adjudication

- objective: Record real blind A/B reviewer decisions before claiming human output review completion.
- blocking reason: No evidence packet has been submitted for review.
- blocked source checks: `5`
- repair rows: `6` blocked
- phase queue: `2` blocked phases
- submission: `evidence/world_class/submissions/human-adjudication.json`
- template: `evidence/world_class/templates/human-adjudication.intake.json`

### Phase Queue

| Phase | Status | Rows | Blocked | Next action |
| --- | --- | ---: | ---: | --- |
| `unblock-access` | `blocked` | `1` | `1` | Assign a real reviewer identity before claiming human adjudication. |
| `collect-source` | `blocked` | `5` | `5` | Set reviewer_attestation only after choices are completed before opening the answer key. |

### Source Runbook

- python3 scripts/yao.py output-review-kit --write-template
- Open reports/output_review_kit.md and choose A or B for each pair without opening the answer key.
- python3 scripts/adjudicate_output_review.py --write-template
- Record reviewer choices in a separate JSON, JSONL, or CSV decision source with reviewer, reviewed_at, case_id, winner_variant, confidence, required reason, and truthful reviewer_attestation only.
- python3 scripts/yao.py output-review-import --input <reviewer-decisions.json> --blind-review-attested --run-adjudication
- python3 scripts/yao.py output-review
- python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD>
- Copy evidence/world_class/templates/human-adjudication.intake.json to evidence/world_class/submissions/human-adjudication.json and fill only real evidence fields.
- python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions

### Commands

- prepare_submission: `python3 scripts/yao.py world-class-submission-kit . --evidence-key human-adjudication --output-dir evidence/world_class/submissions`
- validate_intake: `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions`
- review_queue: `python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions`
- refresh_ledger: `python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions`
- guard_claim: `python3 scripts/yao.py world-class-claim-guard .`

### Must Collect

- real reviewer identity
- blind A/B decisions
- answer key unopened until decisions exist

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

### Privacy Contract

- Reviewer decisions should not include raw user data or private customer detail.
- Reviewer reasons must be rubric-based and must not include raw user data or private customer detail.
- The decision importer rejects raw prompt, output, transcript, message, and answer-key fields.
- The adjudication evidence stores prompt_sha256 instead of raw prompt text.
- The decision and adjudication artifacts preserve blind_pack_sha256 so reviewers can audit exactly which pack was judged.
- Keep the answer key separate until after decisions are recorded.

### Evidence Artifacts

- reports/output_blind_review_pack.md
- reports/output_review_kit.md
- reports/output_review_decisions.json
- reports/output_review_adjudication.json
- reports/output_review_adjudication.md
- scripts/import_output_review_decisions.py
- evidence/world_class/intake.schema.json
- evidence/world_class/templates/human-adjudication.intake.json
- reports/world_class_evidence_intake.json
- reports/world_class_evidence_intake.md

### Next Source Actions

- Record a reviewer choice and reason for every pair.
- Every pair needs one valid human judgment.
- Record reviewer and reviewed_at before adjudication can count.
- Set reviewer_attestation only after choices are completed before opening the answer key.
- Complete all reviewer decisions with metadata and rationale, plus blind-review attestation and integrity fingerprints.

### Source Evidence Snapshot

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

- objective: Prove at least one real target client or external installer runtime guard enforces approved high-permission capabilities.
- blocking reason: No evidence packet has been submitted for review.
- blocked source checks: `1`
- repair rows: `2` blocked
- phase queue: `2` blocked phases
- submission: `evidence/world_class/submissions/native-permission-enforcement.json`
- template: `evidence/world_class/templates/native-permission-enforcement.intake.json`

### Phase Queue

| Phase | Status | Rows | Blocked | Next action |
| --- | --- | ---: | ---: | --- |
| `unblock-access` | `blocked` | `1` | `1` | Attach a real target-client or external installer runtime guard; metadata fallback is not enough. |
| `collect-source` | `blocked` | `1` | `1` | Collect real target-client or external runtime guard proof. |

### Source Runbook

- Implement or connect a real target client or external installer runtime guard that blocks undeclared network, file_write, or subprocess capabilities.
- Update the generated target adapter only when the guard is actually enforced by that target.
- python3 scripts/yao.py package . --platform openai --platform claude --platform generic --platform vscode --output-dir dist --zip
- python3 scripts/yao.py install-simulate . --package-dir dist --install-root dist/install-simulation
- python3 scripts/yao.py runtime-permissions . --package-dir dist
- python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD>
- Copy evidence/world_class/templates/native-permission-enforcement.intake.json to evidence/world_class/submissions/native-permission-enforcement.json and fill only real evidence fields.
- python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions

### Commands

- prepare_submission: `python3 scripts/yao.py world-class-submission-kit . --evidence-key native-permission-enforcement --output-dir evidence/world_class/submissions`
- validate_intake: `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions`
- review_queue: `python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions`
- refresh_ledger: `python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions`
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

### Next Source Actions

- Collect real target-client or external runtime guard proof.

### Source Evidence Snapshot

| Check | Current | Expected | Status | Next action |
| --- | --- | --- | --- | --- |
| Native enforcement | `0` | `>0` | `blocked` | Collect real target-client or external runtime guard proof. |
| Probe failures | `0` | `==0` | `pass` | Runtime permission probes must stay clean. |
| Installer support | `True` | `true` | `pass` | Installer enforcement is supporting evidence, not native proof. |

## Native Client Telemetry

- objective: Import production metadata-only events from a real external client into the local drift loop.
- blocking reason: No evidence packet has been submitted for review.
- blocked source checks: `1`
- repair rows: `2` blocked
- phase queue: `2` blocked phases
- submission: `evidence/world_class/submissions/native-client-telemetry.json`
- template: `evidence/world_class/templates/native-client-telemetry.intake.json`

### Phase Queue

| Phase | Status | Rows | Blocked | Next action |
| --- | --- | ---: | ---: | --- |
| `unblock-access` | `blocked` | `1` | `1` | Install a real Browser, Chrome, IDE, or provider client that emits metadata-only events. |
| `collect-source` | `blocked` | `1` | `1` | Import at least one metadata-only event from a real client. |

### Source Runbook

- python3 scripts/telemetry_native_host.py . --write-launcher /tmp/yao-telemetry-host.sh --write-manifest /tmp/yao-telemetry-host.json --allowed-origin chrome-extension://<extension-id>/
- Install the generated native messaging manifest for the real client and send at least one accepted skill_activation or skill_output event.
- python3 scripts/yao.py telemetry-import . --input-jsonl .yao/telemetry_spool/external_events.jsonl
- python3 scripts/yao.py skill-atlas --workspace-root .
- python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD>
- Copy evidence/world_class/templates/native-client-telemetry.intake.json to evidence/world_class/submissions/native-client-telemetry.json and fill only real evidence fields.
- python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions

### Commands

- prepare_submission: `python3 scripts/yao.py world-class-submission-kit . --evidence-key native-client-telemetry --output-dir evidence/world_class/submissions`
- validate_intake: `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions`
- review_queue: `python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions`
- refresh_ledger: `python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions`
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

### Next Source Actions

- Import at least one metadata-only event from a real client.

### Source Evidence Snapshot

| Check | Current | Expected | Status | Next action |
| --- | --- | --- | --- | --- |
| External events | `0` | `>0` | `blocked` | Import at least one metadata-only event from a real client. |
| Adoption sample | `1` | `>0` | `pass` | Telemetry must include adoption outcome evidence. |
| Raw content blocked | `False` | `false` | `pass` | Telemetry must stay metadata-only. |

## Boundary

- Planned work, draft packets, metadata fallback, pending human decisions, and local command runners do not count as completion.
- Valid intake means ready for submission review; ledger review still requires passing source evidence.
- The world-class ledger and claim guard remain the source of truth.
