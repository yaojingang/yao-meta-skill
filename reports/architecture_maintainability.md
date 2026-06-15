# Architecture Maintainability

Generated at: `2026-06-15`

## Summary

- decision: `pass`
- python files: `173`
- scripts: `110`
- tests: `63`
- internal modules: `31`
- CLI scripts: `81`
- Yao CLI command handlers: `64`
- entrypoint command handlers: `18`
- command modules: `6`
- largest file lines: `897`
- hotspots: `0`
- blockers: `0`

This report keeps maintainability risk visible before the Meta Skill grows more gates, renderers, and CLI commands.

## Hotspots

No file-size hotspots found.

## Largest Files

| File | Lines | Kind | Severity |
| --- | ---: | --- | --- |
| `tests/verify_yao_cli.py` | `897` | `test` | `pass` |
| `scripts/yao_cli_parser.py` | `810` | `internal-module` | `pass` |
| `scripts/skill_report_layout.py` | `808` | `internal-module` | `pass` |
| `scripts/skill_report_model.py` | `801` | `internal-module` | `pass` |
| `tests/verify_review_studio.py` | `751` | `test` | `pass` |
| `scripts/compile_skill.py` | `734` | `cli-script` | `pass` |
| `scripts/build_skill_atlas.py` | `730` | `cli-script` | `pass` |
| `scripts/optimize_description.py` | `723` | `cli-script` | `pass` |
| `scripts/trust_check.py` | `714` | `internal-module` | `pass` |
| `scripts/review_studio_layout.py` | `694` | `internal-module` | `pass` |
| `scripts/render_review_viewer.py` | `685` | `cli-script` | `pass` |
| `scripts/cross_packager.py` | `650` | `cli-script` | `pass` |

## Release Rule

- `block` hotspots should be split before governed release.
- `warn` hotspots can ship only when Review Studio keeps them visible and a reviewer accepts the modularization plan.
- Do not split a file only for line count; split when a stable responsibility boundary is clear.
