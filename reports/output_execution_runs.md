# Output Execution Runs

This report records how output-eval variants were produced and whether timing or token evidence is observed or estimated.

- Cases: `5`
- Variant runs: `10`
- Command executed: `10`
- Model executed: `10`
- Recorded fixtures: `0`
- Timing observed: `10`
- Token observed: `10`
- Token estimated: `0`
- Delta: `20.0`
- Gate pass: `True`

Command runner evidence is present. This proves the eval harness executed an external command, but it is not provider-backed model evidence unless the runner reports model metadata.

## Runs

| Case | Variant | Mode | Model | Duration ms | Tokens | Score | Status |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| skill-package-contract | baseline | model | deepseek-v4-flash | 5980.01 | 484 | 0.0 | pass |
| skill-package-contract | with_skill | model | deepseek-v4-flash | 11217.19 | 1848 | 75.0 | pass |
| output-eval-expectation | baseline | model | deepseek-v4-flash | 3178.95 | 236 | 0.0 | pass |
| output-eval-expectation | with_skill | model | deepseek-v4-flash | 4611.78 | 1121 | 25.0 | pass |
| ir-before-packaging | baseline | model | deepseek-v4-flash | 6772.59 | 765 | 25.0 | pass |
| ir-before-packaging | with_skill | model | deepseek-v4-flash | 17471.19 | 2986 | 25.0 | pass |
| near-neighbor-boundary | baseline | model | deepseek-v4-flash | 3091.33 | 198 | 33.33 | pass |
| near-neighbor-boundary | with_skill | model | deepseek-v4-flash | 4152.85 | 1015 | 33.33 | pass |
| file-backed-governed-package | baseline | model | deepseek-v4-flash | 4750.01 | 502 | 60.0 | pass |
| file-backed-governed-package | with_skill | model | deepseek-v4-flash | 9406.25 | 1610 | 60.0 | pass |

## Next Fixes

- Keep recorded fixtures as reproducible baselines, but do not describe them as model-executed evidence.
- Use `scripts/provider_output_eval_runner.py` for provider-backed holdout cases when release confidence depends on real generation behavior.
- Compare timing, token cost, and assertion deltas before promoting a skill to governed reuse.
