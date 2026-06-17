#!/usr/bin/env python3
"""Pure configuration and shaping helpers for the Yao CLI."""

import json
from pathlib import Path


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by yao.py for CLI target maps and side-effect-free shaping helpers."


ROOT = Path(__file__).resolve().parent.parent

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

ARCHETYPE_MODE = {
    "scaffold": "scaffold",
    "production": "production",
    "library": "library",
    "governed": "governed",
}


def local_output_runner_command() -> str:
    return json.dumps(["python3", "scripts/local_output_eval_runner.py"])


def provider_output_runner_command(
    provider: str,
    model: str | None = None,
    base_url: str | None = None,
    api_format: str | None = None,
    thinking: str | None = None,
    temperature: float | None = None,
    api_key_env: str | None = None,
    allow_insecure_localhost: bool = False,
    allow_custom_base_url: bool = False,
) -> str:
    command = ["python3", "scripts/provider_output_eval_runner.py", "--provider", provider]
    if provider == "deepseek":
        api_format = api_format or "chat-completions"
        thinking = thinking or "disabled"
        api_key_env = api_key_env or "DEEPSEEK_API_KEY"
    if model:
        command.extend(["--model", model])
    if base_url:
        command.extend(["--base-url", base_url])
    if api_format:
        command.extend(["--api-format", api_format])
    if thinking:
        command.extend(["--thinking", thinking])
    if temperature is not None:
        command.extend(["--temperature", str(temperature)])
    if api_key_env:
        command.extend(["--api-key-env", api_key_env])
    if allow_insecure_localhost:
        command.append("--allow-insecure-localhost")
    if allow_custom_base_url:
        command.append("--allow-custom-base-url")
    return json.dumps(command)


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


def explicit_skill_request(job: str, description: str) -> bool:
    text = f"{job} {description}".lower()
    return any(token in text for token in ("skill", "workflow", "checklist", "package", "automate", "standardize"))


def diagnose_skill_candidates(job: str, primary_output: str, archetype: str, confidence: dict) -> dict:
    fuzzy = not explicit_skill_request(job, primary_output) or confidence.get("score", 0) < 75
    candidates = [
        {
            "shape": archetype,
            "recommendation": "recommended",
            "why_it_fits": "This is the lightest shape that matches the current recurring job signal.",
            "limitation": "It should not deepen until the concrete output and exclusion boundary are clear.",
            "first_pass": "Create one routeable skill with honest boundaries, one review report, and one next-step direction.",
        }
    ]
    if archetype != "scaffold":
        candidates.append(
            {
                "shape": "scaffold",
                "recommendation": "fallback",
                "why_it_fits": "Use this if the idea is still exploratory or personal.",
                "limitation": "It may under-serve team reuse, portability, or governance needs.",
                "first_pass": "Ship only SKILL.md, interface metadata, intent confidence, and review viewer.",
            }
        )
    if archetype not in {"production", "governed"}:
        candidates.append(
            {
                "shape": "production",
                "recommendation": "upgrade path",
                "why_it_fits": "Use this when the workflow will be repeated by a team or needs consistent outputs.",
                "limitation": "It adds validation and review cost that a personal scaffold may not need.",
                "first_pass": "Add one practical eval or execution check after the trigger boundary is stable.",
            }
        )
    if archetype != "governed" and any(token in f"{job} {primary_output}".lower() for token in ("risk", "audit", "release", "policy", "security", "compliance")):
        candidates.append(
            {
                "shape": "governed",
                "recommendation": "risk path",
                "why_it_fits": "Use this if the skill affects operational, compliance, security, or release decisions.",
                "limitation": "It is too heavy unless ownership and review cadence are real.",
                "first_pass": "Add owner, review cadence, lifecycle metadata, and reviewer-visible evidence.",
            }
        )
    return {
        "mode": "fuzzy-problem-diagnosis" if fuzzy else "direct-skill-shaping",
        "fuzzy": fuzzy,
        "candidates": candidates[:3],
    }


def diagnosis_note(diagnosis: dict) -> str:
    lines = ["\nProblem-to-skill diagnosis:"]
    for candidate in diagnosis["candidates"]:
        lines.append(
            f"- {candidate['shape']} ({candidate['recommendation']}): {candidate['why_it_fits']} "
            f"First pass: {candidate['first_pass']}"
        )
    return "\n".join(lines) + "\n"


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
