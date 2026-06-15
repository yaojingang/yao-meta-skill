#!/usr/bin/env python3
import argparse
import html
import json
from pathlib import Path

from skill_report_charts import render_chart_set
from skill_report_layout import render_language_switch, render_report_nav, skill_overview_css, skill_overview_script
from skill_report_model import REPORT_NAV_V2, build_report_model


TEXT_ZH = {
    "Create, refactor, evaluate, and package agent skills from workflows, prompts, transcripts, docs, or notes. Use when asked to create a skill, turn a repeated process into a reusable skill, improve an existing skill, add evals, or package a skill for team reuse.": "从工作流、提示词、对话记录、文档或笔记中创建、重构、评估和打包 agent skill；适用于新建 Skill、沉淀重复流程、改进现有 Skill、补充 eval 或团队复用打包。",
    "Understand the request.": "理解用户请求。",
    "Execute the main task.": "执行核心任务。",
    "Validate the result.": "校验交付结果。",
    "Understand the request": "理解用户请求。",
    "Execute the main task": "执行核心任务。",
    "Validate the result": "校验交付结果。",
    "Decide whether the request should become a skill and choose the lightest fit.": "判断请求是否应该沉淀为 Skill，并选择最轻量可靠的模式。",
    "Capture job, output, exclusions, constraints, and standards.": "捕捉任务、输出、排除项、约束和质量标准。",
    "Run reference scan: external benchmarks first, user references second, local fit third; surface only uncertainty or conflict.": "运行参考扫描：先看外部 benchmark，再看用户材料，最后校验本地适配；只暴露不确定性或冲突。",
    "Write the `description` early and test route quality before expanding the package.": "尽早写出 `description`，先测试路由质量，再扩展包体。",
    "Add output-risk, artifact-design, prompt-quality, and system-model reports only when they matter.": "只在确有价值时添加 output-risk、artifact-design、prompt-quality 和 system-model 报告。",
    "Use $yao-meta-skill to turn my workflow or notes into a reusable skill with lean structure, clear triggering, and the right evals.": "当你需要把工作流或笔记沉淀成结构精简、触发清晰且带必要 eval 的可复用 Skill 时使用 $yao-meta-skill。",
    "Turn rough requests into a compact reusable demo skill.": "把粗糙请求整理成紧凑、可复用的演示 Skill。",
    "Tighten trigger and exclusions": "收紧触发与排除边界",
    "Add the first execution asset": "补上第一个执行资产",
    "Promote from scaffold to production-ready": "从脚手架推进到生产可用",
    "Borrow one proven pattern on purpose": "有选择地借鉴一个成熟模式",
    "Harden portability semantics": "加固跨环境语义",
    "Create an iteration evidence loop": "建立迭代证据回路",
    "The package needs clearer near-neighbor exclusions before it grows.": "在继续扩展前，需要先把相邻但不应触发的场景说清楚。",
    "The package is still mostly prose. Add one asset that removes repeated manual work.": "当前包体仍偏文本说明，应先增加一个能减少重复人工操作的资产。",
    "The first version exists; the next gain usually comes from adding the smallest useful gates.": "第一版已经存在，下一步收益通常来自补上最小但有效的质量门禁。",
    "You already have public benchmark objects. The next gain is to choose one pattern intentionally instead of absorbing everything loosely.": "已经有公开 benchmark 对象，下一步应主动选择一个模式借鉴，而不是松散吸收所有做法。",
    "The skill already signals reuse across environments, so contract clarity matters early.": "这个 Skill 已经面向跨环境复用，因此早期就需要把契约语义说清楚。",
    "The package should show what changed and why after the first draft.": "第一版之后，包体应该能说明改了什么以及为什么改。",
    "Add 3 to 5 should-trigger and should-not-trigger examples.": "增加 3 到 5 个应触发和不应触发的例子。",
    "Refine the frontmatter description to name the recurring job and non-goals.": "精炼 frontmatter description，明确重复任务和非目标。",
    "Run a first trigger evaluation pass before expanding the package.": "扩展包体前先跑一轮触发评估。",
    "Move stable procedural guidance into references if users will need it repeatedly.": "如果用户会反复使用某段流程说明，把它沉淀到 references。",
    "Create one deterministic helper script if a repeated step can be executed instead of described.": "如果某个重复步骤可以执行而不是描述，就沉淀成一个确定性 helper script。",
    "Keep the main SKILL.md compact and route-oriented.": "保持主 SKILL.md 简洁，并围绕路由与入口组织。",
    "Decide whether this skill is personal, team-reused, or library-grade.": "判断这个 Skill 是个人使用、团队复用，还是库级基础能力。",
    "Add only the gates that match that risk level.": "只添加与风险等级匹配的质量门禁。",
    "Record lifecycle metadata and review cadence once reuse becomes real.": "一旦进入真实复用，就记录生命周期元数据和评审节奏。",
    "Decide whether to borrow method, structure, execution, or portability, but only one of them first.": "先判断要借鉴的是方法、结构、执行方式还是可迁移性，并且第一轮只借鉴其中一个。",
    "Record what you will not borrow so the package stays light.": "记录本轮不借鉴的内容，避免包体过重。",
    "Confirm activation mode, execution context, and trust assumptions.": "确认激活模式、执行上下文和信任假设。",
    "Add or review degradation strategy for non-native targets.": "补充或复核非原生目标端的降级策略。",
    "Package the skill once to verify adapter expectations.": "至少打包一次 Skill，用来验证 adapter 预期。",
    "Generate the HTML skill report and keep it aligned with the package.": "生成 HTML Skill 报告，并保持它与包体内容一致。",
    "Record reference scan choices and non-goals.": "记录参考扫描的取舍和非目标。",
    "Capture the next iteration choice explicitly before adding more files.": "在继续增加文件前，明确记录下一轮迭代选择。",
    "Cleaner routing and fewer accidental activations.": "路由更清晰，误触发更少。",
    "Stronger execution quality without bloating the entrypoint.": "在不膨胀入口文件的前提下提升执行质量。",
    "A clearer path from exploratory package to maintained asset.": "更清晰地从探索性包体走向可维护资产。",
    "A cleaner package shape with less accidental over-design.": "包体形态更清晰，也减少偶然过度设计。",
    "Safer cross-environment reuse with less target drift.": "跨环境复用更安全，目标漂移更少。",
    "A clearer path for the next author or reviewer.": "让下一位作者或评审者更容易接手。",
}

TEXT_EN = {
    "触发面保持精简，并锚定在 frontmatter description。": "The trigger surface stays lean and anchored in the frontmatter description.",
    "已打包 agents/interface.yaml，便于后续做跨平台适配。": "Portable interface metadata is packaged for later adapter-based export.",
    "长指导被拆到 references 中，入口文件可以保持轻量。": "Extended guidance is separated into references so the entrypoint can stay compact.",
    "确定性辅助逻辑放在 scripts 中，而不是藏在提示词里。": "Deterministic helper logic lives in scripts instead of hidden prompt text.",
    "包内包含可随 Skill 迁移的质量门禁或触发检查。": "The package includes portable quality gates or trigger checks.",
    "这份报告用于快速理解新生成 Skill 的定位、原理、触发边界和交付内容。": "Use this report to quickly understand the generated skill's role, principles, trigger boundary, and deliverables.",
    "先确认重复任务、真实输入形态和可交付输出，再决定是否继续加 references、scripts 或 evals。": "Clarify the recurring job, real input shape, and deliverable output before adding references, scripts, or evals.",
    "如果需求仍然模糊，优先回到 intent dialogue 收紧边界，再扩展包体结构。": "If the request is still fuzzy, tighten the boundary through intent dialogue before expanding the package.",
    "已生成 Output Review Adjudication，可记录盲评决策、一致率和待评审项。": "Output Review Adjudication is generated to record blind-review decisions, agreement rate, and pending cases.",
    "已生成 Output Execution Runs，可区分记录样本、命令执行和模型执行证据。": "Output Execution Runs is generated to distinguish recorded fixtures, command runs, and model-run evidence.",
    "尚未生成盲评审定报告。": "The blind review adjudication report has not been generated yet.",
    "尚未生成输出执行证据报告。": "The output execution evidence report has not been generated yet.",
    "先记录 reviewer 对 A/B 的选择，再打开答案 key 计算一致率。": "Record the reviewer's A/B choice before opening the answer key and calculating agreement.",
    "缺少真实 reviewer 决策时只显示待评审，不伪造人工结论。": "When real reviewer decisions are missing, show pending status instead of fabricating human conclusions.",
    "recorded fixture 只能证明可复现样本，不等同于模型执行。": "A recorded fixture proves reproducible samples only; it is not model execution.",
    "只有 provider runner 返回 model metadata 时才计入 model-executed。": "Only provider runners that return model metadata count as model-executed.",
}

MODE_ZH = {
    "scaffold": "脚手架",
    "production": "生产",
    "library": "库级",
    "governed": "治理",
    "manual": "手动",
    "inline": "内联",
    "agent-skills": "Agent Skills",
}

PACKAGE_LABEL_ZH = {
    "SKILL.md": "Skill 入口文件",
    "README.md": "人类可读使用说明",
    "agents/interface.yaml": "跨平台接口元数据",
    "manifest.json": "生命周期与打包元数据",
    "references": "扩展指导与复用资料",
    "scripts": "确定性脚本或本地工具",
    "evals": "触发与质量检查",
    "reports": "生成的证据与总结报告",
}

KIND_ZH = {"file": "文件", "folder": "目录"}

LABEL_EN = {
    "强项": "Strength",
    "缺口": "Gap",
    "保留并复用": "Keep",
    "纳入下一轮修复": "Fix next",
}


def contains_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in str(text))


def zh_for(text: str) -> str:
    value = str(text).strip()
    if not value:
        return ""
    if value in TEXT_ZH:
        return TEXT_ZH[value]
    if value in TEXT_EN or contains_cjk(value):
        return value
    if value.startswith("Use this skill when the request matches:"):
        return "当用户请求与该 Skill 的触发描述匹配时使用。"
    if value.startswith("用户说出类似需求时："):
        return "当用户提出与该 Skill 触发描述相近的请求时使用。"
    if value.startswith("Use $") and " when you need to " in value:
        skill, need = value.removeprefix("Use ").split(" when you need to ", 1)
        return f"当你需要{zh_for(need).rstrip('。')}时使用 `{skill}`。"
    if value.startswith("Read the strongest pattern from "):
        repo = value.removeprefix("Read the strongest pattern from ").rstrip(".")
        return f"阅读 `{repo}` 中最值得借鉴的模式。"
    if value.startswith("Primary prompt task family:"):
        return "主要提示任务类型已记录在 prompt quality profile 中。"
    if value.startswith("Complexity:"):
        return "复杂度判断已记录在 prompt quality profile 中。"
    if value.startswith("Stability:"):
        return "系统稳定性评分已记录在 system model 中。"
    if value.startswith("Owned job:"):
        return "负责的核心任务已在 system model 中说明。"
    if value.startswith("Leverage:"):
        return "关键杠杆点已在 system model 中说明。"
    return "原始说明可切换到英文查看；默认中文报告保留结论与结构说明。"


def en_for(text: str) -> str:
    value = str(text).strip()
    return TEXT_EN.get(value, value)


def bi_span(zh: str, en: str | None = None) -> str:
    english = en if en is not None else en_for(zh)
    return (
        f'<span data-lang="zh-CN">{html.escape(str(zh))}</span>'
        f'<span data-lang="en">{html.escape(str(english))}</span>'
    )


def bi_item(text: str) -> str:
    return bi_span(zh_for(text), en_for(text))


def mode_zh(value: str) -> str:
    return MODE_ZH.get(str(value), str(value))


def readable_description_zh(description: str) -> str:
    if contains_cjk(description):
        return description
    return "该 Skill 的触发描述来自 SKILL.md frontmatter；默认中文报告先呈现能力边界，原始英文描述可切换到英文查看。"


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
            f"<span class='metric-label'>{html.escape(str(item.get('label', key)))}</span>"
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
            f"<b>{html.escape(label)}</b>"
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
            f"<span>{html.escape(str(item.get('label', key)))}</span>"
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
    assets = summary.get("package_assets", {})
    roadmap = summary.get("iteration_roadmap", {})
    output_execution = summary.get("output_execution", {})
    output_execution_summary = output_execution.get("summary", {})
    output_review = summary.get("output_review_adjudication", {})
    output_review_summary = output_review.get("summary", {})
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
          <p class="lead">{bi_span("这份报告默认使用中文简体，把新 Skill 的定位、指标、原理、契约、质量、风险、资产和迭代路线整理为一份可审计的 HTML 报告。", summary["description"])}</p>
          <div class="hero-meta">{hero_meta_html}</div>
          <div class="badges">{target_badges}</div>
        </div>
        <aside class="hero-card">
          <h3>{bi_span("核心判断", "Core reading")}</h3>
          {render_list([skill.get("core_value", ""), skill.get("audience", ""), "创建完成后建议先打开 reports/skill-overview.html，再继续扩展包体。"])}
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
            <p>{bi_span(readable_description_zh(str(trigger.get("description", ""))), str(trigger.get("description", "")))}</p>
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
