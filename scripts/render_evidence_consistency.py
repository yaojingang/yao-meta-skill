#!/usr/bin/env python3
import argparse
import json
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

from evidence_consistency_artifact_roles import build_preflight_artifact_role_handoff_checks
from evidence_consistency_core import (
    ADOPTION_SUMMARY_KEYS,
    BENCHMARK_SUMMARY_KEYS,
    LEDGER_SUMMARY_KEYS,
    LOCKSTEP_SECTIONS,
    REQUIRED_REPORTS,
    REQUIRED_TEXT_REPORTS,
    add_check,
    as_int,
    compare_summary_keys,
    compare_values,
    gate_by_key,
    load_json,
    load_text,
    nested,
    rel_path,
    render_markdown,
    report_contract,
    scanned_surface_paths,
)
from evidence_consistency_phase_queue import build_phase_queue_consistency_check
from evidence_consistency_release import build_release_evidence_flow_check
from evidence_consistency_skill_os2_review import build_skill_os2_review_current_evidence_check
from evidence_consistency_world_class import build_world_class_workflow_check
from skill_ir_paths import find_skill_ir_path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Renders a cross-report evidence consistency gate for generated Skill OS reports."


def git_worktree_status(skill_dir: Path) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(skill_dir), "status", "--porcelain=v1", "-uall"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return {"available": False, "clean": None, "changed_file_count": None}
    if proc.returncode != 0:
        return {"available": False, "clean": None, "changed_file_count": None}
    changes = [line for line in proc.stdout.splitlines() if line.strip()]
    return {"available": True, "clean": not changes, "changed_file_count": len(changes)}


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
            label="Benchmark release lock matches source dirty state",
            expected=not bool(nested(benchmark, ["git_status", "source_dirty"], True)),
            actual=benchmark_summary.get("release_lock_ready"),
            paths=[REQUIRED_REPORTS["benchmark"]],
            detail=(
                "The benchmark release lock must be blocked by source changes, while generated evidence artifacts are "
                "tracked as generation context."
            ),
        )
        current_git_status = git_worktree_status(skill_dir)
        if current_git_status.get("available") and current_git_status.get("clean") is True:
            compare_values(
                checks,
                key="benchmark-clean-worktree-release-lock",
                label="Clean worktree keeps a clean benchmark release lock",
                expected=True,
                actual=benchmark_summary.get("release_lock_ready"),
                paths=[REQUIRED_REPORTS["benchmark"]],
                detail=(
                    "If the current worktree is clean, the committed benchmark report must not still carry a dirty release lock from an earlier generation."
                ),
            )
        else:
            add_check(
                checks,
                key="benchmark-clean-worktree-release-lock",
                label="Clean worktree keeps a clean benchmark release lock",
                status="pass",
                expected="checked only when git is available and the current worktree is clean",
                actual=current_git_status,
                paths=[REQUIRED_REPORTS["benchmark"]],
                detail=(
                    "Dirty or non-git worktrees cannot prove final release-lock freshness, so this check is advisory until the final clean-lock pass."
                ),
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
        checks.extend(
            build_preflight_artifact_role_handoff_checks(
                skill_dir=skill_dir,
                world_class_preflight=world_class_preflight,
                review_studio=review_studio,
                report_paths=REQUIRED_REPORTS,
            )
        )
        checks.append(
            build_phase_queue_consistency_check(
                world_class_preflight=world_class_preflight,
                world_class_operator_runbook=world_class_operator_runbook,
                review_studio=review_studio,
                report_paths=REQUIRED_REPORTS,
            )
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
    checks.append(
        build_skill_os2_review_current_evidence_check(
            skill_dir=skill_dir,
            skill_os2_review=skill_os2_review,
            studio_summary=studio_summary if isinstance(studio_summary, dict) else {},
            trust_summary=trust_summary if isinstance(trust_summary, dict) else {},
            package_summary=package_summary if isinstance(package_summary, dict) else {},
            install_summary=install_summary if isinstance(install_summary, dict) else {},
            benchmark_summary=benchmark_summary if isinstance(benchmark_summary, dict) else {},
            context_stats=context_stats if isinstance(context_stats, dict) else {},
            required_text_reports=REQUIRED_TEXT_REPORTS,
            required_reports=REQUIRED_REPORTS,
        )
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
