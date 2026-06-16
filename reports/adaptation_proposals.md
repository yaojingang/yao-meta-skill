# Adaptation Proposals

- Generated at: `2026-06-16T21:16:12Z`
- Pattern report: `reports/user_patterns.json`
- Proposal only: `true`
- Writes repository files: `false`
- Proposals: `5`

## Keep reports Chinese-first with optional English

- ID: `adapt-18c7517f3d`
- Status: `proposal-only`
- Pattern: `language_default`
- Risk: `low`
- Requires approval: `true`
- Reason: 2 redacted records matched repeated report-language signals.
- Target files:
  - `scripts/render_skill_overview.py`
  - `references/artifact-design-doctrine.md`
- Suggested changes:
  - Keep user-facing report copy Simplified Chinese by default.
  - Expose English through the existing language switch instead of mixing languages in the default view.
- Verification:
  - `python3 tests/verify_skill_overview.py`
- Rollback: Revert report language template changes and rerun the overview verifier.
- Redacted evidence refs:
  - `line-1`: 新生成的 Skill 报告默认使用中文简体，并在右上角提供英文切换。
  - `line-2`: HTML 报告需要双语能力，但默认内容应该保持中文简体。

## Improve report layout, visual hierarchy, and chart readability

- ID: `adapt-fbfe921ba5`
- Status: `proposal-only`
- Pattern: `report_ui`
- Risk: `medium`
- Requires approval: `true`
- Reason: 5 redacted records matched repeated artifact-design signals.
- Target files:
  - `scripts/render_skill_overview.py`
  - `references/artifact-design-doctrine.md`
  - `tests/verify_skill_overview.py`
- Suggested changes:
  - Prefer vertical narrative sections with limited two-column layouts only when content has enough width.
  - Keep charts inline SVG, with captions and stable responsive constraints.
- Verification:
  - `python3 tests/verify_skill_overview.py`
  - `python3 tests/verify_skill_report_charts.py`
- Rollback: Restore the previous report renderer and regenerate the demo report.
- Redacted evidence refs:
  - `line-1`: 新生成的 Skill 报告默认使用中文简体，并在右上角提供英文切换。
  - `line-2`: HTML 报告需要双语能力，但默认内容应该保持中文简体。
  - `line-3`: 报告排版采用白底 Kami 风格，图表、模块和导航都要清晰。

## Keep adaptive iteration approval-gated

- ID: `adapt-59d219a1fb`
- Status: `proposal-only`
- Pattern: `approval_safety`
- Risk: `low`
- Requires approval: `true`
- Reason: 2 redacted records matched repeated governance signals.
- Target files:
  - `references/user-memory-policy.md`
  - `references/autonomous-adaptation.md`
  - `schemas/adaptation-proposal.schema.json`
- Suggested changes:
  - Require explicit source paths for memory scans.
  - Generate proposals before any source patching.
  - Reserve automatic apply for a future approval ledger and rollback implementation.
- Verification:
  - `python3 tests/verify_adaptation_safety.py`
- Rollback: Remove the adaptive proposal artifacts and keep feedback/adoption drift as the only iteration inputs.
- Redacted evidence refs:
  - `line-5`: 自适应升级必须先生成提案，不能直接自动修改源文件。
  - `line-6`: 用户偏好扫描必须由用户提供明确路径，不要默认扫描私人日志。

## Make generated artifact paths explicit in CLI output

- ID: `adapt-457baca160`
- Status: `proposal-only`
- Pattern: `delivery_format`
- Risk: `low`
- Requires approval: `true`
- Reason: 2 redacted records matched repeated artifact-format signals.
- Target files:
  - `scripts/yao.py`
  - `README.md`
- Suggested changes:
  - Include stable report paths in command output.
  - Document which artifacts are meant for human review.
- Verification:
  - `python3 tests/verify_yao_cli.py`
- Rollback: Revert CLI copy/documentation changes and keep artifact paths unchanged.
- Redacted evidence refs:
  - `line-2`: HTML 报告需要双语能力，但默认内容应该保持中文简体。
  - `line-6`: 用户偏好扫描必须由用户提供明确路径，不要默认扫描私人日志。

## Attach tests and evidence refresh to each upgrade

- ID: `adapt-abfee25d3a`
- Status: `proposal-only`
- Pattern: `evidence_testing`
- Risk: `medium`
- Requires approval: `true`
- Reason: 2 redacted records matched repeated quality-gate signals.
- Target files:
  - `tests/verify_adaptation_safety.py`
  - `scripts/render_skill_os2_coverage.py`
  - `reports/skill_os2_coverage.json`
- Suggested changes:
  - Add focused verifier coverage for every new adaptive behavior.
  - Refresh Skill OS 2.0 coverage so planned, partial, and covered states remain visible.
- Verification:
  - `python3 tests/verify_adaptation_safety.py`
  - `python3 tests/verify_skill_os2_coverage.py`
- Rollback: Revert the new verifier and coverage status updates, then regenerate coverage reports.
- Redacted evidence refs:
  - `line-7`: 每次升级都需要测试、覆盖报告和可审计证据，推送前要跑 CI。
  - `line-8`: 涉及 GitHub 推送时，要保留证据链，避免把计划当作完成证明。
