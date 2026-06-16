# Architecture Maintainability

Generated at: `2026-06-16`

## Summary

- decision: `pass`
- python files: `203`
- scripts: `131`
- tests: `72`
- internal modules: `48`
- CLI scripts: `85`
- Yao CLI command handlers: `68`
- entrypoint command handlers: `18`
- command modules: `6`
- largest file lines: `852`
- watch threshold lines: `720`
- watchlist: `1`
- hotspots: `0`
- blockers: `0`

This report keeps maintainability risk visible before the Meta Skill grows more gates, renderers, and CLI commands.

## Hotspots

No file-size hotspots found.

## Watchlist

| File | Lines | Kind | Recommended next split |
| --- | ---: | --- | --- |
| `tests/verify_review_studio.py` | `852` | `test` | Break broad integration assertions into focused verifier helpers when the next behavior change lands. |

## Largest Files

| File | Lines | Kind | Severity |
| --- | ---: | --- | --- |
| `tests/verify_review_studio.py` | `852` | `test` | `pass` |
| `scripts/trust_check.py` | `714` | `internal-module` | `pass` |
| `scripts/review_studio_gates.py` | `707` | `internal-module` | `pass` |
| `scripts/apply_adaptation.py` | `706` | `cli-script` | `pass` |
| `tests/verify_yao_cli.py` | `696` | `test` | `pass` |
| `scripts/world_class_evidence_contract.py` | `686` | `internal-module` | `pass` |
| `scripts/render_review_viewer.py` | `685` | `cli-script` | `pass` |
| `scripts/skill_report_model.py` | `665` | `internal-module` | `pass` |
| `tests/verify_world_class_evidence_intake.py` | `660` | `test` | `pass` |
| `scripts/render_skill_os2_coverage.py` | `649` | `cli-script` | `pass` |
| `scripts/render_review_studio.py` | `647` | `cli-script` | `pass` |
| `scripts/render_reference_synthesis.py` | `644` | `cli-script` | `pass` |

## Release Rule

- `block` hotspots should be split before governed release.
- `warn` hotspots can ship only when Review Studio keeps them visible and a reviewer accepts the modularization plan.
- Do not split a file only for line count; split when a stable responsibility boundary is clear.
