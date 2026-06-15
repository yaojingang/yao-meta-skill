# Evidence Consistency

Generated at: `2026-06-15`

## Summary

- decision: `consistent`
- checks: `26`
- pass: `26`
- warn: `0`
- fail: `0`

This gate compares generated evidence reports against each other. It does not create provider, human, native-client, or permission-enforcement evidence; it only catches drift between reports that already exist.

## Checks

| Check | Status | Detail | Paths |
| --- | --- | --- | --- |
| Required report artifacts are readable | `pass` | The consistency gate can only be trusted when every source report is present and valid JSON. | `reports/benchmark_reproducibility.json`, `reports/skill-overview.json`, `reports/skill-interpretation.json`, `reports/adoption_drift_report.json`, `reports/world_class_evidence_ledger.json`, `reports/skill_os2_coverage.json`, `reports/review-studio.json` |
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
| Review Studio does not overclaim pending world-class evidence | `pass` | When world-class evidence is pending, Review Studio must stay in a review or warning posture. | `reports/world_class_evidence_ledger.json`, `reports/review-studio.json` |
