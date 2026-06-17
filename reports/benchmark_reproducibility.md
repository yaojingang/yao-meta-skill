# Benchmark Reproducibility

Generated at: `2026-06-17`
Commit: `e79050ed12d057811d7d13ab7d8bcc5a06af76d4`
Working tree dirty at generation: `true`
Source tree dirty at generation: `false`
Generated evidence dirty at generation: `true`
Evidence bundle SHA256: `55a6c33c12e14d6507d4a5d4d4cf1268db35fb323d523e8b23ce9c73aedf8db0`

## Summary

- reproducibility ready: `true`
- release lock ready: `true`
- methodology complete: `true`
- required artifacts: `25`
- missing artifacts: `0`
- source contract sha256: `5a99ef3133b0`
- archive sha256: `7db44f059844`
- output cases: `5`
- disclosed failure cases: `3`
- reproduction commands: `23`
- provider evidence complete: `true`
- human review complete: `false`
- world-class ready: `false`
- world-class source checks: `11` pass / `19` total; `8` blocked
- beta test ready: `true`
- beta test blockers: `0`
- beta deferred evidence: `4`
- public claim ready: `false`
- public claim blockers: `3`
- changed files at generation: `29`
- source changed files at generation: `0`
- generated changed files at generation: `29`

This report proves local benchmark reproducibility only. It keeps external provider and human-review gaps visible instead of counting them as complete. The git commit and dirty samples are generation-time context; the evidence bundle SHA is the durable anchor for the artifacts listed below.

## Beta Test Boundary

- ready: `true`
- scope: beta/public test release without superiority, fully-reviewed, or world-class claims
- policy: Human blind-review, native permission enforcement, real client telemetry, and ledger acceptance may be deferred for beta/public testing, but public claims must remain blocked until those evidence entries are accepted.
- required wording: Use beta, public test, or technical preview wording; do not claim world-class readiness, fully reviewed quality, or proven superiority over baseline.

| Blocker |
| --- |
| none |

| Deferred evidence | Reason |
| --- | --- |
| `provider-holdout` | Provider-backed source evidence exists, but formal ledger submission and reviewer acceptance are still pending before public claims. |
| `human-adjudication` | Human adjudication evidence is still pending; deferred for beta/public testing and still required before superiority, fully-reviewed, or world-class claims. |
| `native-permission-enforcement` | Native enforcement proof is still pending; deferred for beta/public testing and still required before world-class claims. |
| `native-client-telemetry` | Real client telemetry is still pending; deferred for beta/public testing and still required before world-class claims. |

## Public Claim Boundary

- ready: `false`
- scope: public benchmark or world-class readiness claim
- policy: Local reproducibility can pass before public claims; public claims require provider evidence, human adjudication, clean release lock, accepted world-class evidence, and complete source checks.

| Blocker |
| --- |
| human blind-review adjudication is incomplete |
| world-class evidence is not accepted yet (3 open gaps, 4 ledger pending) |
| world-class source checks are not all accepted (11/19 pass, 8 blocked) |

## Release Lock

- ready: `true`
- reason: only generated evidence artifacts were dirty at generation time
- status scope: generation-time status before this report is written

## Evidence Bundle

- algorithm: `sha256(path,label,exists,artifact_sha256)`
- artifacts: `25` / `25`
- sha256: `55a6c33c12e14d6507d4a5d4d4cf1268db35fb323d523e8b23ce9c73aedf8db0`

## Methodology Sections

| Section | Status |
| --- | --- |
| `## Benchmark Types` | present |
| `## Sample Sources` | present |
| `## Evaluation Dimensions` | present |
| `## Weighting Rule` | present |
| `## Failure Disclosure` | present |
| `## Reproduction` | present |

## Required Artifacts

| Label | Path | Status | SHA256 |
| --- | --- | --- | --- |
| methodology | `reports/benchmark_methodology.md` | present | `57025e0123ce` |
| failure_disclosure | `evals/failure-cases.md` | present | `28833c0d4a21` |
| output_cases | `evals/output/cases.jsonl` | present | `a6ae96857116` |
| output_schema | `evals/output/schema.json` | present | `8ee340c95064` |
| output_scorecard | `reports/output_quality_scorecard.json` | present | `0806258a8e08` |
| output_execution | `reports/output_execution_runs.json` | present | `4df66b63d2e7` |
| blind_review | `reports/output_blind_review_pack.json` | present | `bbe2db8ec277` |
| review_adjudication | `reports/output_review_adjudication.json` | present | `91fd88dd9b0f` |
| trigger_scorecard | `reports/route_scorecard.json` | present | `a649547a7d3d` |
| runtime_conformance | `reports/conformance_matrix.json` | present | `97f9ba949c23` |
| trust_report | `reports/security_trust_report.json` | present | `bbff1f1bee0c` |
| python_compatibility | `reports/python_compatibility.json` | present | `d31dc03c74f1` |
| registry_audit | `reports/registry_audit.json` | present | `1feb80c7cdc8` |
| package_verification | `reports/package_verification.json` | present | `7aa6c25e8154` |
| install_simulation | `reports/install_simulation.json` | present | `c1f1122264b8` |
| skill_os2_audit | `reports/skill_os2_audit.json` | present | `6362e79a8cfd` |
| world_class_evidence_plan | `reports/world_class_evidence_plan.json` | present | `8eb5e1fbaa75` |
| world_class_evidence_ledger | `reports/world_class_evidence_ledger.json` | present | `6038b6cd6e06` |
| world_class_evidence_intake | `reports/world_class_evidence_intake.json` | present | `aa262da0ecee` |
| world_class_evidence_preflight | `reports/world_class_evidence_preflight.json` | present | `95cb56581224` |
| world_class_submission_review | `reports/world_class_submission_review.json` | present | `12fbb8492629` |
| world_class_operator_runbook | `reports/world_class_operator_runbook.json` | present | `f321dc118ee9` |
| world_class_operator_runbook_markdown | `reports/world_class_operator_runbook.md` | present | `858ee11bbacb` |
| world_class_operator_runbook_html | `reports/world_class_operator_runbook.html` | present | `31b24658c59e` |
| world_class_claim_guard | `reports/world_class_claim_guard.json` | present | `abe7f7d60c00` |

## Reproduction Commands

- `git rev-parse HEAD`
  - evidence: `git commit hash`
- `make eval-suite`
  - evidence: `reports/eval_suite.json`
- `python3 scripts/yao.py output-eval`
  - evidence: `reports/output_quality_scorecard.json`
- `python3 scripts/yao.py output-exec --runner-command '["python3","scripts/local_output_eval_runner.py"]'`
  - evidence: `reports/output_execution_runs.json`
- `python3 scripts/yao.py output-review`
  - evidence: `reports/output_review_adjudication.json`
- `python3 scripts/yao.py skill-ir . --output-json skill-ir/examples/yao-meta-skill.json`
  - evidence: `skill-ir/examples/yao-meta-skill.json`
- `python3 scripts/yao.py conformance .`
  - evidence: `reports/conformance_matrix.json`
- `python3 scripts/yao.py trust .`
  - evidence: `reports/security_trust_report.json`
- `python3 scripts/yao.py python-compat .`
  - evidence: `reports/python_compatibility.json`
- `python3 scripts/yao.py package . --platform openai --platform claude --platform generic --platform vscode --expectations evals/packaging_expectations.json --output-dir dist --zip`
  - evidence: `dist/yao-meta-skill.zip`
- `python3 scripts/yao.py package-verify . --package-dir dist --require-zip`
  - evidence: `reports/package_verification.json`
- `python3 scripts/yao.py install-simulate . --package-dir dist`
  - evidence: `reports/install_simulation.json`
- `python3 scripts/yao.py registry-audit .`
  - evidence: `reports/registry_audit.json`
- `python3 scripts/yao.py skill-os2-audit .`
  - evidence: `reports/skill_os2_audit.json`
- `python3 scripts/yao.py world-class-evidence .`
  - evidence: `reports/world_class_evidence_plan.json`
- `python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions`
  - evidence: `reports/world_class_evidence_ledger.json`
- `python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions`
  - evidence: `reports/world_class_evidence_intake.json`
- `python3 scripts/yao.py world-class-preflight . --submissions-dir evidence/world_class/submissions`
  - evidence: `reports/world_class_evidence_preflight.json`
- `python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions`
  - evidence: `reports/world_class_submission_review.json`
- `python3 scripts/yao.py world-class-runbook . --submissions-dir evidence/world_class/submissions`
  - evidence: `reports/world_class_operator_runbook.json`
- `python3 scripts/yao.py world-class-claim-guard .`
  - evidence: `reports/world_class_claim_guard.json`
- `python3 scripts/yao.py evidence-consistency .`
  - evidence: `reports/evidence_consistency.json`
- `make ci-test`
  - evidence: `CI target output`

## Failure Disclosure

- path: `evals/failure-cases.md`
- disclosed cases: `3`
- policy: Keep representative failures visible and tied to regression checks.

## Limits

- The git commit and dirty flags are generation-time context; release lock is blocked by source changes, while generated evidence artifacts are tracked separately.
- Provider-backed model holdout source evidence is complete, but ledger acceptance still requires a valid independently reviewed submission packet.
- Pending blind-review decisions are visible but do not count as human adjudication.
- World-class readiness remains false until external and human evidence gaps close.
- Beta/public testing may proceed without human blind-review only when wording avoids superiority, fully-reviewed, or world-class claims.
