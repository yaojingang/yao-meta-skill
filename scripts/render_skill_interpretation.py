#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from render_skill_overview import render_html
from skill_report_model import build_report_model


SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Renders the first-class skill interpretation report while reusing the Skill Overview v2 model and layout."


def build_interpretation_model(skill_dir: Path) -> dict:
    summary = build_report_model(skill_dir)
    contract = dict(summary.get("report_contract", {}))
    contract.update(
        {
            "schema_version": "2.0",
            "report_kind": "skill-interpretation",
            "canonical_overview_report": "reports/skill-overview.html",
            "html_report": "reports/skill-interpretation.html",
            "json_report": "reports/skill-interpretation.json",
            "layout": "kami-white-audit-v2",
            "default_language": "zh-CN",
            "languages": ["zh-CN", "en"],
            "purpose": "Explain the generated skill's role, principles, usage scenarios, trigger contract, inputs, outputs, quality evidence, risks, assets, highlights, and next upgrade directions.",
        }
    )
    summary["report_contract"] = contract
    summary["interpretation_contract"] = {
        "schema_version": "2.0",
        "source_model": "skill-overview-v2",
        "source_model_reused": True,
        "overview_report": "reports/skill-overview.html",
        "html_report": "reports/skill-interpretation.html",
        "json_report": "reports/skill-interpretation.json",
        "default_language": "zh-CN",
        "languages": ["zh-CN", "en"],
        "includes": [
            "skill role",
            "principles",
            "usage scenarios",
            "trigger contract",
            "inputs and outputs",
            "quality evidence",
            "risk governance",
            "package assets",
            "highlights",
            "upgrade roadmap",
        ],
    }
    deliverables = summary.get("skill_summary", {}).get("deliverables", [])
    for artifact in ["reports/skill-interpretation.html", "reports/skill-interpretation.json"]:
        if artifact not in deliverables:
            deliverables.append(artifact)
    if "skill_summary" in summary:
        summary["skill_summary"]["deliverables"] = deliverables
    return summary


def render_skill_interpretation(skill_dir: Path, output_html: Path | None = None, output_json: Path | None = None) -> dict:
    skill_dir = skill_dir.resolve()
    reports_dir = skill_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    output_html = output_html or reports_dir / "skill-interpretation.html"
    output_json = output_json or reports_dir / "skill-interpretation.json"

    summary = build_interpretation_model(skill_dir)
    output_html.write_text(render_html(summary), encoding="utf-8")
    output_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "skill_dir": str(skill_dir),
        "artifacts": {
            "html": str(output_html),
            "json": str(output_json),
            "overview_html": str(skill_dir / "reports" / "skill-overview.html"),
        },
        "summary": {
            "name": summary.get("name"),
            "report_kind": summary.get("report_contract", {}).get("report_kind"),
            "default_language": summary.get("report_contract", {}).get("default_language"),
            "section_count": len(summary.get("report_contract", {}).get("nav_labels", [])),
            "source_model_reused": summary.get("interpretation_contract", {}).get("source_model_reused"),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the first-class HTML skill interpretation report for a skill package.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--output-html")
    parser.add_argument("--output-json")
    args = parser.parse_args()

    result = render_skill_interpretation(
        Path(args.skill_dir),
        Path(args.output_html).resolve() if args.output_html else None,
        Path(args.output_json).resolve() if args.output_json else None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
