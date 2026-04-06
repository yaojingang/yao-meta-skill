PYTHON ?= python3

.PHONY: eval eval-suite route-scorecard route-confusion-check description-optimization judge-blind-eval description-optimization-check promotion-check yao-cli-check skill-overview-check reference-scan-check description-drift-history iteration-ledger results-panel regression-history context-reports portability-report portability-check failure-regression-check package-check package-failure-check snapshot-check validate lint governance-check resource-boundary-check quality-check test clean

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

reference-scan-check:
	$(PYTHON) tests/verify_reference_scan.py

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
	$(PYTHON) scripts/cross_packager.py . --platform openai --platform claude --platform generic --expectations evals/packaging_expectations.json --output-dir dist --zip

package-failure-check:
	$(PYTHON) tests/verify_packager_failures.py

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

test: eval eval-suite route-scorecard route-confusion-check description-optimization description-optimization-check promotion-check yao-cli-check skill-overview-check reference-scan-check description-drift-history iteration-ledger regression-history context-reports portability-report portability-check failure-regression-check package-check package-failure-check snapshot-check validate lint governance-check resource-boundary-check quality-check

clean:
	rm -rf dist tests/tmp tests/tmp_snapshot
