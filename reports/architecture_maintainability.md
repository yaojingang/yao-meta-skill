# Architecture Maintainability

Generated at: `2026-06-13`

## Summary

- decision: `pass`
- python files: `191`
- scripts: `122`
- tests: `69`
- internal modules: `39`
- CLI scripts: `85`
- Yao CLI command handlers: `68`
- entrypoint command handlers: `18`
- command modules: `6`
- largest file lines: `899`
- watch threshold lines: `720`
- watchlist: `10`
- hotspots: `0`
- blockers: `0`

This report keeps maintainability risk visible before the Meta Skill grows more gates, renderers, and CLI commands.

## Hotspots

No file-size hotspots found.

## Watchlist

| File | Lines | Kind | Recommended next split |
| --- | ---: | --- | --- |
| `tests/verify_yao_cli.py` | `899` | `test` | Break broad integration assertions into focused verifier helpers when the next behavior change lands. |
| `scripts/yao_cli_parser.py` | `870` | `internal-module` | Watch this file before adding new responsibilities; extract a helper module when one concern dominates. |
| `tests/verify_world_class_evidence_intake.py` | `867` | `test` | Break broad integration assertions into focused verifier helpers when the next behavior change lands. |
| `tests/verify_review_studio.py` | `834` | `test` | Break broad integration assertions into focused verifier helpers when the next behavior change lands. |
| `scripts/render_world_class_preflight.py` | `814` | `cli-script` | Watch this file before adding new responsibilities; extract a helper module when one concern dominates. |
| `scripts/render_evidence_consistency.py` | `808` | `cli-script` | Watch this file before adding new responsibilities; extract a helper module when one concern dominates. |
| `scripts/skill_report_model.py` | `800` | `internal-module` | Watch this file before adding new responsibilities; extract a helper module when one concern dominates. |
| `scripts/build_skill_atlas.py` | `730` | `cli-script` | Watch this file before adding new responsibilities; extract a helper module when one concern dominates. |
| `scripts/compile_skill.py` | `723` | `cli-script` | Watch this file before adding new responsibilities; extract a helper module when one concern dominates. |
| `scripts/optimize_description.py` | `723` | `cli-script` | Watch this file before adding new responsibilities; extract a helper module when one concern dominates. |

## Largest Files

| File | Lines | Kind | Severity |
| --- | ---: | --- | --- |
| `tests/verify_yao_cli.py` | `899` | `test` | `pass` |
| `scripts/yao_cli_parser.py` | `870` | `internal-module` | `pass` |
| `tests/verify_world_class_evidence_intake.py` | `867` | `test` | `pass` |
| `tests/verify_review_studio.py` | `834` | `test` | `pass` |
| `scripts/render_world_class_preflight.py` | `814` | `cli-script` | `pass` |
| `scripts/render_evidence_consistency.py` | `808` | `cli-script` | `pass` |
| `scripts/skill_report_model.py` | `800` | `internal-module` | `pass` |
| `scripts/build_skill_atlas.py` | `730` | `cli-script` | `pass` |
| `scripts/compile_skill.py` | `723` | `cli-script` | `pass` |
| `scripts/optimize_description.py` | `723` | `cli-script` | `pass` |
| `scripts/trust_check.py` | `714` | `internal-module` | `pass` |
| `scripts/apply_adaptation.py` | `706` | `cli-script` | `pass` |

## Release Rule

- `block` hotspots should be split before governed release.
- `warn` hotspots can ship only when Review Studio keeps them visible and a reviewer accepts the modularization plan.
- Do not split a file only for line count; split when a stable responsibility boundary is clear.
