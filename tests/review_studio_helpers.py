#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
SCRIPT = SCRIPTS / "render_review_studio.py"


def run(args: list[object], allowed_returncodes: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run([str(item) for item in args], cwd=ROOT, check=False, capture_output=True, text=True)
    if proc.returncode not in allowed_returncodes:
        raise subprocess.CalledProcessError(proc.returncode, proc.args, output=proc.stdout, stderr=proc.stderr)
    return proc


def run_script(
    script_name: str,
    *args: object,
    allowed_returncodes: tuple[int, ...] = (0,),
) -> subprocess.CompletedProcess[str]:
    return run([sys.executable, SCRIPTS / script_name, *args], allowed_returncodes=allowed_returncodes)


def prepare_tmp_root() -> Path:
    tmp_root = ROOT / "tests" / "tmp_review_studio"
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    tmp_root.mkdir(parents=True, exist_ok=True)
    return tmp_root


def copy_tmp_report(tmp_root: Path, stem: str) -> None:
    for suffix in ("json", "md"):
        (ROOT / "reports" / f"{stem}.{suffix}").write_text(
            (tmp_root / f"{stem}.{suffix}").read_text(encoding="utf-8"),
            encoding="utf-8",
        )


def output_execution_has_provider_evidence() -> bool:
    path = ROOT / "reports" / "output_execution_runs.json"
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    summary = payload.get("summary", {})
    if not isinstance(summary, dict):
        return False
    return (
        int(summary.get("model_executed_count") or 0) > 0
        and int(summary.get("timing_observed_count") or 0) > 0
        and int(summary.get("token_observed_count") or 0) > 0
    )


def prepare_review_studio_inputs(tmp_root: Path) -> None:
    run_script("run_output_eval.py")
    run_script("prepare_output_review_kit.py")
    if not output_execution_has_provider_evidence():
        run_script("run_output_execution.py", "--runner-command", json.dumps(["python3", "scripts/local_output_eval_runner.py"]))
    run_script("adjudicate_output_review.py")
    run_script("compile_skill.py", ROOT, "--generated-at", "2026-06-13")

    package_dir = tmp_root / "dist"
    run_script(
        "cross_packager.py",
        ROOT,
        "--platform",
        "openai",
        "--platform",
        "claude",
        "--platform",
        "generic",
        "--platform",
        "vscode",
        "--expectations",
        ROOT / "evals" / "packaging_expectations.json",
        "--output-dir",
        package_dir,
        "--zip",
    )
    run_script(
        "simulate_install.py",
        ROOT,
        "--package-dir",
        package_dir,
        "--install-root",
        tmp_root / "install-root",
        "--output-json",
        tmp_root / "install_simulation.json",
        "--output-md",
        tmp_root / "install_simulation.md",
        "--generated-at",
        "2026-06-13",
    )
    copy_tmp_report(tmp_root, "install_simulation")

    run_script("registry_audit.py", ROOT, "--generated-at", "2026-06-13")
    run_script("render_intent_confidence.py", ROOT)
    run_script("trust_check.py", ROOT)
    run_script("python_compat_check.py", ROOT, "--generated-at", "2026-06-13")
    run_script("render_architecture_maintainability.py", ROOT, "--generated-at", "2026-06-13")
    run_script("render_context_reports.py")
    run_script(
        "render_adoption_drift_report.py",
        ROOT,
        "--events-jsonl",
        tmp_root / "telemetry_events.jsonl",
        "--record-event",
        "skill_activation",
        "--activation-type",
        "explicit",
        "--outcome",
        "accepted",
        "--timestamp",
        "2026-06-13T10:00:00Z",
    )
    run_script(
        "build_skill_atlas.py",
        "--workspace-root",
        ROOT,
        "--output-dir",
        ROOT / "skill_atlas",
        "--report-html",
        ROOT / "reports" / "skill_atlas.html",
        "--report-json",
        ROOT / "reports" / "skill_atlas.json",
        "--today",
        "2026-06-13",
    )
    run_script(
        "upgrade_check.py",
        ROOT,
        "--previous-package-json",
        ROOT / "registry" / "examples" / "yao-meta-skill-1.0.0.json",
        "--current-package-json",
        ROOT / "reports" / "registry_audit.json",
        "--output-json",
        tmp_root / "upgrade_check.json",
        "--output-md",
        tmp_root / "upgrade_check.md",
        "--generated-at",
        "2026-06-13",
    )
    copy_tmp_report(tmp_root, "upgrade_check")

    run_script("render_review_waivers.py", ROOT, "--generated-at", "2026-06-13")
    run_script(
        "render_review_annotations.py",
        ROOT,
        "--annotations-json",
        tmp_root / "empty_review_annotations_input.json",
    )
    run_script("probe_runtime_permissions.py", ROOT, "--package-dir", package_dir)

    for script_name in [
        "render_skill_os2_audit.py",
        "render_world_class_evidence_plan.py",
        "render_world_class_evidence_ledger.py",
        "render_world_class_evidence_intake.py",
        "render_world_class_preflight.py",
        "render_world_class_submission_review.py",
        "render_world_class_operator_runbook.py",
        "render_world_class_claim_guard.py",
        "render_skill_os2_coverage.py",
    ]:
        allowed_returncodes = (0, 2) if script_name == "render_world_class_submission_review.py" else (0,)
        run_script(script_name, ROOT, "--generated-at", "2026-06-13", allowed_returncodes=allowed_returncodes)


def render_review_studio_fixture(tmp_root: Path) -> tuple[Path, Path, subprocess.CompletedProcess[str]]:
    prepare_review_studio_inputs(tmp_root)
    output_html = tmp_root / "review-studio.html"
    output_json = tmp_root / "review-studio.json"
    proc = run(
        [
            sys.executable,
            SCRIPT,
            ROOT,
            "--output-html",
            output_html,
            "--output-json",
            output_json,
        ]
    )
    return output_html, output_json, proc
