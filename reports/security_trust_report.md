# Security Trust Report

- OK: `True`
- Scanned files: `153`
- Scripts: `69`
- Internal script modules: `9`
- Secret findings: `0`
- Network-capable scripts: `3`
- Network policy covered scripts: `3`
- Network policy missing scripts: `0`
- File-write scripts: `47`
- Permission approvals: `3 / 3`
- Permission approval gaps: `0`
- CLI help smoke checked: `60`
- CLI help smoke failures: `0`
- Interactive scripts: `0`
- Package hash scope: `source-contract-without-generated-reports`
- Package hash files: `153`
- Package SHA256: `69dd8811ae7fef4aa0dcb296cd7c0587751eb2d7c68091953de620dcbf9aa682`

## Failures

- None

## Warnings

- None

## Dependency Evidence

- Files: `requirements-ci.txt`
- Pinned entries: `1`
- Unpinned entries: `0`

## Network Policy

- Policy file: `security/network_policy.json`
- Present: `True`
- Covered scripts: `3`
- Missing scripts: `none`
- Mismatches: `0`

## Permission Governance

- Policy file: `security/permission_policy.json`
- Present: `True`
- Required capabilities: `file_write, network, subprocess`
- Approved capabilities: `file_write, network, subprocess`
- Missing approvals: `none`
- Invalid approvals: `none`
- Expired approvals: `none`

## CLI Help Smoke

- Enabled: `True`
- Timeout seconds: `5.0`
- Checked scripts: `60`
- Passed scripts: `60`
- Failed scripts: `none`

## Script Surface

| Script | Interface | Declared | Argparse | Main Guard | Input | Network | File Write | Subprocess | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| scripts/adjudicate_output_review.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/build_confusion_matrix.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/build_skill_atlas.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/check_update.py | cli | False | True | True | False | True | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/ci_test.py | cli | False | True | True | False | False | True | True | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/collect_feedback.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/compile_skill.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/context_sizer.py | cli | False | True | True | False | False | False | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/create_iteration_snapshot.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/cross_packager.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/diff_eval.py | cli | False | True | True | False | False | False | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/export_skill_ir.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/github_benchmark_scan.py | cli | False | True | True | False | True | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/governance_check.py | cli | False | True | True | False | False | False | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/init_skill.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/judge_blind_eval.py | cli | False | True | True | False | False | False | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/lint_skill.py | cli | False | True | True | False | False | False | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/local_output_eval_runner.py | cli | False | True | True | False | False | False | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/optimize_description.py | cli | False | True | True | False | False | False | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/probe_runtime_permissions.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/promotion_checker.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/provider_output_eval_runner.py | cli | False | True | True | False | True | False | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/registry_audit.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_adoption_drift_report.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_artifact_design_profile.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_baseline_compare.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_context_reports.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_description_drift_history.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_eval_dashboard.py | cli | False | True | True | False | False | True | True | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_intent_confidence.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_intent_dialogue.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_iteration_directions.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_iteration_ledger.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_output_risk_profile.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_portability_report.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_prompt_quality_profile.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_reference_scan.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_reference_synthesis.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_regression_history.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_review_annotations.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_review_studio.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_review_viewer.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_review_waivers.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_skill_overview.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_social_preview.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_system_model.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/resource_boundary_check.py | cli | False | True | True | False | False | False | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/review_studio_formatting.py | internal-module | True | False | False | False | False | False | False | Imported by render_review_studio.py to format report dictionaries as audit UI panels. |
| scripts/review_studio_gates.py | internal-module | True | False | False | False | False | False | False | Imported by render_review_studio.py to keep Review Studio gate evaluation separate from HTML rendering. |
| scripts/review_studio_layout.py | internal-module | True | False | False | False | False | False | False | Imported by render_review_studio.py to keep Review Studio layout and CSS out of gate logic. |
| scripts/run_conformance_suite.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/run_description_optimization_suite.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/run_eval_suite.py | cli | False | True | True | False | False | False | True | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/run_output_eval.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/run_output_execution.py | cli | False | True | True | False | False | True | True | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/simulate_install.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/skill_report_charts.py | internal-module | True | False | False | False | False | False | False | Imported by render_skill_overview.py to render inline SVG report charts. |
| scripts/skill_report_layout.py | internal-module | True | False | False | False | False | False | False | Imported by render_skill_overview.py to keep overview report layout and CSS out of data rendering. |
| scripts/skill_report_metrics.py | internal-module | True | False | False | False | False | False | False | Imported by skill_report_model.py to calculate overview report metrics. |
| scripts/skill_report_model.py | internal-module | True | False | False | False | False | False | False | Imported by render_skill_overview.py to build the v2 report data model. |
| scripts/sync_local_install.py | cli | False | True | True | False | False | True | True | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/trigger_eval.py | cli | False | True | True | False | False | False | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/trust_check.py | cli | False | True | True | False | False | True | True | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/upgrade_check.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/validate_skill.py | cli | False | True | True | False | False | False | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/verify_package.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/yao.py | cli | False | True | True | False | False | False | True | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/yao_cli_config.py | internal-module | True | False | False | False | False | False | False | Imported by yao.py for CLI target maps and side-effect-free shaping helpers. |
| scripts/yao_cli_parser.py | internal-module | True | True | False | False | False | False | False | Imported by yao.py to keep CLI parser declarations separate from command orchestration. |
