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
    steps = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        key = str(entry.get("key", "")).strip()
        if not key:
            continue
        checklist = intake_by_key.get(key, {})
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
        derived_pass_count = sum(1 for row in source_checks if isinstance(row, dict) and str(row.get("status", "")) == "pass")
        runbook = entry.get("runbook", [])
        if not runbook and isinstance(checklist.get("must_collect", {}), dict):
            runbook = checklist["must_collect"].get("runbook", [])
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
                "commands": action_command_rows(checklist.get("commands", {}) if isinstance(checklist.get("commands", {}), dict) else {}),
                "runbook": [str(item) for item in runbook[:3]],
            }
        )
    return steps


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
            f"<dt>下一步</dt><dd>{html.escape(str(step.get('next_action', '')))}</dd></dl>"
            "<section><h5>阻断检查</h5>"
            + (
                "<ul class='action-evidence-checks'>" + "".join(blocked_checks) + "</ul>"
                if blocked_checks
                else "<p class='muted'>暂无阻断检查。</p>"
            )
            + "</section>"
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
