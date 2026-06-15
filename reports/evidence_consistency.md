# Evidence Consistency

Generated at: `2026-06-16`

## Summary

- decision: `consistent`
- checks: `33`
- pass: `33`
- warn: `0`
- fail: `0`

This gate compares generated evidence reports against each other. It does not create provider, human, native-client, or permission-enforcement evidence; it only catches drift between reports that already exist.

## Checks

| Check | Status | Detail | Paths |
| --- | --- | --- | --- |
| Required report artifacts are readable | `pass` | The consistency gate can only be trusted when every source JSON report parses and every source Markdown report is readable. | `reports/benchmark_reproducibility.json`, `reports/skill-overview.json`, `reports/skill-interpretation.json`, `reports/adoption_drift_report.json`, `reports/world_class_evidence_ledger.json`, `reports/world_class_evidence_plan.json`, `reports/world_class_evidence_intake.json`, `reports/world_class_evidence_preflight.json`, `reports/world_class_submission_review.json`, `reports/world_class_operator_runbook.json`, `reports/skill_os2_coverage.json`, `reports/review-studio.json`, `reports/package_verification.json`, `reports/install_simulation.json`, `reports/security_trust_report.json`, `reports/context_budget.json`, `reports/world_class_claim_guard.json`, `reports/skill-os-2-review.md` |
| Release evidence flow covers first-class reports | `pass` | Release refresh and clean-lock instructions must regenerate every first-class report before evidence consistency can be trusted. | `AGENTS.md`, `reports/output_execution_runs.json`, `reports/install_simulation.json`, `reports/security_trust_report.json`, `reports/registry_audit.json`, `reports/package_verification.json`, `reports/upgrade_check.json`, `reports/adoption_drift_report.json`, `reports/architecture_maintainability.json`, `reports/python_compatibility.json`, `reports/runtime_permission_probes.json`, `reports/review_waivers.json`, `reports/review_annotations.json`, `reports/skill_atlas.json`, `reports/skill_os2_audit.json`, `reports/skill_os2_coverage.json`, `reports/context_budget.json`, `reports/context_budget_summary.json`, `reports/benchmark_reproducibility.json`, `reports/skill-overview.json`, `reports/skill-interpretation.json`, `reports/review-viewer.json`, `reports/world_class_evidence_preflight.json`, `reports/review-studio.json`, `reports/evidence_consistency.json` |
| Review Studio mirrors context budget governance | `pass` | Review Studio must not keep stale context warnings after context reports prove large deferred resources are governed. | `reports/context_budget.json`, `reports/review-studio.json` |
| Benchmark release lock matches git dirty state | `pass` | The benchmark release lock must reflect the generation-time git dirty flag. | `reports/benchmark_reproducibility.json` |
| overview embeds the benchmark commit | `pass` | Human-facing reports must point to the same benchmark release-lock commit. | `reports/benchmark_reproducibility.json`, `reports/skill-overview.json` |
| overview embeds benchmark summary fields | `pass` | Selected summary fields must match exactly across generated reports. | `reports/benchmark_reproducibility.json`, `reports/skill-overview.json` |
| overview embeds adoption drift summary fields | `pass` | Selected summary fields must match exactly across generated reports. | `reports/adoption_drift_report.json`, `reports/skill-overview.json` |
| overview embeds world-class ledger summary fields | `pass` | Selected summary fields must match exactly across generated reports. | `reports/world_class_evidence_ledger.json`, `reports/skill-overview.json` |
| overview derives readiness from the ledger | `pass` | Readiness summaries must be derived from the evidence ledger, not hand-maintained copy. | `reports/world_class_evidence_ledger.json`, `reports/skill-overview.json` |
| interpretation embeds the benchmark commit | `pass` | Human-facing reports must point to the same benchmark release-lock commit. | `reports/benchmark_reproducibility.json`, `reports/skill-interpretation.json` |
| interpretation embeds benchmark summary fields | `pass` | Selected summary fields must match exactly across generated reports. | `reports/benchmark_reproducibility.json`, `reports/skill-interpretation.json` |
| interpretation embeds adoption drift summary fields | `pass` | Selected summary fields must match exactly across generated reports. | `reports/adoption_drift_report.json`, `reports/skill-interpretation.json` |
| interpretation embeds world-class ledger summary fields | `pass` | Selected summary fields must match exactly across generated reports. | `reports/world_class_evidence_ledger.json`, `reports/skill-interpretation.json` |
| interpretation derives readiness from the ledger | `pass` | Readiness summaries must be derived from the evidence ledger, not hand-maintained copy. | `reports/world_class_evidence_ledger.json`, `reports/skill-interpretation.json` |
| Overview and interpretation share scorecard | `pass` | The first-class interpretation report must stay in lockstep with the canonical overview model. | `reports/skill-overview.json`, `reports/skill-interpretation.json` |
| Overview and interpretation share capability_profile | `pass` | The first-class interpretation report must stay in lockstep with the canonical overview model. | `reports/skill-overview.json`, `reports/skill-interpretation.json` |
| Overview and interpretation share principle_model | `pass` | The first-class interpretation report must stay in lockstep with the canonical overview model. | `reports/skill-overview.json`, `reports/skill-interpretation.json` |
| Overview and interpretation share contract_boundary | `pass` | The first-class interpretation report must stay in lockstep with the canonical overview model. | `reports/skill-overview.json`, `reports/skill-interpretation.json` |
| Overview and interpretation share quality_review | `pass` | The first-class interpretation report must stay in lockstep with the canonical overview model. | `reports/skill-overview.json`, `reports/skill-interpretation.json` |
| Overview and interpretation share risk_governance | `pass` | The first-class interpretation report must stay in lockstep with the canonical overview model. | `reports/skill-overview.json`, `reports/skill-interpretation.json` |
| Overview and interpretation share world_class_readiness | `pass` | The first-class interpretation report must stay in lockstep with the canonical overview model. | `reports/skill-overview.json`, `reports/skill-interpretation.json` |
| Overview and interpretation share package_assets | `pass` | The first-class interpretation report must stay in lockstep with the canonical overview model. | `reports/skill-overview.json`, `reports/skill-interpretation.json` |
| Overview and interpretation share iteration_roadmap | `pass` | The first-class interpretation report must stay in lockstep with the canonical overview model. | `reports/skill-overview.json`, `reports/skill-interpretation.json` |
| overview has a stable HTML contract | `pass` | Report output paths and language defaults are part of the user-facing contract. | `reports/skill-overview.json`, `reports/skill-overview.html` |
| interpretation has a stable HTML contract | `pass` | Report output paths and language defaults are part of the user-facing contract. | `reports/skill-interpretation.json`, `reports/skill-interpretation.html` |
| Coverage report mirrors world-class evidence boundary | `pass` | Blueprint coverage can be locally complete while public world-class evidence remains pending. | `reports/world_class_evidence_ledger.json`, `reports/skill_os2_coverage.json` |
| Benchmark report mirrors world-class evidence boundary | `pass` | Benchmark reproducibility must not overstate public claim readiness. | `reports/world_class_evidence_ledger.json`, `reports/benchmark_reproducibility.json` |
| Preflight mirrors ledger without accepting evidence | `pass` | Collection preflight may help operators gather evidence, but it must not print secrets or change world-class readiness. | `reports/world_class_evidence_ledger.json`, `reports/world_class_evidence_preflight.json` |
| Preflight exposes a safe submission-kit handoff | `pass` | Preflight must give operators the exact draft, intake, review, ledger, and claim-guard commands without letting drafts or submissions count as accepted evidence. | `reports/world_class_evidence_preflight.json` |
| Review Studio does not overclaim pending world-class evidence | `pass` | When world-class evidence is pending, Review Studio must stay in a review or warning posture. | `reports/world_class_evidence_ledger.json`, `reports/review-studio.json` |
| Claim guard covers package and runtime claim surfaces | `pass` | The overclaim guard must scan package manifests, adapter metadata, security policy, and ledger surfaces before public readiness can be trusted. | `reports/world_class_claim_guard.json`, `manifest.json`, `agents/interface.yaml`, `dist/manifest.json`, `dist/targets/openai/adapter.json`, `evidence/world_class/README.md`, `security/permission_policy.json`, `reports/world_class_evidence_ledger.json` |
| World-class evidence workflows cover every pending ledger entry | `pass` | Every pending world-class evidence key must have matching plan, intake, submission review, operator runbook, and Review Studio actions without counting planned work as completion. | `reports/world_class_evidence_ledger.json`, `reports/world_class_evidence_plan.json`, `reports/world_class_evidence_intake.json`, `reports/world_class_submission_review.json`, `reports/world_class_operator_runbook.json`, `reports/review-studio.json` |
| Skill OS 2.0 review summary mirrors current evidence | `pass` | Manual 2.0 review summaries must not drift from generated gate, package, trust, context, benchmark, or CI evidence. | `reports/skill-os-2-review.md`, `reports/review-studio.json`, `reports/package_verification.json`, `reports/install_simulation.json`, `reports/security_trust_report.json`, `reports/context_budget.json`, `reports/benchmark_reproducibility.json`, `scripts/ci_test.py` |
