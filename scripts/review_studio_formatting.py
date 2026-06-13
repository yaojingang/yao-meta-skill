#!/usr/bin/env python3
"""Formatting helpers for Review Studio panels."""

import html
from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_review_studio.py to format report dictionaries as audit UI panels."


LABELS = {
    "actionable_owner_gap_count": "待处理 owner",
    "actionable_route_collision_count": "待处理冲突",
    "actionable_skill_count": "纳入审查",
    "actionable_stale_count": "待处理过期",
    "adoption_rate": "采用率",
    "adapter_count": "Adapter",
    "archive_entry_count": "Zip 条目",
    "archive_present": "归档存在",
    "archive_sha256": "归档哈希",
    "answer_revealed_count": "答案揭示",
    "baseline_pass_rate": "Baseline",
    "breaking_change_count": "破坏变更",
    "case_count": "案例数",
    "command_executed_count": "命令执行",
    "compatibility_pass_count": "兼容通过",
    "covered_gate_count": "覆盖 Gate",
    "declared_bump": "声明版本",
    "delta": "增益",
    "event_count": "事件数",
    "failure_count": "失败数",
    "gate_pass": "Gate",
    "help_smoke_failed_count": "Help 失败",
    "install_simulated": "安装模拟",
    "installer_permission_enforced_count": "安装权限",
    "installer_permission_failure_count": "安装权限失败",
    "license": "License",
    "metadata_fallback_count": "Metadata fallback",
    "missed_trigger_count": "漏触发",
    "model_executed_count": "模型执行",
    "name": "名称",
    "native_enforcement_count": "原生执行",
    "network_script_count": "网络脚本",
    "non_actionable_issue_count": "非行动项",
    "open_blocker_count": "阻断批注",
    "open_count": "开放批注",
    "owner": "Owner",
    "package_sha256": "包体哈希",
    "pass_count": "通过数",
    "pending_count": "待审",
    "pending_answer_hidden_count": "答案隐藏",
    "permission_capability_count": "权限能力",
    "permission_target_count": "权限目标",
    "recorded_fixture_count": "记录样本",
    "recommended_bump": "建议版本",
    "residual_risk_count": "残余风险",
    "risk_band": "风险带",
    "route_collision_count": "路由冲突",
    "script_count": "脚本数",
    "secret_findings": "Secret",
    "skill_count": "Skill 数",
    "target_count": "目标数",
    "targets": "目标平台",
    "timing_observed_count": "计时样本",
    "token_estimated_count": "估算 Token",
    "token_observed_count": "真实 Token",
    "trust_level": "信任级别",
    "variant_run_count": "运行数",
    "version": "版本",
    "warning_count": "警告数",
    "with_skill_pass_rate": "With Skill",
}


def label_for_key(key: str) -> str:
    return LABELS.get(key, key.replace("_", " ").title())


def value_text(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, float):
        return str(round(value, 3)).rstrip("0").rstrip(".")
    if isinstance(value, list):
        return ", ".join(value_text(item) for item in value) if value else "无"
    if isinstance(value, dict):
        parts = []
        for key, nested_value in list(value.items())[:6]:
            parts.append(f"{label_for_key(str(key))}: {value_text(nested_value)}")
        return "；".join(parts) if parts else "无"
    return str(value)


def render_kv_grid(
    payload: dict[str, Any],
    keys: list[str],
    empty: str,
) -> str:
    if not payload:
        return f"<p class='muted'>{html.escape(empty)}</p>"
    rows = []
    for key in keys:
        if key not in payload:
            continue
        value = value_text(payload.get(key))
        value_html = html.escape(value)
        if "sha256" in key or "hash" in key or "checksum" in key:
            value_html = f"<code>{value_html}</code>"
        rows.append(
            "<div>"
            f"<dt>{html.escape(label_for_key(key))}</dt>"
            f"<dd>{value_html}</dd>"
            "</div>"
        )
    if not rows:
        return f"<p class='muted'>{html.escape(empty)}</p>"
    return "<dl class='kv-grid'>" + "".join(rows) + "</dl>"


def registry_package_summary(package: dict[str, Any]) -> dict[str, Any]:
    if not package:
        return {}
    compatibility = package.get("compatibility", {}) if isinstance(package.get("compatibility"), dict) else {}
    pass_count = sum(1 for status in compatibility.values() if status == "pass")
    checksums = package.get("checksums", {}) if isinstance(package.get("checksums"), dict) else {}
    return {
        "name": package.get("name", ""),
        "version": package.get("version", ""),
        "maturity": package.get("maturity", ""),
        "owner": package.get("owner", ""),
        "license": package.get("license", ""),
        "trust_level": package.get("trust_level", ""),
        "targets": package.get("targets", []),
        "compatibility_pass_count": f"{pass_count}/{len(compatibility)}",
        "archive_sha256": checksums.get("archive_sha256", ""),
    }
