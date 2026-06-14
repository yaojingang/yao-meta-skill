# Benchmark Reproducibility

Generated at: `2026-06-14`
Commit: `ef0089170c1f57ab337e452a8948ceb3ae625ca1`
Working tree dirty at generation: `false`
Evidence bundle SHA256: `f81d4dd5985eff30c70e3b4720c44a9d5b4984318463637b98645b526bfcbd6b`

## Summary

- reproducibility ready: `true`
- release lock ready: `true`
- methodology complete: `true`
- required artifacts: `24`
- missing artifacts: `0`
- source contract sha256: `d3341950a7fb`
- archive sha256: `c2028f0a12c8`
- output cases: `5`
- disclosed failure cases: `3`
- reproduction commands: `21`
- provider evidence complete: `false`
- human review complete: `false`
- world-class ready: `false`
- public claim ready: `false`
- public claim blockers: `3`
- changed files at generation: `0`

This report proves local benchmark reproducibility only. It keeps external provider and human-review gaps visible instead of counting them as complete. The git commit is generation-time context; the evidence bundle SHA is the durable anchor for the artifacts listed below.

## Public Claim Boundary

- ready: `false`
- scope: public benchmark or world-class readiness claim
- policy: Local reproducibility can pass before public claims; public claims require provider evidence, human adjudication, clean release lock, and accepted world-class evidence.

| Blocker |
| --- |
| provider-backed model holdout evidence is incomplete |
| human blind-review adjudication is incomplete |
| world-class evidence is not accepted yet (4 open gaps, 4 ledger pending) |

## Release Lock

- ready: `true`
- reason: clean generation-time HEAD
- status scope: generation-time status before this report is written

## Evidence Bundle

- algorithm: `sha256(path,label,exists,artifact_sha256)`
- artifacts: `24` / `24`
- sha256: `f81d4dd5985eff30c70e3b4720c44a9d5b4984318463637b98645b526bfcbd6b`

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
| output_execution | `reports/output_execution_runs.json` | present | `46a65f5db667` |
| blind_review | `reports/output_blind_review_pack.json` | present | `bbe2db8ec277` |
| review_adjudication | `reports/output_review_adjudication.json` | present | `240485a721af` |
| trigger_scorecard | `reports/route_scorecard.json` | present | `c164e83e36d0` |
| runtime_conformance | `reports/conformance_matrix.json` | present | `8251329e663d` |
| trust_report | `reports/security_trust_report.json` | present | `d827b410e989` |
| python_compatibility | `reports/python_compatibility.json` | present | `ae16e17266e4` |
| registry_audit | `reports/registry_audit.json` | present | `eba3fd128cb5` |
| package_verification | `reports/package_verification.json` | present | `f7382b0152d9` |
| install_simulation | `reports/install_simulation.json` | present | `8f987e805c92` |
| skill_os2_audit | `reports/skill_os2_audit.json` | present | `6bb2dcb0e1e5` |
| world_class_evidence_plan | `reports/world_class_evidence_plan.json` | present | `164803bb1cea` |
| world_class_evidence_ledger | `reports/world_class_evidence_ledger.json` | present | `0bff14542475` |
| world_class_evidence_intake | `reports/world_class_evidence_intake.json` | present | `72af5fa06f5b` |
| world_class_submission_review | `reports/world_class_submission_review.json` | present | `4f03edb2ef28` |
| world_class_operator_runbook | `reports/world_class_operator_runbook.json` | present | `43492b169ade` |
| world_class_operator_runbook_markdown | `reports/world_class_operator_runbook.md` | present | `cb05eec07f1e` |
| world_class_operator_runbook_html | `reports/world_class_operator_runbook.html` | present | `68b45d5f6f88` |
| world_class_claim_guard | `reports/world_class_claim_guard.json` | present | `250d616b028c` |

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
- `python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions`
  - evidence: `reports/world_class_submission_review.json`
- `python3 scripts/yao.py world-class-runbook . --submissions-dir evidence/world_class/submissions`
  - evidence: `reports/world_class_operator_runbook.json`
- `python3 scripts/yao.py world-class-claim-guard .`
  - evidence: `reports/world_class_claim_guard.json`
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
