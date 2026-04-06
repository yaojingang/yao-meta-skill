#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path


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


def command_init(args: argparse.Namespace) -> int:
    result = run_script(
        "init_skill.py",
        [
            args.name,
            "--description",
            args.description,
            "--output-dir",
            args.output_dir,
            *(["--title", args.title] if args.title else []),
        ],
    )
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
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
            run_script("render_description_drift_history.py", []),
            run_script("render_iteration_ledger.py", []),
            run_script("render_regression_history.py", []),
            run_script("render_context_reports.py", []),
            run_script("render_portability_report.py", []),
        ]
    )
    report = {
        "ok": all(step["ok"] for step in steps),
        "steps": [{"command": step["command"], "ok": step["ok"], "returncode": step["returncode"]} for step in steps],
        "artifacts": {
            "eval_results": "reports/eval_suite.json",
            "route_scorecard": "reports/route_scorecard.json",
            "promotion_decisions": "reports/promotion_decisions.json",
            "iteration_ledger": "reports/iteration_ledger.md",
            "regression_history": "reports/regression_history.md",
            "context_budget": "reports/context_budget.json",
            "portability_score": "reports/portability_score.json",
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


def command_reference_scan(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir]
    for reference in args.reference:
        cmd.extend(["--reference", reference])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    result = run_script("render_reference_scan.py", cmd)
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
    init_cmd.set_defaults(func=command_init)

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

    reference_scan_cmd = subparsers.add_parser(
        "reference-scan",
        help="Render a controlled benchmark scan report for a skill package.",
    )
    reference_scan_cmd.add_argument("skill_dir", nargs="?", default=".")
    reference_scan_cmd.add_argument("--reference", action="append", default=[])
    reference_scan_cmd.add_argument("--output-md")
    reference_scan_cmd.add_argument("--output-json")
    reference_scan_cmd.set_defaults(func=command_reference_scan)

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
