PYTHON ?= python3

.PHONY: eval eval-suite package-check package-failure-check snapshot-check validate lint test clean

eval:
	$(PYTHON) scripts/trigger_eval.py --description-file evals/improved_description.txt --cases evals/trigger_cases.json --baseline-description-file evals/baseline_description.txt

eval-suite:
	$(PYTHON) scripts/run_eval_suite.py

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

test: eval eval-suite package-check package-failure-check snapshot-check validate lint

clean:
	rm -rf dist tests/tmp tests/tmp_snapshot
