#!/usr/bin/env python3
"""Output review HTML helpers for Review Studio."""

import html
from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_review_studio.py to render output review checklist cards."


def render_required_fields(fields: dict[str, Any]) -> str:
    if not fields:
        return "<p class='muted'>暂无字段要求。</p>"
    items = []
    for key, value in fields.items():
        items.append(f"<li><strong>{html.escape(str(key))}</strong><span>{html.escape(str(value))}</span></li>")
    return "<ul class='output-review-fields'>" + "".join(items) + "</ul>"


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
    return "<ul class='output-review-commands'>" + "".join(items) + "</ul>" if items else "<p class='muted'>暂无命令。</p>"


def render_contract(items: list[Any]) -> str:
    if not items:
        return "<p class='muted'>暂无边界。</p>"
    return "<ul>" + "".join(f"<li>{html.escape(str(item))}</li>" for item in items) + "</ul>"


def render_output_review_checklist(adjudication: dict[str, Any]) -> str:
    checklist = adjudication.get("reviewer_checklist", []) if isinstance(adjudication, dict) else []
    if not checklist:
        return "<p class='muted'>当前没有输出评审操作清单。</p>"
    cards = []
    for item in checklist:
        readiness = str(item.get("readiness", "awaiting-decision"))
        answer_key = "可见" if item.get("answer_key_visible") else "隐藏"
        cards.append(
            "<article class='output-review-card "
            + html.escape(readiness)
            + "'>"
            f"<div><span>{html.escape(readiness)} · 答案{html.escape(answer_key)}</span>"
            f"<h3>{html.escape(str(item.get('case_id', 'case')))}</h3></div>"
            f"<p>{html.escape(str(item.get('blocking_reason', '')))}</p>"
            f"<dl><dt>盲评包</dt><dd><code>{html.escape(str(item.get('blind_pack_path', '')))}</code></dd>"
            f"<dt>决策表</dt><dd><code>{html.escape(str(item.get('decisions_path', '')))}</code></dd>"
            f"<dt>提示词</dt><dd>{html.escape(str(item.get('prompt', '')))}</dd></dl>"
            "<div class='output-review-steps'>"
            "<div><h4>操作命令</h4>"
            + render_command_list(item.get("commands", {}) if isinstance(item.get("commands", {}), dict) else {})
            + "</div>"
            "<div><h4>字段要求</h4>"
            + render_required_fields(item.get("required_fields", {}) if isinstance(item.get("required_fields", {}), dict) else {})
            + "</div>"
            "<div><h4>隐私边界</h4>"
            + render_contract(item.get("privacy_contract", []) if isinstance(item.get("privacy_contract", []), list) else [])
            + "</div>"
            "</div>"
            "</article>"
        )
    return "<div class='output-review-grid'>" + "".join(cards) + "</div>"


def render_output_review_section(adjudication: dict[str, Any]) -> str:
    return (
        "<section>"
        "<h2>评审清单</h2>"
        "<p class='muted'>先打开 reports/output_review_kit.md；每张卡片对应一个 blind A/B case，说明当前是否待判、答案是否仍隐藏、应填写的决策文件、有效字段和复跑命令。</p>"
        f"{render_output_review_checklist(adjudication)}"
        "</section>"
    )
