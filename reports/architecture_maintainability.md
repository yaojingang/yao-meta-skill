# Architecture Maintainability

Generated at: `2026-06-16`

## Summary

- decision: `pass`
- python files: `205`
- scripts: `132`
- tests: `73`
- internal modules: `48`
- CLI scripts: `86`
- Yao CLI command handlers: `68`
- entrypoint command handlers: `18`
- command modules: `6`
- largest file lines: `707`
- watch threshold lines: `720`
- watchlist: `0`
- hotspots: `0`
- blockers: `0`

This report keeps maintainability risk visible before the Meta Skill grows more gates, renderers, and CLI commands.

## Hotspots

No file-size hotspots found.

## Watchlist

No near-threshold files found.

## Largest Files

| File | Lines | Kind | Severity |
| --- | ---: | --- | --- |
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
| `scripts/cross_packager.py` | `638` | `cli-script` | `pass` |
| `scripts/build_skill_atlas.py` | `637` | `cli-script` | `pass` |

## Release Rule

- `block` hotspots should be split before governed release.
- `warn` hotspots can ship only when Review Studio keeps them visible and a reviewer accepts the modularization plan.
- Do not split a file only for line count; split when a stable responsibility boundary is clear.
