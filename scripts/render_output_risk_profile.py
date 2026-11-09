#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


RISK_FAMILIES = [
    {
        "key": "tutorial_quality",
        "label": "Tutorial quality",
        "keywords": ["tutorial", "guide", "how to", "lesson", "course", "walkthrough", "教程", "指南", "课程"],
        "risks": [
            "Generic section headings make the tutorial feel templated instead of fitted to the learner's task.",
            "Steps may explain what to do without naming the exact check that proves the step worked.",
            "Examples can become too abstract when the input material is concrete.",
        ],
        "constraints": [
            "Write headings from the user's domain nouns and desired outcome, not from generic labels like Overview or Key Points.",
            "Pair each major step with a visible success check or expected intermediate output.",
            "Use one concrete worked example before adding broad principles.",
        ],
        "self_repair": [
            "Replace generic H2/H3 headings with task-specific headings before final output.",
            "Scan every numbered step for a missing verification cue.",
        ],
    },
    {
        "key": "markdown_readability",
        "label": "Markdown readability",
        "keywords": ["markdown", "md", "table", "report", "brief", "doc", "文档", "表格", "报告", "排版"],
        "risks": [
            "Tables can render as dense grids with weak hierarchy or poor mobile readability.",
            "Long bullets can make the output look complete while hiding the actual decision logic.",
            "Mixed heading levels can reduce scanability.",
        ],
        "constraints": [
            "Use tables only when comparison is the main job; otherwise prefer compact cards or grouped bullets.",
            "Keep table cells short and move explanations below the table.",
            "Use heading levels consistently and keep each section anchored to a user-facing outcome.",
        ],
        "self_repair": [
            "Preview whether each table still reads well when columns are narrow.",
            "Convert any table with paragraph-length cells into bullets or cards.",
        ],
    },
    {
        "key": "citation_clutter",
        "label": "Citation and footnote clutter",
        "keywords": ["citation", "source", "research", "footnote", "reference", "引用", "角标", "来源", "注释"],
        "risks": [
            "Footnote markers or dense citation notes can interrupt the reading flow.",
            "Evidence can be over-attached to obvious statements and under-attached to risky claims.",
            "Source notes may become more prominent than the tutorial itself.",
        ],
        "constraints": [
            "Attach citations only to claims that need evidence, not to every sentence.",
            "Group source notes at the end of a section when inline markers would hurt readability.",
            "Keep the main sentence readable without requiring the reader to chase a footnote.",
        ],
        "self_repair": [
            "Remove decorative citations that do not support a material claim.",
            "Move repeated source explanations into one compact source note.",
        ],
    },
    {
        "key": "visual_capture",
        "label": "Screenshot and visual capture",
        "keywords": ["screenshot", "image", "visual", "screen", "capture", "figma", "截图", "图片", "视觉", "截屏"],
        "risks": [
            "Screenshots can be captured from the wrong state, wrong viewport, or wrong crop.",
            "Missing screenshots can cause the skill to invent visual references instead of declaring the gap.",
            "Image descriptions can omit the action-relevant region.",
        ],
        "constraints": [
            "Never invent a screenshot; state when visual evidence is missing.",
            "Record the source, viewport, and crop intent for any screenshot-dependent output.",
            "Describe what the reader should inspect in the image, not just that an image exists.",
        ],
        "self_repair": [
            "Check that every screenshot reference points to a real provided or generated asset.",
            "Reword any visual instruction that depends on an unseen screen state.",
        ],
    },
    {
        "key": "code_or_command_safety",
        "label": "Code and command safety",
        "keywords": ["code", "script", "cli", "command", "terminal", "api", "代码", "脚本", "命令", "接口"],
        "risks": [
            "Commands can omit environment assumptions, working directory, or rollback notes.",
            "Code snippets can look runnable while missing required inputs.",
            "Error handling can be either absent or over-engineered.",
        ],
        "constraints": [
            "Name the working directory, required inputs, and expected output for each command.",
            "Mark destructive or external side-effect operations explicitly.",
            "Prefer the smallest runnable snippet over broad framework code.",
        ],
        "self_repair": [
            "Scan each command for cwd, input, output, and side-effect assumptions.",
            "Remove speculative error handling that is not tied to a real failure mode.",
        ],
    },
    {
        "key": "tone_and_specificity",
        "label": "Tone and specificity",
        "keywords": ["marketing", "copy", "title", "article", "content", "summary", "标题", "文案", "文章", "总结"],
        "risks": [
            "Headings and summaries can drift into generic, interchangeable language.",
            "The output can sound polished but lose the user's actual taste, audience, or scenario.",
            "Strong claims can appear without examples or constraints.",
        ],
        "constraints": [
            "Anchor titles and summaries in the user's audience, object, and concrete outcome.",
            "Avoid placeholder phrases such as comprehensive guide, ultimate solution, or key insights unless the source demands them.",
            "Preserve one distinctive phrase, constraint, or standard from the user's input.",
        ],
        "self_repair": [
            "Replace generic title candidates with scenario-specific alternatives.",
            "Delete any polished sentence that could fit almost any project unchanged.",
        ],
    },
]


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
    context = intent.get("context", {}) if isinstance(intent, dict) else {}
    parts = [
        str(frontmatter.get("name") or skill_dir.name),
        str(frontmatter.get("description", "")),
        body,
        str(context.get("job", "")),
        str(context.get("primary_output", "")),
        " ".join(context.get("real_inputs", []) or []),
        " ".join(context.get("constraints", []) or []),
        " ".join(context.get("standards", []) or []),
    ]
    return " ".join(parts).lower()


def match_family(text: str, family: dict) -> tuple[int, list[str]]:
    hits = []
    for keyword in family["keywords"]:
        if keyword.lower() in text:
            hits.append(keyword)
    return len(hits), hits


def build_summary(skill_dir: Path) -> dict:
    text = normalized_text(skill_dir)
    frontmatter, _ = parse_frontmatter((skill_dir / "SKILL.md").read_text(encoding="utf-8"))
    matched = []
    for family in RISK_FAMILIES:
        score, hits = match_family(text, family)
        if score:
            matched.append({**family, "score": score, "matched_keywords": hits})
    if not matched:
        matched = [
            {
                **next(item for item in RISK_FAMILIES if item["key"] == "tone_and_specificity"),
                "score": 0,
                "matched_keywords": ["general-output-risk"],
            },
            {
                **next(item for item in RISK_FAMILIES if item["key"] == "markdown_readability"),
                "score": 0,
                "matched_keywords": ["general-output-risk"],
            },
        ]
    matched = sorted(matched, key=lambda item: item["score"], reverse=True)[:5]
    top_risks = []
    constraints = []
    self_repair = []
    for item in matched:
        top_risks.extend(item["risks"][:2])
        constraints.extend(item["constraints"][:2])
        self_repair.extend(item["self_repair"][:2])
    return {
        "skill_name": str(frontmatter.get("name") or skill_dir.name),
        "risk_families": [
            {
                "key": item["key"],
                "label": item["label"],
                "matched_keywords": item["matched_keywords"],
                "score": item["score"],
                "risks": item["risks"],
                "constraints": item["constraints"],
                "self_repair": item["self_repair"],
            }
            for item in matched
        ],
        "top_risks": dedupe(top_risks, 6),
        "output_constraints": dedupe(constraints, 6),
        "self_repair_checks": dedupe(self_repair, 6),
        "reviewer_note": "Use this report before deepening the package and again before approving example outputs.",
    }


def dedupe(items: list[str], limit: int) -> list[str]:
    seen = set()
    output = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
        if len(output) == limit:
            break
    return output


def render_markdown(summary: dict) -> str:
    lines = [
        "# Output Risk Profile",
        "",
        f"Skill: `{summary['skill_name']}`",
        "",
        "## Why This Exists",
        "",
        "Generated skills often fail in small output details: generic headings, cluttered citations, fragile screenshots, weak Markdown rendering, or missing execution assumptions. This profile predicts the most likely output mistakes before the skill is used heavily.",
        "",
        "## Matched Risk Families",
        "",
    ]
    for family in summary["risk_families"]:
        lines.extend(
            [
                f"### {family['label']}",
                f"- Matched keywords: {', '.join(family['matched_keywords'])}",
                f"- Score: `{family['score']}`",
                "",
            ]
        )
    lines.extend(["## Likely Output Mistakes", ""])
    for item in summary["top_risks"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Output Constraints To Apply", ""])
    for item in summary["output_constraints"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Self-Repair Checks", ""])
    for item in summary["self_repair_checks"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Reviewer Note", "", summary["reviewer_note"], ""])
    return "\n".join(lines).strip() + "\n"


def render_output_risk_profile(
    skill_dir: Path,
    output_md: Path | None = None,
    output_json: Path | None = None,
) -> dict:
    skill_dir = skill_dir.resolve()
    reports_dir = skill_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    output_md = output_md or reports_dir / "output-risk-profile.md"
    output_json = output_json or reports_dir / "output-risk-profile.json"
    summary = build_summary(skill_dir)
    output_md.write_text(render_markdown(summary), encoding="utf-8")
    output_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
    parser = argparse.ArgumentParser(description="Render predicted output failure modes and quality constraints.")
    parser.add_argument("skill_dir")
    parser.add_argument("--output-md")
    parser.add_argument("--output-json")
    args = parser.parse_args()
    result = render_output_risk_profile(
        Path(args.skill_dir),
        output_md=Path(args.output_md).resolve() if args.output_md else None,
        output_json=Path(args.output_json).resolve() if args.output_json else None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
