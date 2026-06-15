import html
import os
from pathlib import Path
from typing import Any

from review_studio_action_evidence import render_action_evidence_steps, world_class_action_steps
from review_studio_gates import status_label


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_review_studio.py to keep Review Studio action guidance and source refs out of HTML rendering."


def link_from(output_html: Path, target: Path) -> str:
    return os.path.relpath(target.resolve(), output_html.parent.resolve())


def compact_excerpt(text: str, limit: int = 180) -> str:
    normalized = " ".join(text.strip().split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def find_line_anchor(path: Path, patterns: list[str] | None = None) -> dict[str, Any]:
    if not path.exists():
        return {"line": None, "matched_pattern": "", "excerpt": ""}
    if not patterns:
        return {"line": 1, "matched_pattern": "", "excerpt": ""}
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {"line": 1, "matched_pattern": "", "excerpt": ""}
    for pattern in patterns:
        for index, line in enumerate(lines, start=1):
            if pattern in line:
                return {
                    "line": index,
                    "matched_pattern": pattern,
                    "excerpt": compact_excerpt(line),
                }
    first_line = compact_excerpt(lines[0]) if lines else ""
    return {"line": 1, "matched_pattern": "", "excerpt": first_line}


def find_line(path: Path, patterns: list[str] | None = None) -> int | None:
    return find_line_anchor(path, patterns).get("line")


def source_refs(
    skill_dir: Path,
    output_html: Path,
    specs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for spec in specs:
        rel_path = str(spec.get("path", "")).strip()
        if not rel_path:
            continue
        path = skill_dir / rel_path
        exists = path.exists()
        anchor = find_line_anchor(path, spec.get("patterns", []))
        refs.append(
            {
                "path": rel_path,
                "label": str(spec.get("label", rel_path)),
                "kind": str(spec.get("kind", "source")),
                "line": anchor.get("line"),
                "matched_pattern": anchor.get("matched_pattern", ""),
                "excerpt": anchor.get("excerpt", ""),
                "exists": exists,
                "link": link_from(output_html, path) if exists else "",
            }
        )
    return refs


ACTION_GUIDANCE: dict[str, dict[str, Any]] = {
    "intent-canvas": {
        "summary": "收紧真实任务、输入、输出、排除项和成功标准。",
        "why": "低 intent confidence 会让后续 Skill IR、输出评测和 Review Studio 结论建立在模糊意图上。",
        "source_fix": "reports/intent-dialogue.md + reports/intent-confidence.md",
        "source_paths": [
            {"path": "reports/intent-dialogue.md", "label": "intent dialogue", "kind": "report", "patterns": ["# Intent"]},
            {"path": "reports/intent-confidence.md", "label": "intent confidence", "kind": "report", "patterns": ["# Intent"]},
        ],
        "verification": "python3 scripts/yao.py intent-confidence .",
    },
    "trigger-lab": {
        "summary": "修正 route scorecard 中的误触发、漏触发或 ambiguous case。",
        "why": "触发错误会让正确 Skill 失活，或让相邻 Skill 被错误调用。",
        "source_fix": "SKILL.md frontmatter description + evals/*/trigger_cases.json",
        "source_paths": [
            {"path": "SKILL.md", "label": "frontmatter description", "kind": "source", "patterns": ["description:"]},
            {"path": "evals/trigger_cases.json", "label": "trigger eval cases", "kind": "eval", "patterns": ["should_trigger"]},
            {"path": "reports/route_scorecard.md", "label": "route scorecard", "kind": "report", "patterns": ["# Route"]},
        ],
        "verification": "python3 scripts/build_confusion_matrix.py",
    },
    "output-lab": {
        "summary": "补足 output eval 覆盖、execution evidence、blind A/B 和 reviewer adjudication。",
        "why": "没有输出质量和人工盲评证据时，Skill 只能证明会触发，不能证明输出真的更好且经得起审查。",
        "source_fix": "evals/output/cases.jsonl + reports/output_quality_scorecard.md + reports/output_review_kit.html + reports/output_review_adjudication.md",
        "source_paths": [
            {"path": "evals/output/cases.jsonl", "label": "output eval cases", "kind": "eval", "patterns": ["case_id"]},
            {"path": "reports/output_quality_scorecard.md", "label": "output scorecard", "kind": "report", "patterns": ["# Output"]},
            {"path": "reports/output_execution_runs.md", "label": "output execution runs", "kind": "report", "patterns": ["# Output Execution"]},
            {"path": "reports/output_blind_review_pack.md", "label": "blind A/B review pack", "kind": "report", "patterns": ["# Output Blind"]},
            {"path": "reports/output_review_kit.html", "label": "reviewer cockpit", "kind": "report", "patterns": ["Output Review Kit", "Variant A"]},
            {"path": "reports/output_review_adjudication.md", "label": "review adjudication", "kind": "report", "patterns": ["# Output Review"]},
        ],
        "verification": "python3 scripts/adjudicate_output_review.py --write-template && python3 scripts/yao.py output-review",
    },
    "context-budget": {
        "summary": "压缩或拆分高成本 deferred resources，保留最小可路由上下文。",
        "why": "初始加载可以安全，但后续 references、scripts、evals 体量过大时，reviewer 仍需要看到维护和读取成本。",
        "source_fix": "SKILL.md + references/ + scripts/ + evals/",
        "source_paths": [
            {"path": "SKILL.md", "label": "entrypoint", "kind": "source", "patterns": ["# Yao Meta Skill"]},
            {"path": "reports/context_budget.md", "label": "context budget", "kind": "report", "patterns": ["# Context"]},
            {"path": "scripts/resource_boundary_check.py", "label": "resource boundary checker", "kind": "source", "patterns": ["DEFERRED_RESOURCE"]},
            {"path": "references/skill-engineering-method.md", "label": "skill engineering method", "kind": "method", "patterns": ["Design Principle"]},
        ],
        "verification": "python3 scripts/render_context_reports.py",
    },
    "runtime-matrix": {
        "summary": "修复目标端结构、metadata、相对路径、fallback 或 adapter target 声明。",
        "why": "runtime conformance 失败意味着包可能被目标客户端错误加载或静默降级。",
        "source_fix": "agents/interface.yaml + reports/conformance_matrix.md",
        "source_paths": [
            {"path": "agents/interface.yaml", "label": "portable interface", "kind": "source", "patterns": ["adapter_targets"]},
            {"path": "reports/conformance_matrix.md", "label": "conformance matrix", "kind": "report", "patterns": ["# Runtime"]},
        ],
        "verification": "python3 scripts/run_conformance_suite.py .",
    },
    "trust-report": {
        "summary": "处理脚本 help surface、依赖 pin、network policy、secret 和权限声明。",
        "why": "团队分发时，脚本和依赖是主要供应链风险面，warning 必须有明确处置。",
        "source_fix": "reports/security_trust_report.md + security/*.md + scripts/",
        "source_paths": [
            {"path": "reports/security_trust_report.md", "label": "trust report", "kind": "report", "patterns": ["# Security"]},
            {"path": "security/script_policy.md", "label": "script policy", "kind": "policy", "patterns": ["# Script"]},
            {"path": "security/network_policy.md", "label": "network policy", "kind": "policy", "patterns": ["# Network"]},
        ],
        "verification": "python3 scripts/trust_check.py .",
    },
    "python-compat": {
        "summary": "修复 Python 3.11 语法兼容问题，尤其是 f-string 表达式内的反斜杠转义。",
        "why": "目标运行环境可能仍停留在 Python 3.11，语法漂移会让 CLI、报告生成和 CI 在发布后直接失败。",
        "source_fix": "reports/python_compatibility.md + scripts/*.py + tests/*.py",
        "source_paths": [
            {"path": "reports/python_compatibility.md", "label": "Python compatibility", "kind": "report", "patterns": ["# Python"]},
            {"path": "scripts/python_compat_check.py", "label": "compatibility checker", "kind": "source", "patterns": ["SCRIPT_INTERFACE"]},
            {"path": ".github/workflows/test.yml", "label": "CI test workflow", "kind": "ci", "patterns": ["python"]},
        ],
        "verification": "python3 scripts/yao.py python-compat .",
    },
    "architecture-maintainability": {
        "summary": "处理大文件和 CLI command surface 的维护性热点，优先拆分稳定职责边界。",
        "why": "Meta Skill 的门禁、报告和 CLI 会持续增长；如果不把架构债纳入审查，后续能力会越来越难验证和迁移。",
        "source_fix": "reports/architecture_maintainability.md + scripts/yao.py + scripts/render_review_studio.py",
        "source_paths": [
            {"path": "reports/architecture_maintainability.md", "label": "architecture maintainability", "kind": "report", "patterns": ["# Architecture"]},
            {"path": "scripts/yao.py", "label": "Yao CLI orchestrator", "kind": "source", "patterns": ["def command_"]},
            {"path": "scripts/render_review_studio.py", "label": "Review Studio renderer", "kind": "source", "patterns": ["def render_html"]},
            {"path": "scripts/review_studio_actions.py", "label": "Review Studio actions", "kind": "source", "patterns": ["ACTION_GUIDANCE"]},
            {"path": "scripts/render_review_viewer.py", "label": "review viewer renderer", "kind": "source", "patterns": ["def "]},
        ],
        "verification": "python3 scripts/yao.py architecture-audit .",
    },
    "permission-gates": {
        "summary": "补齐高权限能力的 reviewer、scope、reason、expires_at 和目标端 enforcement 说明。",
        "why": "权限契约只有在批准人、有效期和目标端处置方式明确时，才能支撑 governed release。",
        "source_fix": "security/permission_policy.json + security/permission_policy.md",
        "source_paths": [
            {"path": "security/permission_policy.json", "label": "permission approvals", "kind": "policy", "patterns": ["approved"]},
            {"path": "security/permission_policy.md", "label": "permission method", "kind": "policy", "patterns": ["# Permission"]},
        ],
        "verification": "python3 scripts/trust_check.py .",
    },
    "permission-runtime": {
        "summary": "生成并修复目标包的 runtime permission probe 报告。",
        "why": "目标端即使只能提供 metadata fallback，也必须明确 native enforcement 缺口、表示位置和 operator note。",
        "source_fix": "dist/targets/*/adapter.json + reports/runtime_permission_probes.md",
        "source_paths": [
            {"path": "reports/runtime_permission_probes.md", "label": "runtime permission probes", "kind": "report", "patterns": ["# Runtime"]},
            {"path": "dist/targets/openai/adapter.json", "label": "OpenAI adapter", "kind": "package", "patterns": ["target_permission_contract"]},
            {"path": "dist/targets/claude/adapter.json", "label": "Claude adapter", "kind": "package", "patterns": ["target_permission_contract"]},
            {"path": "dist/targets/generic/adapter.json", "label": "generic adapter", "kind": "package", "patterns": ["target_permission_contract"]},
        ],
        "verification": "python3 scripts/probe_runtime_permissions.py . --package-dir dist",
    },
    "skill-atlas": {
        "summary": "处理 portfolio 里的路由冲突、owner 缺口、stale skill 和重复能力。",
        "why": "单个 Skill 质量很高仍可能在团队 skill library 中被相邻 Skill 冲突削弱。",
        "source_fix": "reports/skill_atlas.html + skill_atlas/catalog.json",
        "source_paths": [
            {"path": "skill_atlas/catalog.json", "label": "skill atlas catalog", "kind": "atlas", "patterns": ["summary"]},
            {"path": "skill_atlas/policy.json", "label": "atlas scope policy", "kind": "policy", "patterns": ["scope"]},
            {"path": "reports/skill_atlas.html", "label": "skill atlas report", "kind": "report", "patterns": ["Skill Atlas"]},
        ],
        "verification": "python3 scripts/build_skill_atlas.py --workspace-root .",
    },
    "operations-loop": {
        "summary": "记录 metadata-only 使用事件，或明确当前 release 缺少真实使用信号。",
        "why": "没有运营回路时，reviewer 无法判断采用率、误触发、坏输出和 review overdue 的真实影响。",
        "source_fix": "reports/adoption_drift_report.md",
        "source_paths": [
            {"path": "reports/adoption_drift_report.md", "label": "adoption drift report", "kind": "report", "patterns": ["# Adoption"]},
            {"path": "references/telemetry-drift-method.md", "label": "telemetry method", "kind": "method", "patterns": ["# Telemetry"]},
        ],
        "verification": "python3 scripts/render_adoption_drift_report.py . --record-event skill_activation --activation-type explicit --outcome accepted",
    },
    "review-waivers": {
        "summary": "对保留的 warning 写入 reviewer、理由、范围和到期时间，或修掉 warning。",
        "why": "warning 可以被接受，但必须可审计、会过期，并且不能掩盖 blocker。",
        "source_fix": "reports/review_waivers.md",
        "source_paths": [
            {"path": "reports/review_waivers.md", "label": "waiver ledger", "kind": "report", "patterns": ["# Review"]},
            {"path": "references/review-waiver-method.md", "label": "waiver method", "kind": "method", "patterns": ["# Review"]},
        ],
        "verification": "python3 scripts/render_review_waivers.py .",
    },
    "world-class-evidence": {
        "summary": "补齐 provider、真人盲评、原生权限执行和真实客户端遥测证据，或明确本次发布不声明 world-class 完成。",
        "why": "世界级结论必须来自已接受的外部/人工证据；计划、metadata fallback、待评审和本地命令都不能替代完成证据。",
        "source_fix": "reports/world_class_operator_runbook.html + reports/world_class_evidence_ledger.md + reports/world_class_evidence_intake.md + reports/world_class_submission_review.md",
        "source_paths": [
            {"path": "reports/world_class_evidence_ledger.md", "label": "world-class evidence ledger", "kind": "report", "patterns": ["# World-Class Evidence Ledger"]},
            {"path": "reports/world_class_evidence_plan.md", "label": "world-class evidence plan", "kind": "report", "patterns": ["# World-Class Evidence Plan"]},
            {"path": "reports/world_class_evidence_intake.md", "label": "world-class evidence intake", "kind": "report", "patterns": ["# World-Class Evidence Intake"]},
            {"path": "reports/world_class_submission_review.md", "label": "world-class submission review", "kind": "report", "patterns": ["# World-Class Submission Review"]},
            {"path": "reports/world_class_claim_guard.md", "label": "world-class claim guard", "kind": "report", "patterns": ["# World-Class Claim Guard"]},
            {"path": "evidence/world_class/intake.schema.json", "label": "evidence intake schema", "kind": "schema", "patterns": ["Yao World-Class Evidence Intake"]},
            {"path": "evidence/world_class/templates/provider-holdout.intake.json", "label": "provider intake template", "kind": "template", "patterns": ["provider-holdout"]},
            {"path": "evidence/world_class/templates/human-adjudication.intake.json", "label": "human intake template", "kind": "template", "patterns": ["human-adjudication"]},
            {"path": "evidence/world_class/templates/native-permission-enforcement.intake.json", "label": "permission intake template", "kind": "template", "patterns": ["native-permission-enforcement"]},
            {"path": "evidence/world_class/templates/native-client-telemetry.intake.json", "label": "telemetry intake template", "kind": "template", "patterns": ["native-client-telemetry"]},
            {"path": "reports/skill_os2_audit.md", "label": "Skill OS 2.0 audit", "kind": "report", "patterns": ["# Skill OS"]},
            {"path": "reports/output_review_decisions.json", "label": "human review decisions", "kind": "report", "patterns": ["winner_variant"]},
            {"path": "reports/runtime_permission_probes.md", "label": "runtime permission probes", "kind": "report", "patterns": ["# Runtime"]},
            {"path": "reports/adoption_drift_report.md", "label": "adoption drift", "kind": "report", "patterns": ["# Adoption"]},
        ],
        "verification": (
            "python3 scripts/yao.py world-class-runbook . --submissions-dir evidence/world_class/submissions "
            "&& python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions "
            "&& python3 scripts/yao.py review-studio ."
        ),
    },
    "registry-audit": {
        "summary": "补齐 registry package metadata、checksum、license、owner、review cadence 和 install evidence。",
        "why": "分发元数据不完整时，团队无法安全安装、升级或追溯包体来源。",
        "source_fix": "registry/ + reports/registry_audit.md",
        "source_paths": [
            {"path": "registry/packages/yao-meta-skill.json", "label": "registry package", "kind": "registry", "patterns": ["version"]},
            {"path": "reports/registry_audit.md", "label": "registry audit", "kind": "report", "patterns": ["# Registry"]},
            {"path": "reports/install_simulation.md", "label": "install simulation", "kind": "report", "patterns": ["# Install"]},
        ],
        "verification": "python3 scripts/registry_audit.py .",
    },
    "release-notes": {
        "summary": "确认 promotion、upgrade diff、breaking changes、migration guide 和 known limitations。",
        "why": "发布说明不完整会让使用者无法判断升级风险和迁移动作。",
        "source_fix": "reports/upgrade_check.md + docs/migration-v2.md",
        "source_paths": [
            {"path": "reports/upgrade_check.md", "label": "upgrade check", "kind": "report", "patterns": ["# Upgrade"]},
            {"path": "docs/migration-v2.md", "label": "migration guide", "kind": "docs", "patterns": ["# Migration"]},
            {"path": "reports/promotion_decisions.md", "label": "promotion decisions", "kind": "report", "patterns": ["# Promotion"]},
        ],
        "verification": "python3 scripts/upgrade_check.py . --previous-package-json registry/examples/yao-meta-skill-1.0.0.json",
    },
}


def build_review_actions(
    gates: list[dict[str, str]],
    skill_dir: Path,
    output_html: Path,
    data: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for gate_item in gates:
        if gate_item["status"] == "pass":
            continue
        guidance = ACTION_GUIDANCE.get(
            gate_item["key"],
            {
                "summary": "打开证据报告，修复当前 gate 暴露的问题。",
                "why": "该 gate 未通过，release reviewer 需要明确处置动作。",
                "source_fix": gate_item.get("evidence", ""),
                "source_paths": [],
                "verification": "python3 scripts/render_review_studio.py .",
            },
        )
        refs = source_refs(skill_dir, output_html, guidance.get("source_paths", []))
        actions.append(
            {
                "gate_key": gate_item["key"],
                "label": gate_item["label"],
                "status": gate_item["status"],
                "priority": "blocker" if gate_item["status"] == "block" else "warning",
                "summary": guidance["summary"],
                "why": guidance["why"],
                "source_fix": guidance["source_fix"],
                "source_refs": refs,
                "evidence": gate_item.get("evidence", ""),
                "evidence_link": gate_item.get("link", ""),
                "verification_command": guidance["verification"],
                "evidence_steps": world_class_action_steps(data or {})
                if gate_item["key"] == "world-class-evidence"
                else [],
            }
        )
    return actions


def render_action_source_refs(refs: list[dict[str, Any]]) -> str:
    if not refs:
        return "<p class='muted'>暂无结构化 source refs；请先打开证据报告。</p>"
    items = []
    for ref in refs:
        line_suffix = f":{ref['line']}" if ref.get("line") else ""
        label = f"{ref['path']}{line_suffix}"
        if ref.get("exists") and ref.get("link"):
            path_html = f"<a href='{html.escape(ref['link'])}'>{html.escape(label)}</a>"
        else:
            path_html = f"<span>{html.escape(label)} · missing</span>"
        pattern = str(ref.get("matched_pattern", "")).strip()
        excerpt = str(ref.get("excerpt", "")).strip()
        anchor_bits = [html.escape(str(ref.get("label", "source"))), html.escape(str(ref.get("kind", "source")))]
        if pattern:
            anchor_bits.append("pattern: " + html.escape(pattern))
        meta_html = " · ".join(anchor_bits)
        excerpt_html = f"<blockquote>{html.escape(excerpt)}</blockquote>" if excerpt else ""
        items.append(
            "<li>"
            f"{path_html}"
            f"<small>{meta_html}</small>"
            f"{excerpt_html}"
            "</li>"
        )
    return "<ul class='source-ref-list'>" + "".join(items) + "</ul>"


def render_review_actions(actions: list[dict[str, Any]]) -> str:
    if not actions:
        return "<p class='muted'>当前没有 blocker 或 warning。保持现有证据链即可。</p>"
    cards = []
    for item in actions:
        link_html = f"<a href='{html.escape(item['evidence_link'])}'>打开证据</a>" if item.get("evidence_link") else ""
        source_refs_html = render_action_source_refs(item.get("source_refs", []))
        evidence_steps_html = render_action_evidence_steps(item.get("evidence_steps", []))
        card_class = "action-card " + html.escape(item["status"])
        if item.get("evidence_steps"):
            card_class += " with-evidence"
        cards.append(
            "<article class='" + card_class + "'>"
            f"<div><span>{html.escape(status_label(item['status']))}</span><h3>{html.escape(item['label'])}</h3></div>"
            f"<p>{html.escape(item['summary'])}</p>"
            f"<small>{html.escape(item['why'])}</small>"
            f"<dl><dt>修复位置</dt><dd>{html.escape(item['source_fix'])}</dd>"
            f"<dt>验证命令</dt><dd><code>{html.escape(item['verification_command'])}</code></dd></dl>"
            f"{evidence_steps_html}"
            f"{source_refs_html}"
            f"<footer>{html.escape(item['evidence'])} {link_html}</footer>"
            "</article>"
        )
    return "".join(cards)
