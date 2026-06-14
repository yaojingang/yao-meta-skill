# Architecture Maintainability

Generated at: `2026-06-14`

## Summary

- decision: `pass`
- python files: `156`
- scripts: `97`
- tests: `59`
- internal modules: `23`
- CLI scripts: `76`
- Yao CLI command handlers: `34`
- largest file lines: `888`
- hotspots: `0`
- blockers: `0`

This report keeps maintainability risk visible before the Meta Skill grows more gates, renderers, and CLI commands.

## Hotspots

No file-size hotspots found.

## Largest Files

| File | Lines | Kind | Severity |
| --- | ---: | --- | --- |
| `tests/verify_yao_cli.py` | `888` | `test` | `pass` |
| `scripts/yao.py` | `874` | `cli-script` | `pass` |
| `scripts/skill_report_model.py` | `792` | `internal-module` | `pass` |
| `scripts/yao_cli_parser.py` | `741` | `internal-module` | `pass` |
| `scripts/compile_skill.py` | `734` | `cli-script` | `pass` |
| `scripts/optimize_description.py` | `723` | `cli-script` | `pass` |
| `scripts/trust_check.py` | `714` | `internal-module` | `pass` |
| `scripts/render_review_viewer.py` | `685` | `cli-script` | `pass` |
| `scripts/build_skill_atlas.py` | `674` | `cli-script` | `pass` |
| `tests/verify_review_studio.py` | `674` | `test` | `pass` |
| `scripts/skill_report_layout.py` | `653` | `internal-module` | `pass` |
| `scripts/render_reference_synthesis.py` | `644` | `cli-script` | `pass` |

## Release Rule

- `block` hotspots should be split before governed release.
- `warn` hotspots can ship only when Review Studio keeps them visible and a reviewer accepts the modularization plan.
- Do not split a file only for line count; split when a stable responsibility boundary is clear.
