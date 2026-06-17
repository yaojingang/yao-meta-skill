# Iteration Bundle: yao-meta-skill

- decision: `keep_current`
- winner label: `Current`
- winner changed: `False`
- next action: Keep the current description and open a new candidate only when fresh route evidence appears.

## Cause Tags

- `no_candidate_outperformed_current`

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
| baseline | `Baseline` | reference | reference | 8 | 1 | 0 |
| current | `Current` | selected_by_dev | kept_current | 53 | 0 | 0 |
| candidate | `Minimal` | not_selected | blocked | 41 | 2 | 0 |
| candidate | `Guardrail` | not_selected | blocked | 56 | 2 | 0 |
| candidate | `Balanced` | not_selected | blocked | 60 | 2 | 0 |
| candidate | `Artifact Aware` | not_selected | blocked | 77 | 2 | 0 |
| candidate | `Boundary` | not_selected | blocked | 83 | 2 | 0 |

## Human Review Stub

- target: yao-meta-skill
- current description: Create, refactor, evaluate, and package agent skills from workflows, prompts, transcripts, docs, or notes. Use for skill creation, reusable workflow packaging, skill improvement, evals, and team-ready distribution.
- candidate description: Create, refactor, evaluate, and package agent skills from workflows, prompts, transcripts, docs, or notes. Use for skill creation, reusable workflow packaging, skill improvement, evals, and team-ready distribution.
- review focus: no_candidate_outperformed_current

## Artifact Paths

- skill: `SKILL.md`
- optimization_report: `reports/description_optimization.json`
- promotion_decisions: `reports/promotion_decisions.json`
- candidate_registry: `reports/candidate_registry.json`
- regression_cause_taxonomy: `references/regression-cause-taxonomy.md`
- human_review_template: `references/human-review-template.md`
