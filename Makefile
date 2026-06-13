PYTHON ?= python3
LOCAL_SKILL_INSTALL_DIR ?= $(HOME)/.agents/skills.disabled/yao-meta-skill
ACTIVE_SKILL_INSTALL_DIR ?= $(HOME)/.agents/skills/yao-meta-skill

.PHONY: eval eval-suite route-scorecard route-confusion-check description-optimization judge-blind-eval description-optimization-check promotion-check yao-cli-check skill-overview-check skill-report-metrics-check skill-report-charts-check skill-ir-check compiler-check output-eval-check output-execution-check output-review-adjudication-check runtime-conformance-check runtime-permission-check trust-check skill-atlas-check registry-audit-check package-verify-check install-simulation-check upgrade-check review-viewer-check review-studio-check feedback-check adoption-drift-check review-waivers-check review-annotations-check baseline-compare-check reference-scan-check github-benchmark-scan-check intent-confidence-check reference-synthesis-check output-risk-profile-check artifact-design-profile-check prompt-quality-profile-check system-model-check iteration-directions-check description-drift-history iteration-ledger results-panel regression-history context-reports portability-report portability-check failure-regression-check package-check package-failure-check security-boundary-check local-install-sync-check snapshot-check validate lint governance-check resource-boundary-check quality-check sync-local-install sync-active-install test ci-test clean

eval:
	$(PYTHON) scripts/trigger_eval.py --description-file evals/improved_description.txt --cases evals/trigger_cases.json --baseline-description-file evals/baseline_description.txt

eval-suite:
	$(PYTHON) scripts/run_eval_suite.py

route-scorecard:
	$(PYTHON) scripts/build_confusion_matrix.py --history-snapshot-output evals/history/2026-04-01-route-scorecard-foundation.json --snapshot-date 2026-04-01

route-confusion-check:
	$(PYTHON) tests/verify_route_confusion.py

description-optimization:
	$(PYTHON) scripts/run_description_optimization_suite.py

judge-blind-eval:
	$(PYTHON) scripts/judge_blind_eval.py --description-file SKILL.md --cases evals/blind_holdout/trigger_cases.json --semantic-config evals/semantic_config.json

description-optimization-check:
	$(PYTHON) tests/verify_description_optimization.py

promotion-check:
	$(PYTHON) tests/verify_promotion_checker.py

yao-cli-check:
	$(PYTHON) tests/verify_yao_cli.py

skill-overview-check:
	$(PYTHON) tests/verify_skill_overview.py

skill-report-metrics-check:
	$(PYTHON) tests/verify_skill_report_metrics.py

skill-report-charts-check:
	$(PYTHON) tests/verify_skill_report_charts.py

skill-ir-check:
	$(PYTHON) tests/verify_skill_ir.py

compiler-check:
	$(PYTHON) tests/verify_compile_skill.py

output-eval-check:
	$(PYTHON) tests/verify_output_eval_lab.py

output-execution-check:
	$(PYTHON) tests/verify_output_execution_runs.py

output-review-adjudication-check:
	$(PYTHON) tests/verify_output_review_adjudication.py

runtime-conformance-check:
	$(PYTHON) tests/verify_conformance_suite.py

runtime-permission-check:
	$(PYTHON) tests/verify_runtime_permission_probes.py

trust-check:
	$(PYTHON) tests/verify_trust_check.py

skill-atlas-check:
	$(PYTHON) tests/verify_skill_atlas.py

registry-audit-check:
	$(PYTHON) tests/verify_registry_audit.py

package-verify-check:
	$(PYTHON) tests/verify_package_verification.py

install-simulation-check:
	$(PYTHON) tests/verify_install_simulation.py

upgrade-check:
	$(PYTHON) tests/verify_upgrade_check.py

review-viewer-check:
	$(PYTHON) tests/verify_review_viewer.py

review-studio-check:
	$(PYTHON) tests/verify_review_studio.py

feedback-check:
	$(PYTHON) tests/verify_feedback.py

adoption-drift-check:
	$(PYTHON) tests/verify_adoption_drift.py

review-waivers-check:
	$(PYTHON) tests/verify_review_waivers.py

review-annotations-check:
	$(PYTHON) tests/verify_review_annotations.py

baseline-compare-check:
	$(PYTHON) tests/verify_baseline_compare.py

reference-scan-check:
	$(PYTHON) tests/verify_reference_scan.py

github-benchmark-scan-check:
	$(PYTHON) tests/verify_github_benchmark_scan.py

intent-confidence-check:
	$(PYTHON) tests/verify_intent_confidence.py

reference-synthesis-check:
	$(PYTHON) tests/verify_reference_synthesis.py

output-risk-profile-check:
	$(PYTHON) tests/verify_output_risk_profile.py

artifact-design-profile-check:
	$(PYTHON) tests/verify_artifact_design_profile.py

prompt-quality-profile-check:
	$(PYTHON) tests/verify_prompt_quality_profile.py

system-model-check:
	$(PYTHON) tests/verify_system_model.py

iteration-directions-check:
	$(PYTHON) tests/verify_iteration_directions.py

description-drift-history:
	$(PYTHON) scripts/render_description_drift_history.py

iteration-ledger:
	$(PYTHON) scripts/render_iteration_ledger.py

results-panel:
	$(PYTHON) scripts/render_eval_dashboard.py

regression-history:
	$(PYTHON) scripts/render_regression_history.py

context-reports:
	$(PYTHON) scripts/render_context_reports.py

portability-report:
	$(PYTHON) scripts/render_portability_report.py

portability-check:
	$(PYTHON) tests/verify_portability_report.py

failure-regression-check:
	$(PYTHON) tests/verify_failure_regressions.py

package-check:
	$(PYTHON) scripts/cross_packager.py . --platform openai --platform claude --platform generic --platform vscode --expectations evals/packaging_expectations.json --output-dir dist --zip

package-failure-check:
	$(PYTHON) tests/verify_packager_failures.py

security-boundary-check:
	$(PYTHON) tests/verify_security_boundaries.py

local-install-sync-check:
	$(PYTHON) tests/verify_local_install_sync.py

snapshot-check:
	$(PYTHON) tests/verify_adapter_snapshots.py

validate:
	$(PYTHON) scripts/validate_skill.py .

lint:
	$(PYTHON) scripts/lint_skill.py .

governance-check:
	$(PYTHON) scripts/governance_check.py . --require-manifest

resource-boundary-check:
	$(PYTHON) scripts/resource_boundary_check.py .

quality-check:
	$(PYTHON) tests/verify_quality_checks.py

sync-local-install: package-check
	$(PYTHON) scripts/sync_local_install.py --install-dir "$(LOCAL_SKILL_INSTALL_DIR)"

sync-active-install: package-check
	$(PYTHON) scripts/sync_local_install.py --install-dir "$(ACTIVE_SKILL_INSTALL_DIR)"

test: eval eval-suite route-scorecard route-confusion-check description-optimization description-optimization-check promotion-check yao-cli-check skill-overview-check skill-report-metrics-check skill-report-charts-check skill-ir-check compiler-check output-eval-check output-execution-check output-review-adjudication-check runtime-conformance-check runtime-permission-check trust-check skill-atlas-check registry-audit-check package-verify-check install-simulation-check upgrade-check review-viewer-check review-studio-check feedback-check adoption-drift-check review-waivers-check review-annotations-check baseline-compare-check reference-scan-check github-benchmark-scan-check intent-confidence-check reference-synthesis-check output-risk-profile-check artifact-design-profile-check prompt-quality-profile-check system-model-check iteration-directions-check description-drift-history iteration-ledger regression-history context-reports portability-report portability-check failure-regression-check package-check package-failure-check security-boundary-check local-install-sync-check snapshot-check validate lint governance-check resource-boundary-check quality-check

ci-test:
	$(PYTHON) scripts/ci_test.py

clean:
	rm -rf dist tests/tmp tests/tmp_snapshot tests/tmp_cli tests/tmp_skill_overview tests/tmp_skill_report_metrics tests/tmp_skill_report_charts tests/tmp_skill_ir tests/tmp_compile_skill tests/tmp_output_eval tests/tmp_output_execution tests/tmp_output_review_adjudication tests/tmp_conformance tests/tmp_runtime_permission tests/tmp_trust tests/tmp_skill_atlas tests/tmp_registry tests/tmp_package_verification tests/tmp_install_simulation tests/tmp_upgrade_check tests/tmp_reference_scan tests/tmp_iteration_directions tests/tmp_review_viewer tests/tmp_review_studio tests/tmp_feedback tests/tmp_adoption_drift tests/tmp_review_waivers tests/tmp_review_annotations tests/tmp_github_benchmark_scan tests/tmp_intent_confidence tests/tmp_reference_synthesis tests/tmp_output_risk_profile tests/tmp_artifact_design_profile tests/tmp_prompt_quality_profile tests/tmp_system_model tests/tmp_security tests/tmp_baseline_compare.json tests/tmp_baseline_compare.md
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
