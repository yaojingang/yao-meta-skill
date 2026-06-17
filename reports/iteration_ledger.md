# Iteration Ledger

## System Milestones

| Date | Label | Trigger Cases | FP | FN | Route Accuracy | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 2026-03-31 | Context First Pack | 66 | 0 | 0 | - | added tiered context budgets; added unused resource detection and quality density; added root and example context budget reports |
| 2026-03-31 | Family Suite Expansion | 66 | 0 | 0 | - | expanded the family-based trigger suite; published the homepage eval dashboard |
| 2026-03-31 | Governance Quality Gates | 66 | 0 | 0 | - | added runnable governance checks; added resource-boundary checks; wired both into make test |
| 2026-03-31 | Governed Assets And History | 66 | 0 | 0 | - | added governance maturity scoring; added regression history snapshots and renderer; added governed incident-command example |
| 2026-04-01 | Route Scorecard Foundation | 13 | 0 | 0 | 1.0 | added route confusion matrix for sibling skills and no-route cases; published route scorecard and iteration ledger foundation |

## Description Optimization Milestones

| Date | Label | Target | Blind Errors | Judge Blind Errors | Judge Agreement | Adversarial Errors | Adversarial Gap | Adversarial Risk | Drift Note |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 2026-03-31 | Description Optimization Suite | `yao-meta-skill` | - | - | - | - | - | - | initial description optimization suite without blind holdout |
| 2026-03-31 | Description Optimization Suite | `team-frontend-review` | - | - | - | - | - | - | compressed example description and stored first holdout report |
| 2026-03-31 | Description Optimization Suite | `governed-incident-command` | - | - | - | - | - | - | compressed governed description and reduced visible holdout misses |
| 2026-04-01 | Adversarial Calibration And Family Drift | `yao-meta-skill` | 0 | - | - | 0 | 0.834 | healthy | tokens stable; blind stable at 0; adversarial gate added with 0 errors; holdout stable at 0; adversarial calibration +0.834; risk n/a -> healthy |
| 2026-04-01 | Adversarial Calibration And Family Drift | `team-frontend-review` | 0 | - | - | 0 | 0.509 | healthy | tokens stable; blind stable at 0; adversarial gate added with 0 errors; holdout stable at 0; adversarial calibration +0.509; risk n/a -> healthy |
| 2026-04-01 | Adversarial Calibration And Family Drift | `governed-incident-command` | 0 | - | - | 0 | 0.598 | healthy | tokens stable; blind stable at 0; adversarial gate added with 0 errors; holdout stable at 1; adversarial calibration +0.598; risk n/a -> healthy |
| 2026-04-01 | Blind Holdout And Drift History | `yao-meta-skill` | 0 | - | - | - | - | - | tokens stable; blind gate added with 0 errors; holdout stable at 0 |
| 2026-04-01 | Blind Holdout And Drift History | `team-frontend-review` | 0 | - | - | - | - | - | tokens stable; blind gate added with 0 errors; holdout stable at 0 |
| 2026-04-01 | Blind Holdout And Drift History | `governed-incident-command` | 0 | - | - | - | - | - | tokens stable; blind gate added with 0 errors; holdout stable at 1 |
| 2026-04-01 | Judge-Backed Blind Eval | `yao-meta-skill` | 0 | 0 | 1.0 | 0 | 0.834 | healthy | tokens stable; blind stable at 0; adversarial gate added with 0 errors; holdout stable at 0; adversarial calibration +0.834; risk n/a -> healthy |
| 2026-04-01 | Judge-Backed Blind Eval | `team-frontend-review` | 0 | 0 | 1.0 | 0 | 0.509 | healthy | tokens stable; blind stable at 0; adversarial gate added with 0 errors; holdout stable at 0; adversarial calibration +0.509; risk n/a -> healthy |
| 2026-04-01 | Judge-Backed Blind Eval | `governed-incident-command` | 0 | 0 | 1.0 | 0 | 0.598 | healthy | tokens stable; blind stable at 0; adversarial gate added with 0 errors; holdout stable at 1; adversarial calibration +0.598; risk n/a -> healthy |

## Current Promotion Decisions

| Target | Decision | Winner | Causes | Next Action |
| --- | --- | --- | --- | --- |
| `yao-meta-skill` | `keep_current` | `Current` | no_candidate_outperformed_current | Keep the current description and open a new candidate only when fresh route evidence appears. |
| `team-frontend-review` | `keep_current` | `Current` | no_candidate_outperformed_current, current_holdout_risk | Keep the current description and open a new candidate only when fresh route evidence appears. |
| `governed-incident-command` | `keep_current` | `Current` | no_candidate_outperformed_current, current_holdout_gap_present, current_holdout_risk, adversarial_watch_risk | Keep the current description and open a new candidate only when fresh route evidence appears. |

## Current Route Scorecard

- total cases: `13`
- accuracy: `1.0`
- ambiguous cases: `0`

| Route | Precision | Recall | Avg Margin |
| --- | ---: | ---: | ---: |
| `yao-meta-skill` | 1.0 | 1.0 | 0.701 |
| `team-frontend-review` | 1.0 | 1.0 | 0.805 |
| `governed-incident-command` | 1.0 | 1.0 | 0.586 |
| `no_route` | 1.0 | 1.0 | - |
