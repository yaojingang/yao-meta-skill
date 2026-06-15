#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "scripts" / "yao.py"
TMP = ROOT / "tests" / "tmp_skill_interpretation"


def run(*args: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)
    return {"ok": proc.returncode == 0, "payload": payload, "stderr": proc.stderr}


def main() -> None:
    shutil.rmtree(TMP, ignore_errors=True)
    init_result = run(
        "init",
        "interpretation-demo-skill",
        "--description",
        "Turn messy launch notes into a reusable launch checklist skill with review gates.",
        "--output-dir",
        str(TMP),
        "--mode",
        "production",
        "--archetype",
        "production",
    )
    assert init_result["ok"], init_result
    skill_dir = Path(init_result["payload"]["root"])
    assert (skill_dir / "reports" / "skill-overview.html").exists(), skill_dir
    assert (skill_dir / "reports" / "skill-interpretation.html").exists(), skill_dir
    assert (skill_dir / "reports" / "skill-interpretation.json").exists(), skill_dir
    report_view = init_result["payload"]["report_view"]
    assert report_view["interpretation_report"].endswith("reports/skill-interpretation.html"), report_view
    assert "reports/skill-interpretation.html" in report_view["message"], report_view

    rerender_result = run("skill-interpretation", str(skill_dir))
    assert rerender_result["ok"], rerender_result
    assert rerender_result["payload"]["artifacts"]["html"].endswith("reports/skill-interpretation.html"), rerender_result
    assert rerender_result["payload"]["summary"]["report_kind"] == "skill-interpretation", rerender_result
    assert rerender_result["payload"]["summary"]["default_language"] == "zh-CN", rerender_result
    assert rerender_result["payload"]["summary"]["section_count"] == 9, rerender_result
    assert rerender_result["payload"]["summary"]["source_model_reused"] is True, rerender_result

    payload = json.loads((skill_dir / "reports" / "skill-interpretation.json").read_text(encoding="utf-8"))
    assert payload["report_contract"]["schema_version"] == "2.0", payload["report_contract"]
    assert payload["report_contract"]["report_kind"] == "skill-interpretation", payload["report_contract"]
    assert payload["report_contract"]["html_report"] == "reports/skill-interpretation.html", payload["report_contract"]
    assert payload["report_contract"]["default_language"] == "zh-CN", payload["report_contract"]
    assert payload["report_contract"]["languages"] == ["zh-CN", "en"], payload["report_contract"]
    assert payload["report_contract"]["layout"] == "kami-white-audit-v2", payload["report_contract"]
    assert payload["interpretation_contract"]["source_model"] == "skill-overview-v2", payload["interpretation_contract"]
    assert payload["interpretation_contract"]["source_model_reused"] is True, payload["interpretation_contract"]
    assert len(payload["interpretation_contract"]["includes"]) >= 10, payload["interpretation_contract"]
    assert all(len(label) == 4 for label in payload["report_contract"]["nav_labels"]), payload["report_contract"]
    assert "reports/skill-interpretation.html" in payload["skill_summary"]["deliverables"], payload["skill_summary"]

    html = (skill_dir / "reports" / "skill-interpretation.html").read_text(encoding="utf-8")
    assert 'data-report-lang="zh-CN"' in html, html[:500]
    assert 'class="language-switch"' in html, html[:2600]
    assert "reports/skill-interpretation.html" in html, html[:10000]
    assert "After creation, open reports/skill-interpretation.html before expanding the package further." in html, html[:12000]
    for label in ("技能概述", "总览指标", "能力画像", "原理结构", "契约边界", "质量评估", "风险治理", "包体资产", "迭代路线"):
        assert f">{label}</span>" in html, label
    for chart_label in ("评分雷达", "交付流程", "能力矩阵", "风险热力", "资产分布", "迭代时间"):
        assert chart_label in html, chart_label

    schema = json.loads((ROOT / "schemas" / "skill-interpretation.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["report_contract"]["properties"]["report_kind"]["const"] == "skill-interpretation", schema
    assert schema["properties"]["interpretation_contract"]["properties"]["source_model_reused"]["const"] is True, schema
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
