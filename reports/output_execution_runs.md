# Output Execution Runs

This report records how output-eval variants were produced and whether timing or token evidence is observed or estimated.

- Cases: `5`
- Variant runs: `10`
- Command executed: `10`
- Model executed: `0`
- Recorded fixtures: `0`
- Timing observed: `10`
- Token observed: `0`
- Token estimated: `10`
- Delta: `100.0`
- Gate pass: `True`

No model-executed runs are recorded yet.

Use `python3 scripts/yao.py output-exec --provider-runner openai` or `--runner-command` with a reviewed provider-backed runner to replace recorded fixtures with real model output evidence.

Command runner evidence is present. This proves the eval harness executed an external command, but it is not provider-backed model evidence unless the runner reports model metadata.

## Runs

| Case | Variant | Mode | Model | Duration ms | Tokens | Score | Status |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| skill-package-contract | baseline | command | local-output-eval-runner | 26.28 | 33 | 0.0 | pass |
| skill-package-contract | with_skill | command | local-output-eval-runner | 26.19 | 73 | 100.0 | pass |
| output-eval-expectation | baseline | command | local-output-eval-runner | 26.08 | 36 | 0.0 | pass |
| output-eval-expectation | with_skill | command | local-output-eval-runner | 26.33 | 80 | 100.0 | pass |
| ir-before-packaging | baseline | command | local-output-eval-runner | 25.89 | 33 | 0.0 | pass |
| ir-before-packaging | with_skill | command | local-output-eval-runner | 26.56 | 80 | 100.0 | pass |
| near-neighbor-boundary | baseline | command | local-output-eval-runner | 26.12 | 36 | 0.0 | pass |
| near-neighbor-boundary | with_skill | command | local-output-eval-runner | 26.4 | 65 | 100.0 | pass |
| file-backed-governed-package | baseline | command | local-output-eval-runner | 26.2 | 37 | 0.0 | pass |
| file-backed-governed-package | with_skill | command | local-output-eval-runner | 26.1 | 98 | 100.0 | pass |

## Next Fixes

- Keep recorded fixtures as reproducible baselines, but do not describe them as model-executed evidence.
- Use `scripts/provider_output_eval_runner.py` for provider-backed holdout cases when release confidence depends on real generation behavior.
- Compare timing, token cost, and assertion deltas before promoting a skill to governed reuse.
