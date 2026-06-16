#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "scripts" / "yao.py"
sys.path.insert(0, str(ROOT / "scripts"))

from skill_report_layout import render_language_switch, render_report_nav, skill_overview_css, skill_overview_script
from skill_report_i18n import en_for
from skill_report_model import REPORT_NAV_V2, build_report_model


def run(*args: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "payload": payload,
        "stderr": proc.stderr,
    }


def main() -> None:
    nav_contract = render_report_nav(REPORT_NAV_V2)
    assert nav_contract.count("<a ") == 9, nav_contract
    assert '#overview' in nav_contract, nav_contract
    assert ">技能概述</span>" in nav_contract, nav_contract
    assert ">Overview</span>" in nav_contract, nav_contract
    assert render_report_nav([]) == ""

    language_switch_contract = render_language_switch()
    assert 'data-set-lang="zh-CN"' in language_switch_contract, language_switch_contract
    assert 'data-set-lang="en"' in language_switch_contract, language_switch_contract
    assert 'aria-pressed="true"' in language_switch_contract, language_switch_contract

    css_contract = skill_overview_css()
    assert css_contract == (ROOT / "assets" / "skill-overview.css").read_text(encoding="utf-8").strip()
    assert "position: sticky" in css_contract, css_contract[:1200]
    assert ".report-nav {" in css_contract, css_contract[:3200]
    assert "background: #ffffff" in css_contract, css_contract[:1600]
    assert ".section-body" in css_contract, css_contract[:7000]
    assert ".metrics-primary" in css_contract, css_contract[:7000]
    assert ".metrics-flow" in css_contract, css_contract[:9000]
    assert ".metric-detail-grid" in css_contract, css_contract[:9000]
    assert ".metrics-primary {\n      display: grid;\n      grid-template-columns: minmax(0, 1fr);" in css_contract, css_contract[:9000]
    assert ".metric-detail-grid {\n      grid-template-columns: repeat(2, minmax(0, 1fr));" in css_contract, css_contract[:9000]
    assert "repeat(auto-fit, minmax(min(100%, 340px), 1fr))" not in css_contract, css_contract[:9000]
    assert "grid-template-columns: minmax(420px, 1fr)" not in css_contract, css_contract[:9000]
    assert "overflow-wrap: break-word" in css_contract, css_contract[:9000]
    assert ".metrics-primary, .metric-detail-grid, .two-col" in css_contract, css_contract[-2600:]
    assert "@media (max-width: 980px)" in css_contract, css_contract[-2200:]

    script_contract = skill_overview_script()
    assert script_contract == (ROOT / "assets" / "skill-overview.js").read_text(encoding="utf-8").strip()
    assert 'setLanguage("zh-CN")' in script_contract, script_contract[-1000:]
    assert "scaleX(" in script_contract, script_contract
    assert "aria-current" in script_contract, script_contract

    assert en_for("把一次性经验沉淀为可复用、可评估、可迁移的 Skill 包体。") == (
        "Turn one-off experience into a reusable, evaluable, and portable skill package."
    )
    assert en_for("交付结果：SKILL.md, agents/interface.yaml") == "Deliverables: SKILL.md, agents/interface.yaml"
    assert en_for("已生成 12 / 20 类报告证据。") == "Generated 12 / 20 evidence report types."
    assert en_for("skill-ir.json 已存在。") == "skill-ir.json exists."
    assert en_for("compiled_targets.json 已存在。") == "compiled_targets.json exists."
    assert en_for("reports 未发现或为空，完整度扣分。") == (
        "reports was not found or is empty, reducing completeness."
    )
    assert en_for("evals/ 证据不足。") == "evals/ evidence is insufficient."
    assert en_for("用户提供的工作流、提示词、文档、记录或散乱笔记") == (
        "User-provided workflows, prompts, documents, records, or rough notes."
    )
    assert en_for("期望沉淀的复用场景、排除项、约束和质量标准") == (
        "The reusable scenario, exclusions, constraints, and quality standards to capture."
    )
    assert en_for("可路由的 SKILL.md") == "A routeable SKILL.md."
    assert en_for("agents/interface.yaml 元数据") == "agents/interface.yaml metadata."
    assert en_for("必要的 references、scripts、evals、reports 证据") == (
        "Necessary references, scripts, evals, and reports evidence."
    )
    assert en_for("入口约 864 个词/字，references 约 565 个词/字。") == (
        "Entrypoint is about 864 words/characters; references are about 565."
    )
    assert en_for("Use this skill when the request matches: 中文描述") == (
        "Use this skill when the request matches the frontmatter description."
    )
    assert en_for("补齐世界证据") == "Close world-class evidence"
    assert en_for("世界级证据仍有 2 项待补；公开完成态 claim 必须继续保持阻塞。") == (
        "World-class evidence still has 2 pending item(s); public completion claims must stay blocked."
    )
    assert en_for("补齐提供商留出证据：缺少真实 provider 模型运行和 token metadata。") == (
        "Close provider holdout evidence: Missing a real provider model run and token metadata."
    )
    assert en_for("提交有效 intake packet，并让 ledger 通过 artifact SHA-256 校验。") == (
        "Submit valid intake packets and let the ledger verify artifact SHA-256 digests."
    )

    root_model = build_report_model(ROOT)
    assert root_model["skill_ir"]["source_path"] == "skill-ir/examples/yao-meta-skill.json", root_model["skill_ir"]
    assert "skill-ir/examples/yao-meta-skill.json" in root_model["skill_summary"]["deliverables"], root_model[
        "skill_summary"
    ]
    assert "reports/skill-ir.json" not in root_model["skill_summary"]["deliverables"], root_model["skill_summary"]

    tmp_root = ROOT / "tests" / "tmp_skill_overview"
    if tmp_root.exists():
        subprocess.run(["rm", "-rf", str(tmp_root)], check=True)
    tmp_root.mkdir(parents=True, exist_ok=True)

    init_result = run(
        "init",
        "skill-overview-demo",
        "--description",
        "Turn rough requests into a compact reusable demo skill.",
        "--output-dir",
        str(tmp_root),
    )
    assert init_result["ok"], init_result

    created = tmp_root / "skill-overview-demo"
    assert (created / "README.md").exists(), created
    assert (created / "manifest.json").exists(), created
    assert (created / "reports" / "intent-dialogue.md").exists(), created
    assert (created / "reports" / "intent-dialogue.json").exists(), created
    assert (created / "reports" / "intent-confidence.md").exists(), created
    assert (created / "reports" / "intent-confidence.json").exists(), created
    assert (created / "reports" / "skill-overview.html").exists(), created
    assert (created / "reports" / "skill-overview.json").exists(), created
    assert (created / "reports" / "skill-interpretation.html").exists(), created
    assert (created / "reports" / "skill-interpretation.json").exists(), created
    assert (created / "reports" / "compiled_targets.md").exists(), created
    assert (created / "reports" / "compiled_targets.json").exists(), created
    assert (created / "reports" / "reference-synthesis.md").exists(), created
    assert (created / "reports" / "reference-synthesis.json").exists(), created
    assert (created / "reports" / "artifact-design-profile.md").exists(), created
    assert (created / "reports" / "artifact-design-profile.json").exists(), created
    assert (created / "reports" / "prompt-quality-profile.md").exists(), created
    assert (created / "reports" / "prompt-quality-profile.json").exists(), created
    assert (created / "reports" / "system-model.md").exists(), created
    assert (created / "reports" / "system-model.json").exists(), created
    assert (created / "reports" / "iteration-directions.md").exists(), created
    assert (created / "reports" / "iteration-directions.json").exists(), created
    assert (created / "reports" / "adoption_drift_report.md").exists(), created
    assert (created / "reports" / "adoption_drift_report.json").exists(), created
    assert (created / "reports" / "review_waivers.md").exists(), created
    assert (created / "reports" / "review_waivers.json").exists(), created

    overview_json = json.loads((created / "reports" / "skill-overview.json").read_text(encoding="utf-8"))
    directions_json = json.loads((created / "reports" / "iteration-directions.json").read_text(encoding="utf-8"))
    assert overview_json["report_contract"]["schema_version"] == "2.0", overview_json.get("report_contract")
    assert overview_json["report_contract"]["layout"] == "kami-white-audit-v2", overview_json.get("report_contract")
    expected_v2_keys = {
        "skill_summary",
        "scorecard",
        "capability_profile",
        "principle_model",
        "contract_boundary",
        "quality_review",
        "risk_governance",
        "package_assets",
        "iteration_roadmap",
        "report_contract",
    }
    assert expected_v2_keys.issubset(overview_json.keys()), overview_json.keys()
    assert "reports/skill-ir.json" in overview_json["skill_summary"]["deliverables"], overview_json["skill_summary"]
    assert overview_json["skill_ir"]["source_path"] == "reports/skill-ir.json", overview_json["skill_ir"]
    assert "reports/compiled_targets.md" in overview_json["skill_summary"]["deliverables"], overview_json["skill_summary"]
    assert "reports/output_quality_scorecard.md" in overview_json["skill_summary"]["deliverables"], overview_json["skill_summary"]
    assert "reports/output_blind_review_pack.md" not in overview_json["skill_summary"]["deliverables"], overview_json["skill_summary"]
    assert "reports/benchmark_reproducibility.md" not in overview_json["skill_summary"]["deliverables"], overview_json["skill_summary"]
    assert "reports/world_class_evidence_ledger.md" not in overview_json["skill_summary"]["deliverables"], overview_json["skill_summary"]
    assert "reports/conformance_matrix.md" in overview_json["skill_summary"]["deliverables"], overview_json["skill_summary"]
    assert "reports/security_trust_report.md" in overview_json["skill_summary"]["deliverables"], overview_json["skill_summary"]
    assert "reports/runtime_permission_probes.md" not in overview_json["skill_summary"]["deliverables"], overview_json["skill_summary"]
    assert "reports/skill_atlas.html" in overview_json["skill_summary"]["deliverables"], overview_json["skill_summary"]
    assert "reports/registry_audit.md" in overview_json["skill_summary"]["deliverables"], overview_json["skill_summary"]
    assert "reports/package_verification.md" in overview_json["skill_summary"]["deliverables"], overview_json["skill_summary"]
    assert "reports/install_simulation.md" in overview_json["skill_summary"]["deliverables"], overview_json["skill_summary"]
    assert "reports/upgrade_check.md" in overview_json["skill_summary"]["deliverables"], overview_json["skill_summary"]
    assert "reports/adoption_drift_report.md" in overview_json["skill_summary"]["deliverables"], overview_json["skill_summary"]
    assert "reports/review_waivers.md" in overview_json["skill_summary"]["deliverables"], overview_json["skill_summary"]
    assert "reports/review-studio.html" in overview_json["skill_summary"]["deliverables"], overview_json["skill_summary"]
    assert "reports/skill-interpretation.html" in overview_json["skill_summary"]["deliverables"], overview_json["skill_summary"]
    assert overview_json["skill_ir"]["schema_version"] in {"", "2.0.0"}, overview_json.get("skill_ir")
    assert overview_json["compiled_targets"]["summary"]["target_count"] >= 3, overview_json.get("compiled_targets")
    assert overview_json["compiled_targets"]["summary"]["block_count"] == 0, overview_json.get("compiled_targets")
    assert "output_quality" in overview_json, overview_json.keys()
    assert "output_execution" in overview_json, overview_json.keys()
    assert overview_json["output_execution"]["summary"] == {}, overview_json["output_execution"]
    assert "output_blind_review" in overview_json, overview_json.keys()
    assert overview_json["output_blind_review"]["summary"] == {}, overview_json["output_blind_review"]
    assert "output_review_adjudication" in overview_json, overview_json.keys()
    assert overview_json["output_review_adjudication"]["summary"] == {}, overview_json["output_review_adjudication"]
    assert "benchmark_reproducibility" in overview_json, overview_json.keys()
    assert overview_json["benchmark_reproducibility"]["summary"] == {}, overview_json["benchmark_reproducibility"]
    assert "world_class_evidence_ledger" in overview_json, overview_json.keys()
    assert overview_json["world_class_evidence_ledger"]["summary"] == {}, overview_json["world_class_evidence_ledger"]
    assert "world_class_readiness" in overview_json, overview_json.keys()
    assert overview_json["world_class_readiness"]["entry_count"] == 0, overview_json["world_class_readiness"]
    assert overview_json["world_class_readiness"]["decision"] == "not-generated", overview_json["world_class_readiness"]
    assert "runtime_conformance" in overview_json, overview_json.keys()
    assert "runtime_permissions" in overview_json, overview_json.keys()
    assert overview_json["runtime_permissions"]["summary"] == {}, overview_json["runtime_permissions"]
    assert "trust_security" in overview_json, overview_json.keys()
    assert "skill_atlas" in overview_json, overview_json.keys()
    assert "registry_distribution" in overview_json, overview_json.keys()
    assert "package_verification" in overview_json, overview_json.keys()
    assert "install_simulation" in overview_json, overview_json.keys()
    assert "upgrade_check" in overview_json, overview_json.keys()
    assert "adoption_drift" in overview_json, overview_json.keys()
    assert "review_waivers" in overview_json, overview_json.keys()
    assert [item["title"] for item in overview_json["iteration_roadmap"]["items"]] == [
        item["title"] for item in directions_json["directions"]
    ], {
        "overview_roadmap": overview_json["iteration_roadmap"],
        "iteration_directions": directions_json["directions"],
    }

    initial_report_html = (created / "reports" / "skill-overview.html").read_text(encoding="utf-8")
    assert directions_json["directions"][0]["title"] in initial_report_html, initial_report_html[:5000]
    assert "世界证据" in initial_report_html, initial_report_html
    assert "No world-class ledger has been generated" in initial_report_html, initial_report_html
    assert "Skill-specific source text is authored in Chinese" not in initial_report_html, initial_report_html

    sample_ledger = {
        "schema_version": "1.0",
        "ok": True,
        "summary": {
            "ledger_entry_count": 2,
            "accepted_count": 0,
            "pending_count": 2,
            "external_pending_count": 1,
            "human_pending_count": 1,
            "source_check_count": 4,
            "source_pass_count": 1,
            "ready_to_claim_world_class": False,
            "decision": "evidence-pending",
        },
        "entries": [
            {
                "key": "provider-holdout",
                "label": "Provider Holdout",
                "category": "external",
                "status": "pending",
                "source_checklist": [
                    {"label": "Provider model run", "status": "blocked"},
                    {"label": "Timing observed", "status": "pass"},
                ],
            },
            {
                "key": "human-adjudication",
                "label": "Human Adjudication",
                "category": "human",
                "status": "pending",
                "source_checklist": [
                    {"label": "No pending decisions", "status": "blocked"},
                ],
            },
        ],
    }
    (created / "reports" / "world_class_evidence_ledger.json").write_text(
        json.dumps(sample_ledger, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (created / "reports" / "world_class_evidence_ledger.md").write_text(
        "# World Class Evidence Ledger\n",
        encoding="utf-8",
    )

    rerender_result = run("skill-report", str(created))
    assert rerender_result["ok"], rerender_result
    assert rerender_result["payload"]["artifacts"]["html"].endswith("reports/skill-overview.html"), rerender_result

    report_html = (created / "reports" / "skill-overview.html").read_text(encoding="utf-8")
    assert 'lang="zh-CN"' in report_html, report_html[:200]
    assert 'data-report-lang="zh-CN"' in report_html, report_html[:400]
    assert 'class="language-switch"' in report_html, report_html[:2400]
    assert 'class="skip-link"' in report_html, report_html[:2400]
    assert 'class="progress-bar"' in report_html, report_html[:2400]
    assert 'aria-current' in report_html, report_html[-3000:]
    assert 'class="section-body metrics-report"' in report_html, report_html[:9000]
    assert 'class="metrics-flow"' in report_html, report_html[:9000]
    assert 'class="metrics-primary"' in report_html, report_html[:9000]
    assert 'class="metrics-stack"' not in report_html, report_html[:9000]
    assert 'class="metric-grid metric-detail-grid"' in report_html, report_html[:12000]
    assert report_html.index('class="metrics-primary"') < report_html.index('class="metric-grid metric-detail-grid"'), report_html[:12000]
    assert "class='metric-summary-list'" in report_html, report_html[:9000]
    assert "class='metric-card-head'" in report_html, report_html[:12000]
    assert 'data-set-lang="zh-CN"' in report_html, report_html[:2600]
    assert 'data-set-lang="en"' in report_html, report_html[:2800]
    assert 'data-lang="zh-CN"' in report_html, report_html[:3200]
    assert 'data-lang="en"' in report_html, report_html[:3400]
    assert "position: sticky" in report_html, report_html[:1200]
    assert "background: #ffffff" in report_html, report_html[:1600]
    assert ".report-nav {" in report_html and "overflow-x: auto" in report_html, report_html[:5000]
    assert "scaleX(" in report_html, report_html[-3000:]
    for label in ("技能概述", "总览指标", "能力画像", "原理结构", "契约边界", "质量评估", "风险治理", "包体资产", "迭代路线"):
        assert f">{label}</span>" in report_html, label
        assert len(label) == 4, label
    assert 'aria-label="Skill principle flow"' in report_html, report_html[:2400]
    for chart_label in ("评分雷达", "交付流程", "能力矩阵", "风险热力", "资产分布", "迭代时间"):
        assert chart_label in report_html, chart_label
    assert "技能名称" in report_html, report_html[:5000]
    assert "成熟度" in report_html, report_html[:5000]
    assert "更新时间" in report_html, report_html[:5000]
    assert "Skill name" in report_html, report_html[:5000]
    assert "Turn one-off experience into a reusable, evaluable, and portable skill package." in report_html, report_html[:9000]
    assert "After creation, open reports/skill-overview.html before expanding the package further." in report_html, report_html[:9000]
    assert "世界证据" in report_html, report_html
    assert "证据待补" in report_html, report_html
    assert "世界级证据尚未完成：2 项待补，0 项已接受。" in report_html, report_html
    assert "World-class evidence is not complete: 2 pending, 0 accepted." in report_html, report_html
    assert "提供商留出" in report_html, report_html
    assert "人工盲评" in report_html, report_html
    assert "Provider Holdout" in report_html, report_html
    assert "阻塞检查" in report_html, report_html
    assert "Blocked Checks" in report_html, report_html
    assert "Provider model run" in report_html, report_html
    assert "No pending decisions" in report_html, report_html
    assert '<span data-lang="en">把一次性经验沉淀为可复用、可评估、可迁移的 Skill 包体。</span>' not in report_html, report_html[:9000]
    assert '<span data-lang="en">创建完成后建议先打开 reports/skill-overview.html，再继续扩展包体。</span>' not in report_html, report_html[:9000]
    assert "输入材料" in report_html, report_html[:3000]
    assert "输出结果" in report_html, report_html[:3400]
    assert "Top 3 Next Moves" not in report_html, report_html[:3800]
    assert "下一步" in report_html, report_html[:4200]

    overview_json = json.loads((created / "reports" / "skill-overview.json").read_text(encoding="utf-8"))
    assert "reports/world_class_evidence_ledger.md" in overview_json["skill_summary"]["deliverables"], overview_json["skill_summary"]
    assert overview_json["world_class_readiness"]["entry_count"] == 2, overview_json["world_class_readiness"]
    assert overview_json["world_class_readiness"]["pending_count"] == 2, overview_json["world_class_readiness"]
    assert overview_json["world_class_readiness"]["source_pass_count"] == 1, overview_json["world_class_readiness"]
    assert overview_json["world_class_readiness"]["source_check_count"] == 4, overview_json["world_class_readiness"]
    assert overview_json["iteration_roadmap"]["items"][0]["title"] == "补齐世界证据", overview_json["iteration_roadmap"]
    assert overview_json["iteration_roadmap"]["items"][0]["source"] == "world_class_evidence_ledger", overview_json["iteration_roadmap"]
    assert "世界级证据仍有 2 项待补" in overview_json["iteration_roadmap"]["items"][0]["why"], overview_json["iteration_roadmap"]
    assert any("补齐提供商留出证据" in item for item in overview_json["iteration_roadmap"]["items"][0]["actions"]), overview_json["iteration_roadmap"]
    assert "Close world-class evidence" in report_html, report_html
    assert "执行流程" in report_html, report_html[:5000]
    assert "调用方式" in report_html, report_html[:5000]
    assert "证据不足" in report_html or "证据充分" in report_html, report_html[:8000]
    assert "执行证据" in report_html, report_html
    assert "尚未生成输出执行证据报告" in report_html, report_html
    assert "盲评审定" in report_html, report_html
    assert "尚未生成盲评审定报告" in report_html, report_html
    assert "原始说明可切换到英文查看；默认中文报告保留结论与结构说明。" not in report_html, report_html[:12000]
    assert "理解用户请求" in report_html, report_html[:5000]
    assert overview_json["logic_steps"][0] in report_html, overview_json.get("logic_steps")
    assert overview_json["usage_steps"][0] in report_html, overview_json.get("usage_steps")
    assert overview_json["report_contract"]["default_language"] == "zh-CN", overview_json.get("report_contract")
    assert overview_json["report_contract"]["languages"] == ["zh-CN", "en"], overview_json.get("report_contract")
    assert overview_json["report_contract"]["nav_labels"] == [
        "技能概述",
        "总览指标",
        "能力画像",
        "原理结构",
        "契约边界",
        "质量评估",
        "风险治理",
        "包体资产",
        "迭代路线",
    ], overview_json.get("report_contract")

    intent_text = (created / "reports" / "intent-dialogue.md").read_text(encoding="utf-8")
    assert "Questions To Ask" in intent_text, intent_text[:400]

    directions_text = (created / "reports" / "iteration-directions.md").read_text(encoding="utf-8")
    assert "Top 3 Next Moves" in directions_text, directions_text[:400]

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
