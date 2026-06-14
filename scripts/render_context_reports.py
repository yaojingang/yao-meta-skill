#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from resource_boundary_check import analyze_skill


ROOT = Path(__file__).resolve().parent.parent
TARGETS = [
    {
        "label": "root",
        "path": ROOT,
        "json_output": ROOT / "reports" / "context_budget.json",
    },
    {
        "label": "complex-release-orchestrator",
        "path": ROOT / "examples" / "complex-release-orchestrator" / "generated-skill",
        "json_output": ROOT / "examples" / "complex-release-orchestrator" / "generated-skill" / "reports" / "context_budget.json",
    },
    {
        "label": "governed-incident-command",
        "path": ROOT / "examples" / "governed-incident-command" / "generated-skill",
        "json_output": ROOT / "examples" / "governed-incident-command" / "generated-skill" / "reports" / "context_budget.json",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render context budget reports for root and example skills.")
    parser.add_argument(
        "--generated-at",
        default="2026-03-31",
        help="Report date written to context_budget_summary.json.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = []
    for target in TARGETS:
        report = analyze_skill(target["path"])
        target["json_output"].parent.mkdir(parents=True, exist_ok=True)
        target["json_output"].write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        stats = report.get("stats", {})
        rows.append(
            {
                "label": target["label"],
                "path": str(target["path"].relative_to(ROOT)) if target["path"] != ROOT else ".",
                "budget_tier": stats.get("context_budget_tier"),
                "budget_limit": stats.get("context_budget_limit"),
                "initial_tokens": stats.get("estimated_initial_load_tokens"),
                "skill_body_tokens": stats.get("skill_body_tokens"),
                "deferred_resource_tokens": stats.get("deferred_resource_tokens"),
                "large_deferred_resource_dirs": stats.get("large_deferred_resource_dirs", []),
                "deferred_resource_governance": stats.get("deferred_resource_governance", {}),
                "quality_density": stats.get("quality_density"),
                "unused_resource_dirs": stats.get("unused_resource_dirs", []),
                "ok": report.get("ok"),
                "warnings": report.get("warnings", []),
            }
        )

    summary = {
        "generated_at": args.generated_at,
        "targets": rows,
    }
    (ROOT / "reports").mkdir(parents=True, exist_ok=True)
    (ROOT / "reports" / "context_budget_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Context Budget Summary",
        "",
        "| Target | Path | Tier | Limit | Initial | SKILL | Deferred | Resource Governance | Large Deferred Dirs | Quality Density | Unused Dirs | Status |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |",
    ]
    for row in rows:
        unused = ", ".join(row["unused_resource_dirs"]) if row["unused_resource_dirs"] else "-"
        governance = row.get("deferred_resource_governance", {}) or {}
        governance_status = governance.get("status", "unknown")
        large_dirs = ", ".join(
            f"{item['path']}:{item['estimated_tokens']}"
            for item in row.get("large_deferred_resource_dirs", [])
        ) or "-"
        status = "ok" if row["ok"] else "fail"
        lines.append(
            f"| {row['label']} | `{row['path']}` | `{row['budget_tier']}` | {row['budget_limit']} | {row['initial_tokens']} | {row['skill_body_tokens']} | {row['deferred_resource_tokens']} | `{governance_status}` | {large_dirs} | {row['quality_density']} | {unused} | {status} |"
        )
    lines.extend(["", "Per-target JSON reports are written beside each target and under `reports/`."])
    (ROOT / "reports" / "context_budget.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
