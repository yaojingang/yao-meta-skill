# Route Scorecard

- total cases: `13`
- accuracy: `1.0`
- ambiguous cases: `0`
- no-route accuracy: `1.0`

## Route Metrics

| Route | Expected | Predicted | Precision | Recall | Avg Margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| `yao-meta-skill` | 3 | 3 | 1.0 | 1.0 | 0.701 |
| `team-frontend-review` | 3 | 3 | 1.0 | 1.0 | 0.805 |
| `governed-incident-command` | 3 | 3 | 1.0 | 1.0 | 0.586 |
| `no_route` | 4 | 4 | 1.0 | 1.0 | - |

## Confusion Matrix

| Expected \ Predicted | `yao-meta-skill` | `team-frontend-review` | `governed-incident-command` | `no_route` |
| --- | ---: | ---: | ---: | ---: |
| `yao-meta-skill` | 3 | 0 | 0 | 0 |
| `team-frontend-review` | 0 | 3 | 0 | 0 |
| `governed-incident-command` | 0 | 0 | 3 | 0 |
| `no_route` | 0 | 0 | 0 | 4 |

## Ambiguous Cases

| Family | Expected | Predicted | Margin |
| --- | --- | --- | ---: |
| - | - | - | - |
