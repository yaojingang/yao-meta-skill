# Architecture Maintainability

Generated at: `2026-06-13`

## Summary

- decision: `pass`
- python files: `224`
- scripts: `148`
- tests: `76`
- internal modules: `64`
- CLI scripts: `86`
- Yao CLI command handlers: `68`
- entrypoint command handlers: `18`
- command modules: `6`
- largest file lines: `696`
- early watch threshold lines: `600`
- early watchlist: `2`
- watch threshold lines: `720`
- watchlist: `0`
- hotspots: `0`
- blockers: `0`

This report keeps maintainability risk visible before the Meta Skill grows more gates, renderers, and CLI commands.

## Hotspots

No file-size hotspots found.

## Watchlist

No near-threshold files found.

## Early Watchlist

| File | Lines | Kind | Recommended next split |
| --- | ---: | --- | --- |
| `tests/verify_yao_cli.py` | `696` | `test` | Break broad integration assertions into focused verifier helpers when the next behavior change lands. |
| `tests/verify_world_class_evidence_intake.py` | `690` | `test` | Break broad integration assertions into focused verifier helpers when the next behavior change lands. |

## Largest Files

| File | Lines | Kind | Severity |
| --- | ---: | --- | --- |
| `tests/verify_yao_cli.py` | `696` | `test` | `pass` |
| `tests/verify_world_class_evidence_intake.py` | `690` | `test` | `pass` |
| `tests/verify_output_review_adjudication.py` | `599` | `test` | `pass` |
| `scripts/render_benchmark_reproducibility.py` | `595` | `cli-script` | `pass` |
| `scripts/render_world_class_preflight.py` | `590` | `cli-script` | `pass` |
| `scripts/render_skill_overview.py` | `588` | `cli-script` | `pass` |
| `scripts/build_skill_atlas.py` | `586` | `cli-script` | `pass` |
| `scripts/optimize_description.py` | `585` | `cli-script` | `pass` |
| `scripts/trust_check.py` | `582` | `cli-script` | `pass` |
| `tests/verify_world_class_evidence_ledger.py` | `579` | `test` | `pass` |
| `scripts/render_evidence_consistency.py` | `568` | `cli-script` | `pass` |
| `scripts/render_review_studio.py` | `568` | `cli-script` | `pass` |

## Release Rule

- `block` hotspots should be split before governed release.
- `warn` hotspots can ship only when Review Studio keeps them visible and a reviewer accepts the modularization plan.
- Do not split a file only for line count; split when a stable responsibility boundary is clear.
