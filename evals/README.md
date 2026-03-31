# Evals

This directory makes trigger quality and packaging quality more reproducible.

Contents:

- `trigger_cases.json`: positive, negative, and near-neighbor prompts
- `baseline_description.txt`: intentionally weaker trigger description
- `improved_description.txt`: current stronger trigger description
- `sample_trigger_report.json`: example comparison output using threshold `0.35`
- `failure-cases.md`: current weak spots and regression targets
- `packaging_expectations.json`: required packaging behaviors for supported targets

Use:

```bash
python3 scripts/trigger_eval.py --description-file evals/improved_description.txt --cases evals/trigger_cases.json --threshold 0.35
python3 scripts/trigger_eval.py --description-file evals/improved_description.txt --cases evals/trigger_cases.json --baseline-description-file evals/baseline_description.txt --threshold 0.35
python3 scripts/cross_packager.py . --platform openai --platform claude --expectations evals/packaging_expectations.json --zip
```
