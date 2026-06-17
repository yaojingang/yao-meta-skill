# Candidate Registry

| Target | Role | Label | Ranking State | Promotion State | Tokens | Dev Errors | Holdout Errors | Reason Tags |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| `yao-meta-skill` | baseline | `Baseline` | reference | reference | 8 | 1 | 0 | - |
| `yao-meta-skill` | current | `Current` | selected_by_dev | kept_current | 53 | 0 | 0 | - |
| `yao-meta-skill` | candidate | `Minimal` | not_selected | blocked | 41 | 2 | 0 | weaker_dev_fit |
| `yao-meta-skill` | candidate | `Guardrail` | not_selected | blocked | 56 | 2 | 0 | weaker_dev_fit, longer_without_gain |
| `yao-meta-skill` | candidate | `Balanced` | not_selected | blocked | 60 | 2 | 0 | weaker_dev_fit, longer_without_gain |
| `yao-meta-skill` | candidate | `Artifact Aware` | not_selected | blocked | 77 | 2 | 0 | weaker_dev_fit, longer_without_gain |
| `yao-meta-skill` | candidate | `Boundary` | not_selected | blocked | 83 | 2 | 0 | weaker_dev_fit, longer_without_gain |
| `team-frontend-review` | baseline | `Baseline` | reference | reference | 52 | 3 | 0 | - |
| `team-frontend-review` | current | `Current` | selected_by_dev | kept_current | 50 | 3 | 0 | - |
| `team-frontend-review` | candidate | `Guardrail` | not_selected | blocked | 62 | 3 | 0 | longer_without_gain |
| `team-frontend-review` | candidate | `Balanced` | not_selected | blocked | 64 | 3 | 0 | longer_without_gain |
| `team-frontend-review` | candidate | `Artifact Aware` | not_selected | blocked | 84 | 3 | 0 | longer_without_gain |
| `team-frontend-review` | candidate | `Boundary` | not_selected | blocked | 90 | 3 | 0 | longer_without_gain |
| `governed-incident-command` | baseline | `Baseline` | reference | reference | 93 | 0 | 1 | - |
| `governed-incident-command` | current | `Current` | selected_by_dev | kept_current | 37 | 0 | 1 | - |
| `governed-incident-command` | candidate | `Balanced` | not_selected | blocked | 54 | 0 | 1 | longer_without_gain |
| `governed-incident-command` | candidate | `Boundary` | not_selected | blocked | 78 | 0 | 1 | longer_without_gain |
| `governed-incident-command` | candidate | `Artifact Aware` | not_selected | blocked | 78 | 0 | 1 | longer_without_gain |
| `governed-incident-command` | candidate | `Guardrail` | not_selected | blocked | 51 | 1 | 1 | weaker_dev_fit, longer_without_gain |
