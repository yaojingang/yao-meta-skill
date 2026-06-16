import html
from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by review_studio_actions.py to keep world-class evidence action cards out of generic Review Studio action wiring."


def action_command_rows(commands: dict[str, Any]) -> list[dict[str, str]]:
    command_labels = {
        "prepare_submission": "准备提交",
        "validate_intake": "校验入口",
        "submission_review": "审查提交",
        "refresh_ledger": "刷新台账",
        "guard_claim": "声明守卫",
    }
    rows = []
    for key in ("prepare_submission", "validate_intake", "submission_review", "refresh_ledger", "guard_claim"):
        command = str(commands.get(key, "")).strip()
        if command:
            rows.append({"key": key, "label": command_labels.get(key, key), "command": command})
    return rows


def first_text_items(*values: Any, limit: int = 4) -> list[str]:
    for value in values:
        if isinstance(value, list) and value:
            return [str(item) for item in value[:limit]]
    return []


def artifact_role_rows(contract: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    roles = contract.get("roles", []) if isinstance(contract.get("roles", []), list) else []
    for role in roles:
        if not isinstance(role, dict):
            continue
        role_name = str(role.get("role", "")).strip()
        if role_name == "submission-ref":
            ready_count = int(contract.get("submission_ref_ready_count", 0) or 0)
            total_count = int(contract.get("submission_ref_total_count", 0) or 0)
        elif role_name == "supporting-evidence":
            ready_count = int(contract.get("supporting_evidence_ready_count", 0) or 0)
            total_count = int(contract.get("supporting_evidence_total_count", 0) or 0)
        else:
            ready_count = 0
            total_count = 0
        rows.append(
            {
                "role": role_name,
                "label": str(role.get("label", role_name)),
                "ready_count": ready_count,
                "total_count": total_count,
                "copy_to_artifact_refs": role.get("copy_to_artifact_refs") is True,
                "description": str(role.get("description", "")),
            }
        )
    return rows


def compact_artifact_role_contract(contract: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(contract, dict) or not contract:
        return {}
    return {
        "role_source": str(contract.get("role_source", "")),
        "counts_as_evidence": contract.get("counts_as_evidence") is True,
        "artifact_prefill_counts_as_evidence": contract.get("artifact_prefill_counts_as_evidence") is True,
        "submission_ref_ready_count": int(contract.get("submission_ref_ready_count", 0) or 0),
        "submission_ref_total_count": int(contract.get("submission_ref_total_count", 0) or 0),
        "supporting_evidence_ready_count": int(contract.get("supporting_evidence_ready_count", 0) or 0),
        "supporting_evidence_total_count": int(contract.get("supporting_evidence_total_count", 0) or 0),
        "roles": artifact_role_rows(contract),
    }


def world_class_action_steps(data: dict[str, Any]) -> list[dict[str, Any]]:
    ledger = data.get("world_class_evidence_ledger", {}) if isinstance(data, dict) else {}
    entries = ledger.get("entries", []) if isinstance(ledger, dict) else []
    intake = data.get("world_class_evidence_intake", {}) if isinstance(data, dict) else {}
    intake_items = intake.get("operator_checklist", []) if isinstance(intake, dict) else []
    intake_by_key = {
        str(item.get("evidence_key", "")): item
        for item in intake_items
        if isinstance(item, dict) and str(item.get("evidence_key", "")).strip()
    }
    preflight = data.get("world_class_evidence_preflight", {}) if isinstance(data, dict) else {}
    preflight_items = preflight.get("items", []) if isinstance(preflight, dict) else []
    preflight_by_key = {
        str(item.get("evidence_key", "")): item
        for item in preflight_items
        if isinstance(item, dict) and str(item.get("evidence_key", "")).strip()
    }
    steps = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        key = str(entry.get("key", "")).strip()
        if not key:
            continue
        checklist = intake_by_key.get(key, {})
        preflight_item = preflight_by_key.get(key, {})
        submission = entry.get("submission_state", {}) if isinstance(entry.get("submission_state", {}), dict) else {}
        source_checks = entry.get("source_checklist", []) if isinstance(entry.get("source_checklist", []), list) else []
        blocked_checks = [
            {
                "label": str(row.get("label", "")),
                "field": str(row.get("field", "")),
                "actual": row.get("actual", ""),
                "expected": str(row.get("expected", "")),
                "status": str(row.get("status", "blocked")),
                "next_action": str(row.get("next_action", "")),
            }
            for row in source_checks
            if isinstance(row, dict) and str(row.get("status", "")) != "pass"
        ]
        repair_rows = []
        for row in preflight_item.get("repair_checklist", []) if isinstance(preflight_item, dict) else []:
            if not isinstance(row, dict):
                continue
            repair_rows.append(
                {
                    "action_id": str(row.get("action_id", "")),
                    "repair_type": str(row.get("repair_type", "")),
                    "target": str(row.get("target", "")),
                    "phase": str(row.get("phase", "")),
                    "priority": int(row.get("priority", 90) or 90),
                    "owner": str(row.get("owner", "")),
                    "status": str(row.get("status", "blocked")),
                    "blocking_reason": str(row.get("blocking_reason", "")),
                    "next_action": str(row.get("next_action", "")),
                    "verification_command": str(row.get("verification_command", "")),
                    "counts_as_completion": row.get("counts_as_completion") is True,
                }
            )
        derived_pass_count = sum(1 for row in source_checks if isinstance(row, dict) and str(row.get("status", "")) == "pass")
        runbook = entry.get("runbook", [])
        if not runbook and isinstance(checklist.get("must_collect", {}), dict):
            runbook = checklist["must_collect"].get("runbook", [])
        must_collect = checklist.get("must_collect", {}) if isinstance(checklist.get("must_collect", {}), dict) else {}
        submission_kit = (
            preflight_item.get("submission_kit", {})
            if isinstance(preflight_item.get("submission_kit", {}), dict)
            else {}
        )
        steps.append(
            {
                "key": key,
                "label": str(entry.get("label", key)),
                "category": str(entry.get("category", "")),
                "status": str(entry.get("status", "pending")),
                "readiness": str(checklist.get("readiness", "")),
                "current": str(entry.get("current", "")),
                "next_action": str(entry.get("next_action") or checklist.get("next_action", "")),
                "submission_path": str(submission.get("path") or checklist.get("submission_path", "")),
                "template_path": str(checklist.get("template_path", "")),
                "source_pass_count": int(entry.get("source_pass_count", 0) or derived_pass_count),
                "source_blocked_count": int(entry.get("source_blocked_count", 0) or len(blocked_checks)),
                "blocked_checks": blocked_checks,
                "repair_rows": repair_rows,
                "repair_blocked_count": sum(1 for row in repair_rows if row.get("status") != "ready"),
                "repair_counts_as_completion": any(row.get("counts_as_completion") for row in repair_rows),
                "commands": action_command_rows(checklist.get("commands", {}) if isinstance(checklist.get("commands", {}), dict) else {}),
                "runbook": [str(item) for item in runbook[:3]],
                "provenance_requirements": first_text_items(
                    must_collect.get("provenance_requirements"),
                    entry.get("provenance_requirements"),
                    limit=3,
                ),
                "success_checks": first_text_items(
                    must_collect.get("success_checks"),
                    entry.get("success_checks"),
                    limit=9,
                ),
                "evidence_artifacts": first_text_items(
                    must_collect.get("evidence_artifacts"),
                    entry.get("evidence_artifacts"),
                    limit=5,
                ),
                "artifact_role_contract": compact_artifact_role_contract(
                    submission_kit.get("artifact_role_contract", {})
                    if isinstance(submission_kit.get("artifact_role_contract", {}), dict)
                    else {}
                ),
                "privacy_contract": first_text_items(
                    must_collect.get("privacy_contract"),
                    entry.get("privacy_contract"),
                    limit=4,
                ),
            }
        )
    return steps


def render_small_list(items: list[Any], empty: str, ordered: bool = False) -> str:
    if not items:
        return f"<p class='muted'>{html.escape(empty)}</p>"
    tag = "ol" if ordered else "ul"
    rows = "".join(f"<li>{html.escape(str(item))}</li>" for item in items)
    return f"<{tag}>{rows}</{tag}>"


def render_artifact_role_contract(contract: dict[str, Any]) -> str:
    roles = contract.get("roles", []) if isinstance(contract, dict) else []
    if not roles:
        return "<p class='muted'>暂无资产角色。</p>"
    rows = []
    for role in roles:
        rows.append(
            "<li>"
            f"<strong>{html.escape(str(role.get('role', '')))}</strong>"
            f"<span>{html.escape(str(role.get('ready_count', 0)))} / {html.escape(str(role.get('total_count', 0)))} ready</span>"
            f"<code>artifact_refs: {html.escape(str(role.get('copy_to_artifact_refs') is True).lower())}</code>"
            f"<small>{html.escape(str(role.get('description', '')))}</small>"
            "</li>"
        )
    source = html.escape(str(contract.get("role_source", "")))
    counts = html.escape(str(contract.get("counts_as_evidence") is True).lower())
    prefill = html.escape(str(contract.get("artifact_prefill_counts_as_evidence") is True).lower())
    return (
        f"<p class='muted'>source: <code>{source}</code>; counts as evidence: <code>{counts}</code>; "
        f"prefill counts as evidence: <code>{prefill}</code></p>"
        "<ul class='action-artifact-roles'>"
        + "".join(rows)
        + "</ul>"
    )


def render_action_evidence_steps(steps: list[dict[str, Any]]) -> str:
    if not steps:
        return ""
    cards = []
    for step in steps:
        blocked_checks = []
        for check in step.get("blocked_checks", []):
            blocked_checks.append(
                "<li class='action-evidence-check "
                + html.escape(str(check.get("status", "blocked")))
                + "'>"
                f"<span>{html.escape(str(check.get('label', '')))}</span>"
                f"<code>{html.escape(str(check.get('field', '')))}: {html.escape(str(check.get('actual', '')))} / {html.escape(str(check.get('expected', '')))}</code>"
                f"<small>{html.escape(str(check.get('next_action', '')))}</small>"
                "</li>"
            )
        command_rows = []
        for command in step.get("commands", [])[:4]:
            command_rows.append(
                "<li>"
                f"<span>{html.escape(str(command.get('label', '')))}</span>"
                f"<code>{html.escape(str(command.get('command', '')))}</code>"
                "</li>"
            )
        runbook_rows = [f"<li>{html.escape(str(item))}</li>" for item in step.get("runbook", [])]
        repair_rows = []
        for row in step.get("repair_rows", []):
            repair_rows.append(
                "<li class='action-repair-row "
                + html.escape(str(row.get("status", "blocked")))
                + "'>"
                f"<span>#{html.escape(str(row.get('priority', '')))} · {html.escape(str(row.get('phase', '')))} · {html.escape(str(row.get('repair_type', '')))}</span>"
                f"<strong>{html.escape(str(row.get('target', '')))}</strong>"
                f"<em>{html.escape(str(row.get('owner', '')))}</em>"
                f"<code>{html.escape(str(row.get('blocking_reason', '')))}</code>"
                f"<small>{html.escape(str(row.get('next_action', '')))}</small>"
                f"<code>{html.escape(str(row.get('verification_command', '')))}</code>"
                "</li>"
            )
        cards.append(
            "<article class='action-evidence-item "
            + html.escape(str(step.get("status", "pending")))
            + "'>"
            f"<div><span>{html.escape(str(step.get('status', 'pending')))} · {html.escape(str(step.get('category', '')))}</span>"
            f"<h4>{html.escape(str(step.get('label', step.get('key', 'evidence'))))}</h4></div>"
            f"<p>{html.escape(str(step.get('current', '')))}</p>"
            f"<dl><dt>提交</dt><dd><code>{html.escape(str(step.get('submission_path', '')))}</code></dd>"
            f"<dt>模板</dt><dd><code>{html.escape(str(step.get('template_path', '')))}</code></dd>"
            f"<dt>阻断</dt><dd>{html.escape(str(step.get('source_blocked_count', 0)))} blocked / {html.escape(str(step.get('source_pass_count', 0)))} pass</dd>"
            f"<dt>修复</dt><dd>{html.escape(str(step.get('repair_blocked_count', 0)))} repair rows; counts as completion: {html.escape(str(step.get('repair_counts_as_completion') is True).lower())}</dd>"
            f"<dt>下一步</dt><dd>{html.escape(str(step.get('next_action', '')))}</dd></dl>"
            "<section><h5>阻断检查</h5>"
            + (
                "<ul class='action-evidence-checks'>" + "".join(blocked_checks) + "</ul>"
                if blocked_checks
                else "<p class='muted'>暂无阻断检查。</p>"
            )
            + "</section>"
            "<details class='action-repair-details'><summary>修复清单</summary>"
            + (
                "<ul class='action-repair-list'>" + "".join(repair_rows) + "</ul>"
                if repair_rows
                else "<p class='muted'>暂无修复项。</p>"
            )
            + "</details>"
            "<details class='action-command-details'><summary>操作命令</summary>"
            + (
                "<ul class='action-command-list'>" + "".join(command_rows) + "</ul>"
                if command_rows
                else "<p class='muted'>暂无操作命令。</p>"
            )
            + "</details>"
            "<details class='action-runbook-details'><summary>首要步骤</summary>"
            + (
                "<ol class='action-runbook-list'>" + "".join(runbook_rows) + "</ol>"
                if runbook_rows
                else "<p class='muted'>暂无首要步骤。</p>"
            )
            + "</details>"
            "<details class='action-collection-details'><summary>采集契约</summary>"
            "<div class='action-collection-grid'>"
            "<section><h5>来源要求</h5>"
            + render_small_list(step.get("provenance_requirements", []), "暂无来源要求。")
            + "</section>"
            "<section><h5>通过条件</h5>"
            + render_small_list(step.get("success_checks", []), "暂无通过条件。")
            + "</section>"
            "<section><h5>证据资产</h5>"
            + render_small_list(step.get("evidence_artifacts", []), "暂无证据资产。")
            + "</section>"
            "<section><h5>资产角色</h5>"
            + render_artifact_role_contract(step.get("artifact_role_contract", {}))
            + "</section>"
            "<section><h5>隐私边界</h5>"
            + render_small_list(step.get("privacy_contract", []), "暂无隐私边界。")
            + "</section>"
            "</div>"
            "</details>"
            "</article>"
        )
    return (
        "<section class='action-evidence-panel'>"
        "<h4>证据采集</h4>"
        "<p>以下条目仍需真实外部或人工证据；提交文件、校验命令和阻断检查必须同时闭环。</p>"
        "<div class='action-evidence-grid'>"
        + "".join(cards)
        + "</div></section>"
    )
