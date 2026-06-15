#!/usr/bin/env python3
import argparse
import json
import re
from datetime import date
from pathlib import Path

from compile_skill import render_compile_report
from export_skill_ir import build_skill_ir, validate_ir
from github_benchmark_scan import run_github_benchmark_scan
from render_intent_confidence import render_intent_confidence
from render_intent_dialogue import render_intent_dialogue
from render_iteration_directions import render_iteration_directions
from render_adoption_drift_report import render_report as render_adoption_drift_report
from render_review_annotations import render_report as render_review_annotations
from render_review_waivers import render_report as render_review_waivers
from render_artifact_design_profile import render_artifact_design_profile
from render_output_risk_profile import render_output_risk_profile
from render_prompt_quality_profile import render_prompt_quality_profile
from render_reference_scan import parse_reference, render_reference_scan
from render_reference_synthesis import render_reference_synthesis
from render_review_studio import render_review_studio
from render_review_viewer import render_review_viewer
from render_skill_interpretation import render_skill_interpretation
from render_skill_overview import render_skill_overview
from render_system_model import render_system_model


SKILL_TEMPLATE = """---
name: {name}
description: {description}
---

# {title}

## Workflow

1. Understand the request.
2. Execute the main task.
3. Validate the result.

## Output Quality Guardrails

- Before final output, apply the likely failure modes in `reports/output-risk-profile.md` when that report is present.
- Before rendering reports, tutorials, review pages, dashboards, or visual artifacts, apply the artifact direction and visual quality gates in `reports/artifact-design-profile.md` when that report is present.
- When prompt behavior, role design, dialogue quality, or output contracts matter, apply `reports/prompt-quality-profile.md` when that report is present.
- Before adding more structure, apply the boundary, feedback-loop, drift, and leverage-point checks in `reports/system-model.md` when that report is present.
- Repair generic headings, cluttered notes, fragile visual assumptions, weak tables, and missing verification cues before handing work back.
- Map role, task, and format into skill behavior rather than copying a large prompt template into `SKILL.md`.
- Let the artifact's content choose the visual system; do not copy a fixed palette or report style from another skill without a clear reason.
- If output-specific evidence is missing, state the gap instead of inventing screenshots, citations, data, or examples.

## Honest Boundaries

- Use this skill for the recurring job described in the trigger, not for one-off adjacent requests.
- Treat missing inputs, unclear outputs, or conflicting constraints as reasons to ask one focused clarification.
- Do not add new references, scripts, evals, or governance unless they improve reliability more than they add weight.
"""


README_TEMPLATE = """# {title}

## What It Does

`{name}` is a reusable skill package for this job:

> {description}

## How To Use

1. Load the skill through `SKILL.md`.
2. Start with `reports/intent-dialogue.md` to tighten the real job, outputs, exclusions, and the standards you care about.
3. Open `reports/reference-scan.md` to capture external benchmarks and any user-supplied references worth learning from.
4. Review `reports/intent-confidence.md` to see whether the real job, inputs, outputs, and exclusions are clear enough yet.
5. Open `reports/reference-synthesis.md` to see the GitHub benchmarks plus curated official, research, and principle tracks in one place.
6. Follow the workflow steps in `SKILL.md`.
7. Open `reports/skill-interpretation.html` first for the first-class bilingual interpretation report: role, principle, scenarios, trigger, inputs, outputs, highlights, risks, assets, and upgrade directions. It defaults to Simplified Chinese and includes an English switch in the top right.
8. Check `reports/skill-overview.html` for the generated bilingual HTML skill audit report: overview, metrics, capability profile, principle, contract, quality, risk, assets, and iteration roadmap.
9. Open `reports/review-studio.html` for the one-page Review Studio 2.0 gate view.
10. Record source-line reviewer comments in `reports/review_annotations.md` when review needs follow-up.
11. Open `reports/review-viewer.html` for a compact visual review of the package.
12. Check `reports/output-risk-profile.md` to see likely output mistakes and self-repair checks.
13. Check `reports/artifact-design-profile.md` to see the intended artifact direction, layout patterns, visual quality gates, and anti-patterns.
14. Check `reports/prompt-quality-profile.md` to see the need model, RTF-to-skill mapping, complexity, and prompt-facing quality matrix.
15. Review `reports/skill-ir.json` for the platform-neutral Skill IR contract before platform-specific packaging.
16. Review `reports/compiled_targets.md` to see how Skill IR compiles into OpenAI, Claude, generic, and Agent Skills compatible target contracts.
17. Review `reports/iteration-directions.md` for the three most valuable next moves.
18. Review `reports/system-model.md` to understand the boundary, feedback loops, drift watch, failure map, and highest-leverage next changes.
19. Review `reports/adoption_drift_report.md` to see local-first metadata-only adoption and drift signals.
20. Review `reports/review_waivers.md` to see human reviewer risk approvals and expiry dates.

## Honest Boundaries

- This package starts from the current intent frame and should not pretend to cover unclear adjacent jobs.
- The first version should ask for clarification when the real input, output, or exclusion boundary is still fuzzy.
- New structure should be added only when it earns its keep through evidence, validation, or reviewer need.

## Package Map

- `SKILL.md`: trigger and workflow entrypoint
- `agents/interface.yaml`: portable interface metadata
- `manifest.json`: lifecycle and packaging metadata
- `reports/intent-dialogue.md`: front-loaded discovery questions for better boundary design and clearer human alignment
- `reports/intent-confidence.md`: current clarity score, open gaps, and the next follow-up questions worth asking
- `reports/github-benchmark-scan.md`: top public benchmark repositories, extracted patterns, and borrow or avoid notes
- `reports/reference-scan.md`: benchmark notes from public references, user references, and local constraints
- `reports/reference-synthesis.md`: a combined view of GitHub benchmarks plus curated world-class pattern tracks
- `reports/output-risk-profile.md`: predicted output failure modes and self-repair constraints for this skill
- `reports/artifact-design-profile.md`: artifact-specific design direction, layout patterns, visual quality gates, and anti-patterns
- `reports/prompt-quality-profile.md`: prompt-facing need model, RTF mapping, complexity, and quality matrix
- `reports/system-model.md`: systems-thinking model for boundary, feedback loops, drift, failure patterns, and leverage points
- `reports/skill-ir.json`: platform-neutral 2.0 Skill IR contract for trigger, workflow, resources, evals, risk, and governance
- `reports/compiled_targets.md`: target compiler report showing generated contracts, adapter modes, preserved semantics, warnings, and unsupported features
- `reports/skill-interpretation.html`: first-class bilingual interpretation report for role, principle, scenarios, trigger, inputs, outputs, quality evidence, risks, assets, highlights, and upgrade directions
- `reports/skill-overview.html`: white-background bilingual HTML skill audit report with sticky four-character Chinese navigation, a top-right language switch, metrics, SVG charts, contract boundary, quality review, risk governance, assets, and iteration roadmap
- `reports/review-studio.html`: Review Studio 2.0 gate page for intent, trigger, output eval, context, runtime conformance, trust, atlas, and release readiness
- `reports/review-viewer.html`: compact review page for architecture, usage, feedback, and next steps
- `reports/iteration-directions.md`: the top three next iteration directions
- `reports/adoption_drift_report.md`: local-first metadata-only telemetry summary for adoption, missed triggers, bad outputs, script errors, and review drift
- `reports/review_waivers.md`: human reviewer risk approval ledger for warning acceptance and expiry
- `reports/review_annotations.md`: source-line reviewer comments linked to Review Studio gates
"""


INTERFACE_TEMPLATE = """interface:
  display_name: "{title}"
  short_description: "{short_description}"
  default_prompt: "Use ${name} when you need to {default_prompt}."
compatibility:
  canonical_format: "agent-skills"
  adapter_targets:
    - "openai"
    - "claude"
    - "generic"
    - "vscode"
  activation:
    mode: "manual"
    paths: []
  execution:
    context: "inline"
    shell: "bash"
  trust:
    source_tier: "local"
    remote_inline_execution: "forbid"
    remote_metadata_policy: "allow-metadata-only"
  degradation:
    openai: "metadata-adapter"
    claude: "neutral-source-plus-adapter"
    generic: "neutral-source"
    vscode: "agent-skills-source-with-vscode-notes"
"""


MODE_CONFIG = {
    "scaffold": {
        "maturity_tier": "scaffold",
        "lifecycle_stage": "scaffold",
        "context_budget_tier": "scaffold",
        "review_cadence": "per-release",
    },
    "production": {
        "maturity_tier": "production",
        "lifecycle_stage": "production",
        "context_budget_tier": "production",
        "review_cadence": "monthly",
    },
    "library": {
        "maturity_tier": "library",
        "lifecycle_stage": "library",
        "context_budget_tier": "library",
        "review_cadence": "quarterly",
    },
    "governed": {
        "maturity_tier": "governed",
        "lifecycle_stage": "governed",
        "context_budget_tier": "governed",
        "review_cadence": "monthly",
    },
}


SKILL_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def validate_skill_name(name: str) -> None:
    if not SKILL_NAME_RE.fullmatch(name):
        raise ValueError(
            "Invalid skill name. Use a slug matching ^[a-z0-9][a-z0-9_-]*$; path separators and absolute paths are not allowed."
        )


def resolve_skill_root(output_dir: str, name: str) -> Path:
    validate_skill_name(name)
    output_root = Path(output_dir).resolve()
    root = (output_root / name).resolve()
    try:
        root.relative_to(output_root)
    except ValueError as exc:
        raise ValueError(f"Skill root escapes output directory: {root}") from exc
    return root


def build_manifest(name: str, mode: str, archetype: str) -> dict:
    mode_payload = MODE_CONFIG.get(mode, MODE_CONFIG["scaffold"])
    return {
        "name": name,
        "version": "0.1.0",
        "owner": "Yao Team",
        "updated_at": str(date.today()),
        "status": "active",
        "maturity_tier": mode_payload["maturity_tier"],
        "lifecycle_stage": mode_payload["lifecycle_stage"],
        "context_budget_tier": mode_payload["context_budget_tier"],
        "review_cadence": mode_payload["review_cadence"],
        "skill_archetype": archetype,
        "target_platforms": [
            "openai",
            "claude",
            "generic",
            "agent-skills-compatible",
            "vscode",
        ],
        "factory_components": [
            "references",
            "scripts",
            "reports",
        ],
    }


def build_report_view(artifacts: dict) -> dict:
    html_report = artifacts.get("skill_overview_html", "")
    json_report = artifacts.get("skill_overview_json", "")
    interpretation_report = artifacts.get("skill_interpretation_html", "")
    system_model = artifacts.get("system_model_md", "")
    review_studio = artifacts.get("review_studio_html", "")
    return {
        "title": "Skill 总结报告",
        "html_report": html_report,
        "json_report": json_report,
        "interpretation_report": interpretation_report,
        "system_model": system_model,
        "review_studio": review_studio,
        "message": (
            f"Skill 已创建完成。建议先打开解读报告：{interpretation_report}；再查看总结报告：{html_report}。"
            "解读报告会用中文简体默认展示这个 Skill 的作用、原理、使用场景、触发方式、输入输出、亮点和后续升级方向；"
            "总结报告会展示概述、指标、原理、触发边界、输入输出、目标编译、质量评估、风险治理、包体资产和升级路线；"
            f"然后打开 Review Studio 2.0：{review_studio}，检查意图、触发、输出评测、运行一致性、信任和发布闸门。"
            "后续 reviewer 的文件级或行级意见可以记录到 reports/review_annotations.md。"
            "如需审查平台适配细节，请打开 reports/compiled_targets.md。"
            "报告默认使用中文简体，右上角可以切换英文版。"
        ),
        "next_action": "Open reports/skill-interpretation.html before editing more files.",
    }


def render_skill_ir(root: Path) -> dict:
    payload = build_skill_ir(root)
    failures = validate_ir(payload)
    output_json = root / "reports" / "skill-ir.json"
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": not failures,
        "artifacts": {"json": str(output_json)},
        "summary": {
            "name": payload.get("name"),
            "maturity": payload.get("governance", {}).get("maturity"),
            "target_count": len(payload.get("targets", [])),
            "trigger_samples": len(payload.get("trigger_surface", {}).get("should_trigger", [])),
        },
        "failures": failures,
    }


def absolute_skill_artifact(root: Path, value: str) -> str:
    path = Path(value)
    return str(path if path.is_absolute() else root / path)


def dedupe_references(references: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for reference in references:
        key = (
            reference.get("source"),
            reference.get("name"),
            reference.get("category"),
            reference.get("borrow"),
            reference.get("avoid"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(reference)
    return deduped


def initialize_skill(
    name: str,
    description: str,
    title: str | None = None,
    output_dir: str = ".",
    mode: str = "scaffold",
    archetype: str = "scaffold",
    external_references: list[dict] | None = None,
    user_references: list[dict] | None = None,
    local_constraints: list[dict] | None = None,
    github_query: str | None = None,
    github_top_n: int = 3,
    github_fixture_dir: str | None = None,
    intent_context: dict | None = None,
) -> dict:
    title = title or name.replace("-", " ").title()
    root = resolve_skill_root(output_dir, name)
    (root / "agents").mkdir(parents=True, exist_ok=True)
    (root / "references").mkdir(exist_ok=True)
    (root / "scripts").mkdir(exist_ok=True)
    (root / "reports").mkdir(exist_ok=True)
    (root / "SKILL.md").write_text(
        SKILL_TEMPLATE.format(name=name, description=json.dumps(description, ensure_ascii=False), title=title),
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        README_TEMPLATE.format(name=name, description=description, title=title),
        encoding="utf-8",
    )
    (root / "agents" / "interface.yaml").write_text(
        INTERFACE_TEMPLATE.format(
            name=name,
            title=title,
            short_description=description[:80],
            default_prompt=description.rstrip("."),
        ),
        encoding="utf-8",
    )
    (root / "manifest.json").write_text(
        json.dumps(build_manifest(name, mode, archetype), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    intent_confidence = render_intent_confidence(root, context=intent_context)
    intent_dialogue = render_intent_dialogue(root)
    benchmark_scan = None
    combined_external_references = [*(external_references or [])]
    if github_query:
        benchmark_scan = run_github_benchmark_scan(
            root,
            query=github_query,
            top_n=github_top_n,
            fixture_dir=Path(github_fixture_dir).resolve() if github_fixture_dir else None,
        )
        combined_external_references = [*benchmark_scan.get("external_references", []), *combined_external_references]
    reference_scan = render_reference_scan(
        root,
        dedupe_references([*combined_external_references, *(user_references or []), *(local_constraints or [])]),
    )
    reference_synthesis = render_reference_synthesis(root)
    output_risk_profile = render_output_risk_profile(root)
    artifact_design_profile = render_artifact_design_profile(root)
    prompt_quality_profile = render_prompt_quality_profile(root)
    system_model = render_system_model(root)
    skill_ir = render_skill_ir(root)
    compiled_targets = render_compile_report(root)
    iteration_directions = render_iteration_directions(root)
    adoption_drift = render_adoption_drift_report(root)
    review_waivers = render_review_waivers(root)
    review_annotations = render_review_annotations(root)
    overview = render_skill_overview(root)
    interpretation = render_skill_interpretation(root)
    review_viewer = render_review_viewer(root)
    review_studio = render_review_studio(root)
    artifacts = {
        "readme": str(root / "README.md"),
        "manifest": str(root / "manifest.json"),
        "intent_confidence_md": intent_confidence["artifacts"]["markdown"],
        "intent_confidence_json": intent_confidence["artifacts"]["json"],
        "intent_context_json": intent_confidence["artifacts"]["context_json"],
        "skill_overview_html": overview["artifacts"]["html"],
        "skill_overview_json": overview["artifacts"]["json"],
        "skill_interpretation_html": interpretation["artifacts"]["html"],
        "skill_interpretation_json": interpretation["artifacts"]["json"],
        "intent_dialogue_md": intent_dialogue["artifacts"]["markdown"],
        "intent_dialogue_json": intent_dialogue["artifacts"]["json"],
        "reference_scan_md": reference_scan["artifacts"]["markdown"],
        "reference_scan_json": reference_scan["artifacts"]["json"],
        "reference_synthesis_md": reference_synthesis["artifacts"]["markdown"],
        "reference_synthesis_json": reference_synthesis["artifacts"]["json"],
        "output_risk_profile_md": output_risk_profile["artifacts"]["markdown"],
        "output_risk_profile_json": output_risk_profile["artifacts"]["json"],
        "artifact_design_profile_md": artifact_design_profile["artifacts"]["markdown"],
        "artifact_design_profile_json": artifact_design_profile["artifacts"]["json"],
        "prompt_quality_profile_md": prompt_quality_profile["artifacts"]["markdown"],
        "prompt_quality_profile_json": prompt_quality_profile["artifacts"]["json"],
        "system_model_md": system_model["artifacts"]["markdown"],
        "system_model_json": system_model["artifacts"]["json"],
        "skill_ir_json": skill_ir["artifacts"]["json"],
        "compiled_targets_md": compiled_targets["artifacts"]["markdown"],
        "compiled_targets_json": compiled_targets["artifacts"]["json"],
        "iteration_directions_md": iteration_directions["artifacts"]["markdown"],
        "iteration_directions_json": iteration_directions["artifacts"]["json"],
        "adoption_drift_md": adoption_drift["artifacts"]["markdown"],
        "adoption_drift_json": adoption_drift["artifacts"]["json"],
        "review_waivers_md": review_waivers["artifacts"]["markdown"],
        "review_waivers_json": review_waivers["artifacts"]["json"],
        "review_annotations_md": review_annotations["artifacts"]["markdown"],
        "review_annotations_json": review_annotations["artifacts"]["json"],
        "review_viewer_html": review_viewer["artifacts"]["html"],
        "review_viewer_json": review_viewer["artifacts"]["json"],
        "review_studio_html": absolute_skill_artifact(root, review_studio["artifacts"]["html"]),
        "review_studio_json": absolute_skill_artifact(root, review_studio["artifacts"]["json"]),
    }
    if benchmark_scan is not None:
        artifacts["github_benchmark_scan_md"] = benchmark_scan["artifacts"]["markdown"]
        artifacts["github_benchmark_scan_json"] = benchmark_scan["artifacts"]["json"]
    report_view = build_report_view(artifacts)
    return {
        "ok": True,
        "root": str(root),
        "mode": mode,
        "archetype": archetype,
        "github_benchmark_scan": benchmark_scan,
        "intent_confidence": intent_confidence["summary"],
        "reference_synthesis": reference_synthesis["summary"],
        "system_model": system_model["summary"],
        "skill_ir": skill_ir["summary"],
        "compiled_targets": compiled_targets["summary"],
        "artifacts": artifacts,
        "report_view": report_view,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize a minimal skill package.")
    parser.add_argument("name", help="skill folder and frontmatter name")
    parser.add_argument("--description", default="Describe what the skill does and when to use it.")
    parser.add_argument("--title", default=None)
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--mode", choices=sorted(MODE_CONFIG.keys()), default="scaffold")
    parser.add_argument("--archetype", choices=sorted(MODE_CONFIG.keys()), default="scaffold")
    parser.add_argument("--external-reference", action="append", default=[])
    parser.add_argument("--user-reference", action="append", default=[])
    parser.add_argument("--local-constraint", action="append", default=[])
    parser.add_argument("--github-query")
    parser.add_argument("--github-top-n", type=int, default=3)
    parser.add_argument("--github-fixture-dir")
    parser.add_argument("--intent-job")
    parser.add_argument("--intent-real-input", action="append", default=[])
    parser.add_argument("--intent-primary-output")
    parser.add_argument("--intent-exclusion", action="append", default=[])
    parser.add_argument("--intent-constraint", action="append", default=[])
    parser.add_argument("--intent-standard", action="append", default=[])
    parser.add_argument("--intent-correction", default="")
    args = parser.parse_args()
    try:
        result = initialize_skill(
            args.name,
            args.description,
            args.title,
            args.output_dir,
            args.mode,
            args.archetype,
            external_references=[parse_reference(item, "external") for item in args.external_reference],
            user_references=[parse_reference(item, "user") for item in args.user_reference],
            local_constraints=[parse_reference(item, "local") for item in args.local_constraint],
            github_query=args.github_query,
            github_top_n=args.github_top_n,
            github_fixture_dir=args.github_fixture_dir,
            intent_context={
                "job": args.intent_job or args.description,
                "real_inputs": args.intent_real_input,
                "primary_output": args.intent_primary_output or "",
                "description": args.description,
                "exclusions": args.intent_exclusion,
                "constraints": args.intent_constraint,
                "standards": args.intent_standard,
                "correction": args.intent_correction,
                "user_references": [parse_reference(item, "user")["name"] for item in args.user_reference],
            },
        )
    except ValueError as exc:
        print(json.dumps({"ok": False, "failures": [str(exc)]}, ensure_ascii=False, indent=2))
        raise SystemExit(2) from exc
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
