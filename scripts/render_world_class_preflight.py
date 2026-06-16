#!/usr/bin/env python3
import argparse
import json
import os
import shlex
from datetime import date
from pathlib import Path
from typing import Any

from prepare_world_class_submission_kit import build_artifact_checklist
from render_world_class_evidence_intake import build_intake
from render_world_class_evidence_ledger import build_ledger
from render_world_class_submission_review import build_submission_review
from world_class_evidence_contract import rel_path
from world_class_preflight_layout import render_html
from world_class_repair_checklist import build_preflight_repair_checklist, summarize_repair_checklist
from world_class_source_checks import summarize_source_checklist


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Renders a preflight checklist for collecting pending world-class evidence without accepting evidence."


PREFLIGHT_SPECS: dict[str, list[dict[str, Any]]] = {
    "provider-holdout": [
        {
            "key": "output-cases",
            "label": "Output eval cases",
            "kind": "file",
            "path": "evals/output/cases.jsonl",
            "required": True,
            "next_action": "Keep output holdout cases available before provider execution.",
        },
        {
            "key": "provider-runner",
            "label": "Provider runner",
            "kind": "file",
            "path": "scripts/provider_output_eval_runner.py",
            "required": True,
            "next_action": "Use the provider runner instead of the local command runner for model-backed evidence.",
        },
        {
            "key": "openai-api-key",
            "label": "Provider credential",
            "kind": "env",
            "name": "OPENAI_API_KEY",
            "required": True,
            "secret": True,
            "next_action": "Set OPENAI_API_KEY in the operator shell; never commit or print the value.",
        },
        {
            "key": "provider-model",
            "label": "Provider model",
            "kind": "env",
            "name": "YAO_OUTPUT_EVAL_MODEL",
            "required": False,
            "default": "gpt-4.1-mini",
            "next_action": "Optionally set YAO_OUTPUT_EVAL_MODEL; the runbook defaults to gpt-4.1-mini.",
        },
    ],
    "human-adjudication": [
        {
            "key": "review-kit",
            "label": "Blind review kit",
            "kind": "file",
            "path": "reports/output_review_kit.html",
            "required": True,
            "next_action": "Open the blind review kit and record real reviewer choices with required rationale.",
        },
        {
            "key": "decision-template",
            "label": "Decision template",
            "kind": "file",
            "path": "reports/output_review_decisions.json",
            "required": True,
            "next_action": "Import real A/B decisions with reviewer, reviewed_at, winner_variant, confidence, reason, and truthful blind-review attestation via `python3 scripts/yao.py output-review-import --input <reviewer-decisions.json> --blind-review-attested --run-adjudication`.",
        },
        {
            "key": "decision-importer",
            "label": "Decision importer",
            "kind": "file",
            "path": "scripts/import_output_review_decisions.py",
            "required": True,
            "next_action": "Use the importer to reject raw content fields and normalize reviewer decisions before adjudication.",
        },
        {
            "key": "human-reviewer",
            "label": "Human reviewer",
            "kind": "human",
            "required": True,
            "next_action": "Assign a real reviewer identity before claiming human adjudication.",
        },
    ],
    "native-permission-enforcement": [
        {
            "key": "permission-policy",
            "label": "Permission policy",
            "kind": "file",
            "path": "security/permission_policy.json",
            "required": True,
            "next_action": "Keep approved high-permission capabilities explicit.",
        },
        {
            "key": "permission-probes",
            "label": "Runtime probes",
            "kind": "file",
            "path": "reports/runtime_permission_probes.json",
            "required": True,
            "next_action": "Refresh runtime permission probes after packaging changes.",
        },
        {
            "key": "native-guard",
            "label": "Native guard",
            "kind": "external",
            "required": True,
            "next_action": "Attach a real target-client or external installer runtime guard; metadata fallback is not enough.",
        },
    ],
    "native-client-telemetry": [
        {
            "key": "native-host",
            "label": "Native telemetry host",
            "kind": "file",
            "path": "scripts/telemetry_native_host.py",
            "required": True,
            "next_action": "Use the native host to receive metadata-only client events.",
        },
        {
            "key": "hook-recipes",
            "label": "Hook recipes",
            "kind": "file",
            "path": "reports/telemetry_hook_recipes.json",
            "required": True,
            "next_action": "Refresh telemetry hook recipes before external client installation.",
        },
        {
            "key": "external-client",
            "label": "External client",
            "kind": "external",
            "required": True,
            "next_action": "Install a real Browser, Chrome, IDE, or provider client that emits metadata-only events.",
        },
    ],
}


def env_present(name: str) -> bool:
    return bool(os.environ.get(name))


def shell_path(path: Path, root: Path) -> str:
    return shlex.quote(rel_path(path, root))


def build_submission_commands(skill_dir: Path, submissions_dir: Path, evidence_key: str | None = None) -> dict[str, str]:
    output_dir = shell_path(submissions_dir, skill_dir)
    prepare = f"python3 scripts/yao.py world-class-submission-kit . --output-dir {output_dir}"
    if evidence_key:
        prepare = f"python3 scripts/yao.py world-class-submission-kit . --evidence-key {evidence_key} --output-dir {output_dir}"
    prefilled_prepare = f"{prepare} --prefill-artifacts"
    return {
        "prepare_submission": prepare,
        "prepare_prefilled_submission": prefilled_prepare,
        "validate_intake": f"python3 scripts/yao.py world-class-intake . --submissions-dir {output_dir}",
        "submission_review": f"python3 scripts/yao.py world-class-submission-review . --submissions-dir {output_dir}",
        "refresh_ledger": f"python3 scripts/yao.py world-class-ledger . --submissions-dir {output_dir}",
        "guard_claim": "python3 scripts/yao.py world-class-claim-guard .",
    }


def build_artifact_role_contract(rows: list[dict[str, Any]]) -> dict[str, Any]:
    submission_ref_rows = [row for row in rows if row.get("submission_ref_required") is True]
    supporting_rows = [row for row in rows if row.get("submission_ref_required") is not True]
    return {
        "schema_version": "1.0",
        "role_source": "world-class-submission-kit",
        "counts_as_evidence": False,
        "artifact_prefill_counts_as_evidence": False,
        "submission_ref_total_count": len(submission_ref_rows),
        "submission_ref_ready_count": sum(1 for row in submission_ref_rows if row.get("artifact_ref_ready")),
        "supporting_evidence_total_count": len(supporting_rows),
        "supporting_evidence_ready_count": sum(1 for row in supporting_rows if row.get("artifact_ref_ready")),
        "roles": [
            {
                "role": "submission-ref",
                "label": "Submission refs",
                "copy_to_artifact_refs": True,
                "description": "Rows marked submission-ref are the aggregate paths expected in artifact_refs.",
            },
            {
                "role": "supporting-evidence",
                "label": "Supporting evidence",
                "copy_to_artifact_refs": False,
                "description": "Supporting-evidence rows help reviewers audit the packet but do not all need to be copied into artifact_refs.",
            },
        ],
    }


def artifact_role_contract_for_key(contract: dict[str, Any], rows: list[dict[str, Any]], evidence_key: str) -> dict[str, Any]:
    item_rows = [row for row in rows if row.get("evidence_key") == evidence_key]
    role_contract = build_artifact_role_contract(item_rows)
    return {
        **role_contract,
        "schema_version": contract.get("schema_version", "1.0"),
        "role_source": contract.get("role_source", "world-class-submission-kit"),
    }


def build_precheck(skill_dir: Path, evidence_key: str, spec: dict[str, Any]) -> dict[str, Any]:
    kind = str(spec.get("kind", ""))
    required = spec.get("required") is True
    row = {
        "evidence_key": evidence_key,
        "key": spec.get("key", ""),
        "label": spec.get("label", ""),
        "kind": kind,
        "required": required,
        "next_action": spec.get("next_action", ""),
        "secret_value_redacted": spec.get("secret") is True,
    }
    if kind == "file":
        path = skill_dir / str(spec.get("path", ""))
        exists = path.exists()
        row.update(
            {
                "path": rel_path(path, skill_dir),
                "status": "pass" if exists else ("missing" if required else "optional"),
                "actual": "present" if exists else "missing",
            }
        )
        return row
    if kind == "env":
        name = str(spec.get("name", ""))
        present = env_present(name)
        row.update(
            {
                "env": name,
                "status": "pass" if present else ("missing" if required else "optional"),
                "actual": "set" if present else "not-set",
                "default": spec.get("default", ""),
            }
        )
        return row
    if kind == "human":
        row.update(
            {
                "status": "human-required",
                "actual": "external-human-action",
            }
        )
        return row
    if kind == "external":
        row.update(
            {
                "status": "external-required",
                "actual": "external-integration-required",
            }
        )
        return row
    row.update({"status": "unknown", "actual": "unknown"})
    return row


def item_status(entry: dict[str, Any], prechecks: list[dict[str, Any]], source_rows: list[dict[str, Any]]) -> str:
    if entry.get("status") == "accepted":
        return "accepted"
    blocking = {row.get("status") for row in prechecks if row.get("required") is True}
    if "missing" in blocking or "external-required" in blocking:
        return "blocked"
    if "human-required" in blocking:
        return "ready-for-human-review"
    if any(row.get("status") != "pass" for row in source_rows):
        return "ready-to-collect"
    return "ready-for-submission"


def first_next_action(prechecks: list[dict[str, Any]], source_rows: list[dict[str, Any]]) -> str:
    for row in prechecks:
        if row.get("required") is True and row.get("status") != "pass":
            return str(row.get("next_action", ""))
    for row in source_rows:
        if row.get("status") != "pass":
            return str(row.get("next_action", ""))
    return "Validate intake, refresh the ledger, and run the claim guard."


def md_cell(value: Any) -> str:
    return str(value).replace("|", "\\|")


def build_preflight(skill_dir: Path, generated_at: str, submissions_dir: Path | None = None) -> dict[str, Any]:
    submissions_dir = submissions_dir or (skill_dir / "evidence" / "world_class" / "submissions")
    ledger = build_ledger(skill_dir, generated_at, submissions_dir=submissions_dir)
    intake = build_intake(skill_dir, generated_at, submissions_dir=submissions_dir)
    review = build_submission_review(skill_dir, generated_at, submissions_dir=submissions_dir)
    review_by_key = {str(item.get("evidence_key", "")): item for item in review.get("items", [])}
    intake_by_key = {str(item.get("evidence_key", "")): item for item in intake.get("operator_checklist", [])}
    operator_items = intake.get("operator_checklist", [])
    operator_items = operator_items if isinstance(operator_items, list) else []
    artifact_checklist = build_artifact_checklist(skill_dir, operator_items)
    artifact_role_contract = build_artifact_role_contract(artifact_checklist)
    items: list[dict[str, Any]] = []
    precheck_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    for entry in ledger.get("entries", []):
        key = str(entry.get("key", ""))
        prechecks = [build_precheck(skill_dir, key, spec) for spec in PREFLIGHT_SPECS.get(key, [])]
        review_item = review_by_key.get(key, {})
        item_source_rows = review_item.get("source_checklist", entry.get("source_checklist", []))
        item_source_rows = item_source_rows if isinstance(item_source_rows, list) else []
        status = item_status(entry, prechecks, item_source_rows)
        item_commands = build_submission_commands(skill_dir, submissions_dir, key)
        item = {
            "evidence_key": key,
            "label": entry.get("label", key),
            "category": entry.get("category", "external"),
            "owner": entry.get("owner", "release reviewer"),
            "status": status,
            "ledger_status": entry.get("status", "pending"),
            "intake_readiness": intake_by_key.get(key, {}).get("readiness", "missing"),
            "review_state": review_item.get("review_state", "missing"),
            "source_accepted": entry.get("source_accepted") is True,
            "prechecks": prechecks,
            "source_checklist": item_source_rows,
            "next_action": first_next_action(prechecks, item_source_rows),
            "submission_path": intake_by_key.get(key, {}).get("submission_path", ""),
            "template_path": intake_by_key.get(key, {}).get("template_path", ""),
            "commands": item_commands,
            "submission_kit": {
                "prepare_command": item_commands["prepare_submission"],
                "prefill_command": item_commands["prepare_prefilled_submission"],
                "output_dir": rel_path(submissions_dir, skill_dir),
                "draft_path": intake_by_key.get(key, {}).get("submission_path", ""),
                "template_path": intake_by_key.get(key, {}).get("template_path", ""),
                "artifact_role_contract": artifact_role_contract_for_key(
                    artifact_role_contract,
                    artifact_checklist,
                    key,
                ),
                "drafts_count_as_evidence": False,
                "artifact_prefill_counts_as_evidence": False,
            },
            "runbook": entry.get("runbook", []),
        }
        items.append(item)
        precheck_rows.extend(prechecks)
        source_rows.extend(item_source_rows)
    repair_checklist = build_preflight_repair_checklist(items)
    repairs_by_key: dict[str, list[dict[str, Any]]] = {}
    for row in repair_checklist:
        key = str(row.get("evidence_key", ""))
        repairs_by_key.setdefault(key, []).append(row)
    for item in items:
        item["repair_checklist"] = repairs_by_key.get(str(item.get("evidence_key", "")), [])
    precheck_status_counts: dict[str, int] = {}
    for row in precheck_rows:
        status = str(row.get("status", "unknown"))
        precheck_status_counts[status] = precheck_status_counts.get(status, 0) + 1
    source_summary = summarize_source_checklist(source_rows)
    repair_summary = summarize_repair_checklist(repair_checklist)
    collection_ready_count = sum(1 for item in items if item["status"] in {"ready-to-collect", "ready-for-human-review", "ready-for-submission"})
    blocked_count = sum(1 for item in items if item["status"] == "blocked")
    ready_to_claim = ledger.get("summary", {}).get("ready_to_claim_world_class") is True
    summary = {
        "evidence_item_count": len(items),
        "precheck_count": len(precheck_rows),
        "precheck_pass_count": precheck_status_counts.get("pass", 0),
        "precheck_missing_count": precheck_status_counts.get("missing", 0),
        "precheck_optional_count": precheck_status_counts.get("optional", 0),
        "precheck_human_required_count": precheck_status_counts.get("human-required", 0),
        "precheck_external_required_count": precheck_status_counts.get("external-required", 0),
        "collection_ready_count": collection_ready_count,
        "collection_blocked_count": blocked_count,
        **source_summary,
        **repair_summary,
        "pending_count": ledger.get("summary", {}).get("pending_count", 0),
        "ready_to_claim_world_class": ready_to_claim,
        "credential_value_exposed": False,
        "preflight_counts_as_evidence": False,
        "decision": "ready-for-completion-audit" if ready_to_claim else ("collection-preflight-blocked" if blocked_count else "ready-to-collect-evidence"),
    }
    return {
        "schema_version": "1.0",
        "ok": True,
        "generated_at": generated_at,
        "skill_dir": rel_path(skill_dir, ROOT),
        "summary": summary,
        "status_counts": {item["status"]: sum(1 for candidate in items if candidate["status"] == item["status"]) for item in items},
        "precheck_status_counts": precheck_status_counts,
        "items": items,
        "prechecks": precheck_rows,
        "source_checklist": source_rows,
        "repair_checklist": repair_checklist,
        "submissions": {
            "directory": rel_path(submissions_dir, skill_dir),
            "commands": build_submission_commands(skill_dir, submissions_dir),
            "submission_kit_command": build_submission_commands(skill_dir, submissions_dir)["prepare_submission"],
            "submission_kit_prefill_command": build_submission_commands(skill_dir, submissions_dir)[
                "prepare_prefilled_submission"
            ],
            "preflight_counts_submission_as_completion": False,
            "drafts_count_as_evidence": False,
            "artifact_prefill_counts_as_evidence": False,
            "artifact_role_contract": artifact_role_contract,
        },
        "source_reports": {
            "ledger": "reports/world_class_evidence_ledger.json",
            "intake": "reports/world_class_evidence_intake.json",
            "submission_review": "reports/world_class_submission_review.json",
            "operator_runbook": "reports/world_class_operator_runbook.json",
        },
        "artifacts": {
            "json": "reports/world_class_evidence_preflight.json",
            "markdown": "reports/world_class_evidence_preflight.md",
            "html": "reports/world_class_evidence_preflight.html",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    role_contract = report["submissions"]["artifact_role_contract"]
    lines = [
        "# World-Class Evidence Preflight",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- decision: `{summary['decision']}`",
        f"- ready to claim world-class: `{str(summary['ready_to_claim_world_class']).lower()}`",
        f"- preflight counts as evidence: `{str(summary['preflight_counts_as_evidence']).lower()}`",
        f"- credential value exposed: `{str(summary['credential_value_exposed']).lower()}`",
        f"- collection ready: `{summary['collection_ready_count']}`",
        f"- collection blocked: `{summary['collection_blocked_count']}`",
        f"- source checks: `{summary['source_pass_count']}` pass / `{summary['source_check_count']}` total",
        f"- repair rows: `{summary['repair_blocked_count']}` blocked / `{summary['repair_checklist_count']}` total",
        f"- next repair action: `{summary.get('next_repair_action_id', '')}`",
        f"- next repair owner: `{summary.get('next_repair_owner', '')}`",
        "",
        "This preflight report checks whether an operator can start collecting the remaining external or human evidence. It never accepts evidence, prints secret values, or changes the world-class ledger.",
        "",
        "## Submission Kit Handoff",
        "",
        f"- submissions directory: `{report['submissions']['directory']}`",
        f"- prepare drafts: `{report['submissions']['commands']['prepare_submission']}`",
        f"- prepare drafts with artifact SHA prefill: `{report['submissions']['commands']['prepare_prefilled_submission']}`",
        f"- validate intake: `{report['submissions']['commands']['validate_intake']}`",
        f"- review queue: `{report['submissions']['commands']['submission_review']}`",
        f"- refresh ledger: `{report['submissions']['commands']['refresh_ledger']}`",
        f"- guard claims: `{report['submissions']['commands']['guard_claim']}`",
        f"- drafts count as evidence: `{str(report['submissions']['drafts_count_as_evidence']).lower()}`",
        f"- artifact prefill counts as evidence: `{str(report['submissions']['artifact_prefill_counts_as_evidence']).lower()}`",
        f"- submission refs ready: `{role_contract['submission_ref_ready_count']}` / `{role_contract['submission_ref_total_count']}`",
        f"- supporting evidence ready: `{role_contract['supporting_evidence_ready_count']}` / `{role_contract['supporting_evidence_total_count']}`",
        "",
        "Generate the submission kit after the real provider, human, native-permission, or native-client work exists. The generated JSON drafts remain `template_only: true` until an operator edits them with real aggregate artifact references and matching SHA-256 digests. The prefill command only inserts local artifact SHA-256 digests; it does not make a draft count as evidence.",
        "",
        "| Role | Copy to artifact_refs | Ready | Meaning |",
        "| --- | --- | --- | --- |",
    ]
    for role in role_contract.get("roles", []):
        if role.get("role") == "submission-ref":
            ready = f"{role_contract['submission_ref_ready_count']} / {role_contract['submission_ref_total_count']}"
        else:
            ready = (
                f"{role_contract['supporting_evidence_ready_count']} / "
                f"{role_contract['supporting_evidence_total_count']}"
            )
        lines.append(
            f"| `{role['role']}` | `{str(role['copy_to_artifact_refs']).lower()}` | `{ready}` | "
            f"{md_cell(role['description'])} |"
        )
    lines.extend(
        [
            "",
            "`submission-ref` rows are the only checklist rows expected in `artifact_refs`; `supporting-evidence` rows stay available for audit context and reviewer traceability.",
            "",
        "## Evidence Items",
        "",
        "| Evidence | Status | Intake | Review | Next action |",
        "| --- | --- | --- | --- | --- |",
        ]
    )
    for item in report["items"]:
        next_action = str(item.get("next_action", "")).replace("|", "\\|")
        lines.append(
            f"| `{item['evidence_key']}` | `{item['status']}` | `{item['intake_readiness']}` | `{item['review_state']}` | {next_action} |"
        )
    lines.extend(
        [
            "",
            "## Repair Checklist",
            "",
            "Repair rows convert preflight and source blockers into a prioritized operator queue. They are guidance only and do not count as completion evidence.",
            "",
            "| Priority | Phase | Owner | Evidence | Type | Target | Status | Verify | Next action |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in report.get("repair_checklist", []):
        lines.append(
            f"| `{row.get('priority', '')}` | `{row.get('phase', '')}` | {md_cell(row.get('owner', ''))} | "
            f"`{row['evidence_key']}` | `{row['repair_type']}` | `{row['target']}` | "
            f"`{row['status']}` | `{md_cell(row.get('verification_command', ''))}` | {md_cell(row['next_action'])} |"
        )
    for item in report["items"]:
        lines.extend(
            [
                "",
                f"## {item['label']}",
                "",
                f"- status: `{item['status']}`",
                f"- ledger: `{item['ledger_status']}`",
                f"- submission: `{item.get('submission_path') or 'missing'}`",
                f"- prepare draft: `{item['commands']['prepare_submission']}`",
                f"- prepare draft with artifact SHA prefill: `{item['commands']['prepare_prefilled_submission']}`",
                f"- submission refs ready: `{item['submission_kit']['artifact_role_contract']['submission_ref_ready_count']}` / `{item['submission_kit']['artifact_role_contract']['submission_ref_total_count']}`",
                f"- supporting evidence ready: `{item['submission_kit']['artifact_role_contract']['supporting_evidence_ready_count']}` / `{item['submission_kit']['artifact_role_contract']['supporting_evidence_total_count']}`",
                "",
                "### Prechecks",
                "",
                "| Check | Kind | Current | Status | Next action |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for row in item.get("prechecks", []):
            action = md_cell(row.get("next_action", ""))
            lines.append(
                f"| {row['label']} | `{row['kind']}` | `{row['actual']}` | `{row['status']}` | {action} |"
            )
        lines.extend(
            [
                "",
                "### Source Checks",
                "",
                "| Check | Current | Expected | Status | Next action |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for row in item.get("source_checklist", []):
            action = md_cell(row.get("next_action", ""))
            lines.append(
                f"| {row['label']} | `{row['actual']}` | `{row['expected']}` | `{row['status']}` | {action} |"
            )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Environment variables are reported only as `set` or `not-set`; values are never printed.",
            "- Human-required and external-required states are operator actions, not accepted evidence.",
            "- The world-class ledger remains the source of truth for `ready_to_claim_world_class`.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render collection preflight checks for pending world-class evidence.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--submissions-dir")
    parser.add_argument("--output-json", default="reports/world_class_evidence_preflight.json")
    parser.add_argument("--output-md", default="reports/world_class_evidence_preflight.md")
    parser.add_argument("--output-html", default="reports/world_class_evidence_preflight.html")
    parser.add_argument("--generated-at", default=date.today().isoformat())
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    submissions_dir = Path(args.submissions_dir).resolve() if args.submissions_dir else None
    report = build_preflight(skill_dir, args.generated_at, submissions_dir=submissions_dir)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_html = Path(args.output_html)
    if not output_json.is_absolute():
        output_json = skill_dir / output_json
    if not output_md.is_absolute():
        output_md = skill_dir / output_md
    if not output_html.is_absolute():
        output_html = skill_dir / output_html
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    output_html.write_text(render_html(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
