#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path

from github_benchmark_scan import build_query
from render_intent_confidence import assess_intent_confidence
from yao_cli_config import (
    ARCHETYPE_MODE,
    archetype_guidance,
    baseline_compare_args,
    diagnose_skill_candidates,
    diagnosis_note,
    discovery_summary,
    infer_archetype,
    local_output_runner_command,
    provider_output_runner_command,
    recommendation_from_synthesis,
    reference_visibility,
    resolve_promotion_target,
    resolve_target,
)
from yao_cli_parser import build_parser as build_cli_parser
from yao_cli_telemetry import add_telemetry_args, maybe_record_cli_event


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


def script_path(name: str) -> str:
    return str(SCRIPTS / name)


def load_json_maybe(text: str) -> dict | None:
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def run_script(name: str, args: list[str], cwd: Path | None = None) -> dict:
    proc = subprocess.run(
        [sys.executable, script_path(name), *args],
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
    )
    payload = load_json_maybe(proc.stdout)
    return {
        "command": f"{name} {' '.join(args)}".strip(),
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "payload": payload,
    }


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

    next_steps = [
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


def command_validate(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    runs = [
        run_script("validate_skill.py", [skill_dir]),
        run_script("lint_skill.py", [skill_dir]),
        run_script("governance_check.py", [skill_dir, *(["--require-manifest"] if args.require_manifest else [])]),
        run_script("resource_boundary_check.py", [skill_dir]),
    ]
    report = {
        "ok": all(item["ok"] for item in runs),
        "skill_dir": skill_dir,
        "steps": [
            {
                "command": item["command"],
                "ok": item["ok"],
                "returncode": item["returncode"],
                "payload": item["payload"],
            }
            for item in runs
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


def optimize_args_for_target(target_name: str, write: bool) -> list[str]:
    target = resolve_target(target_name)
    cmd = [
        "--description-file",
        str(target["description_file"]),
        "--baseline-description-file",
        str(target["baseline_description_file"]),
        "--semantic-config",
        str(target["semantic_config"]),
        "--dev-cases",
        str(target["dev_cases"]),
        "--holdout-cases",
        str(target["holdout_cases"]),
        "--blind-holdout-cases",
        str(target["blind_holdout_cases"]),
        "--adversarial-cases",
        str(target["adversarial_cases"]),
        "--title",
        target["title"],
    ]
    if write:
        cmd.extend(["--output-json", str(target["output_json"]), "--output-md", str(target["output_md"])])
    return cmd


def command_optimize_description(args: argparse.Namespace) -> int:
    if args.target == "all":
        result = run_script("run_description_optimization_suite.py", [])
    else:
        result = run_script("optimize_description.py", optimize_args_for_target(args.target, args.write))
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_promote_check(args: argparse.Namespace) -> int:
    result = run_script("promotion_checker.py", [])
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_report(args: argparse.Namespace) -> int:
    steps = []
    if args.refresh_optimization:
        steps.append(run_script("run_description_optimization_suite.py", []))
    steps.extend(
        [
            run_script("build_confusion_matrix.py", []),
            run_script("promotion_checker.py", []),
            run_script("render_eval_dashboard.py", []),
            run_script("render_intent_confidence.py", [str(ROOT)]),
            run_script("render_description_drift_history.py", []),
            run_script("render_iteration_ledger.py", []),
            run_script("render_baseline_compare.py", baseline_compare_args()),
            run_script("render_regression_history.py", []),
            run_script("render_context_reports.py", []),
            run_script("render_portability_report.py", []),
            run_script("render_reference_synthesis.py", [str(ROOT)]),
            run_script("render_artifact_design_profile.py", [str(ROOT)]),
            run_script("render_prompt_quality_profile.py", [str(ROOT)]),
            run_script("render_system_model.py", [str(ROOT)]),
            run_script("compile_skill.py", [str(ROOT)]),
            run_script("run_output_eval.py", []),
            run_script("run_output_execution.py", ["--runner-command", local_output_runner_command()]),
            run_script("adjudicate_output_review.py", []),
            run_script("render_adoption_drift_report.py", [str(ROOT)]),
            run_script("render_review_waivers.py", [str(ROOT)]),
            run_script("render_review_annotations.py", [str(ROOT)]),
        ]
    )
    report = {
        "ok": all(step["ok"] for step in steps),
        "steps": [{"command": step["command"], "ok": step["ok"], "returncode": step["returncode"]} for step in steps],
        "artifacts": {
            "eval_results": "reports/eval_suite.json",
            "route_scorecard": "reports/route_scorecard.json",
            "promotion_decisions": "reports/promotion_decisions.json",
            "intent_confidence": "reports/intent-confidence.json",
            "iteration_ledger": "reports/iteration_ledger.md",
            "baseline_compare": "reports/baseline-compare.json",
            "regression_history": "reports/regression_history.md",
            "context_budget": "reports/context_budget.json",
            "portability_score": "reports/portability_score.json",
            "reference_synthesis": "reports/reference-synthesis.json",
            "artifact_design_profile": "reports/artifact-design-profile.json",
            "prompt_quality_profile": "reports/prompt-quality-profile.json",
            "system_model": "reports/system-model.json",
            "compiled_targets": "reports/compiled_targets.json",
            "output_execution": "reports/output_execution_runs.json",
            "output_review_adjudication": "reports/output_review_adjudication.json",
            "adoption_drift": "reports/adoption_drift_report.json",
            "review_waivers": "reports/review_waivers.json",
            "review_annotations": "reports/review_annotations.json",
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


def command_skill_report(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir]
    if args.output_html:
        cmd.extend(["--output-html", args.output_html])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    result = run_script("render_skill_overview.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_review_viewer(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir]
    if args.output_html:
        cmd.extend(["--output-html", args.output_html])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    result = run_script("render_review_viewer.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_review_studio(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir]
    if args.output_html:
        cmd.extend(["--output-html", args.output_html])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    result = run_script("render_review_studio.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_reference_scan(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir]
    for reference in args.external_reference:
        cmd.extend(["--external-reference", reference])
    for reference in args.user_reference:
        cmd.extend(["--user-reference", reference])
    for constraint in args.local_constraint:
        cmd.extend(["--local-constraint", constraint])
    for reference in args.reference:
        cmd.extend(["--reference", reference])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    result = run_script("render_reference_scan.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_github_benchmark_scan(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir, "--query", args.query, "--top-n", str(args.top_n)]
    if args.fixture_dir:
        cmd.extend(["--fixture-dir", args.fixture_dir])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    result = run_script("github_benchmark_scan.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_intent_confidence(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir]
    if args.context_json:
        cmd.extend(["--context-json", args.context_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    result = run_script("render_intent_confidence.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_intent_dialogue(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir]
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    result = run_script("render_intent_dialogue.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_reference_synthesis(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir]
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    result = run_script("render_reference_synthesis.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_output_risk_profile(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    result = run_script("render_output_risk_profile.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_artifact_design_profile(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    result = run_script("render_artifact_design_profile.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_prompt_quality_profile(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    result = run_script("render_prompt_quality_profile.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_system_model(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    result = run_script("render_system_model.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_iteration_directions(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir]
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    result = run_script("render_iteration_directions.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_feedback(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir]
    if args.note:
        cmd.extend(["--note", args.note])
    cmd.extend(["--rating", str(args.rating), "--category", args.category, "--recommended-action", args.recommended_action])
    result = run_script("collect_feedback.py", cmd)
    viewer = run_script("render_review_viewer.py", [skill_dir])
    report = {
        "ok": result["ok"] and viewer["ok"],
        "feedback": result["payload"] if result["payload"] is not None else result,
        "review_viewer": viewer["payload"] if viewer["payload"] is not None else viewer,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


def command_adoption_drift(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir]
    if args.events_jsonl:
        cmd.extend(["--events-jsonl", args.events_jsonl])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.generated_at:
        cmd.extend(["--generated-at", args.generated_at])
    if args.record_event:
        cmd.extend(["--record-event", args.record_event])
        cmd.extend(["--activation-type", args.activation_type])
        cmd.extend(["--outcome", args.outcome])
        cmd.extend(["--failure-type", args.failure_type])
        cmd.extend(["--source", args.source])
        cmd.extend(["--command", args.telemetry_command])
        if args.timestamp:
            cmd.extend(["--timestamp", args.timestamp])
        if args.skill_name:
            cmd.extend(["--skill-name", args.skill_name])
        if args.version:
            cmd.extend(["--version", args.version])
    result = run_script("render_adoption_drift_report.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_telemetry_import(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir, "--input-jsonl", args.input_jsonl]
    if args.events_jsonl:
        cmd.extend(["--events-jsonl", args.events_jsonl])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.generated_at:
        cmd.extend(["--generated-at", args.generated_at])
    if args.source:
        cmd.extend(["--source", args.source])
    if args.telemetry_command:
        cmd.extend(["--command", args.telemetry_command])
    if args.dry_run:
        cmd.append("--dry-run")
    result = run_script("import_telemetry_events.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_telemetry_emit(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [
        skill_dir,
        "--event",
        args.event,
        "--activation-type",
        args.activation_type,
        "--outcome",
        args.outcome,
        "--failure-type",
        args.failure_type,
        "--source",
        args.source,
        "--command",
        args.telemetry_command,
    ]
    if args.output_jsonl:
        cmd.extend(["--output-jsonl", args.output_jsonl])
    if args.timestamp:
        cmd.extend(["--timestamp", args.timestamp])
    if args.skill_name:
        cmd.extend(["--skill-name", args.skill_name])
    if args.version:
        cmd.extend(["--version", args.version])
    if args.dry_run:
        cmd.append("--dry-run")
    result = run_script("emit_telemetry_event.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_review_waivers(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir]
    if args.waivers_json:
        cmd.extend(["--waivers-json", args.waivers_json])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.generated_at:
        cmd.extend(["--generated-at", args.generated_at])
    if args.add_waiver:
        required = {
            "--gate-key": args.gate_key,
            "--reviewer": args.reviewer,
            "--reason": args.reason,
            "--expires-at": args.expires_at,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            print(json.dumps({"ok": False, "failures": [f"Missing required fields for --add-waiver: {', '.join(missing)}"]}, ensure_ascii=False, indent=2))
            return 2
        cmd.append("--add-waiver")
        cmd.extend(["--gate-key", args.gate_key])
        cmd.extend(["--decision", args.decision])
        cmd.extend(["--reviewer", args.reviewer])
        cmd.extend(["--reason", args.reason])
        cmd.extend(["--expires-at", args.expires_at])
        if args.created_at:
            cmd.extend(["--created-at", args.created_at])
        if args.evidence:
            cmd.extend(["--evidence", args.evidence])
        if args.scope:
            cmd.extend(["--scope", args.scope])
    result = run_script("render_review_waivers.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_review_annotations(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir]
    if args.annotations_json:
        cmd.extend(["--annotations-json", args.annotations_json])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.write_template:
        cmd.append("--write-template")
    if args.add_annotation:
        cmd.append("--add-annotation")
    if args.annotation_id:
        cmd.extend(["--annotation-id", args.annotation_id])
    if args.gate_key:
        cmd.extend(["--gate-key", args.gate_key])
    if args.target_path:
        cmd.extend(["--target-path", args.target_path])
    if args.line is not None:
        cmd.extend(["--line", str(args.line)])
    if args.severity:
        cmd.extend(["--severity", args.severity])
    if args.status:
        cmd.extend(["--status", args.status])
    if args.reviewer:
        cmd.extend(["--reviewer", args.reviewer])
    if args.created_at:
        cmd.extend(["--created-at", args.created_at])
    if args.body:
        cmd.extend(["--body", args.body])
    if args.suggested_action:
        cmd.extend(["--suggested-action", args.suggested_action])
    if args.evidence:
        cmd.extend(["--evidence", args.evidence])
    result = run_script("render_review_annotations.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_baseline_compare(args: argparse.Namespace) -> int:
    result = run_script("render_baseline_compare.py", baseline_compare_args())
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_skill_ir(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.validate_only:
        cmd.append("--validate-only")
    result = run_script("export_skill_ir.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_compile_skill(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    for target in args.target or []:
        cmd.extend(["--target", target])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.generated_at:
        cmd.extend(["--generated-at", args.generated_at])
    result = run_script("compile_skill.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_output_eval(args: argparse.Namespace) -> int:
    cmd = []
    if args.cases:
        cmd.extend(["--cases", args.cases])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.blind_pack_json:
        cmd.extend(["--blind-pack-json", args.blind_pack_json])
    if args.blind_pack_md:
        cmd.extend(["--blind-pack-md", args.blind_pack_md])
    if args.blind_answer_key_json:
        cmd.extend(["--blind-answer-key-json", args.blind_answer_key_json])
    result = run_script("run_output_eval.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_output_execution(args: argparse.Namespace) -> int:
    cmd = []
    if args.cases:
        cmd.extend(["--cases", args.cases])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.runner_command and args.provider_runner:
        payload = {
            "schema_version": "1.0",
            "ok": False,
            "failures": ["Use either --runner-command or --provider-runner, not both."],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2
    if args.provider_runner:
        cmd.extend(
            [
                "--runner-command",
                provider_output_runner_command(
                    args.provider_runner,
                    model=args.provider_model,
                    base_url=args.provider_base_url,
                    api_key_env=args.api_key_env,
                    allow_insecure_localhost=args.allow_insecure_localhost,
                    allow_custom_base_url=args.allow_custom_base_url,
                ),
            ]
        )
    elif args.runner_command:
        cmd.extend(["--runner-command", args.runner_command])
    if args.timeout_seconds is not None:
        cmd.extend(["--timeout-seconds", str(args.timeout_seconds)])
    result = run_script("run_output_execution.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_output_review(args: argparse.Namespace) -> int:
    cmd = []
    if args.blind_pack:
        cmd.extend(["--blind-pack", args.blind_pack])
    if args.answer_key:
        cmd.extend(["--answer-key", args.answer_key])
    if args.decisions:
        cmd.extend(["--decisions", args.decisions])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.write_template:
        cmd.append("--write-template")
    result = run_script("adjudicate_output_review.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_conformance(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    for target in args.target or []:
        cmd.extend(["--target", target])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    result = run_script("run_conformance_suite.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_runtime_permissions(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    if args.package_dir:
        cmd.extend(["--package-dir", args.package_dir])
    for target in args.target or []:
        cmd.extend(["--target", target])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    result = run_script("probe_runtime_permissions.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_trust(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    result = run_script("trust_check.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_skill_atlas(args: argparse.Namespace) -> int:
    cmd = ["--workspace-root", str(Path(args.workspace_root).resolve())]
    if args.output_dir:
        cmd.extend(["--output-dir", args.output_dir])
    if args.report_html:
        cmd.extend(["--report-html", args.report_html])
    if args.report_json:
        cmd.extend(["--report-json", args.report_json])
    if args.overlap_threshold is not None:
        cmd.extend(["--overlap-threshold", str(args.overlap_threshold)])
    if args.today:
        cmd.extend(["--today", args.today])
    result = run_script("build_skill_atlas.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_registry_audit(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    if args.registry_dir:
        cmd.extend(["--registry-dir", args.registry_dir])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.generated_at:
        cmd.extend(["--generated-at", args.generated_at])
    result = run_script("registry_audit.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_package_verify(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    if args.package_dir:
        cmd.extend(["--package-dir", args.package_dir])
    if args.expectations:
        cmd.extend(["--expectations", args.expectations])
    if args.registry_json:
        cmd.extend(["--registry-json", args.registry_json])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.require_zip:
        cmd.append("--require-zip")
    if args.generated_at:
        cmd.extend(["--generated-at", args.generated_at])
    result = run_script("verify_package.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_install_simulate(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    if args.package_dir:
        cmd.extend(["--package-dir", args.package_dir])
    if args.install_root:
        cmd.extend(["--install-root", args.install_root])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.generated_at:
        cmd.extend(["--generated-at", args.generated_at])
    result = run_script("simulate_install.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_upgrade_check(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    cmd.extend(["--previous-package-json", args.previous_package_json])
    if args.current_package_json:
        cmd.extend(["--current-package-json", args.current_package_json])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.generated_at:
        cmd.extend(["--generated-at", args.generated_at])
    result = run_script("upgrade_check.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_review(args: argparse.Namespace) -> int:
    target_name = resolve_promotion_target(args.target)
    bundle_dir = ROOT / "reports" / "iteration_bundles" / target_name
    report = {
        "ok": (bundle_dir / "bundle.json").exists() and (bundle_dir / "review.md").exists(),
        "target": target_name,
        "artifacts": {
            "bundle_json": str((bundle_dir / "bundle.json").relative_to(ROOT)),
            "bundle_md": str((bundle_dir / "bundle.md").relative_to(ROOT)),
            "review_md": str((bundle_dir / "review.md").relative_to(ROOT)),
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


def command_release_snapshot(args: argparse.Namespace) -> int:
    target_name = resolve_promotion_target(args.target)
    result = run_script(
        "create_iteration_snapshot.py",
        [
            "--target",
            target_name,
            "--label",
            args.label,
        ],
    )
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_workspace_flow(args: argparse.Namespace) -> int:
    selected_targets = (
        ["root", "team-frontend-review", "governed-incident-command"]
        if args.target == "all"
        else [args.target]
    )
    steps = []
    snapshot_artifacts = []

    for target in selected_targets:
        steps.append(
            {
                "phase": "optimize-description",
                "target": target,
                "result": run_script("optimize_description.py", optimize_args_for_target(target, True)),
            }
        )

    steps.extend(
        [
            {"phase": "route-scorecard", "result": run_script("build_confusion_matrix.py", [])},
            {"phase": "promotion-check", "result": run_script("promotion_checker.py", [])},
            {"phase": "report-refresh", "result": run_script("render_eval_dashboard.py", [])},
            {"phase": "report-refresh", "result": run_script("render_description_drift_history.py", [])},
            {"phase": "report-refresh", "result": run_script("render_iteration_ledger.py", [])},
            {"phase": "report-refresh", "result": run_script("render_baseline_compare.py", baseline_compare_args())},
            {"phase": "report-refresh", "result": run_script("render_regression_history.py", [])},
            {"phase": "report-refresh", "result": run_script("render_context_reports.py", [])},
            {"phase": "report-refresh", "result": run_script("render_portability_report.py", [])},
            {"phase": "report-refresh", "result": run_script("compile_skill.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_adoption_drift_report.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_review_waivers.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_review_annotations.py", [str(ROOT)])},
        ]
    )

    for target in selected_targets:
        review_target = resolve_promotion_target(target)
        review_info = {
            "bundle_json": f"reports/iteration_bundles/{review_target}/bundle.json",
            "bundle_md": f"reports/iteration_bundles/{review_target}/bundle.md",
            "review_md": f"reports/iteration_bundles/{review_target}/review.md",
        }
        snapshot = run_script(
            "create_iteration_snapshot.py",
            [
                "--target",
                review_target,
                "--label",
                args.label,
            ],
        )
        snapshot_artifacts.append(
            {
                "target": review_target,
                "review": review_info,
                "snapshot": snapshot["payload"] if snapshot["payload"] is not None else snapshot,
            }
        )
        steps.append({"phase": "release-snapshot", "target": review_target, "result": snapshot})

    report = {
        "ok": all(step["result"]["ok"] for step in steps),
        "target": args.target,
        "label": args.label,
        "steps": [
            {
                "phase": step["phase"],
                **({"target": step["target"]} if "target" in step else {}),
                "command": step["result"]["command"],
                "ok": step["result"]["ok"],
                "returncode": step["result"]["returncode"],
            }
            for step in steps
        ],
        "artifacts": snapshot_artifacts,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


def command_package(args: argparse.Namespace) -> int:
    cmd = [
        str(Path(args.skill_dir).resolve()),
        "--output-dir",
        args.output_dir,
    ]
    for platform in args.platform or ["generic"]:
        cmd.extend(["--platform", platform])
    if args.expectations:
        cmd.extend(["--expectations", args.expectations])
    if args.zip:
        cmd.append("--zip")
    result = run_script("cross_packager.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_test(args: argparse.Namespace) -> int:
    proc = subprocess.run(
        ["make", args.target],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    report = {
        "ok": proc.returncode == 0,
        "target": args.target,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


def command_check_update(args: argparse.Namespace) -> int:
    cmd = []
    if args.force:
        cmd.append("--force")
    if args.no_cache:
        cmd.append("--no-cache")
    if args.version_url:
        cmd.extend(["--version-url", args.version_url])
    if args.manifest_url:
        cmd.extend(["--manifest-url", args.manifest_url])
    if args.timeout is not None:
        cmd.extend(["--timeout", str(args.timeout)])
    if args.allow_custom_update_url:
        cmd.append("--allow-custom-update-url")
    result = run_script("check_update.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def build_parser() -> argparse.ArgumentParser:
    parser = build_cli_parser({name: value for name, value in globals().items() if name.startswith("command_")})
    add_telemetry_args(parser)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    returncode = 2
    try:
        returncode = args.func(args)
    finally:
        maybe_record_cli_event(ROOT, args, returncode)
    raise SystemExit(returncode)


if __name__ == "__main__":
    main()
