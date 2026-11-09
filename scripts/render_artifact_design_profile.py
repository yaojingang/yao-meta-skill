#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


ARTIFACT_FAMILIES = [
    {
        "key": "tutorial",
        "label": "Tutorial or guide",
        "keywords": ["tutorial", "guide", "lesson", "course", "walkthrough", "how to", "教程", "指南", "课程"],
        "direction": "Progressive instructional layout with domain-specific section names, short success checks, and examples close to the user's real input.",
        "layout": ["opening promise", "task-specific sections", "worked example", "success checks", "common mistakes"],
        "quality_gates": [
            "Replace generic headings with learner- and domain-specific headings.",
            "Pair every major step with a visible success check.",
            "Do not add screenshots unless they are real, current, and action-relevant.",
        ],
    },
    {
        "key": "report",
        "label": "Report or brief",
        "keywords": ["report", "brief", "analysis", "summary", "memo", "white paper", "报告", "简报", "分析", "总结"],
        "direction": "High-trust editorial report with a clear first-screen thesis, compact evidence blocks, and decisions separated from supporting detail.",
        "layout": ["thesis", "evidence blocks", "decision table", "risks", "next actions"],
        "quality_gates": [
            "Keep the first screen useful without requiring the reader to parse every detail.",
            "Use tables only for comparisons; move explanations below the table.",
            "Keep source notes readable without flooding the body with markers.",
        ],
    },
    {
        "key": "review_viewer",
        "label": "Review viewer",
        "keywords": ["review", "viewer", "compare", "diff", "audit", "评审", "对比", "审查"],
        "direction": "Side-by-side reviewer studio with explicit tradeoffs, evidence readiness, and fast paths for approving, blocking, or requesting one focused fix.",
        "layout": ["summary", "variant comparison", "evidence", "risks", "review decision"],
        "quality_gates": [
            "Make differences visible instead of hiding them in prose.",
            "Separate author-facing recommendations from reviewer-only evidence.",
            "Surface conflicts clearly and keep routine benchmark synthesis quiet.",
        ],
    },
    {
        "key": "dashboard",
        "label": "Dashboard or metrics page",
        "keywords": ["dashboard", "metric", "score", "kpi", "chart", "table", "scorecard", "仪表盘", "指标", "评分", "图表", "表格"],
        "direction": "Metric-first dashboard with stable dimensions, short labels, visible deltas, and narrative callouts only where they change interpretation.",
        "layout": ["metric board", "ranked signals", "comparison rows", "interpretation", "action queue"],
        "quality_gates": [
            "Avoid paragraph-heavy table cells.",
            "Keep charts tied to one analytical question each.",
            "Preserve stable color meaning across metrics and entities.",
        ],
    },
    {
        "key": "visual_capture",
        "label": "Screenshot or visual evidence",
        "keywords": ["screenshot", "screen capture", "image evidence", "figma", "截图", "图片", "截屏", "视觉证据"],
        "direction": "Evidence-led visual artifact that records source, viewport, crop intent, and the exact region the reader should inspect.",
        "layout": ["source context", "visual frame", "inspection notes", "limitations", "next capture"],
        "quality_gates": [
            "Never invent missing screenshots or visual states.",
            "Record source, viewport, and crop intent.",
            "Describe the action-relevant region instead of only saying an image exists.",
        ],
    },
    {
        "key": "slide_like",
        "label": "Slide-like narrative",
        "keywords": ["slide", "ppt", "deck", "presentation", "one-pager", "演示", "幻灯片", "一页纸"],
        "direction": "Narrative page rhythm with strong section roles, controlled density, and a visual system chosen from the topic rather than a default template.",
        "layout": ["hero claim", "supporting proof", "structured contrast", "implication", "closing action"],
        "quality_gates": [
            "Plan role, density, and rhythm before writing HTML.",
            "Avoid three or more repeated surfaces in a row.",
            "Use structure, spacing, and type before decoration.",
        ],
    },
    {
        "key": "code_or_cli",
        "label": "Code, CLI, or implementation guide",
        "keywords": ["code", "cli", "script", "api", "command", "terminal", "代码", "脚本", "命令", "接口"],
        "direction": "Execution-focused technical artifact with environment assumptions, copyable commands, expected outputs, and side effects made explicit.",
        "layout": ["prerequisites", "commands", "expected output", "failure handling", "rollback or cleanup"],
        "quality_gates": [
            "Name the working directory and required inputs for commands.",
            "Mark destructive, networked, or external side-effect operations.",
            "Prefer the smallest runnable snippet over broad framework scaffolding.",
        ],
    },
]


DESIGN_TOKENS = {
    "type": [
        "Use a distinctive display face or serif for major claims when the artifact is editorial.",
        "Use a restrained sans for dense body text and technical details.",
        "Use mono only for metadata, paths, commands, labels, and evidence tags.",
    ],
    "color": [
        "Choose colors from the artifact's domain, brand, or evidence mood.",
        "Do not default to Kami parchment, purple gradients, or generic SaaS blue unless the content justifies it.",
        "Keep accent color limited to decisions, active states, risk, or section anchors.",
    ],
    "spacing": [
        "Prefer clear grid rhythm over floating decorative cards.",
        "Increase whitespace around decisions and shrink whitespace around supporting metadata.",
        "Split dense content instead of shrinking type or adding scroll traps.",
    ],
    "components": [
        "Use cards for grouped evidence, tables for comparisons, callouts for decisions, and timelines for sequence.",
        "Avoid cards inside cards.",
        "Keep reviewer-only detail visible but visually quieter than user-facing guidance.",
    ],
}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    try:
        end_index = lines[1:].index("---") + 1
    except ValueError:
        return {}, text
    frontmatter_text = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :]).lstrip()
    if yaml is not None:
        payload = yaml.safe_load(frontmatter_text) or {}
        return payload if isinstance(payload, dict) else {}, body
    data = {}
    for line in frontmatter_text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data, body


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def normalized_text(skill_dir: Path) -> str:
    skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(skill_text)
    intent = load_json(skill_dir / "reports" / "intent-confidence.json")
    output_risk = load_json(skill_dir / "reports" / "output-risk-profile.json")
    context = intent.get("context", {}) if isinstance(intent, dict) else {}
    risk_labels = " ".join(item.get("label", "") for item in output_risk.get("risk_families", []))
    parts = [
        str(frontmatter.get("name") or skill_dir.name),
        str(frontmatter.get("description", "")),
        body,
        str(context.get("job", "")),
        str(context.get("primary_output", "")),
        " ".join(context.get("real_inputs", []) or []),
        " ".join(context.get("constraints", []) or []),
        " ".join(context.get("standards", []) or []),
        risk_labels,
    ]
    return " ".join(parts).lower()


def match_family(text: str, family: dict) -> tuple[int, list[str]]:
    hits = []
    for keyword in family["keywords"]:
        if keyword.lower() in text:
            hits.append(keyword)
    return len(hits), hits


def dedupe(items: list[str], limit: int) -> list[str]:
    seen = set()
    output = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        output.append(item)
        if len(output) == limit:
            break
    return output


def design_system_name(matched: list[dict]) -> str:
    keys = {item["key"] for item in matched}
    if "dashboard" in keys:
        return "metric editorial"
    if "review_viewer" in keys:
        return "review studio"
    if "slide_like" in keys:
        return "narrative visual brief"
    if "tutorial" in keys:
        return "guided learning document"
    if "visual_capture" in keys:
        return "evidence frame"
    return "content-led editorial"


def build_summary(skill_dir: Path) -> dict:
    text = normalized_text(skill_dir)
    frontmatter, _ = parse_frontmatter((skill_dir / "SKILL.md").read_text(encoding="utf-8"))
    matched = []
    for family in ARTIFACT_FAMILIES:
        score, hits = match_family(text, family)
        if score:
            matched.append({**family, "score": score, "matched_keywords": hits})
    if not matched:
        fallback = next(item for item in ARTIFACT_FAMILIES if item["key"] == "report")
        matched = [{**fallback, "score": 0, "matched_keywords": ["general-artifact"]}]
    matched = sorted(matched, key=lambda item: item["score"], reverse=True)[:5]
    primary = matched[0]
    layout_patterns = []
    gates = []
    for item in matched:
        layout_patterns.extend(item["layout"])
        gates.extend(item["quality_gates"])
    anti_patterns = [
        "Do not copy Kami's fixed parchment background as a default.",
        "Do not use generic purple gradients, glass cards, or stock SaaS hero sections unless the content calls for them.",
        "Do not let Markdown tables become the default shape for every comparison or explanation.",
        "Do not turn reviewer evidence into user-facing clutter.",
        "Do not invent screenshots, citations, charts, or UI states.",
    ]
    return {
        "skill_name": str(frontmatter.get("name") or skill_dir.name),
        "design_system": design_system_name(matched),
        "primary_artifact": {
            "key": primary["key"],
            "label": primary["label"],
            "direction": primary["direction"],
            "matched_keywords": primary["matched_keywords"],
        },
        "artifact_families": [
            {
                "key": item["key"],
                "label": item["label"],
                "score": item["score"],
                "matched_keywords": item["matched_keywords"],
                "direction": item["direction"],
            }
            for item in matched
        ],
        "layout_patterns": dedupe(layout_patterns, 8),
        "design_tokens": DESIGN_TOKENS,
        "quality_gates": dedupe(gates, 8),
        "anti_patterns": anti_patterns,
        "reviewer_note": "Use this profile to judge whether the generated artifacts feel designed for their job, not merely rendered.",
    }


def render_markdown(summary: dict) -> str:
    lines = [
        "# Artifact Design Profile",
        "",
        f"Skill: `{summary['skill_name']}`",
        f"Design system: `{summary['design_system']}`",
        "",
        "## Primary Artifact Direction",
        "",
        f"**{summary['primary_artifact']['label']}**",
        "",
        summary["primary_artifact"]["direction"],
        "",
        "## Matched Artifact Families",
        "",
    ]
    for family in summary["artifact_families"]:
        lines.extend(
            [
                f"### {family['label']}",
                f"- Matched keywords: {', '.join(family['matched_keywords'])}",
                f"- Score: `{family['score']}`",
                f"- Direction: {family['direction']}",
                "",
            ]
        )
    lines.extend(["## Layout Patterns To Prefer", ""])
    for item in summary["layout_patterns"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Design Tokens", ""])
    for key, values in summary["design_tokens"].items():
        lines.append(f"### {key.title()}")
        for value in values:
            lines.append(f"- {value}")
        lines.append("")
    lines.extend(["## Quality Gates", ""])
    for item in summary["quality_gates"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Anti-Patterns", ""])
    for item in summary["anti_patterns"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Reviewer Note", "", summary["reviewer_note"], ""])
    return "\n".join(lines).strip() + "\n"


def render_artifact_design_profile(
    skill_dir: Path,
    output_md: Path | None = None,
    output_json: Path | None = None,
) -> dict:
    skill_dir = skill_dir.resolve()
    reports_dir = skill_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    output_md = output_md or reports_dir / "artifact-design-profile.md"
    output_json = output_json or reports_dir / "artifact-design-profile.json"
    summary = build_summary(skill_dir)
    output_md.write_text(render_markdown(summary), encoding="utf-8")
    output_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "ok": True,
        "skill_dir": str(skill_dir),
        "artifacts": {
            "markdown": str(output_md),
            "json": str(output_json),
        },
        "summary": summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Render artifact design direction and visual quality gates for a skill package.")
    parser.add_argument("skill_dir")
    parser.add_argument("--output-md")
    parser.add_argument("--output-json")
    args = parser.parse_args()
    result = render_artifact_design_profile(
        Path(args.skill_dir),
        Path(args.output_md).resolve() if args.output_md else None,
        Path(args.output_json).resolve() if args.output_json else None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
