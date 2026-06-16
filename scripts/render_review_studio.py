#!/usr/bin/env python3
import argparse
import html
import json
from pathlib import Path
from typing import Any

from review_studio_actions import build_review_actions, render_review_actions
from review_studio_data import evidence_paths, insight_cards, load_review_data
from review_studio_formatting import registry_package_summary, render_gate_contract_panel, render_kv_grid
from review_studio_gates import add_blockers_from_gate, build_gates, gate_contract, weighted_score
from review_studio_layout import render_review_nav, review_studio_css
from review_studio_output_review import render_output_review_section
from review_studio_panels import render_gate_list, render_insights, render_issue_list, render_review_annotations_panel
from review_studio_skillops import render_skillops_section
from review_studio_waivers import render_waiver_candidates_panel
from review_studio_world_class import render_world_class_evidence_entries, render_world_class_intake_checklist


ROOT = Path(__file__).resolve().parent.parent


def display_path(skill_dir: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(skill_dir.resolve()))
    except ValueError:
        try:
            return str(path.resolve().relative_to(ROOT.resolve()))
        except ValueError:
            return str(path.resolve())


def render_html(report: dict[str, Any]) -> str:
    summary = report["summary"]
    gates = report["gates"]
    gate_details = {item["key"]: item["detail"] for item in gates}
    blockers = report["blockers"]
    warnings = report["warnings"]
    insights = insight_cards(report["data"])
    overview = report["data"]["overview"]
    manifest = report["data"]["manifest"]
    frontmatter = report["data"]["frontmatter"]
    title = overview.get("display_name") or overview.get("title") or frontmatter.get("name") or manifest.get("name") or "Skill"
    description = overview.get("description") or frontmatter.get("description", "")
    nav_html = render_review_nav()
    gates_html = render_gate_list(gates)
    gate_contract_panel = render_gate_contract_panel(report.get("gate_contract", {}))
    metrics_html = render_insights(insights)
    blockers_html = render_issue_list("阻断事项", blockers)
    warnings_html = render_issue_list("关注事项", warnings)
    actions_html = render_review_actions(report["review_actions"])
    annotations_html = render_review_annotations_panel(report["data"].get("review_annotations", {}))
    output_summary = report["data"]["output_quality"].get("summary", {})
    output_execution_summary = report["data"]["output_execution"].get("summary", {})
    output_blind_summary = report["data"]["output_blind_review"].get("summary", {})
    output_review_summary = report["data"]["output_review_adjudication"].get("summary", {})
    benchmark_report = report["data"].get("benchmark_reproducibility", {})
    benchmark_summary = benchmark_report.get("summary", {})
    public_claim = benchmark_report.get("public_claim", {}) if isinstance(benchmark_report.get("public_claim", {}), dict) else {}
    blueprint_summary = report["data"]["skill_os2_coverage"].get("summary", {})
    conformance_summary = report["data"]["conformance"].get("summary", {})
    compiled_summary = report["data"]["compiled_targets"].get("summary", {})
    trust_summary = report["data"]["trust"].get("summary", {})
    python_compat_summary = report["data"]["python_compatibility"].get("summary", {})
    runtime_permissions_summary = report["data"]["runtime_permissions"].get("summary", {})
    atlas_summary = report["data"]["atlas"].get("summary", {})
    adoption_summary = report["data"]["adoption_drift"].get("summary", {})
    waiver_summary = report["data"]["review_waivers"].get("summary", {})
    world_class_ledger = report["data"].get("world_class_evidence_ledger", {})
    world_class_summary = world_class_ledger.get("summary", {})
    world_class_intake = report["data"].get("world_class_evidence_intake", {})
    world_class_intake_summary = world_class_intake.get("summary", {})
    world_class_claim_summary = report["data"].get("world_class_claim_guard", {}).get("summary", {})
    world_class_entries_html = render_world_class_evidence_entries(world_class_ledger)
    world_class_intake_checklist_html = render_world_class_intake_checklist(world_class_intake)
    annotation_summary = report["data"]["review_annotations"].get("summary", {})
    annotation_caption = (
        f"{annotation_summary.get('annotation_count', 0)} 条批注；"
        f"开放 {annotation_summary.get('open_count', 0)}；"
        f"阻断 {annotation_summary.get('open_blocker_count', 0)}"
    )
    registry_package = report["data"]["registry"].get("package", {})
    package_summary = report["data"]["package_verification"].get("summary", {})
    install_summary = report["data"]["install_simulation"].get("summary", {})
    atlas_panel = render_kv_grid(
        atlas_summary,
        [
            "skill_count",
            "actionable_skill_count",
            "actionable_route_collision_count",
            "actionable_owner_gap_count",
            "actionable_stale_count",
            "telemetry_report_count",
            "actionable_drift_signal_count",
            "drift_signal_count",
            "non_actionable_issue_count",
        ],
        "skill atlas summary missing",
    )
    output_panel = render_kv_grid(
        output_summary,
        ["case_count", "with_skill_pass_rate", "baseline_pass_rate", "delta", "gate_pass", "failure_count"],
        "output eval scorecard missing",
    )
    execution_panel = render_kv_grid(
        output_execution_summary,
        [
            "variant_run_count",
            "command_executed_count",
            "model_executed_count",
            "recorded_fixture_count",
            "timing_observed_count",
            "token_estimated_count",
        ],
        "output execution report missing",
    )
    blind_panel = render_kv_grid(
        output_blind_summary,
        ["pair_count", "answer_key_separate", "with_skill_hidden_count"],
        "blind A/B review pack missing",
    )
    review_panel = render_kv_grid(
        output_review_summary,
        [
            "pair_count",
            "judgment_count",
            "pending_count",
            "agreement_count",
            "disagreement_count",
            "invalid_decision_count",
            "answer_revealed_count",
            "pending_answer_hidden_count",
            "reviewer_checklist_count",
            "reviewer_checklist_pending_count",
        ],
        "review adjudication report missing",
    )
    public_claim_panel = render_kv_grid(
        benchmark_summary,
        [
            "reproducibility_ready",
            "release_lock_ready",
            "public_claim_ready",
            "public_claim_blocker_count",
            "provider_evidence_complete",
            "human_review_complete",
            "world_class_ready",
        ],
        "benchmark reproducibility report missing",
    )
    public_claim_blocker_rows = public_claim.get("blockers", [])
    if public_claim_blocker_rows:
        public_claim_blockers_html = (
            "<ul class='issues'>"
            + "".join(
                f"<li><strong>阻断</strong><span>{html.escape(str(item))}</span></li>"
                for item in public_claim_blocker_rows
            )
            + "</ul>"
        )
    else:
        public_claim_blockers_html = "<p class='muted'>无公开声明阻断。</p>"
    output_review_section_html = render_output_review_section(report["data"].get("output_review_adjudication", {}))
    blueprint_panel = render_kv_grid(
        blueprint_summary,
        [
            "item_count",
            "module_count",
            "recommended_pr_count",
            "pass_count",
            "warn_count",
            "missing_count",
            "extension_track_count",
            "extension_covered_count",
            "extension_partial_count",
            "extension_planned_count",
            "adaptive_extension_ready",
            "local_blueprint_ready",
            "public_world_class_ready",
            "world_class_evidence_pending_count",
        ],
        "Skill OS 2.0 blueprint coverage missing",
    )
    conformance_panel = render_kv_grid(
        conformance_summary,
        ["target_count", "pass_count", "fail_count", "warning_count", "failure_count"],
        "runtime conformance matrix missing",
    )
    compiled_panel = render_kv_grid(
        compiled_summary,
        ["target_count", "pass_count", "warn_count", "block_count", "failure_count"],
        "compiled target report missing",
    )
    trust_panel = render_kv_grid(
        trust_summary,
        ["secret_findings", "script_count", "network_script_count", "help_smoke_failed_count", "package_sha256"],
        "security trust report missing",
    )
    python_compat_panel = render_kv_grid(
        python_compat_summary,
        ["target_python", "file_count", "issue_count", "syntax_error_count", "fstring_311_violation_count"],
        "python compatibility report missing",
    )
    runtime_boundary_panel = render_kv_grid(
        runtime_permissions_summary,
        [
            "target_count", "pass_count", "native_enforcement_count", "metadata_fallback_count",
            "installer_enforcement_pass_count", "installer_permission_failure_count", "residual_risk_count", "failure_count",
        ],
        "runtime permission probe summary missing",
    )
    adoption_panel = render_kv_grid(
        adoption_summary,
        ["event_count", "adoption_rate", "missed_trigger_count", "bad_output_count", "risk_band"],
        "no adoption drift summary",
    )
    skillops_section_html = render_skillops_section(report["data"])
    waiver_panel = render_kv_grid(
        waiver_summary,
        ["waiver_count", "active_count", "expired_count", "invalid_count", "covered_gate_count"],
        "no review waiver summary",
    )
    waiver_candidates_panel = render_waiver_candidates_panel(report["data"].get("review_waivers", {}))
    world_class_panel = render_kv_grid(
        world_class_summary,
        [
            "ledger_entry_count",
            "accepted_count",
            "pending_count",
            "human_pending_count",
            "external_pending_count",
            "overclaim_guard_active",
            "ready_to_claim_world_class",
        ],
        "world-class evidence ledger missing",
    )
    world_class_intake_panel = render_kv_grid(
        world_class_intake_summary,
        [
            "schema_present",
            "template_count",
            "template_pass_count",
            "submission_count",
            "valid_submission_count",
            "invalid_submission_count",
            "ready_for_external_collection",
            "ready_for_ledger_review",
            "ready_to_claim_world_class",
        ],
        "world-class evidence intake missing",
    )
    world_class_claim_panel = render_kv_grid(
        world_class_claim_summary,
        [
            "ledger_ready_to_claim_world_class",
            "ledger_pending_count",
            "claim_surface_count",
            "violation_count",
            "overclaim_guard_active",
        ],
        "world-class claim guard missing",
    )
    registry_panel = render_kv_grid(
        registry_package_summary(registry_package),
        [
            "name",
            "version",
            "maturity",
            "owner",
            "license",
            "trust_level",
            "targets",
            "compatibility_pass_count",
            "archive_sha256",
        ],
        "registry package metadata missing",
    )
    package_panel = render_kv_grid(
        package_summary,
        ["target_count", "adapter_count", "archive_present", "archive_entry_count", "failure_count", "warning_count", "archive_sha256"],
        "package verification missing",
    )
    install_panel = render_kv_grid(
        install_summary,
        [
            "archive_extracted",
            "entrypoint_loaded",
            "manifest_loaded",
            "interface_loaded",
            "adapter_count",
            "installer_permission_enforced_count",
            "installer_permission_failure_count",
            "permission_target_count",
            "permission_capability_count",
            "failure_count",
            "warning_count",
        ],
        "install simulation missing",
    )
    evidence_html = "".join(
        f"<li><strong>{html.escape(key)}</strong><span>{html.escape(value)}</span></li>"
        for key, value in report["evidence_paths"].items()
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(str(title))} Review Studio 2.0</title>
  <style>
{review_studio_css()}
  </style>
</head>
<body>
  <nav>{nav_html}</nav>
  <main>
    <header id="overview">
      <div class="eyebrow">Review Studio 2.0</div>
      <h1>{html.escape(str(title))}</h1>
      <p class="lede">{html.escape(str(description))}</p>
      <div class="decision">
        <span>审查结论</span>
        <strong>{html.escape(summary['decision'])}</strong>
        <span>Score {html.escape(str(summary['world_class_score']))}/100</span>
      </div>
    </header>

    <section>
      <h2>核心指标</h2>
      <div class="metrics">{metrics_html}</div>
    </section>

    <section>
      <h2>审查闸门</h2>
      <div class="gates">{gates_html}</div>
    </section>

    <section>
      <h2>闸门契约</h2>
      <div class="panel">{gate_contract_panel}</div>
    </section>

    <div class="twocol">
      {blockers_html}
      {warnings_html}
    </div>

    <section id="actions">
      <h2>修复动作</h2>
      <div class="actions-grid">{actions_html}</div>
    </section>

    <section id="annotations">
      <h2>审查批注</h2>
      <p class="muted">当前批注：{html.escape(annotation_caption)}</p>
      <div class="annotations-grid">{annotations_html}</div>
    </section>

    <section id="intent" class="twocol">
      <div class="panel">
        <h2>意图画布</h2>
        <p>{html.escape(str(report['data']['intent_confidence'].get('anchor_sentence', description)))}</p>
      </div>
      <div class="panel">
        <h2>证据路径</h2>
        <ul class="evidence">{evidence_html}</ul>
      </div>
    </section>

    <section id="trigger" class="twocol">
      <div class="panel"><h2>触发实验</h2><p>{html.escape(gates[1]['detail'])}</p></div>
      <div class="panel"><h2>组合治理</h2>{atlas_panel}</div>
    </section>

    <section id="output" class="twocol">
      <div class="panel"><h2>输出实验</h2>{output_panel}</div>
      <div class="panel"><h2>执行证据</h2>{execution_panel}</div>
    </section>

    <section class="twocol">
      <div class="panel"><h2>盲评包</h2>{blind_panel}</div>
      <div class="panel"><h2>审定报告</h2>{review_panel}</div>
    </section>

    {output_review_section_html}
    <section class="twocol">
      <div class="panel"><h2>发布标准</h2><p>Governed 和 Library 至少需要 5 个 output eval cases，并覆盖 file-backed、near-neighbor、boundary case、execution evidence 和 blind A/B review pack。</p></div>
      <div class="panel"><h2>人工结论</h2><p>没有 reviewer 决策时只显示 pending；只有真实决策文件会进入一致率和分歧统计。</p></div>
    </section>

    <section class="twocol">
      <div class="panel"><h2>评审方式</h2><p>先打开 reports/output_review_kit.html 做盲评，填入 reports/output_review_decisions.json，再用 reports/output_review_adjudication.md 核对答案 key。</p></div>
      <div class="panel"><h2>运行方式</h2><p>reports/output_execution_runs.md 会标明 recorded fixture、command run 或 model run；只有 provider runner 返回 model metadata 时才算 model-executed。</p></div>
    </section>

    <section id="runtime" class="twocol">
      <div class="panel"><h2>运行矩阵</h2>{conformance_panel}</div>
      <div class="panel"><h2>目标编译</h2>{compiled_panel}</div>
    </section>

    <section class="twocol">
      <div class="panel"><h2>上下文</h2><p>{html.escape(gate_details.get('context-budget', 'context budget missing'))}</p></div>
      <div class="panel"><h2>编译证据</h2><p>Review reports/compiled_targets.md before packaging to inspect target adapter modes, generated files, preserved semantics, warnings, and unsupported features.</p></div>
    </section>

    <section id="trust" class="twocol">
      <div class="panel"><h2>信任报告</h2>{trust_panel}</div>
      <div class="panel"><h2>安全边界</h2><p>高风险 secret、远程 inline execution、缺失依赖策略或无法解释的脚本接口应阻断 governed release。</p></div>
    </section>

    <section class="twocol">
      <div class="panel"><h2>Python 兼容</h2>{python_compat_panel}</div>
      <div class="panel"><h2>解释器边界</h2><p>CI 和发布审查以 Python 3.11 兼容为底线；本地更高版本允许的新语法不能绕过兼容门禁。</p></div>
    </section>

    <section id="permissions" class="twocol">
      <div class="panel"><h2>权限批准</h2><p>{html.escape(gate_details.get('permission-gates', 'permission governance missing'))}</p></div>
      <div class="panel"><h2>批准策略</h2><p>高权限能力需要 reviewer、scope、reason、expires_at 和 openai/claude/generic 目标端 enforcement 说明。</p></div>
    </section>

    <section id="permission-probes" class="twocol">
      <div class="panel"><h2>权限探针</h2><p>{html.escape(gate_details.get('permission-runtime', 'runtime permission probes missing'))}</p></div>
      <div class="panel"><h2>运行边界</h2>{runtime_boundary_panel}</div>
    </section>

    <section id="atlas" class="twocol">
      <div class="panel"><h2>组合治理</h2><p>{html.escape(gate_details.get('skill-atlas', 'skill atlas missing'))}</p></div>
      <div class="panel"><h2>下一动作</h2><p>优先处理真实 portfolio 中的 duplicate names、stale skills、owner gaps，再用运营回路判断真实影响。</p></div>
    </section>

    <section id="telemetry" class="twocol">
      <div class="panel"><h2>运营回路</h2><p>{html.escape(gate_details.get('operations-loop', 'adoption drift report missing'))}</p></div>
      <div class="panel"><h2>漂移信号</h2>{adoption_panel}</div>
    </section>

    {skillops_section_html}

    <section id="waivers">
      <h2>人工批准</h2>
      <p class="muted">warning 可以被有边界地接受，但必须写入 reviewer、理由、范围和到期时间；blocker 与 world-class 完成证据不能通过 waiver 变成通过。</p>
      <div class="twocol waiver-summary">
        <div class="panel"><h2>批准概况</h2><p>{html.escape(gate_details.get('review-waivers', 'review waiver ledger missing'))}</p></div>
        <div class="panel"><h2>批准台账</h2>{waiver_panel}</div>
      </div>
      <h3 class="section-subtitle">批准候选</h3>
      {waiver_candidates_panel}
    </section>

    <section id="world-class">
      <h2>世界证据</h2>
      <p class="muted">这里列出每个 world-class 证据项的当前状态、完成定义、证据来源、隐私约束和下一步；计划、metadata fallback、待评审和本地命令不会被当成完成证据。</p>
      {world_class_entries_html}
    </section>

    <section>
      <h2>提交清单</h2>
      <p class="muted">每张卡片给出模板、提交文件、准备命令、校验命令、收集要求、通过条件和隐私边界；只有真实 provider、真人、原生权限或真实客户端证据通过 intake 后，才进入 ledger review。</p>
      {world_class_intake_checklist_html}
    </section>

    <section class="twocol">
      <div class="panel"><h2>蓝图覆盖</h2>{blueprint_panel}</div>
      <div class="panel"><h2>覆盖边界</h2><p>蓝图覆盖只证明 2.0 模块、建议 PR、脚本、报告和测试在本地闭环；public world-class 仍以 world-class evidence ledger 的真人和外部证据为准。</p></div>
    </section>

    <section class="twocol">
      <div class="panel"><h2>公开声明</h2>{public_claim_panel}</div>
      <div class="panel"><h2>声明阻断</h2>{public_claim_blockers_html}</div>
    </section>

    <section class="twocol">
      <div class="panel"><h2>世界证据</h2><p>{html.escape(gate_details.get('world-class-evidence', 'world-class evidence ledger missing'))}</p></div>
      <div class="panel"><h2>证据台账</h2>{world_class_panel}</div>
    </section>

    <section class="twocol">
      <div class="panel"><h2>证据入口</h2>{world_class_intake_panel}</div>
      <div class="panel"><h2>入口边界</h2><p>intake 只校验证据包格式、来源、隐私和反过度声明；只有 ledger 看到真实 provider、真人、原生权限或真实客户端结果后，world-class 才能进入完成审计。</p></div>
    </section>

    <section class="twocol">
      <div class="panel"><h2>声明守卫</h2>{world_class_claim_panel}</div>
      <div class="panel"><h2>声明边界</h2><p>claim guard 扫描 README、docs 和 reports 中的完成态表述；ledger 未 ready 时，任何英文完成断言、true 状态声明或中文完成态都会阻断发布审查。</p></div>
    </section>

    <section id="registry" class="twocol">
      <div class="panel"><h2>注册审计</h2><p>{html.escape(gate_details.get('registry-audit', 'registry audit missing'))}</p></div>
      <div class="panel"><h2>包体元数据</h2>{registry_panel}</div>
    </section>

    <section id="release" class="twocol">
      <div class="panel"><h2>发布路线</h2><p>{html.escape(gate_details.get('release-notes', 'release notes missing'))}</p></div>
      <div class="panel"><h2>包体验证</h2>{package_panel}</div>
    </section>

    <section class="twocol">
      <div class="panel"><h2>安装模拟</h2>{install_panel}</div>
      <div class="panel"><h2>权限覆盖</h2><p>安装模拟会读取解压后的 target adapter，并按 declared_capabilities 核对 security/permission_policy.json 中的有效批准、证据、过期时间和目标端 enforcement 说明。</p></div>
    </section>
  </main>
</body>
</html>
"""


def render_review_studio(skill_dir: Path, output_html: Path | None = None, output_json: Path | None = None) -> dict[str, Any]:
    skill_dir = skill_dir.resolve()
    reports_dir = skill_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    output_html = output_html or reports_dir / "review-studio.html"
    output_json = output_json or reports_dir / "review-studio.json"
    data = load_review_data(skill_dir)
    gates = build_gates(skill_dir, output_html, data)
    contract = gate_contract(gates)
    blockers, warnings = add_blockers_from_gate(gates)
    review_actions = build_review_actions(gates, skill_dir, output_html, data)
    score = weighted_score(gates)
    annotation_summary = data["review_annotations"].get("summary", {})
    open_annotation_blockers = int(annotation_summary.get("open_blocker_count", 0) or 0)
    open_annotation_warnings = int(annotation_summary.get("open_warning_count", 0) or 0)
    decision = "blocked" if blockers or open_annotation_blockers else ("review" if warnings or open_annotation_warnings else "ready")
    report = {
        "schema_version": "2.0",
        "ok": contract["ok"],
        "skill_dir": display_path(skill_dir, skill_dir),
        "summary": {
            "decision": decision,
            "world_class_score": score,
            "gate_count": len(gates),
            "gate_contract_ok": contract["ok"],
            "blocker_count": len(blockers),
            "warning_count": len(warnings),
            "action_count": len(review_actions),
            "annotation_count": int(annotation_summary.get("annotation_count", 0) or 0),
            "open_annotation_count": int(annotation_summary.get("open_count", 0) or 0),
            "open_annotation_blocker_count": open_annotation_blockers,
            "open_annotation_warning_count": open_annotation_warnings,
        },
        "gates": gates,
        "gate_contract": contract,
        "blockers": blockers,
        "warnings": warnings,
        "review_actions": review_actions,
        "evidence_paths": evidence_paths(skill_dir),
        "data": data,
        "artifacts": {
            "html": display_path(skill_dir, output_html),
            "json": display_path(skill_dir, output_json),
        },
    }
    output_html.write_text(render_html(report), encoding="utf-8")
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {key: value for key, value in report.items() if key != "data"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Review Studio 2.0 for a skill package.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--output-html")
    parser.add_argument("--output-json")
    args = parser.parse_args()
    output_html = Path(args.output_html).resolve() if args.output_html else None
    output_json = Path(args.output_json).resolve() if args.output_json else None
    payload = render_review_studio(Path(args.skill_dir), output_html=output_html, output_json=output_json)
    print(json.dumps(payload, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
