#!/usr/bin/env python3
"""Creation command handlers for the Yao CLI."""

import argparse
import json
import sys

from github_benchmark_scan import build_query
from render_intent_confidence import assess_intent_confidence
from yao_cli_config import (
    ARCHETYPE_MODE,
    archetype_guidance,
    diagnose_skill_candidates,
    diagnosis_note,
    discovery_summary,
    infer_archetype,
    recommendation_from_synthesis,
    reference_visibility,
)
from yao_cli_runtime import run_script


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by yao.py to keep skill creation and quickstart command handlers out of the CLI orchestrator."


def prompt_with_default(label: str, default: str) -> str:
    sys.stderr.write(f"{label} [{default}]: ")
    sys.stderr.flush()
    value = sys.stdin.readline().strip()
    return value or default


def prompt_optional(label: str, default: str = "skip") -> str:
    sys.stderr.write(f"{label} [{default}]: ")
    sys.stderr.flush()
    value = sys.stdin.readline().strip()
    return value or default


def prompt_optional_entries(label: str) -> list[str]:
    sys.stderr.write(f"{label} [none]: ")
    sys.stderr.flush()
    value = sys.stdin.readline().strip()
    if not value or value.lower() in {"none", "no", "n"}:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def update_context_slot(context: dict, slot: str, answer: str, list_mode: bool) -> None:
    value = answer.strip()
    if not value or value.lower() in {"skip", "none", "no", "n"}:
        return
    if list_mode:
        context[slot] = [item.strip() for item in value.split(",") if item.strip()]
    else:
        context[slot] = value


def intent_confidence_note(summary: dict) -> str:
    lines = [
        f"\nIntent confidence: {summary['score']}/100 ({summary['band']}).",
        f"- Recommended action: {summary['recommended_action']}",
    ]
    if summary.get("gaps"):
        top_gap = summary["gaps"][0]
        lines.append(f"- Biggest gap: {top_gap['label']} — {top_gap['reason']}")
    return "\n".join(lines) + "\n"


def maybe_emit_update_notice(args: argparse.Namespace) -> None:
    if getattr(args, "no_update_check", False):
        return
    result = run_script("check_update.py", [])
    payload = result["payload"] if result["payload"] is not None else {}
    if not result["ok"] and not payload:
        return
    if payload.get("update_available"):
        sys.stderr.write(
            "\nUpdate available for yao-meta-skill: "
            f"{payload.get('local_version')} -> {payload.get('remote_version')}.\n"
            f"Run: {payload.get('install_hint')}\n"
        )


def command_init(args: argparse.Namespace) -> int:
    cmd = [
        args.name,
        "--description",
        args.description,
        "--output-dir",
        args.output_dir,
        "--mode",
        args.mode,
        "--archetype",
        args.archetype,
        *(["--title", args.title] if args.title else []),
    ]
    for reference in args.external_reference:
        cmd.extend(["--external-reference", reference])
    for reference in args.user_reference:
        cmd.extend(["--user-reference", reference])
    for constraint in args.local_constraint:
        cmd.extend(["--local-constraint", constraint])
    if args.github_query:
        cmd.extend(["--github-query", args.github_query])
    cmd.extend(["--github-top-n", str(args.github_top_n)])
    if args.github_fixture_dir:
        cmd.extend(["--github-fixture-dir", args.github_fixture_dir])
    if args.intent_job:
        cmd.extend(["--intent-job", args.intent_job])
    for item in args.intent_real_input:
        cmd.extend(["--intent-real-input", item])
    if args.intent_primary_output:
        cmd.extend(["--intent-primary-output", args.intent_primary_output])
    for item in args.intent_exclusion:
        cmd.extend(["--intent-exclusion", item])
    for item in args.intent_constraint:
        cmd.extend(["--intent-constraint", item])
    for item in args.intent_standard:
        cmd.extend(["--intent-standard", item])
    if args.intent_correction:
        cmd.extend(["--intent-correction", args.intent_correction])
    result = run_script("init_skill.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_quickstart(args: argparse.Namespace) -> int:
    maybe_emit_update_notice(args)
    sys.stderr.write("Let's start gently. You do not need a polished brief here.\n")
    sys.stderr.write("Give me the real work in your own words, and I will help turn it into a clean first-pass skill.\n")
    sys.stderr.write("While we shape the first pass, I will quietly check a few strong public patterns in the background and only surface them if there is real uncertainty or a design conflict.\n")
    name = args.name or prompt_with_default("Skill name", "my-skill")
    job = args.job or prompt_with_default(
        "In your own words, what repeated work do you most want this skill to reliably handle",
        "Turn a repeated workflow into a reusable skill.",
    )
    real_inputs = args.real_input or prompt_optional_entries(
        "What material will people actually hand to this skill in practice (comma-separated)"
    )
    primary_output = args.primary_output or prompt_with_default(
        "If it works beautifully, what should it hand back so you or the next person can keep moving",
        "A reusable skill package.",
    )
    description = args.description or f"{job.rstrip('.')} Primary output: {primary_output.rstrip('.')}."
    intent_context = {
        "job": job,
        "real_inputs": real_inputs,
        "primary_output": primary_output,
        "description": description,
        "exclusions": [],
        "constraints": [],
        "standards": [],
        "correction": "",
        "user_references": [],
    }
    inferred_archetype, archetype_reason = infer_archetype(job, description)
    guidance = archetype_guidance(inferred_archetype)
    sys.stderr.write(discovery_summary(job, primary_output, inferred_archetype, guidance))
    correction = prompt_optional(
        "If I am off, what is the first thing I should correct before I package this idea",
        "looks right",
    )
    if correction.lower() not in {"looks right", "skip", "none", "no"}:
        description = f"{description.rstrip('.')} Keep this correction in scope: {correction.rstrip('.')}."
        intent_context["description"] = description
        intent_context["correction"] = correction
        inferred_archetype, archetype_reason = infer_archetype(job, description)
        guidance = archetype_guidance(inferred_archetype)
        sys.stderr.write("\nThanks. I tightened the frame before moving on.\n")
        sys.stderr.write(discovery_summary(job, primary_output, inferred_archetype, guidance))
    confidence = assess_intent_confidence(intent_context)
    sys.stderr.write(intent_confidence_note(confidence))
    diagnosis = diagnose_skill_candidates(job, primary_output, inferred_archetype, confidence)
    if diagnosis["fuzzy"]:
        sys.stderr.write(diagnosis_note(diagnosis))
    if not confidence["gate_passed"]:
        sys.stderr.write("Before I package this idea, I want to close the highest-leverage gaps instead of guessing.\n")
        for follow_up in confidence.get("follow_up_questions", [])[:2]:
            answer = prompt_optional(follow_up["question"], "skip")
            update_context_slot(intent_context, follow_up["slot"], answer, follow_up["list"])
        confidence = assess_intent_confidence(intent_context)
        sys.stderr.write("\nI tightened the intent frame once more before moving on.\n")
        sys.stderr.write(intent_confidence_note(confidence))
        diagnosis = diagnose_skill_candidates(job, primary_output, inferred_archetype, confidence)
        if diagnosis["fuzzy"]:
            sys.stderr.write(diagnosis_note(diagnosis))
    archetype = args.archetype or prompt_with_default("I would start with this archetype (scaffold/production/library/governed)", inferred_archetype)
    archetype = archetype if archetype in ARCHETYPE_MODE else inferred_archetype
    default_mode = ARCHETYPE_MODE[archetype]
    mode = args.mode or prompt_with_default("For the first pass, I would keep the mode here (scaffold/production/library/governed)", default_mode)
    mode = mode if mode in ARCHETYPE_MODE.values() else default_mode
    diagnosis = diagnose_skill_candidates(job, primary_output, archetype, confidence)
    guidance = archetype_guidance(archetype)
    sys.stderr.write(
        f"\nGood. I will treat this as `{archetype}` in `{mode}` mode, so the first pass stays focused on {guidance['focus']}.\n"
    )
    user_references = args.user_reference or prompt_optional_entries(
        "If there is anything you admire and want me to learn from as pattern hints, send it here (repo, product, page, workflow; comma-separated)"
    )
    external_references = args.external_reference or []
    prompted_constraints = args.constraint if getattr(args, "constraint", None) else ([] if args.local_constraint else prompt_optional_entries(
        "Tell me any local constraints I must keep in view (privacy, naming, compatibility; comma-separated)"
    ))
    local_constraints = args.local_constraint or prompted_constraints or intent_context.get("constraints", [])
    intent_context["user_references"] = user_references
    intent_context["constraints"] = local_constraints
    confidence = assess_intent_confidence(intent_context)
    github_query = args.github_query or build_query(" ".join(filter(None, [job, primary_output, description])))
    title = args.title or name.replace("-", " ").title()
    guidance = archetype_guidance(archetype)
    cmd = [
        name,
        "--description",
        description,
        "--title",
        title,
        "--output-dir",
        args.output_dir,
        "--mode",
        mode,
        "--archetype",
        archetype,
        "--github-query",
        github_query,
        "--github-top-n",
        str(args.github_top_n),
        "--intent-job",
        job,
        "--intent-primary-output",
        primary_output,
    ]
    for item in real_inputs:
        cmd.extend(["--intent-real-input", item])
    for item in intent_context.get("exclusions", []):
        cmd.extend(["--intent-exclusion", item])
    for item in intent_context.get("constraints", []):
        cmd.extend(["--intent-constraint", item])
    for item in intent_context.get("standards", []):
        cmd.extend(["--intent-standard", item])
    if intent_context.get("correction"):
        cmd.extend(["--intent-correction", intent_context["correction"]])
    if args.github_fixture_dir:
        cmd.extend(["--github-fixture-dir", args.github_fixture_dir])
    for reference in external_references:
        cmd.extend(["--external-reference", reference])
    for reference in user_references:
        cmd.extend(["--user-reference", reference])
    for constraint in local_constraints:
        cmd.extend(["--local-constraint", constraint])
    result = run_script("init_skill.py", cmd)
    payload = result["payload"] if result["payload"] is not None else result
    reference_synthesis = payload.get("reference_synthesis") or {}
    visibility = reference_visibility(reference_synthesis)
    recommendation = recommendation_from_synthesis(reference_synthesis, visibility)
    sys.stderr.write(f"\nRecommendation: {recommendation['summary']}\n")
    if visibility["user_decision_required"]:
        if visibility["conflicts"]:
            sys.stderr.write(f"I am surfacing this because there is a real design conflict: {visibility['conflicts'][0]['summary']}\n")
        else:
            sys.stderr.write("I am surfacing this because intent is still settling and the package should not deepen on guesswork.\n")
    else:
        sys.stderr.write("I will keep the underlying benchmark evidence in the reviewer reports and move ahead with this recommendation.\n")
    if payload.get("report_view", {}).get("html_report"):
        sys.stderr.write(f"Skill report: {payload['report_view']['html_report']}\n")
    if payload.get("report_view", {}).get("interpretation_report"):
        sys.stderr.write(f"Skill interpretation: {payload['report_view']['interpretation_report']}\n")

    next_steps = [
        "Open reports/skill-interpretation.html to review the generated Skill interpretation report.",
        "Open reports/skill-overview.html to review the generated Skill audit report.",
        "Open reports/intent-dialogue.md and tighten the real job, outputs, and exclusions.",
        "Open reports/review-studio.html to inspect the Review Studio 2.0 gate view before release.",
        "Open reports/review-viewer.html to explain the package to a first-time reviewer.",
        "Use reports/iteration-directions.md to choose only one high-value next move before adding more files.",
    ]
    if visibility["user_decision_required"]:
        next_steps.insert(
            1,
            "Open reports/reference-synthesis.md if you want to inspect why the recommendation was surfaced and which tradeoff needs a call.",
        )
    report = {
        "ok": result["ok"],
        "root": payload.get("root"),
        "mode": mode,
        "archetype": archetype,
        "artifacts": payload.get("artifacts", {}),
        "report_view": payload.get("report_view", {}),
        "intent_confidence": {
            "score": confidence["score"],
            "band": confidence["band"],
            "gate_passed": confidence["gate_passed"],
            "recommended_action": confidence["recommended_action"],
        },
        "recommendation": recommendation,
        "reference_mode": {
            "mode": visibility["mode"],
            "user_decision_required": visibility["user_decision_required"],
        },
        "reviewer_evidence": {
            "visibility": "full evidence in reports and review-viewer",
            "artifacts": {
                "benchmark_scan": payload.get("artifacts", {}).get("github_benchmark_scan_md"),
                "reference_synthesis": payload.get("artifacts", {}).get("reference_synthesis_md"),
                "artifact_design_profile": payload.get("artifacts", {}).get("artifact_design_profile_md"),
                "prompt_quality_profile": payload.get("artifacts", {}).get("prompt_quality_profile_md"),
                "system_model": payload.get("artifacts", {}).get("system_model_md"),
                "skill_interpretation": payload.get("artifacts", {}).get("skill_interpretation_html"),
                "review_studio": payload.get("artifacts", {}).get("review_studio_html"),
                "review_viewer": payload.get("artifacts", {}).get("review_viewer_html"),
            },
        },
        "guidance": {
            "archetype_reason": archetype_reason,
            "problem_diagnosis": diagnosis,
            "why_this_mode": (
                "Scaffold mode keeps the first package light and lets you postpone governance-heavy work until reuse becomes real."
                if mode == "scaffold"
                else "This mode expects stronger lifecycle metadata, validation, and review discipline."
            ),
            "first_gate": guidance["first_gate"],
            "focus": guidance["focus"],
            "next_steps": next_steps,
            "experience_note": (
                "The first pass should feel more like guided co-creation than a worksheet. "
                "The system should make benchmark and pattern calls quietly unless there is a real reason to ask you to choose."
            ),
        },
    }
    if visibility["user_decision_required"]:
        report["uncertainty_or_conflict"] = {
            "reasons": visibility["reasons"],
            "conflicts": visibility["conflicts"],
            "note": "A design decision still needs your input before the package should be deepened.",
        }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2
