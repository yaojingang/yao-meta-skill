# Governed Incident Description Optimization

Winner: `Current`

- current tokens: `37`
- winner tokens: `37`
- baseline tokens: `93`

## Winner

Build governed incident command packets. Use when asked to standardize incident review, run severity assessment, or assemble incident communication.

## Candidate Ranking

| Candidate | Tokens | Dev FP | Dev FN | Dev Near | Holdout FP | Holdout FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `Current` | 37 | 0 | 0 | 1.0 | 0 | 1 |
| `Balanced` | 54 | 0 | 0 | 1.0 | 0 | 1 |
| `Boundary` | 78 | 0 | 0 | 1.0 | 0 | 1 |
| `Artifact Aware` | 78 | 0 | 0 | 1.0 | 0 | 1 |
| `Guardrail` | 51 | 0 | 1 | 1.0 | 0 | 1 |

## Acceptance Gates

| Gate | Winner FP | Winner FN | Current FP | Current FN | Baseline FP | Baseline FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Holdout | 0 | 1 | 0 | 1 | 0 | 1 |
| Blind Holdout | 0 | 0 | 0 | 0 | 0 | 0 |
| Judge Blind Holdout | 0 | 0 | 0 | 0 | 0 | 0 |
| Adversarial Holdout | 0 | 0 | 0 | 0 | 0 | 0 |

## Calibration

| Gate | Winner Gap | Winner Risk | Winner Boundary Rate | Current Gap | Baseline Gap |
| --- | ---: | --- | ---: | ---: | ---: |
| Holdout | 0.023 | overlap | 0.0 | 0.023 | 0.101 |
| Blind Holdout | 0.417 | healthy | 0.0 | 0.417 | 0.374 |
| Adversarial Holdout | 0.538 | watch | 0.167 | 0.538 | 0.467 |

## Judge Blind Summary

| Gate | Winner Agreement | Winner Mean Confidence | Current Agreement | Baseline Agreement |
| --- | ---: | ---: | ---: | ---: |
| Judge Blind Holdout | 1.0 | 0.677 | 1.0 | 1.0 |

## Family Health

| Gate | Winner Clean Families | Winner Weakest Family | Current Clean Families | Baseline Clean Families |
| --- | --- | --- | --- | --- |
| Holdout | 5/6 | packet_assembly (1 errors) | 5/6 | 5/6 |
| Blind Holdout | 6/6 | blind_summary_only (0 errors) | 6/6 | 6/6 |
| Judge Blind Holdout | 6/6 | blind_summary_only (0 errors) | 6/6 | 6/6 |
| Adversarial Holdout | 6/6 | adversarial_single_update_collision (0 errors) | 6/6 | 6/6 |

## Selection Logic

Ordered by:
- fewest false positives
- fewest false negatives
- highest near-neighbor pass rate
- highest negative pass rate
- highest precision
- highest recall
- shortest description
