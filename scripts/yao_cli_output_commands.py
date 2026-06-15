"""Output evaluation and human-review command handlers for the Yao CLI."""

import argparse
import json

from yao_cli_config import provider_output_runner_command
from yao_cli_runtime import run_script


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by yao.py to keep output evaluation and review handlers outside the thin CLI orchestrator."


def emit_result(result: dict) -> int:
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
    return emit_result(run_script("run_output_eval.py", cmd))


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
    return emit_result(run_script("run_output_execution.py", cmd))


def command_output_review_kit(args: argparse.Namespace) -> int:
    cmd = []
    if args.blind_pack_json:
        cmd.extend(["--blind-pack-json", args.blind_pack_json])
    if args.blind_pack_md:
        cmd.extend(["--blind-pack-md", args.blind_pack_md])
    if args.decisions:
        cmd.extend(["--decisions", args.decisions])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.output_html:
        cmd.extend(["--output-html", args.output_html])
    if args.write_template:
        cmd.append("--write-template")
    return emit_result(run_script("prepare_output_review_kit.py", cmd))


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
    return emit_result(run_script("adjudicate_output_review.py", cmd))


def command_output_review_import(args: argparse.Namespace) -> int:
    cmd = ["--input", args.input]
    if args.format:
        cmd.extend(["--format", args.format])
    if args.blind_pack:
        cmd.extend(["--blind-pack", args.blind_pack])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.reviewer:
        cmd.extend(["--reviewer", args.reviewer])
    if args.reviewed_at:
        cmd.extend(["--reviewed-at", args.reviewed_at])
    if args.run_adjudication:
        cmd.append("--run-adjudication")
    if args.answer_key:
        cmd.extend(["--answer-key", args.answer_key])
    if args.adjudication_json:
        cmd.extend(["--adjudication-json", args.adjudication_json])
    if args.adjudication_md:
        cmd.extend(["--adjudication-md", args.adjudication_md])
    return emit_result(run_script("import_output_review_decisions.py", cmd))
