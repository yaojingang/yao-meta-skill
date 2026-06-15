from pathlib import Path
from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_evidence_consistency.py to verify release evidence refresh instructions."

SOURCE_REFRESH_HEADER = "After source changes that affect scripts"
CLEAN_LOCK_HEADER = "For final release evidence"
CLEAN_LOCK_END = "If `reports/benchmark_reproducibility.json`"

SOURCE_REFRESH_REPORT_COMMANDS = [
    'python3 scripts/run_output_execution.py --runner-command \'["python3","scripts/local_output_eval_runner.py"]\'',
    'python3 scripts/compile_skill.py . --generated-at "$GENERATED_AT"',
    "python3 scripts/cross_packager.py . --platform openai --platform claude --platform generic --platform vscode --expectations evals/packaging_expectations.json --output-dir dist --zip",
    'python3 scripts/simulate_install.py . --package-dir dist --install-root dist/install-simulation --output-json reports/install_simulation.json --output-md reports/install_simulation.md --generated-at "$GENERATED_AT"',
    "python3 scripts/trust_check.py . --output-json reports/security_trust_report.json --output-md reports/security_trust_report.md",
    'python3 scripts/registry_audit.py . --generated-at "$GENERATED_AT"',
    'python3 scripts/verify_package.py . --package-dir dist --expectations evals/packaging_expectations.json --registry-json reports/registry_audit.json --output-json reports/package_verification.json --output-md reports/package_verification.md --require-zip --generated-at "$GENERATED_AT"',
    'python3 scripts/upgrade_check.py . --previous-package-json registry/examples/yao-meta-skill-1.0.0.json --current-package-json reports/registry_audit.json --output-json reports/upgrade_check.json --output-md reports/upgrade_check.md --generated-at "$GENERATED_AT"',
    'python3 scripts/render_adoption_drift_report.py . --generated-at "$GENERATED_AT"',
    'python3 scripts/render_architecture_maintainability.py . --generated-at "$GENERATED_AT"',
    'python3 scripts/python_compat_check.py . --generated-at "$GENERATED_AT"',
    "python3 scripts/probe_runtime_permissions.py . --package-dir dist",
    'python3 scripts/render_review_waivers.py . --generated-at "$GENERATED_AT"',
    "python3 scripts/render_review_annotations.py .",
    'python3 scripts/build_skill_atlas.py --workspace-root . --output-dir skill_atlas --report-html reports/skill_atlas.html --report-json reports/skill_atlas.json --today "$GENERATED_AT"',
    'python3 scripts/render_world_class_evidence_plan.py . --generated-at "$GENERATED_AT"',
    'python3 scripts/render_world_class_evidence_ledger.py . --generated-at "$GENERATED_AT"',
    'python3 scripts/render_world_class_evidence_intake.py . --generated-at "$GENERATED_AT"',
    'python3 scripts/render_world_class_submission_review.py . --generated-at "$GENERATED_AT"',
    'python3 scripts/render_world_class_operator_runbook.py . --generated-at "$GENERATED_AT"',
    'python3 scripts/render_world_class_claim_guard.py . --generated-at "$GENERATED_AT"',
    'python3 scripts/render_daily_skillops_report.py . --generated-at "$GENERATED_AT"',
    'python3 scripts/render_weekly_curator_report.py . --generated-at "$GENERATED_AT"',
    'python3 scripts/render_skill_os2_audit.py . --generated-at "$GENERATED_AT"',
    'python3 scripts/render_skill_os2_coverage.py . --generated-at "$GENERATED_AT"',
    'python3 scripts/render_context_reports.py --generated-at "$GENERATED_AT"',
    'python3 scripts/render_benchmark_reproducibility.py . --generated-at "$GENERATED_AT"',
    "python3 scripts/render_skill_overview.py .",
    "python3 scripts/render_skill_interpretation.py .",
    "python3 scripts/render_review_viewer.py .",
    'python3 scripts/render_world_class_preflight.py . --generated-at "$GENERATED_AT"',
    "python3 scripts/render_review_studio.py . --output-html reports/review-studio.html --output-json reports/review-studio.json",
    'python3 scripts/render_evidence_consistency.py . --generated-at "$GENERATED_AT"',
]
CLEAN_LOCK_REPORT_COMMANDS = [
    'python3 scripts/render_context_reports.py --generated-at "$GENERATED_AT"',
    'python3 scripts/render_benchmark_reproducibility.py . --generated-at "$GENERATED_AT"',
    'python3 scripts/render_daily_skillops_report.py . --generated-at "$GENERATED_AT"',
    'python3 scripts/render_weekly_curator_report.py . --generated-at "$GENERATED_AT"',
    "python3 scripts/render_skill_overview.py .",
    "python3 scripts/render_skill_interpretation.py .",
    "python3 scripts/render_review_viewer.py .",
    'python3 scripts/render_world_class_preflight.py . --generated-at "$GENERATED_AT"',
    "python3 scripts/render_review_studio.py . --output-html reports/review-studio.html --output-json reports/review-studio.json",
    'python3 scripts/render_evidence_consistency.py . --generated-at "$GENERATED_AT"',
]


def section_between(text: str, start: str, end: str) -> str:
    if start not in text:
        return ""
    section = text.split(start, 1)[1]
    if end in section:
        section = section.split(end, 1)[0]
    return section


def command_presence(section: str, commands: list[str]) -> dict[str, bool]:
    return {command: command in section for command in commands}


def build_release_evidence_flow_check(skill_dir: Path) -> dict[str, Any]:
    agents_path = skill_dir / "AGENTS.md"
    agents_text = agents_path.read_text(encoding="utf-8") if agents_path.exists() else ""
    source_refresh = section_between(agents_text, SOURCE_REFRESH_HEADER, CLEAN_LOCK_HEADER)
    clean_lock = section_between(agents_text, CLEAN_LOCK_HEADER, CLEAN_LOCK_END)
    expected = {
        "AGENTS.md": True,
        "source_refresh_section": True,
        "clean_lock_section": True,
        "source_refresh_commands": {command: True for command in SOURCE_REFRESH_REPORT_COMMANDS},
        "clean_lock_commands": {command: True for command in CLEAN_LOCK_REPORT_COMMANDS},
    }
    actual = {
        "AGENTS.md": agents_path.exists(),
        "source_refresh_section": bool(source_refresh),
        "clean_lock_section": bool(clean_lock),
        "source_refresh_commands": command_presence(source_refresh, SOURCE_REFRESH_REPORT_COMMANDS),
        "clean_lock_commands": command_presence(clean_lock, CLEAN_LOCK_REPORT_COMMANDS),
    }
    return {
        "key": "release-evidence-flow-covers-first-class-reports",
        "label": "Release evidence flow covers first-class reports",
        "status": "pass" if expected == actual else "fail",
        "expected": expected,
        "actual": actual,
        "paths": [
            "AGENTS.md",
            "reports/output_execution_runs.json",
            "reports/install_simulation.json",
            "reports/security_trust_report.json",
            "reports/registry_audit.json",
            "reports/package_verification.json",
            "reports/upgrade_check.json",
            "reports/adoption_drift_report.json",
            "reports/architecture_maintainability.json",
            "reports/python_compatibility.json",
            "reports/runtime_permission_probes.json",
            "reports/review_waivers.json",
            "reports/review_annotations.json",
            "reports/skill_atlas.json",
            "reports/skill_os2_audit.json",
            "reports/skill_os2_coverage.json",
            "reports/context_budget.json",
            "reports/context_budget_summary.json",
            "reports/benchmark_reproducibility.json",
            "reports/skill-overview.json",
            "reports/skill-interpretation.json",
            "reports/review-viewer.json",
            "reports/world_class_evidence_preflight.json",
            "reports/skillops/daily",
            "reports/skillops/weekly",
            "reports/review-studio.json",
            "reports/evidence_consistency.json",
        ],
        "detail": (
            "Release refresh and clean-lock instructions must regenerate every first-class report "
            "before evidence consistency can be trusted."
        ),
    }
