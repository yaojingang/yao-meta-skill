# Security Trust Report

- OK: `True`
- Scanned files: `226`
- Scripts: `135`
- Internal script modules: `49`
- Secret findings: `0`
- Network-capable scripts: `3`
- Network policy covered scripts: `3`
- Network policy missing scripts: `0`
- File-write scripts: `73`
- Permission approvals: `3 / 3`
- Permission approval gaps: `0`
- CLI help smoke checked: `86`
- CLI help smoke failures: `0`
- Interactive scripts: `0`
- Package hash scope: `source-contract-without-generated-reports`
- Package hash files: `226`
- Package SHA256: `6149b95fa5fb9a93108ed5099f3f53e629fa6ac673e03206371d5837a31bae97`

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
- Checked scripts: `86`
- Passed scripts: `86`
- Failed scripts: `none`

## Script Surface

| Script | Interface | Declared | Argparse | Main Guard | Input | Network | File Write | Subprocess | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| scripts/adaptation_patch_safety.py | internal-module | True | False | False | False | False | False | False | Shared adaptation patch target parsing and target-file baseline verification helpers. |
| scripts/adaptation_report_contracts.py | internal-module | True | False | False | False | False | False | False | Shared adaptation approval and regression report contract decoration helpers. |
| scripts/adjudicate_output_review.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/apply_adaptation.py | cli | True | True | True | False | False | True | True | Approval-gated adaptive patch application with dry-run, allowlist, regression, and rollback evidence. |
| scripts/build_confusion_matrix.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/build_skill_atlas.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/build_skill_atlas_layout.py | internal-module | True | False | False | False | False | False | False | Imported by build_skill_atlas.py to render the static Skill Atlas HTML report. |
| scripts/check_update.py | cli | False | True | True | False | True | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/ci_test.py | cli | False | True | True | False | False | True | True | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/collect_feedback.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/compile_skill.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/compile_skill_targets.py | internal-module | True | False | False | False | False | False | False | Imported by compile_skill for target platform model and contract builders. |
| scripts/context_sizer.py | cli | False | True | True | False | False | False | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/create_iteration_snapshot.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/cross_packager.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/description_optimizer_reporting.py | internal-module | True | False | False | False | False | False | False | Imported by optimize_description.py to render description optimization reports. |
| scripts/diff_eval.py | cli | False | True | True | False | False | False | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/emit_telemetry_event.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/evidence_consistency_artifact_roles.py | internal-module | True | False | False | False | False | False | False | Imported by render_evidence_consistency.py to compare preflight and Review Studio artifact-role contracts. |
| scripts/evidence_consistency_core.py | internal-module | True | False | False | False | False | False | False | Imported by render_evidence_consistency.py for shared report loading, comparison, and Markdown rendering helpers. |
| scripts/evidence_consistency_release.py | internal-module | True | False | False | False | False | False | False | Imported by render_evidence_consistency.py to verify release evidence refresh instructions. |
| scripts/evidence_consistency_skill_os2_review.py | internal-module | True | False | False | False | False | False | False | Imported by render_evidence_consistency.py to keep Skill OS 2.0 review summary drift checks out of the main consistency renderer. |
| scripts/evidence_consistency_world_class.py | internal-module | True | False | False | False | False | False | False | Imported by render_evidence_consistency.py to isolate world-class evidence workflow consistency checks. |
| scripts/export_skill_ir.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/github_benchmark_scan.py | cli | False | True | True | False | True | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/governance_check.py | cli | False | True | True | False | False | False | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/html_rendering.py | internal-module | True | False | False | False | False | False | False | Used by report renderers to escape HTML while preserving meaningful falsey values. |
| scripts/import_output_review_decisions.py | cli | True | True | True | False | False | True | False | Imports human blind A/B reviewer decisions into the canonical output-review decision file. |
| scripts/import_telemetry_events.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/init_skill.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/judge_blind_eval.py | cli | False | True | True | False | False | False | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/lint_skill.py | cli | False | True | True | False | False | False | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/local_output_eval_runner.py | cli | False | True | True | False | False | False | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/optimize_description.py | cli | False | True | True | False | False | False | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/prepare_output_review_kit.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/prepare_world_class_submission_kit.py | cli | True | True | True | False | False | True | False | Prepares editable world-class evidence intake packets without counting drafts as accepted evidence. |
| scripts/probe_runtime_permissions.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/promotion_checker.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/propose_adaptation.py | cli | True | True | True | False | False | True | False | Turns redacted repeated preference patterns into proposal-only adaptation plans. |
| scripts/provider_output_eval_runner.py | cli | False | True | True | False | True | False | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/python_compat_check.py | cli | True | True | True | False | False | True | False | Checks repository Python source for syntax that can pass locally but fail on the supported CI interpreter. |
| scripts/registry_audit.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_adoption_drift_report.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_architecture_maintainability.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_artifact_design_profile.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_baseline_compare.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_benchmark_reproducibility.py | cli | True | True | True | False | False | True | True | Renders a release-facing benchmark reproducibility manifest and Markdown report. |
| scripts/render_context_reports.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_daily_skillops_report.py | cli | True | True | True | False | False | True | False | Renders a Daily SkillOps report that summarizes explicit-source patterns, proposals, approval state, and release evidence without scanning private logs or applying patches. |
| scripts/render_description_drift_history.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_eval_dashboard.py | cli | False | True | True | False | False | True | True | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_evidence_consistency.py | cli | True | True | True | False | False | True | False | Renders a cross-report evidence consistency gate for generated Skill OS reports. |
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
| scripts/render_skill_interpretation.py | cli | True | True | True | False | False | True | False | Renders the first-class skill interpretation report while reusing the Skill Overview v2 model and layout. |
| scripts/render_skill_os2_audit.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_skill_os2_coverage.py | cli | True | True | True | False | False | True | False | Renders a Skill OS 2.0 blueprint-to-evidence coverage audit. |
| scripts/render_skill_overview.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_social_preview.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_system_model.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_telemetry_hook_recipes.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_weekly_curator_report.py | cli | True | True | True | False | False | True | False | Renders a weekly SkillOps curator report from generated reports without scanning private logs or writing source files. |
| scripts/render_world_class_claim_guard.py | cli | True | True | True | False | False | True | False | Scans public claim surfaces so world-class completion is not claimed before accepted evidence exists. |
| scripts/render_world_class_evidence_intake.py | cli | True | True | True | False | False | True | False | Validates world-class human and external evidence intake packets before ledger review. |
| scripts/render_world_class_evidence_ledger.py | cli | True | True | True | False | False | True | False | Renders a machine-checkable ledger for world-class external and human evidence gaps. |
| scripts/render_world_class_evidence_plan.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/render_world_class_operator_runbook.py | cli | True | True | True | False | False | True | False | Renders an operator runbook for collecting pending world-class evidence without accepting evidence. |
| scripts/render_world_class_preflight.py | cli | True | True | True | False | False | True | False | Renders a preflight checklist for collecting pending world-class evidence without accepting evidence. |
| scripts/render_world_class_submission_review.py | cli | True | True | True | False | False | True | False | Renders a read-only review queue for world-class evidence submissions before ledger acceptance. |
| scripts/resource_boundary_check.py | cli | False | True | True | False | False | False | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/review_studio_action_evidence.py | internal-module | True | False | False | False | False | False | False | Imported by review_studio_actions.py to keep world-class evidence action cards out of generic Review Studio action wiring. |
| scripts/review_studio_actions.py | internal-module | True | False | False | False | False | False | False | Imported by render_review_studio.py to keep Review Studio action guidance and source refs out of HTML rendering. |
| scripts/review_studio_data.py | internal-module | True | False | False | False | False | False | False | Imported by render_review_studio.py to load Review Studio source reports and metric cards. |
| scripts/review_studio_formatting.py | internal-module | True | False | False | False | False | False | False | Imported by render_review_studio.py to format report dictionaries as audit UI panels. |
| scripts/review_studio_gate_contract.py | internal-module | True | False | False | False | False | False | False | Imported by review_studio_gates.py for stable gate scoring and contract checks. |
| scripts/review_studio_gates.py | internal-module | True | False | False | False | False | False | False | Imported by render_review_studio.py to keep Review Studio gate evaluation separate from HTML rendering. |
| scripts/review_studio_layout.py | internal-module | True | False | False | False | False | False | False | Imported by render_review_studio.py to keep Review Studio layout and CSS out of gate logic. |
| scripts/review_studio_output_review.py | internal-module | True | False | False | False | False | False | False | Imported by render_review_studio.py to render output review checklist cards. |
| scripts/review_studio_skillops.py | internal-module | True | False | False | False | False | False | False | Imported by render_review_studio.py to keep SkillOps summary panels out of the main HTML renderer. |
| scripts/review_studio_waivers.py | internal-module | True | False | False | False | False | False | False | Imported by render_review_studio.py to keep waiver candidate layout out of the main renderer. |
| scripts/review_studio_world_class.py | internal-module | True | False | False | False | False | False | False | Imported by render_review_studio.py to render world-class evidence cards. |
| scripts/review_viewer_data.py | internal-module | True | False | False | False | False | False | False | Imported by render_review_viewer.py to assemble Review Viewer data before HTML rendering. |
| scripts/run_conformance_suite.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/run_description_optimization_suite.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/run_eval_suite.py | cli | False | True | True | False | False | False | True | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/run_output_eval.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/run_output_execution.py | cli | False | True | True | False | False | True | True | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/simulate_install.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/skill_ir_paths.py | internal-module | True | False | False | False | False | False | False | Imported by compiler, registry, conformance, and report scripts to locate canonical Skill IR artifacts. |
| scripts/skill_report_charts.py | internal-module | True | False | False | False | False | False | False | Imported by render_skill_overview.py to render inline SVG report charts. |
| scripts/skill_report_i18n.py | internal-module | True | False | False | False | False | False | False | Imported by render_skill_overview.py to keep bilingual report copy and fallback rules out of HTML rendering. |
| scripts/skill_report_layout.py | internal-module | True | False | False | False | False | False | False | Imported by render_skill_overview.py to keep overview report layout and CSS out of data rendering. |
| scripts/skill_report_metrics.py | internal-module | True | False | False | False | False | False | False | Imported by skill_report_model.py to calculate overview report metrics. |
| scripts/skill_report_model.py | internal-module | True | False | False | False | False | False | False | Imported by render_skill_overview.py to build the v2 report data model. |
| scripts/skill_report_sources.py | internal-module | True | False | False | False | False | False | False | Imported by skill_report_model.py to load source files and scan overview package assets. |
| scripts/skill_report_world_class.py | internal-module | True | False | False | False | False | False | False | Imported by skill_report_model.py to summarize world-class evidence readiness and roadmap actions. |
| scripts/skillops_opportunity.py | internal-module | True | False | False | False | False | False | False | Imported by render_daily_skillops_report.py to score SkillOps opportunities without writing files. |
| scripts/summarize_user_signals.py | cli | True | True | True | False | False | True | False | Scans an explicit local source file and summarizes redacted repeated user preference signals. |
| scripts/sync_local_install.py | cli | False | True | True | False | False | True | True | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/telemetry_native_host.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/trigger_eval.py | cli | False | True | True | False | False | False | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/trust_check.py | cli | False | True | True | False | False | True | True | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/trust_check_scripts.py | internal-module | True | True | True | False | False | False | False | Static script inventory helpers imported by trust_check.py. |
| scripts/upgrade_check.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/validate_skill.py | cli | False | True | True | False | False | False | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/verify_package.py | cli | False | True | True | False | False | True | False | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/world_class_evidence_contract.py | internal-module | True | False | False | False | False | False | False | Imported by world-class evidence reports to share intake validation and artifact integrity checks. |
| scripts/world_class_preflight_layout.py | internal-module | True | False | False | False | False | False | False | Imported by render_world_class_preflight.py to keep preflight HTML layout out of data assembly. |
| scripts/world_class_source_checks.py | internal-module | True | False | False | False | False | False | False | Imported by world-class evidence reports to keep source-evidence readiness checks consistent. |
| scripts/world_class_submission_kit_rendering.py | internal-module | True | False | False | False | False | False | False | Shared renderer for world-class submission kit Markdown and HTML artifacts. |
| scripts/world_class_submission_matrix.py | internal-module | True | False | False | False | False | False | False | Shared by submission kit rendering to summarize draft, artifact, and source-check readiness. |
| scripts/yao.py | cli | False | True | True | False | False | False | True | Default CLI classification; add SCRIPT_INTERFACE for internal modules. |
| scripts/yao_cli_adaptation_commands.py | internal-module | True | True | False | False | False | False | False | Imported by yao.py to keep adaptive scan/proposal/apply command handlers outside the thin CLI orchestrator. |
| scripts/yao_cli_config.py | internal-module | True | False | False | False | False | False | False | Imported by yao.py for CLI target maps and side-effect-free shaping helpers. |
| scripts/yao_cli_create_commands.py | internal-module | True | True | False | False | False | False | False | Imported by yao.py to keep skill creation and quickstart command handlers out of the CLI orchestrator. |
| scripts/yao_cli_distribution_commands.py | internal-module | True | True | False | False | False | False | False | Imported by yao.py to keep distribution and runtime gate handlers outside the thin CLI orchestrator. |
| scripts/yao_cli_output_commands.py | internal-module | True | True | False | False | False | False | False | Imported by yao.py to keep output evaluation and review handlers outside the thin CLI orchestrator. |
| scripts/yao_cli_parser.py | internal-module | True | True | False | False | False | False | False | Imported by yao.py to keep CLI parser declarations separate from command orchestration. |
| scripts/yao_cli_parser_evidence.py | internal-module | True | True | False | False | False | False | False | Imported by yao_cli_parser.py to keep evidence command declarations out of the main parser module. |
| scripts/yao_cli_parser_operations.py | internal-module | True | True | False | False | False | False | False | Imported by yao_cli_parser.py to keep SkillOps, telemetry, and review-loop command declarations out of the main parser module. |
| scripts/yao_cli_report_commands.py | internal-module | True | True | False | False | False | False | False | Imported by yao.py to keep report and evidence command handlers out of the CLI orchestrator. |
| scripts/yao_cli_runtime.py | internal-module | True | False | False | False | False | False | True | Imported by yao.py and command modules for shared subprocess execution and JSON payload parsing. |
| scripts/yao_cli_telemetry.py | internal-module | True | True | False | False | False | False | False | Imported by yao.py to record opt-in metadata-only CLI run telemetry. |
