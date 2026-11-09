# World-Class Evidence Preflight

Generated at: `2026-11-09`

## Summary

- decision: `collection-preflight-blocked`
- ready to claim world-class: `false`
- preflight counts as evidence: `false`
- credential value exposed: `false`
- collection ready: `1`
- collection blocked: `3`
- source checks: `11` pass / `14` total
- repair rows: `7` blocked / `7` total
- phase queue: `2` blocked / `2` phases
- phase queue rows: `7`
- next repair action: `human-adjudication-precheck-human-reviewer`
- next repair owner: `human reviewer`
- next phase: `unblock-access`
- next phase action: `human-adjudication-precheck-human-reviewer`

This preflight report checks whether an operator can start collecting the remaining external or human evidence. It never accepts evidence, prints secret values, or changes the world-class ledger.

## Submission Kit Handoff

- submissions directory: `evidence/world_class/submissions`
- prepare drafts: `python3 scripts/yao.py world-class-submission-kit . --output-dir evidence/world_class/submissions --self`
- prepare drafts with artifact SHA prefill: `python3 scripts/yao.py world-class-submission-kit . --output-dir evidence/world_class/submissions --prefill-artifacts --self`
- validate intake: `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions --self`
- review queue: `python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions --self`
- refresh ledger: `python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions --self`
- guard claims: `python3 scripts/yao.py world-class-claim-guard . --self`
- drafts count as evidence: `false`
- artifact prefill counts as evidence: `false`
- submission refs ready: `6` / `7`
- supporting evidence ready: `31` / `33`

Generate the submission kit after the real provider, human, native-permission, or native-client work exists. The generated JSON drafts remain `template_only: true` until an operator edits them with real aggregate artifact references and matching SHA-256 digests. The prefill command only inserts local artifact SHA-256 digests; it does not make a draft count as evidence.

| Role | Copy to artifact_refs | Ready | Meaning |
| --- | --- | --- | --- |
| `submission-ref` | `true` | `6 / 7` | Rows marked submission-ref are the aggregate paths expected in artifact_refs. |
| `supporting-evidence` | `false` | `31 / 33` | Supporting-evidence rows help reviewers audit the packet but do not all need to be copied into artifact_refs. |

`submission-ref` rows are the only checklist rows expected in `artifact_refs`; `supporting-evidence` rows stay available for audit context and reviewer traceability.

## Phase Queue

Phase queue rows group the same repair checklist into operator execution phases. They are procedural guidance only and do not count as completion evidence.

| Priority | Phase | Status | Rows | Owners | Evidence | Verify | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `20` | `unblock-access` | `blocked` | 4 / 4 blocked | Browser/Chrome/IDE/provider client integrator, human reviewer, operator with provider credentials, target client or installer integrator | human-adjudication, native-client-telemetry, native-permission-enforcement, provider-holdout | `python3 scripts/yao.py world-class-preflight . --submissions-dir evidence/world_class/submissions --self` | Assign three independent controlled reviewer identities before claiming human adjudication. |
| `40` | `collect-source` | `blocked` | 3 / 3 blocked | Browser/Chrome/IDE/provider client integrator, target client or installer integrator | native-client-telemetry, native-permission-enforcement | `python3 scripts/yao.py telemetry-import . --input-jsonl .yao/telemetry_spool/external_events.jsonl --self && python3 scripts/yao.py world-class-preflight . --submissions-dir evidence/world_class/submissions --self` | Telemetry must include adoption outcome evidence. |

## Evidence Items

| Evidence | Status | Intake | Review | Next action |
| --- | --- | --- | --- | --- |
| `provider-holdout` | `blocked` | `awaiting-submission` | `awaiting-submission` | Set DEEPSEEK_API_KEY in the operator shell; never commit or print the value. |
| `human-adjudication` | `ready-for-human-review` | `awaiting-submission` | `awaiting-submission` | Assign three independent controlled reviewer identities before claiming human adjudication. |
| `native-permission-enforcement` | `blocked` | `awaiting-submission` | `awaiting-submission` | Attach a real target-client or external installer runtime guard; metadata fallback is not enough. |
| `native-client-telemetry` | `blocked` | `awaiting-submission` | `awaiting-submission` | Install a real Browser, Chrome, IDE, or provider client that emits metadata-only events. |

## Repair Checklist

Repair rows convert preflight and source blockers into a prioritized operator queue. They are guidance only and do not count as completion evidence.

| Priority | Phase | Owner | Evidence | Type | Target | Status | Verify | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `20` | `unblock-access` | human reviewer | `human-adjudication` | `precheck` | `human-reviewer` | `blocked` | `python3 scripts/yao.py world-class-preflight . --submissions-dir evidence/world_class/submissions --self` | Assign three independent controlled reviewer identities before claiming human adjudication. |
| `20` | `unblock-access` | Browser/Chrome/IDE/provider client integrator | `native-client-telemetry` | `precheck` | `external-client` | `blocked` | `python3 scripts/yao.py world-class-preflight . --submissions-dir evidence/world_class/submissions --self` | Install a real Browser, Chrome, IDE, or provider client that emits metadata-only events. |
| `20` | `unblock-access` | target client or installer integrator | `native-permission-enforcement` | `precheck` | `native-guard` | `blocked` | `python3 scripts/yao.py world-class-preflight . --submissions-dir evidence/world_class/submissions --self` | Attach a real target-client or external installer runtime guard; metadata fallback is not enough. |
| `20` | `unblock-access` | operator with provider credentials | `provider-holdout` | `precheck` | `provider-api-key` | `blocked` | `python3 scripts/yao.py world-class-preflight . --submissions-dir evidence/world_class/submissions --self` | Set DEEPSEEK_API_KEY in the operator shell; never commit or print the value. |
| `40` | `collect-source` | Browser/Chrome/IDE/provider client integrator | `native-client-telemetry` | `source-check` | `adoption_sample_count` | `blocked` | `python3 scripts/yao.py telemetry-import . --input-jsonl .yao/telemetry_spool/external_events.jsonl --self && python3 scripts/yao.py world-class-preflight . --submissions-dir evidence/world_class/submissions --self` | Telemetry must include adoption outcome evidence. |
| `40` | `collect-source` | Browser/Chrome/IDE/provider client integrator | `native-client-telemetry` | `source-check` | `external_source_events` | `blocked` | `python3 scripts/yao.py telemetry-import . --input-jsonl .yao/telemetry_spool/external_events.jsonl --self && python3 scripts/yao.py world-class-preflight . --submissions-dir evidence/world_class/submissions --self` | Import at least one metadata-only event from a real client. |
| `40` | `collect-source` | target client or installer integrator | `native-permission-enforcement` | `source-check` | `native_enforcement_count` | `blocked` | `python3 scripts/yao.py runtime-permissions . --package-dir dist --self && python3 scripts/yao.py world-class-preflight . --submissions-dir evidence/world_class/submissions --self` | Collect real target-client or external runtime guard proof. |

## Provider Holdout

- status: `blocked`
- ledger: `pending`
- submission: `evidence/world_class/submissions/provider-holdout.json`
- prepare draft: `python3 scripts/yao.py world-class-submission-kit . --evidence-key provider-holdout --output-dir evidence/world_class/submissions --self`
- prepare draft with artifact SHA prefill: `python3 scripts/yao.py world-class-submission-kit . --evidence-key provider-holdout --output-dir evidence/world_class/submissions --prefill-artifacts --self`
- submission refs ready: `1` / `1`
- supporting evidence ready: `7` / `8`

### Prechecks

| Check | Kind | Current | Status | Next action |
| --- | --- | --- | --- | --- |
| Output eval cases | `file` | `present` | `pass` | Keep output holdout cases available before provider execution. |
| Provider runner | `file` | `present` | `pass` | Use the provider runner instead of the local command runner for model-backed evidence. |
| Provider credential | `env` | `not-set` | `missing` | Set DEEPSEEK_API_KEY in the operator shell; never commit or print the value. |

### Source Checks

| Check | Current | Expected | Status | Next action |
| --- | --- | --- | --- | --- |
| Provider calls | `40` | `==40` | `pass` | Complete all 40 fixed DeepSeek calls. |
| Provider model runs | `40` | `==40` | `pass` | Require model identity on all 40 calls. |
| Provider failures | `0` | `==0` | `pass` | Resolve every fixed-matrix failure. |
| Token budget | `40938` | `<=250000` | `pass` | Keep the matrix within the 250000-token ceiling. |

## Human Adjudication

- status: `ready-for-human-review`
- ledger: `pending`
- submission: `evidence/world_class/submissions/human-adjudication.json`
- prepare draft: `python3 scripts/yao.py world-class-submission-kit . --evidence-key human-adjudication --output-dir evidence/world_class/submissions --self`
- prepare draft with artifact SHA prefill: `python3 scripts/yao.py world-class-submission-kit . --evidence-key human-adjudication --output-dir evidence/world_class/submissions --prefill-artifacts --self`
- submission refs ready: `1` / `2`
- supporting evidence ready: `7` / `8`

### Prechecks

| Check | Kind | Current | Status | Next action |
| --- | --- | --- | --- | --- |
| Blind review kit | `file` | `present` | `pass` | Use the provider run's role-neutral pack and finalizer for three controlled reviews. |
| Decision template | `file` | `present` | `pass` | Collect three exact 20-pair reviewer packets with integrity and independent-review attestations. |
| Decision importer | `file` | `present` | `pass` | Keep the fixed reviewer count and promotion thresholds unchanged. |
| Human reviewer | `human` | `external-human-action` | `human-required` | Assign three independent controlled reviewer identities before claiming human adjudication. |

### Source Checks

| Check | Current | Expected | Status | Next action |
| --- | --- | --- | --- | --- |
| Registered reviewers | `3` | `==3` | `pass` | Collect reviewer-a, reviewer-b, and reviewer-c. |
| Blind pairs | `20` | `==20` | `pass` | Complete all 20 blind pairs. |
| Review failures | `0` | `==0` | `pass` | Resolve packet, identity, or adjudication failures. |
| Blind pack binding | `True` | `true` | `pass` | Bind adjudication to the reviewed blind pack SHA256. |

## Native Permission Enforcement

- status: `blocked`
- ledger: `pending`
- submission: `evidence/world_class/submissions/native-permission-enforcement.json`
- prepare draft: `python3 scripts/yao.py world-class-submission-kit . --evidence-key native-permission-enforcement --output-dir evidence/world_class/submissions --self`
- prepare draft with artifact SHA prefill: `python3 scripts/yao.py world-class-submission-kit . --evidence-key native-permission-enforcement --output-dir evidence/world_class/submissions --prefill-artifacts --self`
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
- prepare draft: `python3 scripts/yao.py world-class-submission-kit . --evidence-key native-client-telemetry --output-dir evidence/world_class/submissions --self`
- prepare draft with artifact SHA prefill: `python3 scripts/yao.py world-class-submission-kit . --evidence-key native-client-telemetry --output-dir evidence/world_class/submissions --prefill-artifacts --self`
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
| Adoption sample | `0` | `>0` | `blocked` | Telemetry must include adoption outcome evidence. |
| Raw content blocked | `False` | `false` | `pass` | Telemetry must stay metadata-only. |

## Boundary

- Environment variables are reported only as `set` or `not-set`; values are never printed.
- Human-required and external-required states are operator actions, not accepted evidence.
- The world-class ledger remains the source of truth for `ready_to_claim_world_class`.
