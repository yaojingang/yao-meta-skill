#!/usr/bin/env python3
"""World-class evidence HTML helpers for Review Studio."""

import html
from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_review_studio.py to render world-class evidence cards."


def render_inline_list(items: list[Any], empty_label: str) -> str:
    if not items:
        return f"<p class='muted'>{html.escape(empty_label)}</p>"
    return "<ul>" + "".join(f"<li>{html.escape(str(item))}</li>" for item in items) + "</ul>"


def render_world_class_evidence_entries(ledger: dict[str, Any]) -> str:
    entries = ledger.get("entries", []) if isinstance(ledger, dict) else []
    if not entries:
        return "<p class='muted'>当前没有 world-class 证据条目。</p>"
    cards = []
    for entry in entries:
        observed = entry.get("observed_state", {}) if isinstance(entry.get("observed_state", {}), dict) else {}
        observed_summary = "; ".join(f"{key}: {value}" for key, value in observed.items())
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
            f"<dt>观测值</dt><dd>{html.escape(observed_summary or '无')}</dd></dl>"
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
            "</article>"
        )
    return "<div class='world-evidence-grid'>" + "".join(cards) + "</div>"
