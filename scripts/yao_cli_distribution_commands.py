"""Distribution, packaging, and runtime-gate command handlers for the Yao CLI."""

import argparse
import json
from pathlib import Path

from yao_cli_runtime import run_script


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by yao.py to keep distribution and runtime gate handlers outside the thin CLI orchestrator."


def emit_result(result: dict) -> int:
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_skill_ir(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.validate_only:
        cmd.append("--validate-only")
    return emit_result(run_script("export_skill_ir.py", cmd))


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
    return emit_result(run_script("compile_skill.py", cmd))


def command_conformance(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    for target in args.target or []:
        cmd.extend(["--target", target])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    return emit_result(run_script("run_conformance_suite.py", cmd))


def command_runtime_permissions(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    if args.package_dir:
        cmd.extend(["--package-dir", args.package_dir])
    for target in args.target or []:
        cmd.extend(["--target", target])
    if getattr(args, "install_simulation_json", None):
        cmd.extend(["--install-simulation-json", args.install_simulation_json])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    return emit_result(run_script("probe_runtime_permissions.py", cmd))


def command_trust(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    return emit_result(run_script("trust_check.py", cmd))


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
    return emit_result(run_script("build_skill_atlas.py", cmd))


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
    return emit_result(run_script("registry_audit.py", cmd))


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
    return emit_result(run_script("verify_package.py", cmd))


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
    return emit_result(run_script("simulate_install.py", cmd))


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
    return emit_result(run_script("upgrade_check.py", cmd))


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
    return emit_result(run_script("cross_packager.py", cmd))
