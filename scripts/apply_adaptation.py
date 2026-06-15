#!/usr/bin/env python3
"""Apply an approved adaptation patch with allowlisted targets and regression evidence."""

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Approval-gated adaptive patch application with dry-run, allowlist, regression, and rollback evidence."

BLOCKED_PATH_PARTS = {".git", "__pycache__", ".pytest_cache", "dist"}
ABSENT_FILE_SHA256 = "__absent__"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def display_path(path: Path, skill_dir: Path) -> str:
    try:
        return str(path.resolve().relative_to(skill_dir.resolve()))
    except ValueError:
        return str(path)


def resolve_path(skill_dir: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else skill_dir / path


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_patch_path(raw: str) -> str | None:
    token = raw.strip().split("\t", 1)[0].split(" ", 1)[0]
    if token == "/dev/null":
        return None
    if token.startswith("a/") or token.startswith("b/"):
        token = token[2:]
    path = Path(token)
    if path.is_absolute() or ".." in path.parts or any(part in BLOCKED_PATH_PARTS for part in path.parts):
        raise ValueError(f"Unsafe patch path: {raw}")
    if not token or token == ".":
        raise ValueError(f"Empty patch path: {raw}")
    return token


def patch_target_files(patch_text: str) -> list[str]:
    targets: set[str] = set()
    for line in patch_text.splitlines():
        if line.startswith("--- ") or line.startswith("+++ "):
            raw = line[4:].strip()
            path = normalize_patch_path(raw)
            if path:
                targets.add(path)
    return sorted(targets)


def approved_entries(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    entries = ledger.get("entries")
    return [item for item in entries if isinstance(item, dict)] if isinstance(entries, list) else []


def find_proposal(proposals: dict[str, Any], proposal_id: str) -> dict[str, Any]:
    for item in proposals.get("proposals", []):
        if isinstance(item, dict) and item.get("proposal_id") == proposal_id:
            return item
    return {}


def find_approval(ledger: dict[str, Any], proposal_id: str) -> dict[str, Any]:
    for item in approved_entries(ledger):
        if item.get("proposal_id") == proposal_id and item.get("decision") == "approved":
            return item
    return {}


def parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def validate_approval(approval: dict[str, Any], today: date) -> list[str]:
    failures = []
    required = [
        "reviewer",
        "reason",
        "approved_at",
        "patch_sha256",
        "target_files",
        "target_file_sha256",
        "verification_commands",
        "rollback_plan",
    ]
    for key in required:
        if not approval.get(key):
            failures.append(f"Approval entry missing required field: {key}")
    expires_at = parse_date(str(approval.get("expires_at", "")))
    if expires_at and expires_at < today:
        failures.append(f"Approval entry is expired: {approval.get('expires_at')}")
    if not isinstance(approval.get("target_files"), list):
        failures.append("Approval target_files must be a list.")
    if not isinstance(approval.get("target_file_sha256"), dict):
        failures.append("Approval target_file_sha256 must be an object.")
    if not isinstance(approval.get("verification_commands"), list):
        failures.append("Approval verification_commands must be a list.")
    return failures


def validate_target_file_sha256(
    skill_dir: Path,
    target_files: list[str],
    expected_sha256: dict[str, Any],
) -> tuple[list[str], dict[str, str]]:
    failures: list[str] = []
    observed: dict[str, str] = {}
    for target in target_files:
        path = skill_dir / target
        expected = str(expected_sha256.get(target, ""))
        if not expected:
            failures.append(f"Approval target_file_sha256 missing target: {target}")
            continue
        if path.exists() and not path.is_file():
            failures.append(f"Patch target is not a file: {target}")
            continue
        current = sha256_file(path) if path.exists() else ABSENT_FILE_SHA256
        observed[target] = current
        if current != expected:
            failures.append(f"Target file baseline sha256 does not match approval ledger: {target}")
    return failures, observed


def safe_command(command: str) -> tuple[bool, list[str], str]:
    try:
        parts = shlex.split(command)
    except ValueError as exc:
        return False, [], f"cannot parse command: {exc}"
    if not parts:
        return False, [], "empty command"
    if parts[0] == "make" and len(parts) == 2 and all(ch.isalnum() or ch in {"-", "_"} for ch in parts[1]):
        return True, parts, "make target"
    if parts[0] in {"python3", sys.executable} and len(parts) >= 2:
        script = Path(parts[1])
        if not script.is_absolute() and script.parts and script.parts[0] in {"tests", "scripts"} and script.suffix == ".py":
            return True, parts, "local python verifier"
    return False, parts, "command is not in the safe regression allowlist"


def run_command(command: str, skill_dir: Path) -> dict[str, Any]:
    allowed, parts, reason = safe_command(command)
    if not allowed:
        return {"command": command, "ok": False, "returncode": None, "stdout": "", "stderr": reason}
    proc = subprocess.run(parts, cwd=skill_dir, capture_output=True, text=True)
    return {
        "command": command,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-4000:],
    }


def git_apply_check(skill_dir: Path, patch_file: Path) -> dict[str, Any]:
    env = dict(os.environ)
    env["GIT_CEILING_DIRECTORIES"] = str(skill_dir.parent)
    proc = subprocess.run(["git", "apply", "--check", str(patch_file)], cwd=skill_dir, capture_output=True, text=True, env=env)
    return {"ok": proc.returncode == 0, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def git_apply(skill_dir: Path, patch_file: Path) -> dict[str, Any]:
    env = dict(os.environ)
    env["GIT_CEILING_DIRECTORIES"] = str(skill_dir.parent)
    proc = subprocess.run(["git", "apply", str(patch_file)], cwd=skill_dir, capture_output=True, text=True, env=env)
    return {"ok": proc.returncode == 0, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def git_apply_reverse(skill_dir: Path, patch_file: Path) -> dict[str, Any]:
    env = dict(os.environ)
    env["GIT_CEILING_DIRECTORIES"] = str(skill_dir.parent)
    proc = subprocess.run(["git", "apply", "-R", str(patch_file)], cwd=skill_dir, capture_output=True, text=True, env=env)
    return {"ok": proc.returncode == 0, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def empty_approval_ledger(generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "ok": True,
        "generated_at": generated_at,
        "summary": {
            "approval_count": 0,
            "active_approval_count": 0,
            "applied_count": 0,
            "rollback_count": 0,
        },
        "approval_contract": {
            "approval_required": True,
            "patch_sha256_required": True,
            "allowlisted_targets_required": True,
            "target_file_sha256_required": True,
            "dry_run_default": True,
            "writes_repository_files_only_with_apply": True,
            "rollback_required": True,
        },
        "entries": [],
    }


def empty_regression_report(skill_dir: Path, generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "ok": True,
        "generated_at": generated_at,
        "skill_dir": display_path(skill_dir, skill_dir),
        "summary": {
            "apply_supported": True,
            "attempt_count": 0,
            "applied_count": 0,
            "dry_run_count": 0,
            "rollback_count": 0,
            "regression_run_count": 0,
            "regression_pass_count": 0,
            "failure_count": 0,
        },
        "apply_contract": {
            "approval_required": True,
            "patch_sha256_required": True,
            "allowlisted_targets_required": True,
            "target_file_sha256_required": True,
            "dry_run_default": True,
            "writes_repository_files_only_with_apply": True,
            "rollback_required": True,
            "safe_regression_commands_only": True,
            "rollback_on_failure_default": True,
        },
        "attempts": [],
        "failures": [],
        "artifacts": {
            "json": "reports/adaptation_regression_report.json",
            "approval_ledger": "reports/adaptation_approval_ledger.json",
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Adaptation Regression Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- apply_supported: `{str(summary['apply_supported']).lower()}`",
        f"- attempts: `{summary['attempt_count']}`",
        f"- applied: `{summary['applied_count']}`",
        f"- dry runs: `{summary['dry_run_count']}`",
        f"- rollbacks: `{summary.get('rollback_count', 0)}`",
        f"- failures: `{summary['failure_count']}`",
        "",
        "This report proves the adaptive apply harness behavior. It does not count proposals as applied changes.",
        "",
    ]
    for attempt in report.get("attempts", []):
        lines.extend(
            [
                f"## {attempt['proposal_id']}",
                "",
                f"- mode: `{attempt['mode']}`",
                f"- status: `{attempt['status']}`",
                f"- patch: `{attempt['patch']}`",
                f"- patch sha256: `{attempt['patch_sha256']}`",
                f"- targets: `{', '.join(attempt['target_files'])}`",
                f"- rollback: {attempt['rollback']['plan']}",
            ]
        )
        if attempt.get("regression_runs"):
            lines.append("- regression:")
            lines.extend(f"  - `{item['command']}`: `{str(item['ok']).lower()}`" for item in attempt["regression_runs"])
        lines.append("")
    if report.get("failures"):
        lines.extend(["## Failures", ""])
        lines.extend(f"- {failure}" for failure in report["failures"])
    return "\n".join(lines).rstrip() + "\n"


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    skill_dir = Path(args.skill_dir).resolve()
    generated_at = args.generated_at or utc_now()
    ledger_path = resolve_path(skill_dir, args.approval_ledger)
    output_json = resolve_path(skill_dir, args.output_json)
    output_md = resolve_path(skill_dir, args.output_md)
    if args.write_template:
        ledger = empty_approval_ledger(generated_at)
        report = empty_regression_report(skill_dir, generated_at)
        write_json(ledger_path, ledger)
        write_json(output_json, report)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(render_markdown(report), encoding="utf-8")
        return report

    failures: list[str] = []
    proposals_path = resolve_path(skill_dir, args.proposals_json)
    patch_path = resolve_path(skill_dir, args.patch_file) if args.patch_file else Path("")
    proposals = load_json(proposals_path)
    ledger = load_json(ledger_path)
    if not proposals:
        failures.append(f"Proposal report missing or invalid: {display_path(proposals_path, skill_dir)}")
    if not ledger:
        failures.append(f"Approval ledger missing or invalid: {display_path(ledger_path, skill_dir)}")
    if not args.proposal_id:
        failures.append("--proposal-id is required unless --write-template is used.")
    if not args.patch_file or not patch_path.exists():
        failures.append("--patch-file must point to an existing unified diff.")

    today = parse_date(str(args.today or date.today().isoformat()))
    if today is None:
        failures.append("--today must be an ISO date when provided.")

    proposal = find_proposal(proposals, args.proposal_id) if not failures else {}
    approval = find_approval(ledger, args.proposal_id) if not failures else {}
    if not failures and not proposal:
        failures.append(f"Proposal id is not present in proposal report: {args.proposal_id}")
    if not failures and not approval:
        failures.append(f"Proposal id is not approved in the ledger: {args.proposal_id}")
    if approval:
        failures.extend(validate_approval(approval, today or date.today()))

    patch_sha = sha256_file(patch_path) if patch_path.exists() else ""
    target_files: list[str] = []
    observed_target_file_sha256: dict[str, str] = {}
    if not failures:
        try:
            target_files = patch_target_files(patch_path.read_text(encoding="utf-8", errors="replace"))
        except ValueError as exc:
            failures.append(str(exc))
    if not failures:
        approved_targets = set(str(item) for item in approval.get("target_files", []))
        proposal_targets = set(str(item) for item in proposal.get("target_files", []))
        patch_targets = set(target_files)
        if patch_sha != approval.get("patch_sha256"):
            failures.append("Patch sha256 does not match approval ledger.")
        if not patch_targets:
            failures.append("Patch does not declare any target files.")
        if not patch_targets <= approved_targets:
            failures.append("Patch touches files outside approval target_files.")
        if not patch_targets <= proposal_targets:
            failures.append("Patch touches files outside proposal target_files.")
        if not failures:
            baseline_failures, observed_target_file_sha256 = validate_target_file_sha256(
                skill_dir,
                target_files,
                approval.get("target_file_sha256", {}),
            )
            failures.extend(baseline_failures)

    check = git_apply_check(skill_dir, patch_path) if not failures else {"ok": False, "returncode": None, "stdout": "", "stderr": ""}
    if not failures and not check["ok"]:
        failures.append(f"git apply --check failed: {check['stderr'].strip()}")

    mode = "apply" if args.apply else "dry-run"
    applied = False
    apply_result = {"ok": False, "returncode": None, "stdout": "", "stderr": "not requested"}
    if not failures and args.apply:
        apply_result = git_apply(skill_dir, patch_path)
        applied = bool(apply_result["ok"])
        if not applied:
            failures.append(f"git apply failed: {apply_result['stderr'].strip()}")

    regression_runs: list[dict[str, Any]] = []
    if not failures and args.run_verification:
        for command in approval.get("verification_commands", []):
            regression_runs.append(run_command(str(command), skill_dir))
        if any(not item["ok"] for item in regression_runs):
            failures.append("One or more regression commands failed or were not allowed.")

    rollback_result = {"ok": None, "returncode": None, "stdout": "", "stderr": "not needed"}
    rolled_back = False
    if applied and failures and args.rollback_on_failure:
        rollback_result = git_apply_reverse(skill_dir, patch_path)
        rolled_back = bool(rollback_result["ok"])
        if not rolled_back:
            failures.append(f"Automatic rollback failed: {rollback_result['stderr'].strip()}")

    attempt = {
        "proposal_id": args.proposal_id or "",
        "mode": mode,
        "status": "failed-rolled-back" if rolled_back else ("failed" if failures else ("applied" if applied else "dry-run-pass")),
        "patch": display_path(patch_path, skill_dir) if args.patch_file else "",
        "patch_sha256": patch_sha,
        "target_files": target_files,
        "approval": {
            "reviewer": approval.get("reviewer", ""),
            "approved_at": approval.get("approved_at", ""),
            "expires_at": approval.get("expires_at", ""),
        },
        "target_file_sha256": {
            "expected": {
                target: str(approval.get("target_file_sha256", {}).get(target, ""))
                for target in target_files
            },
            "observed": observed_target_file_sha256,
        },
        "git_apply_check": check,
        "git_apply": apply_result,
        "regression_runs": regression_runs,
        "rollback_result": rollback_result,
        "rollback": {
            "plan": approval.get("rollback_plan", ""),
            "command": f"git apply -R {display_path(patch_path, skill_dir)}" if args.patch_file else "",
        },
    }
    report = {
        "schema_version": "1.0",
        "ok": not failures,
        "generated_at": generated_at,
        "skill_dir": display_path(skill_dir, skill_dir),
        "summary": {
            "apply_supported": True,
            "attempt_count": 1,
            "applied_count": 1 if applied and not rolled_back else 0,
            "dry_run_count": 0 if args.apply else 1,
            "rollback_count": 1 if rolled_back else 0,
            "regression_run_count": len(regression_runs),
            "regression_pass_count": sum(1 for item in regression_runs if item["ok"]),
            "failure_count": len(failures),
        },
        "apply_contract": {
            "approval_required": True,
            "patch_sha256_required": True,
            "allowlisted_targets_required": True,
            "target_file_sha256_required": True,
            "dry_run_default": True,
            "writes_repository_files_only_with_apply": True,
            "rollback_required": True,
            "safe_regression_commands_only": True,
            "rollback_on_failure_default": True,
        },
        "attempts": [attempt],
        "failures": failures,
        "artifacts": {
            "json": display_path(output_json, skill_dir),
            "markdown": display_path(output_md, skill_dir),
            "approval_ledger": display_path(ledger_path, skill_dir),
        },
    }
    write_json(output_json, report)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(render_markdown(report), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply an approved adaptation patch with review and regression evidence.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--proposal-id")
    parser.add_argument("--patch-file")
    parser.add_argument("--proposals-json", default="reports/adaptation_proposals.json")
    parser.add_argument("--approval-ledger", default="reports/adaptation_approval_ledger.json")
    parser.add_argument("--output-json", default="reports/adaptation_regression_report.json")
    parser.add_argument("--output-md", default="reports/adaptation_regression_report.md")
    parser.add_argument("--generated-at")
    parser.add_argument("--today")
    parser.add_argument("--write-template", action="store_true")
    parser.add_argument("--apply", action="store_true", help="Write the patch after every approval and allowlist check passes.")
    parser.add_argument("--run-verification", action="store_true")
    parser.add_argument(
        "--no-rollback-on-failure",
        dest="rollback_on_failure",
        action="store_false",
        help="Leave an applied patch in place if verification fails. Default is to reverse the patch.",
    )
    parser.set_defaults(rollback_on_failure=True)
    args = parser.parse_args()

    report = build_report(args)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["ok"] else 2)


if __name__ == "__main__":
    main()
