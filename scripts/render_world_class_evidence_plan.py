#!/usr/bin/env python3
import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from render_skill_os2_audit import build_audit


ROOT = Path(__file__).resolve().parent.parent


TASK_TEMPLATES: dict[str, dict[str, Any]] = {
    "provider-holdout": {
        "category": "external",
        "owner": "operator with provider credentials",
        "objective": "Collect at least one provider-backed output-eval holdout run with model, timing, and token metadata.",
        "runbook": [
            "YAO_OUTPUT_EVAL_MODEL=gpt-4.1-mini OPENAI_API_KEY=<redacted> python3 scripts/yao.py output-exec --provider-runner openai --timeout-seconds 60",
            "python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD>",
        ],
        "success_checks": [
            "reports/output_execution_runs.json summary.model_executed_count > 0",
            "reports/output_execution_runs.json summary.timing_observed_count > 0",
            "reports/output_execution_runs.json summary.token_observed_count > 0",
            "reports/skill_os2_audit.json item provider-holdout status becomes pass",
        ],
        "evidence_artifacts": [
            "reports/output_execution_runs.json",
            "reports/output_execution_runs.md",
            "reports/skill_os2_audit.json",
        ],
        "privacy_contract": [
            "Do not commit provider credentials or environment dumps.",
            "The output execution report records output hashes and aggregate run metadata, not raw provider prompts.",
        ],
    },
    "human-adjudication": {
        "category": "human",
        "owner": "human reviewer",
        "objective": "Record real blind A/B reviewer decisions before claiming human output review completion.",
        "runbook": [
            "python3 scripts/adjudicate_output_review.py --write-template",
            "Open reports/output_blind_review_pack.md and choose A or B for each pair without opening the answer key.",
            "Edit reports/output_review_decisions.json with winner_variant values and reviewer metadata.",
            "python3 scripts/yao.py output-review",
            "python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD>",
        ],
        "success_checks": [
            "reports/output_review_adjudication.json summary.pending_count == 0",
            "reports/output_review_adjudication.json summary.judgment_count == summary.pair_count",
            "reports/output_review_adjudication.json summary.invalid_decision_count == 0",
            "reports/skill_os2_audit.json item human-adjudication status becomes pass",
        ],
        "evidence_artifacts": [
            "reports/output_blind_review_pack.md",
            "reports/output_review_decisions.json",
            "reports/output_review_adjudication.json",
            "reports/output_review_adjudication.md",
        ],
        "privacy_contract": [
            "Reviewer decisions should not include raw user data or private customer detail.",
            "Keep the answer key separate until after decisions are recorded.",
        ],
    },
    "native-permission-enforcement": {
        "category": "external",
        "owner": "target client or installer integrator",
        "objective": "Prove at least one target or installer enforces approved high-permission capabilities at runtime.",
        "runbook": [
            "Implement or connect a real target client/installer guard that blocks undeclared network, file_write, or subprocess capabilities.",
            "Update the generated target adapter only when the guard is actually enforced by that target.",
            "python3 scripts/yao.py package . --platform openai --platform claude --platform generic --platform vscode --output-dir dist --zip",
            "python3 scripts/yao.py runtime-permissions . --package-dir dist",
            "python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD>",
        ],
        "success_checks": [
            "reports/runtime_permission_probes.json summary.native_enforcement_count > 0",
            "reports/runtime_permission_probes.json summary.failure_count == 0",
            "reports/skill_os2_audit.json item native-permission-enforcement status becomes pass",
        ],
        "evidence_artifacts": [
            "dist/targets/*/adapter.json",
            "reports/runtime_permission_probes.json",
            "reports/runtime_permission_probes.md",
            "security/permission_policy.json",
        ],
        "privacy_contract": [
            "Do not mark native_enforcement true for metadata-only fallbacks.",
            "Keep residual risks visible for targets that still rely on operator enforcement.",
        ],
    },
    "native-client-telemetry": {
        "category": "external",
        "owner": "Browser/Chrome/IDE/provider client integrator",
        "objective": "Import production metadata-only events from a real external client into the local drift loop.",
        "runbook": [
            "python3 scripts/telemetry_native_host.py . --write-launcher /tmp/yao-telemetry-host.sh --write-manifest /tmp/yao-telemetry-host.json --allowed-origin chrome-extension://<extension-id>/",
            "Install the generated native messaging manifest for the real client and send at least one accepted skill_activation or skill_output event.",
            "python3 scripts/yao.py telemetry-import . --input-jsonl .yao/telemetry_spool/external_events.jsonl",
            "python3 scripts/yao.py skill-atlas --workspace-root .",
            "python3 scripts/yao.py skill-os2-audit . --generated-at <YYYY-MM-DD>",
        ],
        "success_checks": [
            "reports/adoption_drift_report.json summary.source_types.external > 0",
            "reports/adoption_drift_report.json summary.adoption_sample_count > 0",
            "reports/skill_os2_audit.json item native-client-telemetry status becomes pass",
        ],
        "evidence_artifacts": [
            "reports/adoption_drift_report.json",
            "reports/adoption_drift_report.md",
            "reports/telemetry_hook_recipes.json",
            "scripts/telemetry_native_host.py",
        ],
        "privacy_contract": [
            "Telemetry must remain metadata-only and local-first.",
            "Do not package reports/telemetry_events.jsonl or any raw prompt, output, transcript, note, or message field.",
        ],
    },
}


def rel_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def build_task(item: dict[str, Any]) -> dict[str, Any]:
    template = TASK_TEMPLATES.get(
        item["key"],
        {
            "category": "review",
            "owner": "release reviewer",
            "objective": item.get("target", "Collect stronger evidence for this non-pass audit item."),
            "runbook": ["Open reports/skill_os2_audit.md and resolve the listed next action."],
            "success_checks": [f"reports/skill_os2_audit.json item {item['key']} status becomes pass"],
            "evidence_artifacts": [entry["path"] for entry in item.get("evidence", []) if entry.get("exists")],
            "privacy_contract": ["Do not add raw private user content to release evidence."],
        },
    )
    return {
        "key": item["key"],
        "label": item["label"],
        "status": item["status"],
        "category": template["category"],
        "owner": template["owner"],
        "current": item["current"],
        "objective": template["objective"],
        "runbook": template["runbook"],
        "success_checks": template["success_checks"],
        "evidence_artifacts": template["evidence_artifacts"],
        "privacy_contract": template["privacy_contract"],
        "audit_next_action": item["next_action"],
    }


def build_plan(skill_dir: Path, generated_at: str) -> dict[str, Any]:
    audit = build_audit(skill_dir, generated_at)
    tasks = [build_task(item) for item in audit["items"] if item["status"] != "pass"]
    category_counts: dict[str, int] = {}
    for task in tasks:
        category_counts[task["category"]] = category_counts.get(task["category"], 0) + 1
    ready = len(tasks) == 0 and audit["summary"].get("world_class_ready") is True
    return {
        "schema_version": "1.0",
        "ok": audit["ok"],
        "generated_at": generated_at,
        "skill_dir": rel_path(skill_dir, ROOT),
        "summary": {
            "audit_decision": audit["summary"]["decision"],
            "world_class_ready": bool(audit["summary"]["world_class_ready"]),
            "ready_to_claim_world_class": ready,
            "task_count": len(tasks),
            "human_task_count": category_counts.get("human", 0),
            "external_task_count": category_counts.get("external", 0),
            "review_task_count": category_counts.get("review", 0),
            "decision": "ready-for-completion-audit" if ready else "collect-external-evidence",
        },
        "tasks": tasks,
        "source_audit": {
            "json": "reports/skill_os2_audit.json",
            "markdown": "reports/skill_os2_audit.md",
            "open_gap_count": audit["summary"]["open_gap_count"],
        },
        "artifacts": {
            "json": "reports/world_class_evidence_plan.json",
            "markdown": "reports/world_class_evidence_plan.md",
            "ledger": "reports/world_class_evidence_ledger.md",
        },
    }


def render_markdown(plan: dict[str, Any]) -> str:
    summary = plan["summary"]
    lines = [
        "# World-Class Evidence Plan",
        "",
        f"Generated at: `{plan['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- decision: `{summary['decision']}`",
        f"- audit decision: `{summary['audit_decision']}`",
        f"- ready to claim world-class: `{str(summary['ready_to_claim_world_class']).lower()}`",
        f"- tasks: `{summary['task_count']}`",
        f"- human tasks: `{summary['human_task_count']}`",
        f"- external tasks: `{summary['external_task_count']}`",
        "",
        "This report is an execution plan for the remaining world-class evidence gaps. It does not count a plan as completion.",
        "",
        "## Task Table",
        "",
        "| Task | Status | Category | Owner | Current |",
        "| --- | --- | --- | --- | --- |",
    ]
    for task in plan["tasks"]:
        current = str(task["current"]).replace("|", "\\|")
        lines.append(
            f"| `{task['key']}` | `{task['status']}` | `{task['category']}` | {task['owner']} | {current} |"
        )
    if not plan["tasks"]:
        lines.append("| `none` | `pass` | `none` | none | all evidence collected |")
    for task in plan["tasks"]:
        lines.extend(
            [
                "",
                f"## {task['label']}",
                "",
                f"- objective: {task['objective']}",
                f"- audit next action: {task['audit_next_action']}",
                "",
                "### Runbook",
                "",
            ]
        )
        for command in task["runbook"]:
            lines.append(f"- `{command}`" if command.startswith("python3 ") or "=" in command else f"- {command}")
        lines.extend(["", "### Success Checks", ""])
        lines.extend(f"- {check}" for check in task["success_checks"])
        lines.extend(["", "### Evidence Artifacts", ""])
        lines.extend(f"- `{artifact}`" for artifact in task["evidence_artifacts"])
        lines.extend(["", "### Privacy Contract", ""])
        lines.extend(f"- {item}" for item in task["privacy_contract"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a world-class evidence collection plan.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--output-json", default="reports/world_class_evidence_plan.json")
    parser.add_argument("--output-md", default="reports/world_class_evidence_plan.md")
    parser.add_argument("--generated-at", default=date.today().isoformat())
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    plan = build_plan(skill_dir, args.generated_at)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    if not output_json.is_absolute():
        output_json = skill_dir / output_json
    if not output_md.is_absolute():
        output_md = skill_dir / output_md
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(plan), encoding="utf-8")
    print(json.dumps(plan, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
