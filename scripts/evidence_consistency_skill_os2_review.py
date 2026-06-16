import ast
from pathlib import Path
from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = (
    "Imported by render_evidence_consistency.py to keep Skill OS 2.0 review summary drift checks "
    "out of the main consistency renderer."
)


def ci_default_target_count(path: Path) -> int | None:
    if not path.exists():
        return None
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "DEFAULT_TARGETS" for target in node.targets):
            continue
        if isinstance(node.value, (ast.List, ast.Tuple)):
            return len(node.value.elts)
    return None


def build_skill_os2_review_current_evidence_check(
    *,
    skill_dir: Path,
    skill_os2_review: str,
    studio_summary: dict[str, Any],
    trust_summary: dict[str, Any],
    package_summary: dict[str, Any],
    install_summary: dict[str, Any],
    benchmark_summary: dict[str, Any],
    context_stats: dict[str, Any],
    required_text_reports: dict[str, str],
    required_reports: dict[str, str],
) -> dict[str, Any]:
    ci_target_count = ci_default_target_count(skill_dir / "scripts" / "ci_test.py")
    expected_review_snippets = [
        f"score `{studio_summary.get('world_class_score')}`",
        f"`{studio_summary.get('gate_count')}` gates",
        f"`{studio_summary.get('warning_count')}` warnings",
        f"`{trust_summary.get('internal_module_count')}` declared internal modules",
        (
            f"`{trust_summary.get('help_smoke_checked_count')} / {trust_summary.get('help_smoke_checked_count')}` "
            f"CLI help smoke checks passing across `{trust_summary.get('script_count')}` scripts"
        ),
        f"`{package_summary.get('archive_entry_count')}` zip entries",
        f"archive with `{package_summary.get('archive_entry_count')}` entries",
        f"`{install_summary.get('installer_permission_enforced_count')}` installer permission checks enforced",
        f"`{install_summary.get('installer_permission_failure_count')}` permission failures",
        f"`{benchmark_summary.get('required_artifact_count')}` required artifacts",
        f"`{benchmark_summary.get('command_count')}` reproduction commands",
        (
            f"initial load `{context_stats.get('estimated_initial_load_tokens')}/"
            f"{context_stats.get('context_budget_limit')}`"
        ),
        f"target count is `{ci_target_count}`",
    ]
    missing_review_snippets = [snippet for snippet in expected_review_snippets if snippet not in skill_os2_review]
    return {
        "key": "skill-os-2-review-current-evidence",
        "label": "Skill OS 2.0 review summary mirrors current evidence",
        "status": "pass" if not missing_review_snippets else "fail",
        "expected": expected_review_snippets,
        "actual": "all present" if not missing_review_snippets else {"missing": missing_review_snippets},
        "paths": [
            required_text_reports["skill_os2_review"],
            required_reports["review_studio"],
            required_reports["package_verification"],
            required_reports["install_simulation"],
            required_reports["trust"],
            required_reports["context_budget"],
            required_reports["benchmark"],
            "scripts/ci_test.py",
        ],
        "detail": (
            "Manual 2.0 review summaries must not drift from generated gate, package, trust, "
            "context, benchmark, or CI evidence."
        ),
    }
