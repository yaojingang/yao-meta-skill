#!/usr/bin/env python3
import argparse
import html
import json
from pathlib import Path

from skill_report_charts import render_chart_set
from skill_report_i18n import (
    KIND_ZH,
    LABEL_EN,
    PACKAGE_LABEL_ZH,
    bi_item,
    bi_span,
    en_for,
    mode_zh,
    readable_description_zh,
)
from skill_report_layout import render_language_switch, render_report_nav, skill_overview_css, skill_overview_script
from skill_report_model import REPORT_NAV_V2, build_report_model


def render_list(items: list[str], class_name: str = "list") -> str:
    if not items:
        return f'<ul class="{class_name}"><li>{bi_span("暂无记录。", "No records yet.")}</li></ul>'
    return f'<ul class="{class_name}">' + "".join(f"<li>{bi_item(str(item))}</li>" for item in items) + "</ul>"


def render_ordered_steps(items: list[str], class_name: str = "step-list") -> str:
    if not items:
        return f'<ol class="{class_name}"><li>{bi_span("暂无步骤。", "No steps yet.")}</li></ol>'
    return f'<ol class="{class_name}">' + "".join(f"<li>{bi_item(str(item))}</li>" for item in items) + "</ol>"


def render_metric_cards(scorecard: dict) -> str:
    cards = []
    for key, item in scorecard.items():
        reasons = render_list(item.get("reasons", [])[:3], "compact-list")
        cards.append(
            "<article class='metric-card'>"
            "<div class='metric-card-head'>"
            f"<span class='metric-label'>{bi_item(str(item.get('label', key)))}</span>"
            f"<strong>{html.escape(str(item.get('score', 'n/a')))}</strong>"
            "</div>"
            f"<div class='metric-card-body'>{reasons}</div>"
            "</article>"
        )
    return "".join(cards)


def render_metric_summary(scorecard: dict) -> str:
    items = []
    for key, item in scorecard.items():
        score = int(item.get("score", 0))
        label = str(item.get("label", key))
        reason = str(item.get("reasons", [""])[0])
        if score >= 85:
            verdict = "稳定"
            verdict_en = "Stable"
        elif score >= 70:
            verdict = "可用"
            verdict_en = "Usable"
        else:
            verdict = "关注"
            verdict_en = "Watch"
        items.append(
            "<li>"
            f"<span class='metric-status'>{bi_span(verdict, verdict_en)}</span>"
            f"<b>{bi_item(label)}</b>"
            f"<em>{score}</em>"
            f"<small>{bi_item(reason)}</small>"
            "</li>"
        )
    return "<ol class='metric-summary-list'>" + "".join(items) + "</ol>"


def render_audit_rows(items: list[dict]) -> str:
    rows = []
    for item in items:
        name = str(item.get("name", item.get("label", "项目")))
        response = str(item.get("response", item.get("kind", "")))
        rows.append(
            "<tr>"
            f"<td>{bi_span(name, LABEL_EN.get(name, name))}</td>"
            f"<td>{bi_item(str(item.get('signal', item.get('body', ''))))}</td>"
            f"<td>{bi_span(response, LABEL_EN.get(response, response))}</td>"
            "</tr>"
        )
    return "".join(rows)


WORLD_CLASS_CHECK_COPY = {
    "Provider model run": ("提供商实跑", "Provider model run"),
    "Token usage observed": ("Token 用量", "Token usage observed"),
    "No pending decisions": ("无待判定", "No pending decisions"),
    "Judgments complete": ("盲评完成", "Judgments complete"),
    "Native enforcement": ("原生执行", "Native enforcement"),
    "External events": ("外部事件", "External events"),
    "Adoption sample": ("采用样本", "Adoption sample"),
}


def render_world_class_check(check: object) -> str:
    if isinstance(check, dict):
        label_en = str(check.get("label_en") or check.get("label") or "")
        label_zh = str(check.get("label_zh") or "")
    else:
        label_en = str(check)
        label_zh = ""
    label_zh, label_en = WORLD_CLASS_CHECK_COPY.get(label_en, (label_zh or label_en, label_en))
    return f"<li>{bi_span(label_zh, label_en)}</li>"


def render_world_class_readiness(readiness: dict) -> str:
    if not readiness:
        return ""
    kpis = [
        (
            "待补证据",
            "Pending",
            readiness.get("pending_count", 0),
            "仍需外部或人工证据接受。",
            "External or human evidence still needs acceptance.",
        ),
        (
            "已接受",
            "Accepted",
            readiness.get("accepted_count", 0),
            "已通过 source check 与提交契约。",
            "Passed source checks and submission contract.",
        ),
        (
            "源检查",
            "Source Checks",
            f"{readiness.get('source_pass_count', 0)} / {readiness.get('source_check_count', 0)}",
            "通过数 / 总检查数。",
            "Passed checks / total checks.",
        ),
    ]
    kpi_html = "".join(
        "<article class='evidence-kpi'>"
        f"<span>{bi_span(zh, en)}</span>"
        f"<strong>{html.escape(str(value))}</strong>"
        f"<small>{bi_span(note_zh, note_en)}</small>"
        "</article>"
        for zh, en, value, note_zh, note_en in kpis
    )
    entries = readiness.get("entries", [])
    if entries:
        blocks = []
        for item in entries:
            blocked_checks = [
                str(check).strip()
                for check in item.get("blocked_checks", [])
                if str(check).strip()
            ]
            if blocked_checks:
                checks_html = (
                    "<ul class='blocked-checks'>"
                    + "".join(render_world_class_check(check) for check in blocked_checks)
                    + "</ul>"
                )
            else:
                checks_html = (
                    "<p class='blocked-checks-empty'>"
                    f"{bi_span('当前没有阻塞检查。', 'No blocked checks right now.')}"
                    "</p>"
                )
            blocks.append(
                "<article class='evidence-item'>"
                "<div>"
                f"<span>{bi_span(str(item.get('category_zh', '外部证据')), str(item.get('category_en', 'External evidence')))}</span>"
                f"<h4>{bi_span(str(item.get('label_zh', item.get('key', '证据项'))), str(item.get('label_en', item.get('key', 'Evidence item'))))}</h4>"
                "</div>"
                f"<p>{bi_span(str(item.get('summary_zh', '仍待补充证据。')), str(item.get('summary_en', 'Evidence is still pending.')))}</p>"
                f"<h5>{bi_span('阻塞检查', 'Blocked Checks')}</h5>"
                f"{checks_html}"
                "</article>"
            )
        entry_html = "".join(blocks)
    else:
        entry_html = (
            "<article class='evidence-item empty'>"
            f"<p>{bi_span('尚未生成 world-class ledger；这里只保留反过度承诺提示。', 'No world-class ledger has been generated; this panel keeps the anti-overclaim guard visible.')}</p>"
            "</article>"
        )
    status = "可宣称" if readiness.get("ready") else "证据待补"
    status_en = "Claim-ready" if readiness.get("ready") else "Evidence pending"
    return (
        "<article class='panel world-readiness'>"
        "<div class='world-readiness-head'>"
        "<div>"
        f"<h3>{bi_span('世界证据', 'World Evidence')}</h3>"
        f"<p>{bi_span(str(readiness.get('conclusion_zh', '世界级证据状态未知。')), str(readiness.get('conclusion_en', 'World-class evidence status is unknown.')))}</p>"
        "</div>"
        f"<span class='world-status'>{bi_span(status, status_en)}</span>"
        "</div>"
        f"<div class='evidence-kpis'>{kpi_html}</div>"
        f"<div class='evidence-list'>{entry_html}</div>"
        "</article>"
    )


def render_score_strip(scorecard: dict) -> str:
    keys = ["completeness_score", "trigger_score", "evidence_score", "context_cost"]
    cards = []
    for key in keys:
        item = scorecard.get(key)
        if not item:
            continue
        score = int(item.get("score", 0))
        reason = item.get("reasons", [""])[0]
        cards.append(
            "<article class='score-chip'>"
            f"<span>{bi_item(str(item.get('label', key)))}</span>"
            f"<strong>{score}</strong>"
            f"<i style='--score:{score}%'></i>"
            f"<small>{bi_item(str(reason))}</small>"
            "</article>"
        )
    return "".join(cards)


def render_roadmap(items: list[dict]) -> str:
    blocks = []
    for index, item in enumerate(items[:3], start=1):
        actions = render_list([str(action) for action in item.get("actions", [])], "compact-list")
        blocks.append(
            "<article class='roadmap-item'>"
            f"<span class='step'>{bi_span(f'下一步 {index}', f'Next {index}')}</span>"
            f"<h3>{bi_item(str(item.get('title', '升级方向')))}</h3>"
            f"<p>{bi_item(str(item.get('why', '提升复用稳定性。')))}</p>"
            f"{actions}"
            f"<p class='unlock'>{bi_item(str(item.get('unlocks', '')))}</p>"
            "</article>"
        )
    return "".join(blocks)


def render_html(summary: dict) -> str:
    charts = render_chart_set(summary)
    nav_html = render_report_nav(REPORT_NAV_V2)
    language_switch = render_language_switch()
    skill = summary.get("skill_summary", {})
    metadata = summary.get("metadata", {})
    scorecard = summary.get("scorecard", {})
    profile = summary.get("capability_profile", {})
    contract = summary.get("contract_boundary", {})
    quality = summary.get("quality_review", {})
    risk = summary.get("risk_governance", {})
    world_readiness = summary.get("world_class_readiness", {})
    assets = summary.get("package_assets", {})
    roadmap = summary.get("iteration_roadmap", {})
    output_execution = summary.get("output_execution", {})
    output_execution_summary = output_execution.get("summary", {})
    output_review = summary.get("output_review_adjudication", {})
    output_review_summary = output_review.get("summary", {})
    report_contract = summary.get("report_contract", {})
    html_report_path = str(report_contract.get("html_report") or "reports/skill-overview.html")
    open_report_message = f"创建完成后建议先打开 {html_report_path}，再继续扩展包体。"
    hero_meta = [
        (f"技能名称：{summary['name']}", f"Skill name: {summary['name']}"),
        (f"成熟度：{mode_zh(metadata.get('maturity_tier', 'scaffold'))}", f"Maturity: {metadata.get('maturity_tier', 'scaffold')}"),
        (f"格式：{mode_zh(metadata.get('canonical_format', 'agent-skills'))}", f"Format: {metadata.get('canonical_format', 'agent-skills')}"),
        (f"更新时间：{metadata.get('updated_at', '')}", f"Updated: {metadata.get('updated_at', '')}"),
    ]
    hero_meta_html = "".join(f"<span>{bi_span(zh, en)}</span>" for zh, en in hero_meta)
    target_badges = "".join(f"<span>{bi_span(str(target), str(target))}</span>" for target in metadata.get("targets", []))
    score_strip = render_score_strip(scorecard)
    package_rows = "".join(
        (
            "<tr>"
            f"<td>{html.escape(str(item.get('path', '')))}</td>"
            f"<td>{bi_span(PACKAGE_LABEL_ZH.get(str(item.get('path', '')), str(item.get('label', ''))), str(item.get('label', '')))}</td>"
            f"<td>{bi_span(KIND_ZH.get(str(item.get('kind', '')), str(item.get('kind', ''))), str(item.get('kind', '')))}</td>"
            "</tr>"
        )
        for item in assets.get("entries", [])
    )
    quality_rows = render_audit_rows(
        [{"name": "强项", "signal": item, "response": "保留并复用"} for item in quality.get("strengths", [])[:3]]
        + [{"name": "缺口", "signal": item, "response": "纳入下一轮修复"} for item in quality.get("gaps", [])[:3]]
    )
    if output_review_summary:
        agreement = output_review_summary.get("agreement_rate")
        review_items = [
            f"评审进度：{output_review_summary.get('judgment_count', 0)} / {output_review_summary.get('pair_count', 0)}",
            f"待评审：{output_review_summary.get('pending_count', 0)}",
            f"一致率：{agreement if agreement is not None else '暂无'}",
            f"非法决策：{output_review_summary.get('invalid_decision_count', 0)}",
        ]
    else:
        review_items = ["尚未生成盲评审定报告。"]
    if output_execution_summary:
        execution_items = [
            f"变体运行：{output_execution_summary.get('variant_run_count', 0)}",
            f"模型执行：{output_execution_summary.get('model_executed_count', 0)}",
            f"记录样本：{output_execution_summary.get('recorded_fixture_count', 0)}",
            f"Token 估算：{output_execution_summary.get('token_estimated_count', 0)}",
        ]
    else:
        execution_items = ["尚未生成输出执行证据报告。"]
    capability_items = [
        f"能力类型：{profile.get('task_family', 'Skill workflow')}",
        f"成熟度：{profile.get('maturity', 'scaffold')}",
        f"触发强度：{profile.get('trigger_strength', 'manual')}",
        f"复用范围：{profile.get('reuse_scope', '本地复用')}",
    ]
    trigger = contract.get("trigger", {})
    risk_rows = render_audit_rows(risk.get("risks", []))

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(summary['name'])} Skill 生成审计报告</title>
  <style>
{skill_overview_css()}
  </style>
</head>
<body data-report-lang="zh-CN">
  <a class="skip-link" href="#overview">{bi_span("跳到正文", "Skip to content")}</a>
  <header class="topbar">
    <div class="progress-track" aria-hidden="true"><span class="progress-bar"></span></div>
    <div class="topbar-inner">
      <div class="nav-shell">
        <span class="report-mark">Skill audit</span>
        <nav class="report-nav" aria-label="报告导航">{nav_html}</nav>
      </div>
      {language_switch}
    </div>
  </header>
  <main id="main-content" class="wrap">
    <section class="hero" aria-labelledby="report-title">
      <div class="hero-grid">
        <div>
          <p class="eyebrow">{bi_span("YAO Skill 生成审计报告", "YAO Skill Generation Audit")}</p>
          <p class="slug">{html.escape(summary['name'])}</p>
          <h1 id="report-title">{bi_span("技能审计报告", f"{summary['display_name']} Audit Report")}</h1>
          <p class="lead">{bi_span("这份报告默认使用中文简体，把新 Skill 的定位、指标、原理、契约、质量、风险、资产和迭代路线整理为一份可审计的 HTML 报告。", en_for(str(summary["description"])))}</p>
          <div class="hero-meta">{hero_meta_html}</div>
          <div class="badges">{target_badges}</div>
        </div>
        <aside class="hero-card">
          <h3>{bi_span("核心判断", "Core reading")}</h3>
          {render_list([skill.get("core_value", ""), skill.get("audience", ""), open_report_message])}
        </aside>
      </div>
      <div class="score-strip" aria-label="报告关键指标">{score_strip}</div>
    </section>

    <section id="overview">
      <div class="section-head">
        <div>
          <h2>{bi_span("技能概述", "Overview")}</h2>
          <p>{bi_span("先用一屏说明这个 Skill 是什么、给谁用、交付什么。", "A first-screen explanation of what this skill is, who it serves, and what it delivers.")}</p>
        </div>
        <div class="two-col">
          <article class="panel">
            <h3>{bi_span("作用定位", "Role")}</h3>
            {render_list([summary["description"], skill.get("core_value", ""), f"交付结果：{', '.join(skill.get('deliverables', []))}"])}
          </article>
          {charts["flow"]}
        </div>
      </div>
    </section>

    <section id="metrics">
      <div class="section-head">
        <div>
          <h2>{bi_span("总览指标", "Metrics")}</h2>
          <p>{bi_span("分数来自本地文件和 reports 证据，缺失时明确标为证据不足。", "Scores are derived from package files and reports; missing inputs are shown as evidence gaps.")}</p>
        </div>
        <article class="panel metrics-note">
          <h3>{bi_span("指标判读", "Reading")}</h3>
          <p>{bi_span("先看雷达图判断能力短板，再看每项分数的证据原因。分数不是装饰数字，必须和本地文件、reports 证据或证据不足提示对应。", "Read the radar first for weak spots, then inspect each score with its evidence. Scores must map to local files, reports, or explicit evidence gaps.")}</p>
        </article>
      </div>
      <div class="section-body metrics-report">
        <div class="metrics-flow">
          <div class="metrics-primary">
            {charts["radar"]}
            <article class="panel metrics-note metrics-summary-panel">
              <h3>{bi_span("成熟度条", "Maturity Bar")}</h3>
              {render_metric_summary(scorecard)}
            </article>
          </div>
          <div class="metric-grid metric-detail-grid">{render_metric_cards(scorecard)}</div>
        </div>
      </div>
    </section>

    <section id="capability">
      <div class="section-head">
        <div>
          <h2>{bi_span("能力画像", "Capability")}</h2>
          <p>{bi_span("判断这个 Skill 在能力地图中的位置和复用范围。", "Places this skill on a capability map and clarifies reuse scope.")}</p>
        </div>
        <div class="two-col">
          {charts["matrix"]}
          <article class="panel">
            <h3>{bi_span("画像摘要", "Profile")}</h3>
            {render_list(capability_items)}
          </article>
        </div>
      </div>
    </section>

    <section id="principle">
      <div class="section-head">
        <div>
          <h2>{bi_span("原理结构", "Principle")}</h2>
          <p>{bi_span("说明入口、参考、脚本、评估和报告如何组成一个稳定闭环。", "Explains how entrypoint, references, scripts, evals, and reports form a stable loop.")}</p>
        </div>
        <div>
          <div class="chart-grid">{charts["layers"]}</div>
          <div class="two-col">
            <article class="panel">
              <h3>{bi_span("执行流程", "Execution Flow")}</h3>
              {render_ordered_steps(summary.get("logic_steps", []))}
            </article>
            <article class="panel">
              <h3>{bi_span("调用方式", "How To Use")}</h3>
              {render_ordered_steps(summary.get("usage_steps", []))}
            </article>
          </div>
        </div>
      </div>
    </section>

    <section id="contract">
      <div class="section-head">
        <div>
          <h2>{bi_span("契约边界", "Contract")}</h2>
          <p>{bi_span("把触发、输入、输出和排除场景放在同一屏。", "Keeps trigger, inputs, outputs, and exclusions on the same screen.")}</p>
        </div>
        <div class="two-col">
          <article class="panel">
            <h3>{bi_span("触发描述", "Trigger")}</h3>
            <p>{bi_span(readable_description_zh(str(trigger.get("description", ""))), en_for(str(trigger.get("description", ""))))}</p>
            <h3>{bi_span("输入材料", "Inputs")}</h3>
            {render_list(contract.get("inputs", []))}
          </article>
          <article class="panel">
            <h3>{bi_span("输出结果", "Outputs")}</h3>
            {render_list(contract.get("outputs", []))}
            <h3>{bi_span("不应触发", "Should Not Trigger")}</h3>
            {render_list(contract.get("should_not_trigger", []))}
          </article>
        </div>
      </div>
    </section>

    <section id="quality">
      <div class="section-head">
        <div>
          <h2>{bi_span("质量评估", "Quality")}</h2>
          <p>{bi_span("展示强项、缺口和建议，避免只给分不解释。", "Shows strengths, gaps, and recommendations instead of scores without explanation.")}</p>
        </div>
        <div>
          <table>
            <thead><tr><th>{bi_span("类型", "Type")}</th><th>{bi_span("证据", "Evidence")}</th><th>{bi_span("建议", "Action")}</th></tr></thead>
            <tbody>{quality_rows}</tbody>
          </table>
          <div class="two-col quality-panels">
            <article class="panel">
              <h3>{bi_span("执行证据", "Execution Evidence")}</h3>
              {render_list(execution_items)}
            </article>
            <article class="panel">
              <h3>{bi_span("盲评审定", "Blind Adjudication")}</h3>
              {render_list(review_items)}
            </article>
          </div>
          <div class="two-col quality-panels">
            <article class="panel">
              <h3>{bi_span("评审原则", "Review Rule")}</h3>
              {render_list(["先记录 reviewer 对 A/B 的选择，再打开答案 key 计算一致率。", "缺少真实 reviewer 决策时只显示待评审，不伪造人工结论。"])}
            </article>
            <article class="panel">
              <h3>{bi_span("运行原则", "Run Rule")}</h3>
              {render_list(["recorded fixture 只能证明可复现样本，不等同于模型执行。", "只有 provider runner 返回 model metadata 时才计入 model-executed。"])}
            </article>
          </div>
        </div>
      </div>
    </section>

    <section id="risk">
      <div class="section-head">
        <div>
          <h2>{bi_span("风险治理", "Risk")}</h2>
          <p>{bi_span("提前暴露误触发、漂移、证据不足和迁移风险。", "Surfaces trigger, drift, evidence, and portability risks before the package grows.")}</p>
        </div>
        <div class="two-col">
          {charts["risk_heatmap"]}
          <div>
            <table>
              <thead><tr><th>{bi_span("风险", "Risk")}</th><th>{bi_span("信号", "Signal")}</th><th>{bi_span("应对", "Response")}</th></tr></thead>
              <tbody>{risk_rows}</tbody>
            </table>
          </div>
        </div>
        {render_world_class_readiness(world_readiness)}
      </div>
    </section>

    <section id="assets">
      <div class="section-head">
        <div>
          <h2>{bi_span("包体资产", "Assets")}</h2>
          <p>{bi_span("让 reviewer 快速确认关键文件、目录和资产分布。", "Lets reviewers confirm key files, directories, and asset distribution quickly.")}</p>
        </div>
        <div class="two-col">
          {charts["asset_donut"]}
          <table>
            <thead><tr><th>{bi_span("路径", "Path")}</th><th>{bi_span("作用", "Role")}</th><th>{bi_span("类型", "Type")}</th></tr></thead>
            <tbody>{package_rows}</tbody>
          </table>
        </div>
      </div>
    </section>

    <section id="roadmap">
      <div class="section-head">
        <div>
          <h2>{bi_span("迭代路线", "Roadmap")}</h2>
          <p>{bi_span("把下一步升级收束为少数高价值动作。", "Keeps next iteration moves focused and actionable.")}</p>
        </div>
        <div>
          <div class="chart-grid">{charts["timeline"]}</div>
          <div class="roadmap">{render_roadmap(roadmap.get("items", []))}</div>
        </div>
      </div>
    </section>
  </main>
  <script>
{skill_overview_script()}
  </script>
</body>
</html>
"""


def render_skill_overview(skill_dir: Path, output_html: Path | None = None, output_json: Path | None = None) -> dict:
    skill_dir = skill_dir.resolve()
    reports_dir = skill_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    output_html = output_html or reports_dir / "skill-overview.html"
    output_json = output_json or reports_dir / "skill-overview.json"

    summary = build_report_model(skill_dir)
    output_html.write_text(render_html(summary), encoding="utf-8")
    output_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "skill_dir": str(skill_dir),
        "artifacts": {
            "html": str(output_html),
            "json": str(output_json),
        },
        "summary": summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the HTML skill report for a skill package.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--output-html")
    parser.add_argument("--output-json")
    args = parser.parse_args()

    result = render_skill_overview(
        Path(args.skill_dir),
        Path(args.output_html).resolve() if args.output_html else None,
        Path(args.output_json).resolve() if args.output_json else None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
