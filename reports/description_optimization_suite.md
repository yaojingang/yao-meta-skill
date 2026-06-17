# Description Optimization Suite

| Target | Winner | Winner Tokens | Holdout FP | Holdout FN | Blind FP | Blind FN | Judge Blind Errors | Adv FP | Adv FN | Adv Gap | Adv Risk | Status |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `yao-meta-skill` | `Current` | 53 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1.0 | healthy | ok |
| `team-frontend-review` | `Current` | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.509 | healthy | ok |
| `governed-incident-command` | `Current` | 37 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0.538 | watch | ok |

## Family Coverage

| Target | Blind Families | Judge Blind Families | Adversarial Families |
| --- | --- | --- | --- |
| `yao-meta-skill` | 6/6 clean; weakest=blind_operationalize | 6/6 clean; weakest=blind_operationalize | 6/6 clean; weakest=adversarial_summary_translation_collision |
| `team-frontend-review` | 6/6 clean; weakest=blind_premerge | 6/6 clean; weakest=blind_premerge | 6/6 clean; weakest=adversarial_quality_gate_review |
| `governed-incident-command` | 6/6 clean; weakest=blind_summary_only | 6/6 clean; weakest=blind_summary_only | 6/6 clean; weakest=adversarial_single_update_collision |
