#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path

from github_benchmark_scan import build_query
from render_intent_confidence import assess_intent_confidence


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

TARGETS = {
    "root": {
        "description_file": ROOT / "SKILL.md",
        "baseline_description_file": ROOT / "evals" / "baseline_description.txt",
        "semantic_config": ROOT / "evals" / "semantic_config.json",
        "dev_cases": ROOT / "evals" / "dev" / "trigger_cases.json",
        "holdout_cases": ROOT / "evals" / "holdout" / "trigger_cases.json",
        "blind_holdout_cases": ROOT / "evals" / "blind_holdout" / "trigger_cases.json",
        "adversarial_cases": ROOT / "evals" / "adversarial" / "trigger_cases.json",
        "output_json": ROOT / "reports" / "description_optimization.json",
        "output_md": ROOT / "reports" / "description_optimization.md",
        "title": "Root Description Optimization",
    },
    "team-frontend-review": {
        "description_file": ROOT / "examples" / "team-frontend-review" / "generated-skill" / "SKILL.md",
        "baseline_description_file": ROOT / "examples" / "team-frontend-review" / "optimization" / "baseline_description.txt",
        "semantic_config": ROOT / "examples" / "team-frontend-review" / "optimization" / "semantic_config.json",
        "dev_cases": ROOT / "examples" / "team-frontend-review" / "optimization" / "dev" / "trigger_cases.json",
        "holdout_cases": ROOT / "examples" / "team-frontend-review" / "optimization" / "holdout" / "trigger_cases.json",
        "blind_holdout_cases": ROOT / "examples" / "team-frontend-review" / "optimization" / "blind_holdout" / "trigger_cases.json",
        "adversarial_cases": ROOT / "examples" / "team-frontend-review" / "optimization" / "adversarial" / "trigger_cases.json",
        "output_json": ROOT / "examples" / "team-frontend-review" / "optimization" / "reports" / "description_optimization.json",
        "output_md": ROOT / "examples" / "team-frontend-review" / "optimization" / "reports" / "description_optimization.md",
        "title": "Frontend Review Description Optimization",
    },
    "governed-incident-command": {
        "description_file": ROOT / "examples" / "governed-incident-command" / "generated-skill" / "SKILL.md",
        "baseline_description_file": ROOT / "examples" / "governed-incident-command" / "optimization" / "baseline_description.txt",
        "semantic_config": ROOT / "examples" / "governed-incident-command" / "optimization" / "semantic_config.json",
        "dev_cases": ROOT / "examples" / "governed-incident-command" / "optimization" / "dev" / "trigger_cases.json",
        "holdout_cases": ROOT / "examples" / "governed-incident-command" / "optimization" / "holdout" / "trigger_cases.json",
        "blind_holdout_cases": ROOT / "examples" / "governed-incident-command" / "optimization" / "blind_holdout" / "trigger_cases.json",
        "adversarial_cases": ROOT / "examples" / "governed-incident-command" / "optimization" / "adversarial" / "trigger_cases.json",
        "output_json": ROOT / "examples" / "governed-incident-command" / "optimization" / "reports" / "description_optimization.json",
        "output_md": ROOT / "examples" / "governed-incident-command" / "optimization" / "reports" / "description_optimization.md",
        "title": "Governed Incident Description Optimization",
    },
}

PROMOTION_TARGETS = {
    "root": "yao-meta-skill",
    "team-frontend-review": "team-frontend-review",
    "governed-incident-command": "governed-incident-command",
}


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


def resolve_target(name: str) -> dict:
    if name not in TARGETS:
        raise KeyError(f"Unknown target: {name}")
    return TARGETS[name]


def resolve_promotion_target(name: str) -> str:
    if name not in PROMOTION_TARGETS:
        raise KeyError(f"Unknown promotion target: {name}")
    return PROMOTION_TARGETS[name]


def baseline_compare_args() -> list[str]:
    args = []
    for label, target in TARGETS.items():
        args.extend(["--entry", f"{label}::{target['output_json']}"])
    args.extend(
        [
            "--output-json",
            str(ROOT / "reports" / "baseline-compare.json"),
            "--output-md",
            str(ROOT / "reports" / "baseline-compare.md"),
        ]
    )
    return args


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


ARCHETYPE_MODE = {
    "scaffold": "scaffold",
    "production": "production",
    "library": "library",
    "governed": "governed",
}


def infer_archetype(job: str, description: str) -> tuple[str, str]:
    text = f"{job} {description}".lower()
    if any(token in text for token in ("incident", "compliance", "security", "release", "govern", "audit", "policy")):
        return "governed", "The request looks operationally sensitive, so governed is the safest default."
    if any(token in text for token in ("shared", "cross-team", "library", "portable", "platform", "reusable across")):
        return "library", "The request signals multi-team reuse or portability, so library is the better fit."
    if any(token in text for token in ("review", "checklist", "team", "workflow", "process", "standardize")):
        return "production", "The request looks team-reused and repeatable, so production fits better than scaffold."
    return "scaffold", "The request still looks exploratory or lightweight, so scaffold keeps the first package lean."


def archetype_guidance(archetype: str) -> dict:
    mapping = {
        "scaffold": {
            "first_gate": "trigger and exclusions",
            "focus": "keep the first package small and avoid governance overhead",
        },
        "production": {
            "first_gate": "trigger plus one execution or eval asset",
            "focus": "make the package reliable for team reuse",
        },
        "library": {
            "first_gate": "trigger, portability, and packaging semantics",
            "focus": "treat the package as a shared capability with visible evidence",
        },
        "governed": {
            "first_gate": "trigger, governance, and review cadence",
            "focus": "treat the package as a high-trust asset from the start",
        },
    }
    return mapping.get(archetype, mapping["scaffold"])


def discovery_summary(job: str, primary_output: str, archetype: str, guidance: dict) -> str:
    return (
        "\nHere's the shape I'm hearing so far:\n"
        f"- Repeated job: {job}\n"
        f"- Desired hand-back: {primary_output}\n"
        f"- Best starting archetype: {archetype}\n"
        f"- First gate: {guidance['first_gate']}\n"
        f"- Current focus: {guidance['focus']}\n"
    )


def reference_visibility(reference_synthesis: dict) -> dict:
    synthesis = reference_synthesis.get("synthesis", {}) if isinstance(reference_synthesis, dict) else {}
    visibility = synthesis.get("visibility", {}) if isinstance(synthesis, dict) else {}
    reasons = list(visibility.get("reasons", []))
    mode = visibility.get("mode", "explicit" if reasons else "silent")
    return {
        "mode": mode,
        "user_decision_required": mode == "explicit",
        "reasons": reasons,
        "conflicts": synthesis.get("conflicts", []),
    }


def recommendation_from_synthesis(reference_synthesis: dict, visibility: dict) -> dict:
    synthesis = reference_synthesis.get("synthesis", {}) if isinstance(reference_synthesis, dict) else {}
    recommendation = synthesis.get("recommendation", {}) if isinstance(synthesis, dict) else {}
    borrow_now = recommendation.get("borrow_now") or synthesis.get("borrow_now", [])
    avoid_now = recommendation.get("avoid_for_now") or synthesis.get("avoid_now", [])
    summary = recommendation.get("summary") or (
        f"Start with {borrow_now[0]} Avoid {avoid_now[0]} for the first pass."
        if borrow_now and avoid_now
        else "Start with the smallest high-confidence pattern and keep the first pass light."
    )
    why = recommendation.get("why") or "This recommendation comes from the benchmark synthesis and current intent confidence."
    return {
        "summary": summary,
        "borrow_now": borrow_now[:2],
        "avoid_for_now": avoid_now[:2],
        "why": why,
        "user_decision_required": visibility["user_decision_required"],
    }


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
    if not confidence["gate_passed"]:
        sys.stderr.write("Before I package this idea, I want to close the highest-leverage gaps instead of guessing.\n")
        for follow_up in confidence.get("follow_up_questions", [])[:2]:
            answer = prompt_optional(follow_up["question"], "skip")
            update_context_slot(intent_context, follow_up["slot"], answer, follow_up["list"])
        confidence = assess_intent_confidence(intent_context)
        sys.stderr.write("\nI tightened the intent frame once more before moving on.\n")
        sys.stderr.write(intent_confidence_note(confidence))
    archetype = args.archetype or prompt_with_default("I would start with this archetype (scaffold/production/library/governed)", inferred_archetype)
    archetype = archetype if archetype in ARCHETYPE_MODE else inferred_archetype
    default_mode = ARCHETYPE_MODE[archetype]
    mode = args.mode or prompt_with_default("For the first pass, I would keep the mode here (scaffold/production/library/governed)", default_mode)
    mode = mode if mode in ARCHETYPE_MODE.values() else default_mode
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

    next_steps = [
        "Open reports/intent-dialogue.md and tighten the real job, outputs, and exclusions.",
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
                "review_viewer": payload.get("artifacts", {}).get("review_viewer_html"),
            },
        },
        "guidance": {
            "archetype_reason": archetype_reason,
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


def command_baseline_compare(args: argparse.Namespace) -> int:
    result = run_script("render_baseline_compare.py", baseline_compare_args())
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified authoring CLI for yao-meta-skill.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_cmd = subparsers.add_parser("init", help="Initialize a minimal skill package.")
    init_cmd.add_argument("name")
    init_cmd.add_argument("--description", default="Describe what the skill does and when to use it.")
    init_cmd.add_argument("--title")
    init_cmd.add_argument("--output-dir", default=".")
    init_cmd.add_argument("--mode", choices=["scaffold", "production", "library", "governed"], default="scaffold")
    init_cmd.add_argument("--archetype", choices=["scaffold", "production", "library", "governed"], default="scaffold")
    init_cmd.add_argument("--external-reference", action="append", default=[])
    init_cmd.add_argument("--user-reference", action="append", default=[])
    init_cmd.add_argument("--local-constraint", action="append", default=[])
    init_cmd.add_argument("--github-query")
    init_cmd.add_argument("--github-top-n", type=int, default=3)
    init_cmd.add_argument("--github-fixture-dir")
    init_cmd.add_argument("--intent-job")
    init_cmd.add_argument("--intent-real-input", action="append", default=[])
    init_cmd.add_argument("--intent-primary-output")
    init_cmd.add_argument("--intent-exclusion", action="append", default=[])
    init_cmd.add_argument("--intent-constraint", action="append", default=[])
    init_cmd.add_argument("--intent-standard", action="append", default=[])
    init_cmd.add_argument("--intent-correction")
    init_cmd.set_defaults(func=command_init)

    quickstart_cmd = subparsers.add_parser(
        "quickstart",
        help="Interactive fast path for creating a scaffold-first skill package.",
    )
    quickstart_cmd.add_argument("--name")
    quickstart_cmd.add_argument("--job")
    quickstart_cmd.add_argument("--real-input", action="append", default=[])
    quickstart_cmd.add_argument("--primary-output")
    quickstart_cmd.add_argument("--description")
    quickstart_cmd.add_argument("--title")
    quickstart_cmd.add_argument("--output-dir", default=".")
    quickstart_cmd.add_argument("--mode", choices=["scaffold", "production", "library", "governed"])
    quickstart_cmd.add_argument("--archetype", choices=["scaffold", "production", "library", "governed"])
    quickstart_cmd.add_argument("--external-reference", action="append", default=[])
    quickstart_cmd.add_argument("--user-reference", action="append", default=[])
    quickstart_cmd.add_argument("--local-constraint", action="append", default=[])
    quickstart_cmd.add_argument("--constraint", action="append", default=[])
    quickstart_cmd.add_argument("--github-query")
    quickstart_cmd.add_argument("--github-top-n", type=int, default=3)
    quickstart_cmd.add_argument("--github-fixture-dir")
    quickstart_cmd.set_defaults(func=command_quickstart)

    validate_cmd = subparsers.add_parser("validate", help="Run validate, lint, governance, and resource checks.")
    validate_cmd.add_argument("skill_dir", nargs="?", default=".")
    validate_cmd.add_argument("--require-manifest", action="store_true")
    validate_cmd.set_defaults(func=command_validate)

    optimize_cmd = subparsers.add_parser("optimize-description", help="Optimize description candidates for a target.")
    optimize_cmd.add_argument(
        "--target",
        choices=["root", "team-frontend-review", "governed-incident-command", "all"],
        default="root",
    )
    optimize_cmd.add_argument("--write", action="store_true", help="Write default report artifacts for the target.")
    optimize_cmd.set_defaults(func=command_optimize_description)

    promote_cmd = subparsers.add_parser("promote-check", help="Apply promotion policy and build iteration bundles.")
    promote_cmd.set_defaults(func=command_promote_check)

    review_cmd = subparsers.add_parser("review", help="Locate the current bundle and human review stub for a target.")
    review_cmd.add_argument(
        "--target",
        choices=["root", "team-frontend-review", "governed-incident-command"],
        default="root",
    )
    review_cmd.set_defaults(func=command_review)

    snapshot_cmd = subparsers.add_parser("release-snapshot", help="Create a versioned snapshot from current promotion outputs.")
    snapshot_cmd.add_argument(
        "--target",
        choices=["root", "team-frontend-review", "governed-incident-command"],
        default="root",
    )
    snapshot_cmd.add_argument("--label", default="manual")
    snapshot_cmd.set_defaults(func=command_release_snapshot)

    flow_cmd = subparsers.add_parser(
        "workspace-flow",
        help="Run optimize, promotion, review refresh, and release snapshots as one authoring flow.",
    )
    flow_cmd.add_argument(
        "--target",
        choices=["root", "team-frontend-review", "governed-incident-command", "all"],
        default="root",
    )
    flow_cmd.add_argument("--label", default="manual")
    flow_cmd.set_defaults(func=command_workspace_flow)

    report_cmd = subparsers.add_parser("report", help="Render route, iteration, regression, and context reports.")
    report_cmd.add_argument("--refresh-optimization", action="store_true")
    report_cmd.set_defaults(func=command_report)

    skill_report_cmd = subparsers.add_parser("skill-report", help="Render a visual overview report for a skill package.")
    skill_report_cmd.add_argument("skill_dir", nargs="?", default=".")
    skill_report_cmd.add_argument("--output-html")
    skill_report_cmd.add_argument("--output-json")
    skill_report_cmd.set_defaults(func=command_skill_report)

    review_viewer_cmd = subparsers.add_parser("review-viewer", help="Render a compact HTML review page for a skill package.")
    review_viewer_cmd.add_argument("skill_dir", nargs="?", default=".")
    review_viewer_cmd.add_argument("--output-html")
    review_viewer_cmd.add_argument("--output-json")
    review_viewer_cmd.set_defaults(func=command_review_viewer)

    reference_scan_cmd = subparsers.add_parser(
        "reference-scan",
        help="Render a controlled benchmark scan report for a skill package.",
    )
    reference_scan_cmd.add_argument("skill_dir", nargs="?", default=".")
    reference_scan_cmd.add_argument("--reference", action="append", default=[])
    reference_scan_cmd.add_argument("--external-reference", action="append", default=[])
    reference_scan_cmd.add_argument("--user-reference", action="append", default=[])
    reference_scan_cmd.add_argument("--local-constraint", action="append", default=[])
    reference_scan_cmd.add_argument("--output-md")
    reference_scan_cmd.add_argument("--output-json")
    reference_scan_cmd.set_defaults(func=command_reference_scan)

    github_scan_cmd = subparsers.add_parser(
        "github-benchmark-scan",
        help="Search top public GitHub repositories and extract borrow or avoid patterns for a skill.",
    )
    github_scan_cmd.add_argument("skill_dir", nargs="?", default=".")
    github_scan_cmd.add_argument("--query", required=True)
    github_scan_cmd.add_argument("--top-n", type=int, default=3)
    github_scan_cmd.add_argument("--fixture-dir")
    github_scan_cmd.add_argument("--output-md")
    github_scan_cmd.add_argument("--output-json")
    github_scan_cmd.set_defaults(func=command_github_benchmark_scan)

    intent_confidence_cmd = subparsers.add_parser(
        "intent-confidence",
        help="Render a confidence report for how well the real job, inputs, outputs, and exclusions are understood.",
    )
    intent_confidence_cmd.add_argument("skill_dir", nargs="?", default=".")
    intent_confidence_cmd.add_argument("--context-json")
    intent_confidence_cmd.add_argument("--output-md")
    intent_confidence_cmd.add_argument("--output-json")
    intent_confidence_cmd.set_defaults(func=command_intent_confidence)

    intent_dialogue_cmd = subparsers.add_parser(
        "intent-dialogue",
        help="Render a front-loaded intent dialogue guide for a skill package.",
    )
    intent_dialogue_cmd.add_argument("skill_dir", nargs="?", default=".")
    intent_dialogue_cmd.add_argument("--output-md")
    intent_dialogue_cmd.add_argument("--output-json")
    intent_dialogue_cmd.set_defaults(func=command_intent_dialogue)

    reference_synthesis_cmd = subparsers.add_parser(
        "reference-synthesis",
        help="Render a multi-source reference synthesis report for a skill package.",
    )
    reference_synthesis_cmd.add_argument("skill_dir", nargs="?", default=".")
    reference_synthesis_cmd.add_argument("--output-md")
    reference_synthesis_cmd.add_argument("--output-json")
    reference_synthesis_cmd.set_defaults(func=command_reference_synthesis)

    iteration_directions_cmd = subparsers.add_parser(
        "iteration-directions",
        help="Render the top three next iteration directions for a skill package.",
    )
    iteration_directions_cmd.add_argument("skill_dir", nargs="?", default=".")
    iteration_directions_cmd.add_argument("--output-md")
    iteration_directions_cmd.add_argument("--output-json")
    iteration_directions_cmd.set_defaults(func=command_iteration_directions)

    feedback_cmd = subparsers.add_parser(
        "feedback",
        help="Capture lightweight reviewer feedback without running the full promotion flow.",
    )
    feedback_cmd.add_argument("skill_dir", nargs="?", default=".")
    feedback_cmd.add_argument("--note")
    feedback_cmd.add_argument("--rating", type=int, default=3)
    feedback_cmd.add_argument("--category", default="general")
    feedback_cmd.add_argument("--recommended-action", default="review")
    feedback_cmd.set_defaults(func=command_feedback)

    baseline_compare_cmd = subparsers.add_parser(
        "baseline-compare",
        help="Render a lightweight with-skill vs baseline comparison across tracked targets.",
    )
    baseline_compare_cmd.set_defaults(func=command_baseline_compare)

    package_cmd = subparsers.add_parser("package", help="Export compatibility artifacts for selected targets.")
    package_cmd.add_argument("skill_dir", nargs="?", default=".")
    package_cmd.add_argument("--platform", action="append")
    package_cmd.add_argument("--output-dir", default="dist")
    package_cmd.add_argument("--expectations")
    package_cmd.add_argument("--zip", action="store_true")
    package_cmd.set_defaults(func=command_package)

    test_cmd = subparsers.add_parser("test", help="Run a Makefile test target.")
    test_cmd.add_argument("--target", default="test")
    test_cmd.set_defaults(func=command_test)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
