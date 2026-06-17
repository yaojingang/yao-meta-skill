# Iteration Bundle: governed-incident-command

- decision: `keep_current`
- winner label: `Current`
- winner changed: `False`
- next action: Keep the current description and open a new candidate only when fresh route evidence appears.

## Cause Tags

- `no_candidate_outperformed_current`
- `current_holdout_gap_present`
- `current_holdout_risk`
- `adversarial_watch_risk`

## Gate Status

| Gate | Pass |
| --- | --- |
| `visible_holdout_non_regression` | True |
| `blind_holdout_non_regression` | True |
| `judge_blind_non_regression` | True |
| `judge_blind_agreement` | True |
| `adversarial_non_regression` | True |
| `adversarial_risk_ok` | True |
| `route_confusion_clean` | True |
| `family_stability` | True |

## Candidate Registry

| Role | Label | Ranking State | Promotion State | Tokens | Dev Errors | Holdout Errors |
| --- | --- | --- | --- | ---: | ---: | ---: |
| baseline | `Baseline` | reference | reference | 93 | 0 | 1 |
| current | `Current` | selected_by_dev | kept_current | 37 | 0 | 1 |
| candidate | `Balanced` | not_selected | blocked | 54 | 0 | 1 |
| candidate | `Boundary` | not_selected | blocked | 78 | 0 | 1 |
| candidate | `Artifact Aware` | not_selected | blocked | 78 | 0 | 1 |
| candidate | `Guardrail` | not_selected | blocked | 51 | 1 | 1 |

## Human Review Stub

- target: governed-incident-command
- current description: Build governed incident command packets. Use when asked to standardize incident review, run severity assessment, or assemble incident communication.
- candidate description: Build governed incident command packets. Use when asked to standardize incident review, run severity assessment, or assemble incident communication.
- review focus: no_candidate_outperformed_current, current_holdout_gap_present, current_holdout_risk

## Artifact Paths

- skill: `examples/governed-incident-command/generated-skill/SKILL.md`
- optimization_report: `examples/governed-incident-command/optimization/reports/description_optimization.json`
- promotion_decisions: `reports/promotion_decisions.json`
- candidate_registry: `reports/candidate_registry.json`
- regression_cause_taxonomy: `references/regression-cause-taxonomy.md`
- human_review_template: `references/human-review-template.md`
