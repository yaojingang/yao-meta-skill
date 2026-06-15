#!/usr/bin/env python3
import argparse
import ast
import json
from datetime import date
from pathlib import Path
from typing import Any

from evidence_consistency_release import build_release_evidence_flow_check
from evidence_consistency_world_class import build_world_class_workflow_check
from skill_ir_paths import find_skill_ir_path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Renders a cross-report evidence consistency gate for generated Skill OS reports."
REQUIRED_REPORTS = {
    "benchmark": "reports/benchmark_reproducibility.json",
    "overview": "reports/skill-overview.json",
    "interpretation": "reports/skill-interpretation.json",
    "adoption": "reports/adoption_drift_report.json",
    "world_class_ledger": "reports/world_class_evidence_ledger.json",
    "world_class_plan": "reports/world_class_evidence_plan.json",
    "world_class_intake": "reports/world_class_evidence_intake.json",
    "world_class_preflight": "reports/world_class_evidence_preflight.json",
    "world_class_submission_review": "reports/world_class_submission_review.json",
    "world_class_operator_runbook": "reports/world_class_operator_runbook.json",
    "skill_os2_coverage": "reports/skill_os2_coverage.json",
    "review_studio": "reports/review-studio.json",
    "package_verification": "reports/package_verification.json",
    "install_simulation": "reports/install_simulation.json",
    "trust": "reports/security_trust_report.json",
    "context_budget": "reports/context_budget.json",
    "world_class_claim_guard": "reports/world_class_claim_guard.json",
}
REQUIRED_TEXT_REPORTS = {
    "skill_os2_review": "reports/skill-os-2-review.md",
}
BENCHMARK_SUMMARY_KEYS = [
    "release_lock_ready",
    "required_artifact_count",
    "missing_artifact_count",
    "source_contract_sha256",
    "archive_sha256",
    "world_class_ledger_pending_count",
    "world_class_source_check_count",
    "world_class_source_pass_count",
    "world_class_source_blocked_count",
    "public_claim_ready",
    "public_claim_blocker_count",
]
ADOPTION_SUMMARY_KEYS = [
    "event_count",
    "adoption_sample_count",
    "activation_count",
    "accepted_count",
    "adoption_rate",
    "risk_band",
    "event_types",
    "source_types",
]
LEDGER_SUMMARY_KEYS = [
    "ledger_entry_count",
    "accepted_count",
    "pending_count",
    "human_pending_count",
    "external_pending_count",
    "source_check_count",
    "source_pass_count",
    "source_blocked_count",
    "ready_to_claim_world_class",
    "decision",
]
LOCKSTEP_SECTIONS = [
    "scorecard",
    "capability_profile",
    "principle_model",
    "contract_boundary",
    "quality_review",
    "risk_governance",
    "world_class_readiness",
    "package_assets",
    "iteration_roadmap",
]


def load_json(path: Path) -> tuple[dict[str, Any], str | None]:
    if not path.exists():
        return {}, "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, f"invalid-json: {exc}"
    if not isinstance(payload, dict):
        return {}, "json-root-not-object"
    return payload, None


def load_text(path: Path) -> tuple[str, str | None]:
    if not path.exists():
        return "", "missing"
    return path.read_text(encoding="utf-8"), None


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


def rel_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def nested(payload: dict[str, Any], path: list[str], default: Any = None) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def scanned_surface_paths(payload: dict[str, Any]) -> set[str]:
    surfaces = payload.get("scanned_surfaces")
    if not isinstance(surfaces, list):
        return set()
    paths: set[str] = set()
    for item in surfaces:
        if isinstance(item, dict) and isinstance(item.get("path"), str):
            paths.add(item["path"])
        elif isinstance(item, str):
            paths.add(item)
    return paths


def as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def add_check(
    checks: list[dict[str, Any]],
    *,
    key: str,
    label: str,
    status: str,
    expected: Any,
    actual: Any,
    paths: list[str],
    detail: str,
) -> None:
    checks.append(
        {
            "key": key,
            "label": label,
            "status": status,
            "expected": expected,
            "actual": actual,
            "paths": paths,
            "detail": detail,
        }
    )


def compare_values(
    checks: list[dict[str, Any]],
    *,
    key: str,
    label: str,
    expected: Any,
    actual: Any,
    paths: list[str],
    detail: str,
) -> None:
    add_check(
        checks,
        key=key,
        label=label,
        status="pass" if expected == actual else "fail",
        expected=expected,
        actual=actual,
        paths=paths,
        detail=detail,
    )


def compare_summary_keys(
    checks: list[dict[str, Any]],
    *,
    key_prefix: str,
    label: str,
    source_summary: dict[str, Any],
    embedded_summary: dict[str, Any],
    keys: list[str],
    paths: list[str],
) -> None:
    expected = {key: source_summary.get(key) for key in keys}
    actual = {key: embedded_summary.get(key) for key in keys}
    compare_values(
        checks,
        key=key_prefix,
        label=label,
        expected=expected,
        actual=actual,
        paths=paths,
        detail="Selected summary fields must match exactly across generated reports.",
    )


def gate_by_key(review_studio: dict[str, Any], key: str) -> dict[str, Any]:
    gates = review_studio.get("gates")
    if not isinstance(gates, list):
        return {}
    for item in gates:
        if isinstance(item, dict) and item.get("key") == key:
            return item
    return {}


def report_contract(payload: dict[str, Any]) -> dict[str, Any]:
    contract = payload.get("report_contract")
    return contract if isinstance(contract, dict) else {}


def build_report(skill_dir: Path, generated_at: str) -> dict[str, Any]:
    reports: dict[str, dict[str, Any]] = {}
    text_reports: dict[str, str] = {}
    checks: list[dict[str, Any]] = []
    load_failures: dict[str, str] = {}
    for name, relative in REQUIRED_REPORTS.items():
        payload, failure = load_json(skill_dir / relative)
        reports[name] = payload
        if failure:
            load_failures[relative] = failure
    for name, relative in REQUIRED_TEXT_REPORTS.items():
        text, failure = load_text(skill_dir / relative)
        text_reports[name] = text
        if failure:
            load_failures[relative] = failure
    add_check(
        checks,
        key="required-report-artifacts",
        label="Required report artifacts are readable",
        status="pass" if not load_failures else "fail",
        expected="all required JSON and Markdown reports exist and parse",
        actual=load_failures or "all readable",
        paths=list(REQUIRED_REPORTS.values()) + list(REQUIRED_TEXT_REPORTS.values()),
        detail="The consistency gate can only be trusted when every source JSON report parses and every source Markdown report is readable.",
    )
    checks.append(build_release_evidence_flow_check(skill_dir))

    benchmark = reports["benchmark"]
    overview = reports["overview"]
    interpretation = reports["interpretation"]
    adoption = reports["adoption"]
    ledger = reports["world_class_ledger"]
    world_class_plan = reports["world_class_plan"]
    world_class_intake = reports["world_class_intake"]
    world_class_preflight = reports["world_class_preflight"]
    world_class_submission_review = reports["world_class_submission_review"]
    world_class_operator_runbook = reports["world_class_operator_runbook"]
    coverage = reports["skill_os2_coverage"]
    review_studio = reports["review_studio"]
    package_verification = reports["package_verification"]
    install_simulation = reports["install_simulation"]
    trust = reports["trust"]
    context_budget = reports["context_budget"]
    claim_guard = reports["world_class_claim_guard"]

    benchmark_summary = nested(benchmark, ["summary"], {})
    adoption_summary = nested(adoption, ["summary"], {})
    ledger_summary = nested(ledger, ["summary"], {})
    coverage_summary = nested(coverage, ["summary"], {})
    studio_summary = nested(review_studio, ["summary"], {})
    package_summary = nested(package_verification, ["summary"], {})
    install_summary = nested(install_simulation, ["summary"], {})
    trust_summary = nested(trust, ["summary"], {})
    context_stats = nested(context_budget, ["stats"], {})
    claim_guard_summary = nested(claim_guard, ["summary"], {})
    preflight_summary = nested(world_class_preflight, ["summary"], {})
    context_governance = (
        context_stats.get("deferred_resource_governance", {}) if isinstance(context_stats, dict) else {}
    )
    if not isinstance(context_governance, dict):
        context_governance = {}
    large_deferred_dirs = context_stats.get("large_deferred_resource_dirs", []) if isinstance(context_stats, dict) else []
    top_deferred = "none"
    if isinstance(large_deferred_dirs, list) and large_deferred_dirs:
        first = large_deferred_dirs[0] if isinstance(large_deferred_dirs[0], dict) else {}
        top_deferred = f"{first.get('path', 'resource')} {first.get('estimated_tokens', 'n/a')}"
    context_expected_status = "pass" if context_budget.get("ok") else "block"
    if context_budget.get("warnings") and context_expected_status == "pass":
        context_expected_status = "warn"
    context_expected_detail = (
        f"initial load {context_stats.get('estimated_initial_load_tokens', 'n/a')}/"
        f"{context_stats.get('context_budget_limit', 'n/a')}; "
        f"deferred {context_stats.get('deferred_resource_tokens', 'n/a')}/"
        f"{context_stats.get('deferred_resource_warn_threshold', 'n/a')}; "
        f"top deferred {top_deferred}; "
        f"resource governance {context_governance.get('status', 'unknown')}; "
        f"quality density {context_stats.get('quality_density', 'n/a')}"
    )
    context_gate = gate_by_key(review_studio, "context-budget")
    compare_values(
        checks,
        key="review-studio-context-budget-mirror",
        label="Review Studio mirrors context budget governance",
        expected={
            "status": context_expected_status,
            "detail": context_expected_detail,
            "evidence": REQUIRED_REPORTS["context_budget"],
        },
        actual={
            "status": context_gate.get("status"),
            "detail": context_gate.get("detail"),
            "evidence": context_gate.get("evidence"),
        },
        paths=[REQUIRED_REPORTS["context_budget"], REQUIRED_REPORTS["review_studio"]],
        detail=(
            "Review Studio must not keep stale context warnings after context reports prove large deferred resources are governed."
        ),
    )
    if isinstance(benchmark_summary, dict):
        compare_values(
            checks,
            key="benchmark-release-lock-self-consistency",
            label="Benchmark release lock matches git dirty state",
            expected=not bool(nested(benchmark, ["git_status", "dirty"], True)),
            actual=benchmark_summary.get("release_lock_ready"),
            paths=[REQUIRED_REPORTS["benchmark"]],
            detail="The benchmark release lock must reflect the generation-time git dirty flag.",
        )
    skill_name = str(overview.get("name") or nested(review_studio, ["data", "frontmatter", "name"]) or skill_dir.name)
    expected_skill_ir_path = find_skill_ir_path(skill_dir, skill_name, require_schema=True)
    expected_skill_ir = {
        "source_path": expected_skill_ir_path,
        "exists": bool(expected_skill_ir_path and (skill_dir / expected_skill_ir_path).exists()),
        "schema_version": load_json(skill_dir / expected_skill_ir_path)[0].get("schema_version")
        if expected_skill_ir_path
        else "",
    }
    actual_skill_ir = {
        "overview_source_path": nested(overview, ["skill_ir", "source_path"], ""),
        "interpretation_source_path": nested(interpretation, ["skill_ir", "source_path"], ""),
        "review_studio_evidence_path": nested(review_studio, ["evidence_paths", "skill_ir"], ""),
        "overview_deliverable": expected_skill_ir_path in nested(overview, ["skill_summary", "deliverables"], []),
        "interpretation_deliverable": expected_skill_ir_path
        in nested(interpretation, ["skill_summary", "deliverables"], []),
    }
    compare_values(
        checks,
        key="skill-ir-evidence-path-contract",
        label="Human-facing reports expose the canonical Skill IR artifact",
        expected={
            "overview_source_path": expected_skill_ir["source_path"],
            "interpretation_source_path": expected_skill_ir["source_path"],
            "review_studio_evidence_path": expected_skill_ir["source_path"],
            "overview_deliverable": True,
            "interpretation_deliverable": True,
            "exists": True,
            "schema_version": "2.0.0",
        },
        actual={**actual_skill_ir, **{key: expected_skill_ir[key] for key in ("exists", "schema_version")}},
        paths=[
            REQUIRED_REPORTS["overview"],
            REQUIRED_REPORTS["interpretation"],
            REQUIRED_REPORTS["review_studio"],
            expected_skill_ir_path or "skill-ir/examples",
        ],
        detail="Skill IR is the 2.0 platform-neutral semantic source, so user-facing reports must link to the artifact that actually exists.",
    )
    for report_key, payload in [("overview", overview), ("interpretation", interpretation)]:
        embedded_benchmark = nested(payload, ["benchmark_reproducibility"], {})
        compare_values(
            checks,
            key=f"{report_key}-benchmark-commit",
            label=f"{report_key} embeds the benchmark commit",
            expected=benchmark.get("commit"),
            actual=nested(embedded_benchmark, ["commit"]),
            paths=[REQUIRED_REPORTS["benchmark"], REQUIRED_REPORTS[report_key]],
            detail="Human-facing reports must point to the same benchmark release-lock commit.",
        )
        compare_summary_keys(
            checks,
            key_prefix=f"{report_key}-benchmark-summary",
            label=f"{report_key} embeds benchmark summary fields",
            source_summary=benchmark_summary if isinstance(benchmark_summary, dict) else {},
            embedded_summary=nested(embedded_benchmark, ["summary"], {}),
            keys=BENCHMARK_SUMMARY_KEYS,
            paths=[REQUIRED_REPORTS["benchmark"], REQUIRED_REPORTS[report_key]],
        )
        compare_summary_keys(
            checks,
            key_prefix=f"{report_key}-adoption-summary",
            label=f"{report_key} embeds adoption drift summary fields",
            source_summary=adoption_summary if isinstance(adoption_summary, dict) else {},
            embedded_summary=nested(payload, ["adoption_drift", "summary"], {}),
            keys=ADOPTION_SUMMARY_KEYS,
            paths=[REQUIRED_REPORTS["adoption"], REQUIRED_REPORTS[report_key]],
        )
        compare_summary_keys(
            checks,
            key_prefix=f"{report_key}-world-class-ledger-summary",
            label=f"{report_key} embeds world-class ledger summary fields",
            source_summary=ledger_summary if isinstance(ledger_summary, dict) else {},
            embedded_summary=nested(payload, ["world_class_evidence_ledger", "summary"], {}),
            keys=LEDGER_SUMMARY_KEYS,
            paths=[REQUIRED_REPORTS["world_class_ledger"], REQUIRED_REPORTS[report_key]],
        )
        readiness_expected = {
            "ready": ledger_summary.get("ready_to_claim_world_class") if isinstance(ledger_summary, dict) else None,
            "decision": ledger_summary.get("decision") if isinstance(ledger_summary, dict) else None,
            "pending_count": ledger_summary.get("pending_count") if isinstance(ledger_summary, dict) else None,
            "accepted_count": ledger_summary.get("accepted_count") if isinstance(ledger_summary, dict) else None,
            "source_check_count": ledger_summary.get("source_check_count") if isinstance(ledger_summary, dict) else None,
            "source_pass_count": ledger_summary.get("source_pass_count") if isinstance(ledger_summary, dict) else None,
        }
        readiness = nested(payload, ["world_class_readiness"], {})
        readiness_actual = {key: readiness.get(key) if isinstance(readiness, dict) else None for key in readiness_expected}
        compare_values(
            checks,
            key=f"{report_key}-world-class-readiness",
            label=f"{report_key} derives readiness from the ledger",
            expected=readiness_expected,
            actual=readiness_actual,
            paths=[REQUIRED_REPORTS["world_class_ledger"], REQUIRED_REPORTS[report_key]],
            detail="Readiness summaries must be derived from the evidence ledger, not hand-maintained copy.",
        )

    for section in LOCKSTEP_SECTIONS:
        compare_values(
            checks,
            key=f"overview-interpretation-lockstep-{section.replace('_', '-')}",
            label=f"Overview and interpretation share {section}",
            expected=overview.get(section),
            actual=interpretation.get(section),
            paths=[REQUIRED_REPORTS["overview"], REQUIRED_REPORTS["interpretation"]],
            detail="The first-class interpretation report must stay in lockstep with the canonical overview model.",
        )

    for report_key, expected_html in [
        ("overview", "reports/skill-overview.html"),
        ("interpretation", "reports/skill-interpretation.html"),
    ]:
        contract = report_contract(reports[report_key])
        expected = {
            "schema_version": "2.0",
            "default_language": "zh-CN",
            "layout": "kami-white-audit-v2",
            "html_report": expected_html,
            "html_exists": True,
        }
        actual = {
            "schema_version": contract.get("schema_version"),
            "default_language": contract.get("default_language"),
            "layout": contract.get("layout"),
            "html_report": contract.get("html_report"),
            "html_exists": (skill_dir / expected_html).exists(),
        }
        compare_values(
            checks,
            key=f"{report_key}-html-contract",
            label=f"{report_key} has a stable HTML contract",
            expected=expected,
            actual=actual,
            paths=[REQUIRED_REPORTS[report_key], expected_html],
            detail="Report output paths and language defaults are part of the user-facing contract.",
        )

    if isinstance(ledger_summary, dict):
        expected_boundary = {
            "world_class_evidence_pending_count": ledger_summary.get("pending_count"),
            "public_world_class_ready": ledger_summary.get("ready_to_claim_world_class"),
        }
        actual_boundary = {
            "world_class_evidence_pending_count": coverage_summary.get("world_class_evidence_pending_count")
            if isinstance(coverage_summary, dict)
            else None,
            "public_world_class_ready": coverage_summary.get("public_world_class_ready")
            if isinstance(coverage_summary, dict)
            else None,
        }
        compare_values(
            checks,
            key="coverage-world-class-boundary",
            label="Coverage report mirrors world-class evidence boundary",
            expected=expected_boundary,
            actual=actual_boundary,
            paths=[REQUIRED_REPORTS["world_class_ledger"], REQUIRED_REPORTS["skill_os2_coverage"]],
            detail="Blueprint coverage can be locally complete while public world-class evidence remains pending.",
        )
        benchmark_boundary = {
            "world_class_ledger_pending_count": ledger_summary.get("pending_count"),
            "world_class_source_check_count": ledger_summary.get("source_check_count"),
            "world_class_source_pass_count": ledger_summary.get("source_pass_count"),
            "world_class_source_blocked_count": ledger_summary.get("source_blocked_count"),
            "public_claim_ready": ledger_summary.get("ready_to_claim_world_class"),
        }
        actual_benchmark_boundary = {
            key: benchmark_summary.get(key) if isinstance(benchmark_summary, dict) else None
            for key in benchmark_boundary
        }
        compare_values(
            checks,
            key="benchmark-world-class-boundary",
            label="Benchmark report mirrors world-class evidence boundary",
            expected=benchmark_boundary,
            actual=actual_benchmark_boundary,
            paths=[REQUIRED_REPORTS["world_class_ledger"], REQUIRED_REPORTS["benchmark"]],
            detail="Benchmark reproducibility must not overstate public claim readiness.",
        )
        preflight_boundary = {
            "pending_count": ledger_summary.get("pending_count"),
            "source_check_count": ledger_summary.get("source_check_count"),
            "source_pass_count": ledger_summary.get("source_pass_count"),
            "source_blocked_count": ledger_summary.get("source_blocked_count"),
            "ready_to_claim_world_class": ledger_summary.get("ready_to_claim_world_class"),
            "preflight_counts_as_evidence": False,
            "credential_value_exposed": False,
        }
        actual_preflight_boundary = {
            key: preflight_summary.get(key) if isinstance(preflight_summary, dict) else None
            for key in preflight_boundary
        }
        compare_values(
            checks,
            key="preflight-world-class-boundary",
            label="Preflight mirrors ledger without accepting evidence",
            expected=preflight_boundary,
            actual=actual_preflight_boundary,
            paths=[REQUIRED_REPORTS["world_class_ledger"], REQUIRED_REPORTS["world_class_preflight"]],
            detail="Collection preflight may help operators gather evidence, but it must not print secrets or change world-class readiness.",
        )
        preflight_submissions = (
            world_class_preflight.get("submissions", {})
            if isinstance(world_class_preflight.get("submissions", {}), dict)
            else {}
        )
        preflight_commands = (
            preflight_submissions.get("commands", {})
            if isinstance(preflight_submissions.get("commands", {}), dict)
            else {}
        )
        preflight_role_contract = (
            preflight_submissions.get("artifact_role_contract", {})
            if isinstance(preflight_submissions.get("artifact_role_contract", {}), dict)
            else {}
        )
        preflight_roles = {
            str(item.get("role", "")): item
            for item in preflight_role_contract.get("roles", [])
            if isinstance(item, dict)
        }
        default_submissions_dir = "evidence/world_class/submissions"
        expected_preflight_handoff = {
            "directory": default_submissions_dir,
            "drafts_count_as_evidence": False,
            "preflight_counts_submission_as_completion": False,
            "html_report": "reports/world_class_evidence_preflight.html",
            "html_exists": True,
            "prepare_submission": f"python3 scripts/yao.py world-class-submission-kit . --output-dir {default_submissions_dir}",
            "prepare_prefilled_submission": (
                f"python3 scripts/yao.py world-class-submission-kit . --output-dir {default_submissions_dir} "
                "--prefill-artifacts"
            ),
            "validate_intake": f"python3 scripts/yao.py world-class-intake . --submissions-dir {default_submissions_dir}",
            "submission_review": f"python3 scripts/yao.py world-class-submission-review . --submissions-dir {default_submissions_dir}",
            "refresh_ledger": f"python3 scripts/yao.py world-class-ledger . --submissions-dir {default_submissions_dir}",
            "guard_claim": "python3 scripts/yao.py world-class-claim-guard .",
            "artifact_prefill_counts_as_evidence": False,
            "artifact_role_source": "world-class-submission-kit",
            "artifact_role_counts_as_evidence": False,
            "artifact_role_prefill_counts_as_evidence": False,
            "submission_ref_role_present": True,
            "supporting_evidence_role_present": True,
            "submission_ref_copy_to_artifact_refs": True,
            "supporting_evidence_copy_to_artifact_refs": False,
            "submission_ref_total_present": True,
            "supporting_evidence_total_present": True,
        }
        actual_preflight_handoff = {
            "directory": preflight_submissions.get("directory"),
            "drafts_count_as_evidence": preflight_submissions.get("drafts_count_as_evidence"),
            "preflight_counts_submission_as_completion": preflight_submissions.get(
                "preflight_counts_submission_as_completion"
            ),
            "html_report": world_class_preflight.get("artifacts", {}).get("html")
            if isinstance(world_class_preflight.get("artifacts", {}), dict)
            else None,
            "html_exists": (skill_dir / "reports" / "world_class_evidence_preflight.html").exists(),
            "prepare_submission": preflight_commands.get("prepare_submission"),
            "prepare_prefilled_submission": preflight_commands.get("prepare_prefilled_submission"),
            "validate_intake": preflight_commands.get("validate_intake"),
            "submission_review": preflight_commands.get("submission_review"),
            "refresh_ledger": preflight_commands.get("refresh_ledger"),
            "guard_claim": preflight_commands.get("guard_claim"),
            "artifact_prefill_counts_as_evidence": preflight_submissions.get(
                "artifact_prefill_counts_as_evidence"
            ),
            "artifact_role_source": preflight_role_contract.get("role_source"),
            "artifact_role_counts_as_evidence": preflight_role_contract.get("counts_as_evidence"),
            "artifact_role_prefill_counts_as_evidence": preflight_role_contract.get(
                "artifact_prefill_counts_as_evidence"
            ),
            "submission_ref_role_present": "submission-ref" in preflight_roles,
            "supporting_evidence_role_present": "supporting-evidence" in preflight_roles,
            "submission_ref_copy_to_artifact_refs": preflight_roles.get("submission-ref", {}).get(
                "copy_to_artifact_refs"
            ),
            "supporting_evidence_copy_to_artifact_refs": preflight_roles.get("supporting-evidence", {}).get(
                "copy_to_artifact_refs"
            ),
            "submission_ref_total_present": int(preflight_role_contract.get("submission_ref_total_count", 0)) > 0,
            "supporting_evidence_total_present": int(
                preflight_role_contract.get("supporting_evidence_total_count", 0)
            )
            > 0,
        }
        compare_values(
            checks,
            key="preflight-submission-kit-handoff",
            label="Preflight exposes a safe submission-kit handoff",
            expected=expected_preflight_handoff,
            actual=actual_preflight_handoff,
            paths=[REQUIRED_REPORTS["world_class_preflight"], "reports/world_class_evidence_preflight.html"],
            detail=(
                "Preflight must give operators the exact draft, SHA-prefill, intake, review, ledger, "
                "and claim-guard commands without letting drafts, prefill, or submissions count as accepted evidence."
            ),
        )

    public_ready = bool(ledger_summary.get("ready_to_claim_world_class")) if isinstance(ledger_summary, dict) else False
    compare_values(
        checks,
        key="review-studio-no-overclaim",
        label="Review Studio does not overclaim pending world-class evidence",
        expected=False if not public_ready else True,
        actual=studio_summary.get("decision") in {"pass", "release", "ready", "world-class-ready"}
        if isinstance(studio_summary, dict)
        else None,
        paths=[REQUIRED_REPORTS["world_class_ledger"], REQUIRED_REPORTS["review_studio"]],
        detail="When world-class evidence is pending, Review Studio must stay in a review or warning posture.",
    )
    claim_surface_paths = scanned_surface_paths(claim_guard)
    required_claim_surfaces = [
        "README.md",
        "SKILL.md",
        "manifest.json",
        "agents/interface.yaml",
        "evidence/world_class/README.md",
        "security/permission_policy.json",
        "reports/world_class_evidence_ledger.json",
    ]
    optional_claim_surfaces = [
        "dist/manifest.json",
        "dist/targets/openai/adapter.json",
    ]
    required_claim_surfaces.extend(
        path for path in optional_claim_surfaces if (skill_dir / path).exists()
    )
    prohibited_claim_surface_prefixes = [
        "dist/install-simulation/",
        "evidence/world_class/submissions/",
    ]
    json_claim_surface_count = as_int(claim_guard_summary.get("json_claim_surface_count"))
    metadata_claim_surface_count = as_int(claim_guard_summary.get("metadata_claim_surface_count"))
    package_claim_surface_count = as_int(claim_guard_summary.get("package_claim_surface_count"))
    claim_surface_count = as_int(claim_guard_summary.get("claim_surface_count"))
    expected_claim_guard_surface = {
        "overclaim_guard_active": True,
        "violation_count": 0,
        "ledger_ready_to_claim_world_class": ledger_summary.get("ready_to_claim_world_class")
        if isinstance(ledger_summary, dict)
        else None,
        "ledger_pending_count": ledger_summary.get("pending_count") if isinstance(ledger_summary, dict) else None,
        "metadata_covers_json": True,
        "package_surface_minimum": True,
        "claim_surface_covers_package": True,
        "required_surfaces": {path: True for path in required_claim_surfaces},
        "prohibited_surfaces": [],
    }
    actual_claim_guard_surface = {
        "overclaim_guard_active": claim_guard_summary.get("overclaim_guard_active"),
        "violation_count": claim_guard_summary.get("violation_count"),
        "ledger_ready_to_claim_world_class": claim_guard_summary.get("ledger_ready_to_claim_world_class"),
        "ledger_pending_count": claim_guard_summary.get("ledger_pending_count"),
        "metadata_covers_json": (
            metadata_claim_surface_count is not None
            and json_claim_surface_count is not None
            and metadata_claim_surface_count >= json_claim_surface_count
        ),
        "package_surface_minimum": package_claim_surface_count is not None and package_claim_surface_count >= 5,
        "claim_surface_covers_package": (
            claim_surface_count is not None
            and package_claim_surface_count is not None
            and claim_surface_count >= package_claim_surface_count
        ),
        "required_surfaces": {path: path in claim_surface_paths for path in required_claim_surfaces},
        "prohibited_surfaces": sorted(
            path
            for path in claim_surface_paths
            if any(path.startswith(prefix) for prefix in prohibited_claim_surface_prefixes)
        ),
    }
    compare_values(
        checks,
        key="claim-guard-package-runtime-surface",
        label="Claim guard covers package and runtime claim surfaces",
        expected=expected_claim_guard_surface,
        actual=actual_claim_guard_surface,
        paths=[
            REQUIRED_REPORTS["world_class_claim_guard"],
            "manifest.json",
            "agents/interface.yaml",
            "dist/manifest.json",
            "dist/targets/openai/adapter.json",
            "evidence/world_class/README.md",
            "security/permission_policy.json",
            REQUIRED_REPORTS["world_class_ledger"],
        ],
        detail="The overclaim guard must scan package manifests, adapter metadata, security policy, and ledger surfaces before public readiness can be trusted.",
    )
    checks.append(
        build_world_class_workflow_check(
            ledger=ledger,
            world_class_plan=world_class_plan,
            world_class_intake=world_class_intake,
            world_class_submission_review=world_class_submission_review,
            world_class_operator_runbook=world_class_operator_runbook,
            review_studio=review_studio,
            report_paths=REQUIRED_REPORTS,
        )
    )
    skill_os2_review = text_reports.get("skill_os2_review", "")
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
    add_check(
        checks,
        key="skill-os-2-review-current-evidence",
        label="Skill OS 2.0 review summary mirrors current evidence",
        status="pass" if not missing_review_snippets else "fail",
        expected=expected_review_snippets,
        actual="all present" if not missing_review_snippets else {"missing": missing_review_snippets},
        paths=[
            REQUIRED_TEXT_REPORTS["skill_os2_review"],
            REQUIRED_REPORTS["review_studio"],
            REQUIRED_REPORTS["package_verification"],
            REQUIRED_REPORTS["install_simulation"],
            REQUIRED_REPORTS["trust"],
            REQUIRED_REPORTS["context_budget"],
            REQUIRED_REPORTS["benchmark"],
            "scripts/ci_test.py",
        ],
        detail="Manual 2.0 review summaries must not drift from generated gate, package, trust, context, benchmark, or CI evidence.",
    )
    status_counts: dict[str, int] = {"pass": 0, "warn": 0, "fail": 0}
    for check in checks:
        status_counts[check["status"]] = status_counts.get(check["status"], 0) + 1
    summary = {
        "check_count": len(checks),
        "pass_count": status_counts.get("pass", 0),
        "warn_count": status_counts.get("warn", 0),
        "fail_count": status_counts.get("fail", 0),
        "decision": "consistent" if status_counts.get("fail", 0) == 0 else "evidence-drift-detected",
    }
    return {
        "schema_version": "1.0",
        "ok": summary["fail_count"] == 0,
        "generated_at": generated_at,
        "skill_dir": rel_path(skill_dir, ROOT),
        "summary": summary,
        "status_counts": status_counts,
        "checks": checks,
        "artifacts": {
            "json": "reports/evidence_consistency.json",
            "markdown": "reports/evidence_consistency.md",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Evidence Consistency",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- decision: `{summary['decision']}`",
        f"- checks: `{summary['check_count']}`",
        f"- pass: `{summary['pass_count']}`",
        f"- warn: `{summary['warn_count']}`",
        f"- fail: `{summary['fail_count']}`",
        "",
        "This gate compares generated evidence reports against each other. It does not create provider, human, native-client, or permission-enforcement evidence; it only catches drift between reports that already exist.",
        "",
        "## Checks",
        "",
        "| Check | Status | Detail | Paths |",
        "| --- | --- | --- | --- |",
    ]
    for check in report["checks"]:
        paths = ", ".join(f"`{path}`" for path in check["paths"])
        lines.append(
            "| "
            + " | ".join(
                [
                    check["label"].replace("|", "\\|"),
                    f"`{check['status']}`",
                    check["detail"].replace("|", "\\|"),
                    paths.replace("|", "\\|"),
                ]
            )
            + " |"
        )
    failures = [check for check in report["checks"] if check["status"] == "fail"]
    if failures:
        lines.extend(["", "## Failures", ""])
        for check in failures:
            lines.extend(
                [
                    f"### {check['label']}",
                    "",
                    f"- key: `{check['key']}`",
                    f"- expected: `{json.dumps(check['expected'], ensure_ascii=False, sort_keys=True)}`",
                    f"- actual: `{json.dumps(check['actual'], ensure_ascii=False, sort_keys=True)}`",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render cross-report evidence consistency checks.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--output-json", default="reports/evidence_consistency.json")
    parser.add_argument("--output-md", default="reports/evidence_consistency.md")
    parser.add_argument("--generated-at", default=date.today().isoformat())
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    report = build_report(skill_dir, args.generated_at)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    if not output_json.is_absolute():
        output_json = skill_dir / output_json
    if not output_md.is_absolute():
        output_md = skill_dir / output_md
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["ok"] else 2)


if __name__ == "__main__":
    main()
