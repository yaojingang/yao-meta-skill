"""World-class evidence shaping for the static skill overview report."""

SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by skill_report_model.py to summarize world-class evidence readiness and roadmap actions."

WORLD_CLASS_ENTRY_COPY = {
    "provider-holdout": {
        "label_zh": "提供商留出",
        "label_en": "Provider Holdout",
        "summary_zh": "缺少真实 provider 模型运行和 token metadata。",
        "summary_en": "Missing a real provider model run and token metadata.",
    },
    "human-adjudication": {
        "label_zh": "人工盲评",
        "label_en": "Human Adjudication",
        "summary_zh": "盲评 pair 仍待真实 reviewer 决策。",
        "summary_en": "Blind-review pairs still need real reviewer decisions.",
    },
    "native-permission-enforcement": {
        "label_zh": "原生权限",
        "label_en": "Native Permission",
        "summary_zh": "原生 runtime enforcement 仍待目标客户端或外部安装器证明。",
        "summary_en": "Native runtime enforcement still needs target-client or external-installer proof.",
    },
    "native-client-telemetry": {
        "label_zh": "原生遥测",
        "label_en": "Native Telemetry",
        "summary_zh": "真实外部客户端 metadata-only 事件仍未导入。",
        "summary_en": "Real external-client metadata-only events have not been imported yet.",
    },
}


def world_class_readiness(ledger: dict) -> dict:
    summary = ledger.get("summary", {}) if isinstance(ledger, dict) else {}
    entries = ledger.get("entries", []) if isinstance(ledger, dict) else []
    if not isinstance(entries, list):
        entries = []
    source_check_count = int(summary.get("source_check_count", 0) or 0)
    source_pass_count = int(summary.get("source_pass_count", 0) or 0)
    pending_count = int(summary.get("pending_count", len(entries)) or 0)
    accepted_count = int(summary.get("accepted_count", 0) or 0)
    entry_count = int(summary.get("ledger_entry_count", len(entries)) or 0)
    ready = bool(summary.get("ready_to_claim_world_class", False))
    decision = str(summary.get("decision", "not-generated" if entry_count == 0 else "evidence-pending"))
    if entry_count == 0:
        conclusion_zh = "未生成 world-class ledger；当前报告不会宣称世界级完成。"
        conclusion_en = "No world-class ledger was generated; this report does not claim world-class completion."
    elif ready:
        conclusion_zh = "世界级证据已被 ledger 接受，可进入公开 claim 前的最终复核。"
        conclusion_en = "World-class evidence is accepted by the ledger and can move to final claim review."
    else:
        conclusion_zh = f"世界级证据尚未完成：{pending_count} 项待补，{accepted_count} 项已接受。"
        conclusion_en = f"World-class evidence is not complete: {pending_count} pending, {accepted_count} accepted."

    items = []
    for entry in entries[:4]:
        if not isinstance(entry, dict):
            continue
        key = str(entry.get("key", ""))
        copy = WORLD_CLASS_ENTRY_COPY.get(key, {})
        category = str(entry.get("category", "external"))
        checklist = entry.get("source_checklist", [])
        blocked_checks = [
            str(check.get("label", ""))
            for check in checklist
            if isinstance(check, dict) and check.get("status") == "blocked" and str(check.get("label", "")).strip()
        ][:3]
        items.append(
            {
                "key": key,
                "label_zh": copy.get("label_zh", str(entry.get("label", key))),
                "label_en": copy.get("label_en", str(entry.get("label", key))),
                "category": category,
                "category_zh": "人工证据" if category == "human" else "外部证据",
                "category_en": "Human evidence" if category == "human" else "External evidence",
                "status": str(entry.get("status", "pending")),
                "summary_zh": copy.get("summary_zh", str(entry.get("current", ""))),
                "summary_en": copy.get("summary_en", str(entry.get("current", ""))),
                "blocked_checks": blocked_checks,
            }
        )
    return {
        "ready": ready,
        "decision": decision,
        "entry_count": entry_count,
        "pending_count": pending_count,
        "accepted_count": accepted_count,
        "external_pending_count": int(summary.get("external_pending_count", 0) or 0),
        "human_pending_count": int(summary.get("human_pending_count", 0) or 0),
        "source_check_count": source_check_count,
        "source_pass_count": source_pass_count,
        "conclusion_zh": conclusion_zh,
        "conclusion_en": conclusion_en,
        "entries": items,
    }


def world_class_roadmap_item(readiness: dict) -> dict | None:
    if not isinstance(readiness, dict):
        return None
    pending_count = int(readiness.get("pending_count", 0) or 0)
    if readiness.get("ready") or pending_count <= 0:
        return None
    actions = []
    entries = [entry for entry in readiness.get("entries", []) if isinstance(entry, dict)]
    for entry in entries[:2]:
        label = str(entry.get("label_zh") or entry.get("key") or "证据项")
        summary = str(entry.get("summary_zh") or "仍待补充真实证据。")
        actions.append(f"补齐{label}证据：{summary}")
    remaining = pending_count - len(actions)
    if remaining > 0:
        actions.append(f"继续补齐剩余 {remaining} 项外部/人工证据，并保持 claim guard 为 pending 状态。")
    else:
        actions.append("提交有效 intake packet，并让 ledger 通过 artifact SHA-256 校验。")
    return {
        "title": "补齐世界证据",
        "why": f"世界级证据仍有 {pending_count} 项待补；公开完成态 claim 必须继续保持阻塞。",
        "actions": actions[:3],
        "unlocks": "全部外部/人工证据被 ledger 接受后，才能进入公开 world-class claim 复核。",
        "source": "world_class_evidence_ledger",
    }
