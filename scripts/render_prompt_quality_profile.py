#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


TASK_FAMILIES = [
    {
        "key": "creative_generation",
        "label": "Creative generation",
        "keywords": ["creative", "idea", "copy", "campaign", "title", "content", "concept", "创意", "文案", "标题", "内容"],
        "role_guidance": "Use a taste-aware creator role with clear audience, tone, and originality boundaries.",
        "task_guidance": "Generate variants, explain selection logic, and preserve the user's distinctive constraints.",
        "format_guidance": "Return options with rationale, selection criteria, and refinement paths.",
    },
    {
        "key": "analytical_reasoning",
        "label": "Analytical reasoning",
        "keywords": ["analysis", "analyze", "diagnose", "compare", "synthesis", "decision", "评估", "分析", "诊断", "对比", "决策"],
        "role_guidance": "Use an analyst role that separates evidence, inference, uncertainty, and recommendation.",
        "task_guidance": "State assumptions, compare alternatives, and make the decision path inspectable.",
        "format_guidance": "Return findings, evidence, tradeoffs, recommendation, and residual risks.",
    },
    {
        "key": "execution_operation",
        "label": "Execution operation",
        "keywords": ["workflow", "runbook", "execute", "operate", "checklist", "standardize", "流程", "操作", "执行", "清单", "标准化"],
        "role_guidance": "Use an operator role with explicit boundaries, inputs, outputs, and failure handling.",
        "task_guidance": "Convert the job into ordered steps with validation checks and stop conditions.",
        "format_guidance": "Return a runbook-like handoff with commands, checks, owners, and next actions when relevant.",
    },
    {
        "key": "teaching_guidance",
        "label": "Teaching guidance",
        "keywords": ["tutorial", "teach", "lesson", "guide", "course", "coach", "教程", "教学", "课程", "指导", "老师"],
        "role_guidance": "Use a teacher role that adapts to learner level and avoids overloading the first pass.",
        "task_guidance": "Explain through progressive steps, examples, and visible success checks.",
        "format_guidance": "Return learner-facing sections, worked examples, checkpoints, and common mistakes.",
    },
    {
        "key": "dialogue_interaction",
        "label": "Dialogue interaction",
        "keywords": ["dialogue", "interview", "conversation", "support", "chat", "discovery", "对话", "访谈", "客服", "沟通"],
        "role_guidance": "Use a conversational role that asks only high-leverage questions and remembers the user's goal.",
        "task_guidance": "Clarify intent, resolve uncertainty, and converge toward a recommendation instead of a long option list.",
        "format_guidance": "Return concise prompts, decision points, and reviewer-visible assumptions.",
    },
    {
        "key": "prompt_engineering",
        "label": "Prompt engineering",
        "keywords": ["prompt", "metaprompt", "meta prompt", "instruction", "role", "format", "rtf", "提示词", "元提示词", "指令"],
        "role_guidance": "Use a prompt engineer role only when role design materially improves execution.",
        "task_guidance": "Map Role, Task, and Format into skill behavior rather than copying a large prompt template.",
        "format_guidance": "Return a compact prompt contract plus tests, quality matrix, and usage notes.",
    },
]


QUALITY_DIMENSIONS = [
    {
        "key": "completeness",
        "label": "Completeness",
        "signals": ["input", "output", "constraint", "standard", "example", "输入", "输出", "约束", "标准"],
        "repair": "Name missing inputs, outputs, constraints, or success standards before deepening the package.",
    },
    {
        "key": "clarity",
        "label": "Clarity",
        "signals": ["clear", "specific", "unambiguous", "明确", "清晰", "具体"],
        "repair": "Replace broad verbs with observable actions and define what done means.",
    },
    {
        "key": "consistency",
        "label": "Consistency",
        "signals": ["consistent", "aligned", "boundary", "一致", "边界", "对齐"],
        "repair": "Check that role, task, format, exclusions, and examples do not contradict each other.",
    },
    {
        "key": "practicality",
        "label": "Practicality",
        "signals": ["action", "execute", "use", "workflow", "落地", "执行", "使用"],
        "repair": "Add runnable steps, examples, or verification cues instead of abstract advice.",
    },
    {
        "key": "specificity",
        "label": "Specificity",
        "signals": ["audience", "domain", "scenario", "tone", "用户", "场景", "领域", "风格"],
        "repair": "Anchor wording in the user's audience, domain nouns, and target outcome.",
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


def normalized_context(skill_dir: Path) -> tuple[str, dict]:
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
        str(context.get("correction", "")),
    ]
    return " ".join(parts).lower(), context


def keyword_hits(text: str, keywords: list[str]) -> list[str]:
    return [keyword for keyword in keywords if keyword.lower() in text]


def complexity_band(text: str, context: dict, matched_count: int) -> dict:
    list_signal_count = sum(
        len(context.get(key, []) or [])
        for key in ("real_inputs", "constraints", "standards", "exclusions", "user_references")
        if isinstance(context.get(key, []), list)
    )
    expert_terms = ["governance", "eval", "audit", "security", "compliance", "expert", "治理", "评测", "审计", "合规"]
    score = matched_count + list_signal_count
    score += 2 if any(term in text for term in expert_terms) else 0
    if score >= 8:
        return {"band": "expert", "score": score, "reason": "multiple task families plus governance, evaluation, or expert-level constraints"}
    if score >= 5:
        return {"band": "complex", "score": score, "reason": "multiple inputs, constraints, or task families require tradeoff handling"}
    if score >= 3:
        return {"band": "medium", "score": score, "reason": "some judgment and multi-step structure are needed"}
    return {"band": "simple", "score": score, "reason": "single dominant task shape with limited constraints"}


def need_model(context: dict, description: str) -> dict:
    return {
        "explicit_need": context.get("job") or description,
        "implicit_need": "The reusable skill needs a stable role, task, and output contract rather than a one-off prompt.",
        "scenario": ", ".join(context.get("real_inputs", []) or []) or "not yet explicit",
        "user_level": "infer from examples and standards; ask only if it changes output depth",
        "success_standard": ", ".join(context.get("standards", []) or []) or context.get("primary_output") or "usable output with clear validation cues",
    }


def quality_matrix(text: str, context: dict) -> list[dict]:
    matrix = []
    for dimension in QUALITY_DIMENSIONS:
        hits = keyword_hits(text, dimension["signals"])
        score = 80
        if hits:
            score += min(15, len(hits) * 5)
        if dimension["key"] == "completeness":
            has_output = bool(context.get("primary_output"))
            has_inputs = bool(context.get("real_inputs"))
            score += 5 if has_output and has_inputs else -15
        if dimension["key"] == "specificity" and not (context.get("standards") or context.get("constraints")):
            score -= 10
        score = max(0, min(100, score))
        matrix.append(
            {
                "key": dimension["key"],
                "label": dimension["label"],
                "score": score,
                "matched_signals": hits,
                "repair": dimension["repair"],
            }
        )
    return matrix


def build_summary(skill_dir: Path) -> dict:
    text, context = normalized_context(skill_dir)
    skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    frontmatter, _ = parse_frontmatter(skill_text)
    description = str(frontmatter.get("description", ""))
    matched = []
    for family in TASK_FAMILIES:
        hits = keyword_hits(text, family["keywords"])
        if hits:
            matched.append({**family, "score": len(hits), "matched_keywords": hits})
    if not matched:
        fallback = next(item for item in TASK_FAMILIES if item["key"] == "execution_operation")
        matched = [{**fallback, "score": 0, "matched_keywords": ["general-skill"]}]
    matched = sorted(matched, key=lambda item: item["score"], reverse=True)[:4]
    primary = matched[0]
    complexity = complexity_band(text, context, len(matched))
    matrix = quality_matrix(text, context)
    overall = round(sum(item["score"] for item in matrix) / len(matrix), 1)
    rtf_mapping = {
        "role": primary["role_guidance"],
        "task": primary["task_guidance"],
        "format": primary["format_guidance"],
    }
    return {
        "skill_name": str(frontmatter.get("name") or skill_dir.name),
        "relevance": "prompt-heavy" if any(item["key"] == "prompt_engineering" for item in matched) else "prompt-aware",
        "primary_task_family": {
            "key": primary["key"],
            "label": primary["label"],
            "matched_keywords": primary["matched_keywords"],
        },
        "task_families": [
            {
                "key": item["key"],
                "label": item["label"],
                "score": item["score"],
                "matched_keywords": item["matched_keywords"],
                "role_guidance": item["role_guidance"],
                "task_guidance": item["task_guidance"],
                "format_guidance": item["format_guidance"],
            }
            for item in matched
        ],
        "complexity": complexity,
        "need_model": need_model(context, description),
        "rtf_to_skill": rtf_mapping,
        "quality_matrix": matrix,
        "overall_quality_score": overall,
        "self_repair_checks": [
            "Check explicit need, implicit need, scenario, user level, and success standard before deepening.",
            "Map Role, Task, and Format into skill behavior, not decorative prompt labels.",
            "Ask one focused clarification only when missing information changes the package boundary.",
            "Add tests or examples for prompt-heavy behavior before treating it as reusable.",
            "Keep prompt methodology in references and reports instead of bloating SKILL.md.",
        ],
        "reviewer_note": "Use this profile when the package depends on prompt behavior, role design, output contracts, or conversation quality.",
    }


def render_markdown(summary: dict) -> str:
    lines = [
        "# Prompt Quality Profile",
        "",
        f"Skill: `{summary['skill_name']}`",
        f"Relevance: `{summary['relevance']}`",
        f"Overall quality score: `{summary['overall_quality_score']}/100`",
        "",
        "## Primary Task Family",
        "",
        f"**{summary['primary_task_family']['label']}**",
        f"- Matched keywords: {', '.join(summary['primary_task_family']['matched_keywords'])}",
        "",
        "## Complexity",
        "",
        f"- Band: `{summary['complexity']['band']}`",
        f"- Score: `{summary['complexity']['score']}`",
        f"- Reason: {summary['complexity']['reason']}",
        "",
        "## Need Model",
        "",
    ]
    for key, value in summary["need_model"].items():
        lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    lines.extend(["", "## RTF To Skill Mapping", ""])
    for key, value in summary["rtf_to_skill"].items():
        lines.append(f"- {key.title()}: {value}")
    lines.extend(["", "## Quality Matrix", ""])
    for item in summary["quality_matrix"]:
        signals = ", ".join(item["matched_signals"]) if item["matched_signals"] else "none"
        lines.extend(
            [
                f"### {item['label']} — {item['score']}/100",
                f"- Matched signals: {signals}",
                f"- Repair: {item['repair']}",
                "",
            ]
        )
    lines.extend(["## Matched Task Families", ""])
    for family in summary["task_families"]:
        lines.extend(
            [
                f"### {family['label']}",
                f"- Score: `{family['score']}`",
                f"- Keywords: {', '.join(family['matched_keywords'])}",
                f"- Role: {family['role_guidance']}",
                f"- Task: {family['task_guidance']}",
                f"- Format: {family['format_guidance']}",
                "",
            ]
        )
    lines.extend(["## Self-Repair Checks", ""])
    for item in summary["self_repair_checks"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Reviewer Note", "", summary["reviewer_note"], ""])
    return "\n".join(lines).strip() + "\n"


def render_prompt_quality_profile(
    skill_dir: Path,
    output_md: Path | None = None,
    output_json: Path | None = None,
) -> dict:
    skill_dir = skill_dir.resolve()
    reports_dir = skill_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    output_md = output_md or reports_dir / "prompt-quality-profile.md"
    output_json = output_json or reports_dir / "prompt-quality-profile.json"
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
    parser = argparse.ArgumentParser(description="Render prompt behavior quality, RTF mapping, and need-model checks for a skill package.")
    parser.add_argument("skill_dir")
    parser.add_argument("--output-md")
    parser.add_argument("--output-json")
    args = parser.parse_args()
    result = render_prompt_quality_profile(
        Path(args.skill_dir),
        Path(args.output_md).resolve() if args.output_md else None,
        Path(args.output_json).resolve() if args.output_json else None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
