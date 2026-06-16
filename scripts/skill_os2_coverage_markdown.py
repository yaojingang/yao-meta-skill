from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_skill_os2_coverage.py to keep coverage data assembly separate from Markdown rendering."


def render_table(items: list[dict[str, Any]]) -> list[str]:
    lines = ["| Item | Status | Current | Command | Test |", "| --- | --- | --- | --- | --- |"]
    for item in items:
        lines.append(
            "| "
            + " | ".join(
                [
                    item["label"].replace("|", "\\|"),
                    f"`{item['status']}`",
                    item["current"].replace("|", "\\|"),
                    f"`{item['command']}`",
                    f"`{item['test']}`",
                ]
            )
            + " |"
        )
    return lines


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Skill OS 2.0 Blueprint Coverage",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- decision: `{summary['decision']}`",
        f"- local blueprint ready: `{str(summary['local_blueprint_ready']).lower()}`",
        f"- public world-class ready: `{str(summary['public_world_class_ready']).lower()}`",
        f"- pass: `{summary['pass_count']}` / `{summary['item_count']}`",
        f"- missing: `{summary['missing_count']}`",
        f"- warn: `{summary['warn_count']}`",
        f"- reference extensions: `{summary['extension_track_count']}`",
        f"- extension covered: `{summary['extension_covered_count']}`",
        f"- extension partial: `{summary['extension_partial_count']}`",
        f"- extension planned: `{summary['extension_planned_count']}`",
        f"- adaptive extension ready: `{str(summary['adaptive_extension_ready']).lower()}`",
        f"- world-class evidence pending: `{summary['world_class_evidence_pending_count']}`",
        "",
        "This report maps the Skill OS 2.0 upgrade blueprint to concrete local artifacts, commands, and tests. It does not count pending human review, provider runs, metadata fallbacks, or planned work as public world-class evidence.",
        "",
        "## Core Modules",
        "",
        *render_table(report["modules"]),
        "",
        "## Recommended PR Coverage",
        "",
        *render_table(report["recommended_prs"]),
        "",
        "## Reference Extension Tracks",
        "",
        "| Track | Status | Current | Target | Next action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in report["reference_extension_tracks"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    item["label"].replace("|", "\\|"),
                    f"`{item['status']}`",
                    item["current"].replace("|", "\\|"),
                    item["target"].replace("|", "\\|"),
                    item["next_action"].replace("|", "\\|"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "These extension tracks come from the user-supplied 2.0 reference plan. They are tracked separately from the formal Skill OS blueprint so the report can distinguish landed local architecture from planned explainer/adaptor evolution.",
            "",
            "## Next Highest-Leverage Moves",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in report["next_highest_leverage"])
    lines.extend(["", "## Evidence Detail", ""])
    for item in report["modules"] + report["recommended_prs"] + report["reference_extension_tracks"]:
        existing = [entry["path"] for entry in item["evidence"] if entry["exists"]]
        missing = [entry["path"] for entry in item["evidence"] if not entry["exists"]]
        lines.append(f"### {item['label']}")
        lines.append("")
        lines.append(f"- objective: {item['objective']}")
        lines.append(f"- status: `{item['status']}`")
        lines.append(f"- existing evidence: {', '.join(f'`{path}`' for path in existing) if existing else '`none`'}")
        if missing:
            lines.append(f"- missing evidence: {', '.join(f'`{path}`' for path in missing)}")
        lines.append(f"- next action: {item['next_action']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
