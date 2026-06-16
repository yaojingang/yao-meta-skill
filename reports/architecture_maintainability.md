# Architecture Maintainability

Generated at: `2026-06-13`

## Summary

- decision: `pass`
- python files: `215`
- scripts: `140`
- tests: `75`
- internal modules: `56`
- CLI scripts: `86`
- Yao CLI command handlers: `68`
- entrypoint command handlers: `18`
- command modules: `6`
- largest file lines: `696`
- early watch threshold lines: `600`
- early watchlist: `9`
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
| `scripts/skill_report_model.py` | `665` | `internal-module` | Watch this file before adding new responsibilities; extract a helper module when one concern dominates. |
| `scripts/render_skill_os2_coverage.py` | `649` | `cli-script` | Watch this file before adding new responsibilities; extract a helper module when one concern dominates. |
| `scripts/render_review_studio.py` | `647` | `cli-script` | Move data loading and large section renderers into focused review_studio_* modules. |
| `scripts/review_studio_gates.py` | `646` | `internal-module` | Watch this file before adding new responsibilities; extract a helper module when one concern dominates. |
| `scripts/render_reference_synthesis.py` | `644` | `cli-script` | Watch this file before adding new responsibilities; extract a helper module when one concern dominates. |
| `scripts/cross_packager.py` | `638` | `cli-script` | Watch this file before adding new responsibilities; extract a helper module when one concern dominates. |
| `scripts/build_skill_atlas.py` | `637` | `cli-script` | Watch this file before adding new responsibilities; extract a helper module when one concern dominates. |
| `tests/verify_world_class_evidence_intake.py` | `628` | `test` | Break broad integration assertions into focused verifier helpers when the next behavior change lands. |

## Largest Files

| File | Lines | Kind | Severity |
| --- | ---: | --- | --- |
| `tests/verify_yao_cli.py` | `696` | `test` | `pass` |
| `scripts/skill_report_model.py` | `665` | `internal-module` | `pass` |
| `scripts/render_skill_os2_coverage.py` | `649` | `cli-script` | `pass` |
| `scripts/render_review_studio.py` | `647` | `cli-script` | `pass` |
| `scripts/review_studio_gates.py` | `646` | `internal-module` | `pass` |
| `scripts/render_reference_synthesis.py` | `644` | `cli-script` | `pass` |
| `scripts/cross_packager.py` | `638` | `cli-script` | `pass` |
| `scripts/build_skill_atlas.py` | `637` | `cli-script` | `pass` |
| `tests/verify_world_class_evidence_intake.py` | `628` | `test` | `pass` |
| `scripts/render_benchmark_reproducibility.py` | `595` | `cli-script` | `pass` |
| `scripts/optimize_description.py` | `585` | `cli-script` | `pass` |
| `scripts/render_skill_overview.py` | `584` | `cli-script` | `pass` |

## Release Rule

- `block` hotspots should be split before governed release.
- `warn` hotspots can ship only when Review Studio keeps them visible and a reviewer accepts the modularization plan.
- Do not split a file only for line count; split when a stable responsibility boundary is clear.
