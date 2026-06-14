#!/usr/bin/env python3
"""World-class evidence HTML helpers for Review Studio."""

import html
from typing import Any

from world_class_source_checks import build_source_checklist


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_review_studio.py to render world-class evidence cards."


def render_inline_list(items: list[Any], empty_label: str) -> str:
    if not items:
        return f"<p class='muted'>{html.escape(empty_label)}</p>"
    return "<ul>" + "".join(f"<li>{html.escape(str(item))}</li>" for item in items) + "</ul>"


def render_source_checks(entry: dict[str, Any]) -> str:
    rows = build_source_checklist([entry])
    if not rows:
        return "<p class='muted'>暂无源证据检查。</p>"
    items = []
    for row in rows:
        status = str(row.get("status", "blocked"))
        items.append(
            "<li class='world-source-check "
            + html.escape(status)
            + "'>"
            f"<span>{html.escape(str(row.get('label', '')))}</span>"
            f"<code>{html.escape(str(row.get('field', '')))}: {html.escape(str(row.get('actual', '')))} / {html.escape(str(row.get('expected', '')))}</code>"
            f"<small>{html.escape(str(row.get('next_action', '')))}</small>"
            "</li>"
        )
    return "<ul class='world-source-checks'>" + "".join(items) + "</ul>"


def render_world_class_evidence_entries(ledger: dict[str, Any]) -> str:
    entries = ledger.get("entries", []) if isinstance(ledger, dict) else []
    if not entries:
        return "<p class='muted'>当前没有 world-class 证据条目。</p>"
    cards = []
    for entry in entries:
        observed = entry.get("observed_state", {}) if isinstance(entry.get("observed_state", {}), dict) else {}
        observed_summary = "; ".join(f"{key}: {value}" for key, value in observed.items())
        submission = entry.get("submission_state", {}) if isinstance(entry.get("submission_state", {}), dict) else {}
        submission_summary = "; ".join(
            f"{key}: {value}" for key, value in submission.items() if key in {"status", "path", "attested_real_evidence", "privacy_contract_satisfied"}
        )
        status = str(entry.get("status", "pending"))
        status_label_text = "已接受" if status == "accepted" else "待补证"
        cards.append(
            "<article class='world-evidence-card "
            + html.escape(status)
            + "'>"
            f"<div><span>{html.escape(status_label_text)} · {html.escape(str(entry.get('category', '')))}</span>"
            f"<h3>{html.escape(str(entry.get('label', entry.get('key', 'evidence'))))}</h3></div>"
            f"<p>{html.escape(str(entry.get('objective', '')))}</p>"
            f"<dl><dt>负责人</dt><dd>{html.escape(str(entry.get('owner', '')))}</dd>"
            f"<dt>当前状态</dt><dd>{html.escape(str(entry.get('current', '')))}</dd>"
            f"<dt>下一步</dt><dd>{html.escape(str(entry.get('next_action', '')))}</dd>"
            f"<dt>观测值</dt><dd>{html.escape(observed_summary or '无')}</dd>"
            f"<dt>提交态</dt><dd>{html.escape(submission_summary or 'missing')}</dd></dl>"
            "<div class='world-evidence-columns'>"
            "<div><h4>完成定义</h4>"
            + render_inline_list(entry.get("success_checks", []), "暂无完成定义。")
            + "</div>"
            "<div><h4>证据来源</h4>"
            + render_inline_list(entry.get("evidence_artifacts", []), "暂无证据来源。")
            + "</div>"
            "<div><h4>隐私约束</h4>"
            + render_inline_list(entry.get("privacy_contract", []), "暂无隐私约束。")
            + "</div>"
            "</div>"
            "<section class='world-source-panel'><h4>源证据检查</h4>"
            + render_source_checks(entry)
            + "</section>"
            "</article>"
        )
    return "<div class='world-evidence-grid'>" + "".join(cards) + "</div>"


def render_command_list(commands: dict[str, Any]) -> str:
    if not commands:
        return "<p class='muted'>暂无命令。</p>"
    items = []
    for label, command in commands.items():
        if not command:
            continue
        items.append(
            "<li>"
            f"<span>{html.escape(str(label))}</span>"
            f"<code>{html.escape(str(command))}</code>"
            "</li>"
        )
    return "<ul class='world-intake-commands'>" + "".join(items) + "</ul>" if items else "<p class='muted'>暂无命令。</p>"


def render_world_class_intake_checklist(intake: dict[str, Any]) -> str:
    items = intake.get("operator_checklist", []) if isinstance(intake, dict) else []
    if not items:
        return "<p class='muted'>当前没有 world-class 证据操作清单。</p>"
    cards = []
    for item in items:
        readiness = str(item.get("readiness", "awaiting-submission"))
        must_collect = item.get("must_collect", {}) if isinstance(item.get("must_collect", {}), dict) else {}
        cards.append(
            "<article class='world-intake-card "
            + html.escape(readiness)
            + "'>"
            f"<div><span>{html.escape(readiness)} · {html.escape(str(item.get('category', '')))}</span>"
            f"<h3>{html.escape(str(item.get('label', item.get('evidence_key', 'evidence'))))}</h3></div>"
            f"<p>{html.escape(str(item.get('blocking_reason', '')))}</p>"
            f"<dl><dt>负责人</dt><dd>{html.escape(str(item.get('owner', '')))}</dd>"
            f"<dt>模板</dt><dd><code>{html.escape(str(item.get('template_path', '')))}</code></dd>"
            f"<dt>提交</dt><dd><code>{html.escape(str(item.get('submission_path', '')))}</code></dd>"
            f"<dt>下一步</dt><dd>{html.escape(str(item.get('next_action', '')))}</dd></dl>"
            "<div class='world-intake-steps'>"
            "<div><h4>操作命令</h4>"
            + render_command_list(item.get("commands", {}) if isinstance(item.get("commands", {}), dict) else {})
            + "</div>"
            "<div><h4>收集要求</h4>"
            + render_inline_list(must_collect.get("provenance_requirements", []), "暂无来源要求。")
            + "</div>"
            "<div><h4>通过条件</h4>"
            + render_inline_list(must_collect.get("success_checks", []), "暂无通过条件。")
            + "</div>"
            "<div><h4>隐私边界</h4>"
            + render_inline_list(must_collect.get("privacy_contract", []), "暂无隐私边界。")
            + "</div>"
            "</div>"
            "</article>"
        )
    return "<div class='world-intake-grid'>" + "".join(cards) + "</div>"
