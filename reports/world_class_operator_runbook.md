# World-Class Operator Runbook

Generated at: `2026-11-09`

## Summary

- decision: `collect-evidence`
- ready to claim world-class: `false`
- runbook counts as completion: `false`
- evidence items: `4`
- pending: `4`
- awaiting submission: `4`
- ready for ledger review: `0`
- phase queue: `2` blocked / `2` phases
- phase queue rows: `7`
- phase queue counts as completion: `false`
- coordination steps: `6` user-required / `6` total
- coordination pending keys: `human-adjudication, native-client-telemetry, native-permission-enforcement, provider-holdout`
- coordination counts as completion: `false`
- release gate ready: `false`
- release gate blocked checks: `4` / `5`
- release gate counts as completion: `false`

This runbook coordinates evidence collection only. It does not accept submissions or make world-class completion true.

## Fast Path

1. Run the real external or human work for one evidence item.
2. Generate the matching submission draft.
3. Replace template-only fields with aggregate evidence and provenance.
4. Validate intake, review the queue, refresh the ledger, then run the claim guard.

## Coordination Plan

| Step | Evidence | Owner | Needs user | User action | Assistant action | Command | Pass condition |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `prepare-evidence-session` | `all` | assistant + user | `true` | Confirm provider access, reviewer availability, target client path, and telemetry client path before collection starts. | Run preflight and prepare submission drafts without accepting them as evidence. | `python3 scripts/yao.py world-class-preflight . --submissions-dir evidence/world_class/submissions --self && python3 scripts/yao.py world-class-submission-kit . --output-dir evidence/world_class/submissions --prefill-artifacts --self` | Preflight lists the same pending evidence keys and no credential values are printed. |
| `collect-provider-holdout` | `provider-holdout` | assistant + operator with provider credentials | `true` | Provide DEEPSEEK_API_KEY through the environment for the fixed Flash+Pro matrix. | Run evidence-build, verify 40 governed calls and the private blind-review material boundary, then prepare the evidence packet. | `python3 scripts/yao.py evidence-build . --run-id <PROVIDER_RUN_ID> --self` | reports/provider_output_evaluation.json records 40/40 model calls, zero failures, and total_tokens <= 250000. |
| `collect-human-adjudication` | `human-adjudication` | human reviewer + assistant | `true` | Have reviewer-a, reviewer-b, and reviewer-c independently complete the same 20-pair role-neutral pack through controlled submissions. | Verify the three packet identities and commitments, then finalize the source provider run without rerunning the matrix. | `python3 scripts/yao.py evidence-finalize-review . --source-run <PROVIDER_RUN_ID> --decisions <A.json> --decisions <B.json> --decisions <C.json> --reviewer-registry <registry.json> --self` | reports/provider_output_adjudication.json has reviewer_count == 3, pair_count == 20, and failure_count == 0. |
| `collect-native-permission-enforcement` | `native-permission-enforcement` | target client or installer integrator + assistant | `true` | Select a real target client or external installer guard that can enforce declared capabilities instead of metadata-only fallback. | Run runtime permission probes, package verification, install simulation, and prepare the native enforcement evidence packet. | `python3 scripts/yao.py runtime-permissions . --package-dir dist --self` | reports/runtime_permission_probes.json has native_enforcement_count > 0 and failure_count == 0. |
| `collect-native-client-telemetry` | `native-client-telemetry` | real client integrator + assistant | `true` | Install the native host manifest in a real Browser, Chrome, IDE, or provider client and trigger a metadata-only event. | Generate native host assets, import the external event JSONL, refresh adoption drift, and prepare the telemetry evidence packet. | `python3 scripts/yao.py telemetry-import . --input-jsonl .yao/telemetry_spool/external_events.jsonl --source external --self` | reports/adoption_drift_report.json has source_types.external > 0 and adoption_sample_count > 0. |
| `review-and-release-gate` | `all` | assistant + ledger reviewer | `true` | Approve only validated evidence packets and confirm the release wording after the claim guard passes. | Run intake, submission review, ledger, claim guard, benchmark, evidence consistency, Review Studio, and CI before final publish. | `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions --self && python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions --self && python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions --self && python3 scripts/yao.py world-class-claim-guard . --self && make ci-test` | Ledger ready_to_claim_world_class, benchmark public_claim_ready, claim guard violation_count == 0, Review Studio has no blockers, and CI passes. |

## Phase Queue

| Phase | Status | Rows | Blocked | Owners | Next action | Verify |
| --- | --- | ---: | ---: | --- | --- | --- |
| `unblock-access` | `blocked` | `4` | `4` | Browser/Chrome/IDE/provider client integrator, human reviewer, operator with provider credentials, target client or installer integrator | Assign three independent controlled reviewer identities before claiming human adjudication. | `python3 scripts/yao.py world-class-preflight . --submissions-dir evidence/world_class/submissions --self` |
| `collect-source` | `blocked` | `3` | `3` | Browser/Chrome/IDE/provider client integrator, target client or installer integrator | Telemetry must include adoption outcome evidence. | `python3 scripts/yao.py telemetry-import . --input-jsonl .yao/telemetry_spool/external_events.jsonl --self && python3 scripts/yao.py world-class-preflight . --submissions-dir evidence/world_class/submissions --self` |

## Evidence Items

| Evidence | Ledger | Intake | Review | Blocked checks | Next source action | Owner |
| --- | --- | --- | --- | ---: | --- | --- |
| `provider-holdout` | `pending` | `awaiting-submission` | `awaiting-submission` | `0` | none | operator with provider credentials |
| `human-adjudication` | `pending` | `awaiting-submission` | `awaiting-submission` | `0` | none | human reviewer |
| `native-permission-enforcement` | `pending` | `awaiting-submission` | `awaiting-submission` | `1` | Collect real target-client or external runtime guard proof. | target client or installer integrator |
| `native-client-telemetry` | `pending` | `awaiting-submission` | `awaiting-submission` | `2` | Import at least one metadata-only event from a real client. | Browser/Chrome/IDE/provider client integrator |

## Provider Holdout

- objective: Complete the fixed 10-case DeepSeek Flash+Pro matrix with 40 real calls and governed budget evidence.
- blocking reason: No evidence packet has been submitted for review.
- blocked source checks: `0`
- repair rows: `1` blocked
- phase queue: `1` blocked phases
- submission: `evidence/world_class/submissions/provider-holdout.json`
- template: `evidence/world_class/templates/provider-holdout.intake.json`

### Phase Queue

| Phase | Status | Rows | Blocked | Next action |
| --- | --- | ---: | ---: | --- |
| `unblock-access` | `blocked` | `1` | `1` | Set DEEPSEEK_API_KEY in the operator shell; never commit or print the value. |

### Source Runbook

- Set DEEPSEEK_API_KEY in the operator shell; never commit or print the value.
- python3 scripts/yao.py evidence-build . --run-id <PROVIDER_RUN_ID> --self
- Keep the generated private answer key and role-neutral review materials inside .yao/runs/<PROVIDER_RUN_ID>.
- python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD> --self
- Copy evidence/world_class/templates/provider-holdout.intake.json to evidence/world_class/submissions/provider-holdout.json and fill only real evidence fields.
- python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions --self

### Commands

- prepare_submission: `python3 scripts/yao.py world-class-submission-kit . --evidence-key provider-holdout --output-dir evidence/world_class/submissions --self`
- validate_intake: `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions --self`
- review_queue: `python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions --self`
- refresh_ledger: `python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions --self`
- guard_claim: `python3 scripts/yao.py world-class-claim-guard . --self`

### Must Collect

- provider-backed model run
- observed timing
- observed token metadata

### Success Checks

- reports/provider_output_evaluation.json summary.call_count == 40
- reports/provider_output_evaluation.json summary.model_executed_count == 40
- reports/provider_output_evaluation.json summary.failure_count == 0
- reports/provider_output_evaluation.json summary.total_tokens <= 250000
- reports/skill_os2_audit.json item provider-holdout status becomes pass

### Privacy Contract

- Do not commit provider credentials or environment dumps.
- The output execution report records output hashes and aggregate run metadata, not raw provider prompts.

### Evidence Artifacts

- evals/output/provider_matrix.json
- reports/provider_output_evaluation.json
- reports/provider_output_blind_pack.json
- reports/provider_output_answer_commitment.json
- reports/skill_os2_audit.json
- evidence/world_class/intake.schema.json
- evidence/world_class/templates/provider-holdout.intake.json
- reports/world_class_evidence_intake.json
- reports/world_class_evidence_intake.md

### Next Source Actions

- No blocked source checks.

### Source Evidence Snapshot

| Check | Current | Expected | Status | Next action |
| --- | --- | --- | --- | --- |
| Provider calls | `40` | `==40` | `pass` | Complete all 40 fixed DeepSeek calls. |
| Provider model runs | `40` | `==40` | `pass` | Require model identity on all 40 calls. |
| Provider failures | `0` | `==0` | `pass` | Resolve every fixed-matrix failure. |
| Token budget | `40938` | `<=250000` | `pass` | Keep the matrix within the 250000-token ceiling. |

## Human Adjudication

- objective: Collect three controlled, independent reviews of the same 20-pair provider blind pack.
- blocking reason: No evidence packet has been submitted for review.
- blocked source checks: `0`
- repair rows: `1` blocked
- phase queue: `1` blocked phases
- submission: `evidence/world_class/submissions/human-adjudication.json`
- template: `evidence/world_class/templates/human-adjudication.intake.json`

### Phase Queue

| Phase | Status | Rows | Blocked | Next action |
| --- | --- | ---: | ---: | --- |
| `unblock-access` | `blocked` | `1` | `1` | Assign three independent controlled reviewer identities before claiming human adjudication. |

### Source Runbook

- Give each registered reviewer an independent copy of the matching provider_review_reviewer-*.json template and the role-neutral blind pack.
- Collect all 20 A/B choices, reasons, controlled submission ids, timestamps, and truthful independent-review attestations.
- Export an access-controlled reviewer registry that binds each reviewer id to the exact packet SHA256.
- python3 scripts/yao.py evidence-finalize-review . --source-run <PROVIDER_RUN_ID> --decisions <reviewer-a.json> --decisions <reviewer-b.json> --decisions <reviewer-c.json> --reviewer-registry <registry.json> --run-id <FINAL_RUN_ID> --self
- python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD> --self
- Copy evidence/world_class/templates/human-adjudication.intake.json to evidence/world_class/submissions/human-adjudication.json and fill only real evidence fields.
- python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions --self

### Commands

- prepare_submission: `python3 scripts/yao.py world-class-submission-kit . --evidence-key human-adjudication --output-dir evidence/world_class/submissions --self`
- validate_intake: `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions --self`
- review_queue: `python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions --self`
- refresh_ledger: `python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions --self`
- guard_claim: `python3 scripts/yao.py world-class-claim-guard . --self`

### Must Collect

- real reviewer identity
- blind A/B decisions
- answer key unopened until decisions exist

### Success Checks

- reports/provider_output_adjudication.json summary.reviewer_count == 3
- reports/provider_output_adjudication.json summary.pair_count == 20
- reports/provider_output_adjudication.json summary.failure_count == 0
- reports/provider_output_adjudication.json evidence_binding.blind_pack_sha256 matches the source run
- reports/skill_os2_audit.json item human-adjudication status becomes pass

### Privacy Contract

- Reviewer packets contain choices, reasons, hashes, and controlled submission metadata without raw prompts or answer-key roles.
- The private answer key remains under .yao/runs and is opened by the finalizer after all controlled packets are fixed.
- The adjudication and lineage artifacts preserve blind_pack_sha256 and answer_key_sha256 commitments.

### Evidence Artifacts

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

### Next Source Actions

- No blocked source checks.

### Source Evidence Snapshot

| Check | Current | Expected | Status | Next action |
| --- | --- | --- | --- | --- |
| Registered reviewers | `3` | `==3` | `pass` | Collect reviewer-a, reviewer-b, and reviewer-c. |
| Blind pairs | `20` | `==20` | `pass` | Complete all 20 blind pairs. |
| Review failures | `0` | `==0` | `pass` | Resolve packet, identity, or adjudication failures. |
| Blind pack binding | `True` | `true` | `pass` | Bind adjudication to the reviewed blind pack SHA256. |

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
- python3 scripts/yao.py package . --platform openai --platform claude --platform generic --platform vscode --output-dir dist --zip --self
- python3 scripts/yao.py install-simulate . --package-dir dist --install-root dist/install-simulation --self
- python3 scripts/yao.py runtime-permissions . --package-dir dist --self
- python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD> --self
- Copy evidence/world_class/templates/native-permission-enforcement.intake.json to evidence/world_class/submissions/native-permission-enforcement.json and fill only real evidence fields.
- python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions --self

### Commands

- prepare_submission: `python3 scripts/yao.py world-class-submission-kit . --evidence-key native-permission-enforcement --output-dir evidence/world_class/submissions --self`
- validate_intake: `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions --self`
- review_queue: `python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions --self`
- refresh_ledger: `python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions --self`
- guard_claim: `python3 scripts/yao.py world-class-claim-guard . --self`

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
- blocked source checks: `2`
- repair rows: `3` blocked
- phase queue: `2` blocked phases
- submission: `evidence/world_class/submissions/native-client-telemetry.json`
- template: `evidence/world_class/templates/native-client-telemetry.intake.json`

### Phase Queue

| Phase | Status | Rows | Blocked | Next action |
| --- | --- | ---: | ---: | --- |
| `unblock-access` | `blocked` | `1` | `1` | Install a real Browser, Chrome, IDE, or provider client that emits metadata-only events. |
| `collect-source` | `blocked` | `2` | `2` | Telemetry must include adoption outcome evidence. |

### Source Runbook

- python3 scripts/telemetry_native_host.py . --write-launcher /tmp/yao-telemetry-host.sh --write-manifest /tmp/yao-telemetry-host.json --allowed-origin chrome-extension://<extension-id>/
- Install the generated native messaging manifest for the real client and send at least one accepted skill_activation or skill_output event.
- python3 scripts/yao.py telemetry-import . --input-jsonl .yao/telemetry_spool/external_events.jsonl --self
- python3 scripts/yao.py skill-atlas --workspace-root . --self
- python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD> --self
- Copy evidence/world_class/templates/native-client-telemetry.intake.json to evidence/world_class/submissions/native-client-telemetry.json and fill only real evidence fields.
- python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions --self

### Commands

- prepare_submission: `python3 scripts/yao.py world-class-submission-kit . --evidence-key native-client-telemetry --output-dir evidence/world_class/submissions --self`
- validate_intake: `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions --self`
- review_queue: `python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions --self`
- refresh_ledger: `python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions --self`
- guard_claim: `python3 scripts/yao.py world-class-claim-guard . --self`

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
- Telemetry must include adoption outcome evidence.

### Source Evidence Snapshot

| Check | Current | Expected | Status | Next action |
| --- | --- | --- | --- | --- |
| External events | `0` | `>0` | `blocked` | Import at least one metadata-only event from a real client. |
| Adoption sample | `0` | `>0` | `blocked` | Telemetry must include adoption outcome evidence. |
| Raw content blocked | `False` | `false` | `pass` | Telemetry must stay metadata-only. |

## Release Gate

- decision: `blocked-until-evidence-accepted`
- ready: `false`
- blocked checks: `4` / `5`
- counts as completion: `false`
- final manual check: Run make ci-test in a clean worktree and verify GitHub Actions before converting the PR out of Draft.

| Check | Current | Expected | Status | Artifact |
| --- | --- | --- | --- | --- |
| World-class ledger ready | `evidence-pending` | `ready_to_claim_world_class == true` | `blocked` | `reports/world_class_evidence_ledger.json` |
| Claim guard clean | `violations 0; ledger ready False` | `violation_count == 0 and ledger_ready_to_claim_world_class == true` | `blocked` | `reports/world_class_claim_guard.json` |
| Benchmark public claim ready | `public_claim_ready False` | `public_claim_ready == true` | `blocked` | `reports/benchmark_reproducibility.json` |
| Review Studio clean | `blockers 0; warnings 5` | `blocker_count == 0 and warning_count == 0` | `blocked` | `reports/review-studio.json` |
| Evidence consistency clean | `consistent` | `decision == consistent and fail_count == 0` | `pass` | `reports/evidence_consistency.json` |

## Boundary

- Planned work, draft packets, metadata fallback, pending human decisions, and local command runners do not count as completion.
- Valid intake means ready for submission review; ledger review still requires passing source evidence.
- The world-class ledger and claim guard remain the source of truth.
