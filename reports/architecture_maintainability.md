# Architecture Maintainability

Generated at: `2026-11-09`

## Summary

- decision: `pass`
- python files: `260`
- scripts: `174`
- tests: `86`
- internal modules: `83`
- CLI scripts: `96`
- Yao CLI command handlers: `74`
- entrypoint command handlers: `17`
- command modules: `8`
- largest file lines: `719`
- early watch threshold lines: `600`
- early watchlist: `7`
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
| `scripts/render_benchmark_reproducibility.py` | `719` | `cli-script` | Watch this file before adding new responsibilities; extract a helper module when one concern dominates. |
| `tests/verify_evidence_consistency.py` | `719` | `test` | Break broad integration assertions into focused verifier helpers when the next behavior change lands. |
| `tests/verify_world_class_evidence_intake.py` | `706` | `test` | Break broad integration assertions into focused verifier helpers when the next behavior change lands. |
| `tests/verify_yao_cli.py` | `700` | `test` | Break broad integration assertions into focused verifier helpers when the next behavior change lands. |
| `scripts/render_evidence_consistency.py` | `670` | `cli-script` | Watch this file before adding new responsibilities; extract a helper module when one concern dominates. |
| `scripts/render_world_class_operator_runbook.py` | `651` | `cli-script` | Watch this file before adding new responsibilities; extract a helper module when one concern dominates. |
| `tests/verify_output_review_adjudication.py` | `600` | `test` | Break broad integration assertions into focused verifier helpers when the next behavior change lands. |

## Largest Files

| File | Lines | Kind | Severity |
| --- | ---: | --- | --- |
| `scripts/render_benchmark_reproducibility.py` | `719` | `cli-script` | `pass` |
| `tests/verify_evidence_consistency.py` | `719` | `test` | `pass` |
| `tests/verify_world_class_evidence_intake.py` | `706` | `test` | `pass` |
| `tests/verify_yao_cli.py` | `700` | `test` | `pass` |
| `scripts/render_evidence_consistency.py` | `670` | `cli-script` | `pass` |
| `scripts/render_world_class_operator_runbook.py` | `651` | `cli-script` | `pass` |
| `tests/verify_output_review_adjudication.py` | `600` | `test` | `pass` |
| `scripts/build_skill_atlas.py` | `598` | `cli-script` | `pass` |
| `scripts/intent_clarification.py` | `592` | `internal-module` | `pass` |
| `scripts/render_review_studio.py` | `592` | `cli-script` | `pass` |
| `scripts/world_class_evidence_contract.py` | `592` | `internal-module` | `pass` |
| `scripts/render_skill_overview.py` | `588` | `cli-script` | `pass` |

## Release Rule

- `block` hotspots should be split before governed release.
- `warn` hotspots can ship only when Review Studio keeps them visible and a reviewer accepts the modularization plan.
- Do not split a file only for line count; split when a stable responsibility boundary is clear.
