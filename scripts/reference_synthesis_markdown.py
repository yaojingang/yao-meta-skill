from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_reference_synthesis.py to keep reference synthesis modeling separate from Markdown rendering."


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Reference Synthesis",
        "",
        f"Skill: `{summary['skill_name']}`",
        f"- Description: {summary['description']}",
        f"- Intent confidence: `{summary['intent_confidence']['score']}/100` (`{summary['intent_confidence']['band']}`)",
        "",
        "## Live GitHub Benchmarks",
        "",
    ]
    if summary["github_benchmarks"]:
        for repo in summary["github_benchmarks"]:
            lines.extend(
                [
                    f"### {repo['name']}",
                    f"- URL: {repo['url']}",
                    f"- Stars: `{repo['stars']}`",
                ]
            )
            for item in repo.get("borrow", []):
                lines.append(f"- Borrow: {item}")
            lines.append("")
    else:
        lines.append("- No live GitHub benchmarks are attached yet.")
        lines.append("")

    lines.extend(["## Curated World-Class Pattern Tracks", ""])
    for track in summary["source_tracks"]:
        lines.extend(
            [
                f"### {track['name']}",
                f"- Type: `{track['source_type']}`",
                f"- Evidence mode: `{track['evidence_mode']}`",
                f"- Why relevant: {track['why_relevant']}",
                f"- Borrow: {track['borrow']}",
                f"- Avoid: {track['avoid']}",
                "",
            ]
        )

    lines.extend(["## Borrow Now", ""])
    for item in summary["synthesis"]["borrow_now"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Avoid Now", ""])
    for item in summary["synthesis"]["avoid_now"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Pattern Gate", ""])
    pattern_gate = summary["synthesis"]["pattern_gate"]
    lines.append(f"- Summary: {pattern_gate['summary']}")
    lines.append(f"- Acceptance threshold: `{pattern_gate['threshold']}/4`")
    if pattern_gate["accepted"]:
        lines.append("- Accepted patterns:")
        for item in pattern_gate["accepted"][:5]:
            lines.append(
                f"  - **{item['name']}**: {item['score']}/4 "
                f"({', '.join(item['passed'])})"
            )
    if pattern_gate["deferred"]:
        lines.append("- Deferred patterns:")
        for item in pattern_gate["deferred"][:5]:
            lines.append(
                f"  - **{item['name']}**: missing {', '.join(item['missing']) or 'none'}"
            )

    lines.extend(["", "## Default Recommendation", ""])
    lines.append(f"- Summary: {summary['synthesis']['recommendation']['summary']}")
    lines.append(f"- Why: {summary['synthesis']['recommendation']['why']}")
    lines.append(f"- User decision required: `{summary['synthesis']['recommendation']['user_decision_required']}`")

    lines.extend(["", "## Visibility Mode", ""])
    lines.append(f"- Mode: `{summary['synthesis']['visibility']['mode']}`")
    if summary["synthesis"]["visibility"]["reasons"]:
        lines.append(f"- Reasons: {', '.join(summary['synthesis']['visibility']['reasons'])}")
    lines.append(f"- User note: {summary['synthesis']['visibility']['user_note']}")
    lines.append(f"- Reviewer note: {summary['synthesis']['visibility']['reviewer_note']}")

    lines.extend(["", "## Conflict Check", ""])
    if summary["synthesis"]["conflicts"]:
        for conflict in summary["synthesis"]["conflicts"]:
            lines.append(f"- **{conflict['key']}**: {conflict['summary']}")
    else:
        lines.append("- No material design conflict detected. Keep the synthesis silent for the user.")

    lines.extend(["", "## Quality Lift Thesis", ""])
    for item in summary["synthesis"]["quality_risers"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Decision Prompt", "", summary["synthesis"]["decision_prompt"], ""])
    return "\n".join(lines).strip() + "\n"
