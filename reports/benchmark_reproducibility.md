# Benchmark Reproducibility

Generated at: `2026-06-17`
Commit: `223ff6dc510ba5913e2aa018fe8911176093ff94`
Working tree dirty at generation: `false`
Evidence bundle SHA256: `7c06a90ef22863af93b97f65065a2324ccc5eaa38688a1ee8bdf9fd258a3c6ca`

## Summary

- reproducibility ready: `true`
- release lock ready: `true`
- methodology complete: `true`
- required artifacts: `25`
- missing artifacts: `0`
- source contract sha256: `d085dd56b0bd`
- archive sha256: `8789dec9d02f`
- output cases: `5`
- disclosed failure cases: `3`
- reproduction commands: `23`
- provider evidence complete: `false`
- human review complete: `false`
- world-class ready: `false`
- world-class source checks: `7` pass / `13` total; `6` blocked
- public claim ready: `false`
- public claim blockers: `4`
- changed files at generation: `0`

This report proves local benchmark reproducibility only. It keeps external provider and human-review gaps visible instead of counting them as complete. The git commit is generation-time context; the evidence bundle SHA is the durable anchor for the artifacts listed below.

## Public Claim Boundary

- ready: `false`
- scope: public benchmark or world-class readiness claim
- policy: Local reproducibility can pass before public claims; public claims require provider evidence, human adjudication, clean release lock, accepted world-class evidence, and complete source checks.

| Blocker |
| --- |
| provider-backed model holdout evidence is incomplete |
| human blind-review adjudication is incomplete |
| world-class evidence is not accepted yet (4 open gaps, 4 ledger pending) |
| world-class source checks are not all accepted (7/13 pass, 6 blocked) |

## Release Lock

- ready: `true`
- reason: clean generation-time HEAD
- status scope: generation-time status before this report is written

## Evidence Bundle

- algorithm: `sha256(path,label,exists,artifact_sha256)`
- artifacts: `25` / `25`
- sha256: `7c06a90ef22863af93b97f65065a2324ccc5eaa38688a1ee8bdf9fd258a3c6ca`

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
| output_execution | `reports/output_execution_runs.json` | present | `3a3235633d40` |
| blind_review | `reports/output_blind_review_pack.json` | present | `bbe2db8ec277` |
| review_adjudication | `reports/output_review_adjudication.json` | present | `bb8c72a9291e` |
| trigger_scorecard | `reports/route_scorecard.json` | present | `c164e83e36d0` |
| runtime_conformance | `reports/conformance_matrix.json` | present | `97f9ba949c23` |
| trust_report | `reports/security_trust_report.json` | present | `b910b05f5ade` |
| python_compatibility | `reports/python_compatibility.json` | present | `bb1f5efd3372` |
| registry_audit | `reports/registry_audit.json` | present | `d9408d3baf8f` |
| package_verification | `reports/package_verification.json` | present | `1fb37aae43ee` |
| install_simulation | `reports/install_simulation.json` | present | `f0a9469da6a5` |
| skill_os2_audit | `reports/skill_os2_audit.json` | present | `967f94840151` |
| world_class_evidence_plan | `reports/world_class_evidence_plan.json` | present | `af3c3f101ad9` |
| world_class_evidence_ledger | `reports/world_class_evidence_ledger.json` | present | `74deeabfac9f` |
| world_class_evidence_intake | `reports/world_class_evidence_intake.json` | present | `69afd0ff3d49` |
| world_class_evidence_preflight | `reports/world_class_evidence_preflight.json` | present | `b7fd72d7e754` |
| world_class_submission_review | `reports/world_class_submission_review.json` | present | `17def7ba6982` |
| world_class_operator_runbook | `reports/world_class_operator_runbook.json` | present | `00bfa998b24a` |
| world_class_operator_runbook_markdown | `reports/world_class_operator_runbook.md` | present | `337fb764b98a` |
| world_class_operator_runbook_html | `reports/world_class_operator_runbook.html` | present | `ca72c65b437b` |
| world_class_claim_guard | `reports/world_class_claim_guard.json` | present | `c846ffc8565a` |

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

- The git commit and dirty flag are generation-time context; the evidence bundle hash is the durable artifact anchor inside a committed report.
- Local command-runner evidence is reproducible but does not replace provider-backed model holdout evidence.
- Pending blind-review decisions are visible but do not count as human adjudication.
- World-class readiness remains false until external and human evidence gaps close.
