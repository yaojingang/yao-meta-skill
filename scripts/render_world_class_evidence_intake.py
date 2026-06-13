#!/usr/bin/env python3
import argparse
import json
import shlex
from datetime import date
from pathlib import Path
from typing import Any

from render_world_class_evidence_ledger import build_ledger


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Validates world-class human and external evidence intake packets before ledger review."

REQUIRED_TOP_LEVEL = [
    "schema_version",
    "evidence_key",
    "template_only",
    "category",
    "source_type",
    "submitted_by",
    "submitted_at",
    "summary",
    "artifact_refs",
    "provenance",
    "privacy",
    "anti_overclaim",
    "attestation",
]
REQUIRED_PRIVACY_FALSE = [
    "raw_user_content_included",
    "raw_provider_prompt_included",
    "credentials_included",
    "secrets_included",
]
REQUIRED_ANTI_OVERCLAIM_FALSE = [
    "planned_work_counts_as_evidence",
    "metadata_fallback_counts_as_native_enforcement",
    "pending_review_counts_as_human_decision",
    "local_command_runner_counts_as_provider_model",
]
REQUIRED_ATTESTATION_TRUE = [
    "real_external_or_human_evidence",
    "reviewer_or_operator_identity_present",
    "artifact_refs_reviewed",
    "privacy_contract_satisfied",
]
EXPECTED_SOURCE_TYPES = {
    "provider-holdout": "provider-output-eval",
    "human-adjudication": "blind-ab-review",
    "native-permission-enforcement": "runtime-permission-guard",
    "native-client-telemetry": "native-client-telemetry",
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def rel_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def add_error(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_artifact_refs(payload: dict[str, Any], errors: list[str]) -> None:
    refs = payload.get("artifact_refs")
    add_error(errors, isinstance(refs, list) and len(refs) > 0, "artifact_refs must contain at least one reference")
    if not isinstance(refs, list):
        return
    for index, ref in enumerate(refs):
        if not isinstance(ref, dict):
            errors.append(f"artifact_refs[{index}] must be an object")
            continue
        add_error(errors, bool(str(ref.get("path", "")).strip()), f"artifact_refs[{index}].path is required")
        add_error(errors, bool(str(ref.get("kind", "")).strip()), f"artifact_refs[{index}].kind is required")
        add_error(errors, ref.get("contains_raw_content") is False, f"artifact_refs[{index}] must not contain raw content")


def validate_evidence_specific(payload: dict[str, Any], errors: list[str]) -> None:
    key = str(payload.get("evidence_key", ""))
    provenance = payload.get("provenance", {}) if isinstance(payload.get("provenance", {}), dict) else {}
    if key == "provider-holdout":
        add_error(errors, bool(str(provenance.get("provider", "")).strip()), "provider-holdout provenance.provider is required")
        add_error(errors, bool(str(provenance.get("model", "")).strip()), "provider-holdout provenance.model is required")
        add_error(
            errors,
            provenance.get("credential_material_committed") is False,
            "provider-holdout must attest credential_material_committed is false",
        )
    elif key == "human-adjudication":
        add_error(errors, bool(str(provenance.get("reviewer", "")).strip()), "human-adjudication provenance.reviewer is required")
        add_error(
            errors,
            provenance.get("answer_key_opened_after_decisions") is True,
            "human-adjudication must attest answer_key_opened_after_decisions is true",
        )
    elif key == "native-permission-enforcement":
        add_error(errors, bool(str(provenance.get("target", "")).strip()), "native-permission-enforcement provenance.target is required")
        add_error(
            errors,
            bool(str(provenance.get("guard_location", "")).strip()),
            "native-permission-enforcement provenance.guard_location is required",
        )
        add_error(
            errors,
            provenance.get("metadata_fallback_retained_for_other_targets") is True,
            "native-permission-enforcement must retain metadata fallback for non-native targets",
        )
    elif key == "native-client-telemetry":
        add_error(errors, bool(str(provenance.get("client", "")).strip()), "native-client-telemetry provenance.client is required")
        add_error(errors, provenance.get("event_source") == "external", "native-client-telemetry event_source must be external")
        add_error(errors, provenance.get("metadata_only") is True, "native-client-telemetry must be metadata_only")


def validate_payload(
    payload: dict[str, Any],
    entry: dict[str, Any],
    *,
    path: Path,
    root: Path,
    template_expected: bool,
) -> dict[str, Any]:
    errors: list[str] = []
    for key in REQUIRED_TOP_LEVEL:
        add_error(errors, key in payload, f"missing {key}")
    evidence_key = str(entry.get("key", ""))
    add_error(errors, payload.get("schema_version") == "1.0", "schema_version must be 1.0")
    add_error(errors, payload.get("evidence_key") == evidence_key, f"evidence_key must be {evidence_key}")
    add_error(errors, payload.get("template_only") is template_expected, f"template_only must be {str(template_expected).lower()}")
    add_error(errors, payload.get("category") == entry.get("category"), f"category must be {entry.get('category')}")
    add_error(
        errors,
        payload.get("source_type") == EXPECTED_SOURCE_TYPES.get(evidence_key),
        f"source_type must be {EXPECTED_SOURCE_TYPES.get(evidence_key)}",
    )
    add_error(errors, bool(str(payload.get("submitted_by", "")).strip()), "submitted_by is required")
    add_error(errors, bool(str(payload.get("submitted_at", "")).strip()), "submitted_at is required")
    add_error(errors, bool(str(payload.get("summary", "")).strip()), "summary is required")
    validate_artifact_refs(payload, errors)
    privacy = payload.get("privacy", {}) if isinstance(payload.get("privacy", {}), dict) else {}
    for key in REQUIRED_PRIVACY_FALSE:
        add_error(errors, privacy.get(key) is False, f"privacy.{key} must be false")
    anti_overclaim = payload.get("anti_overclaim", {}) if isinstance(payload.get("anti_overclaim", {}), dict) else {}
    for key in REQUIRED_ANTI_OVERCLAIM_FALSE:
        add_error(errors, anti_overclaim.get(key) is False, f"anti_overclaim.{key} must be false")
    validate_evidence_specific(payload, errors)
    attestation = payload.get("attestation", {}) if isinstance(payload.get("attestation", {}), dict) else {}
    if not template_expected:
        for key in REQUIRED_ATTESTATION_TRUE:
            add_error(errors, attestation.get(key) is True, f"attestation.{key} must be true for a real submission")
    return {
        "path": rel_path(path, root),
        "evidence_key": evidence_key,
        "status": "pass" if not errors else "fail",
        "template_only": template_expected,
        "errors": errors,
    }


def template_paths(skill_dir: Path, keys: list[str]) -> dict[str, Path]:
    template_dir = skill_dir / "evidence" / "world_class" / "templates"
    return {key: template_dir / f"{key}.intake.json" for key in keys}


def submission_paths(submissions_dir: Path) -> list[Path]:
    if not submissions_dir.exists():
        return []
    ignored_names = {"submission_manifest.json"}
    return sorted(path for path in submissions_dir.glob("*.json") if path.is_file() and path.name not in ignored_names)


def find_entry(entries: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    for entry in entries:
        if entry.get("key") == key:
            return entry
    return None


def first_by_key(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for item in items:
        key = str(item.get("evidence_key", ""))
        if key and key not in by_key:
            by_key[key] = item
    return by_key


def shell_path(path: Path, root: Path) -> str:
    return shlex.quote(rel_path(path, root))


def checklist_readiness(
    entry: dict[str, Any],
    template_result: dict[str, Any] | None,
    submission_result: dict[str, Any] | None,
) -> tuple[str, str]:
    if entry.get("status") == "accepted":
        return "accepted", "Ledger already accepts this evidence item."
    if template_result is None or template_result.get("status") != "pass":
        return "fix-template", "The intake template is missing or invalid."
    if submission_result is None:
        return "awaiting-submission", "No real evidence submission has been provided yet."
    if submission_result.get("status") == "pass":
        return "ready-for-ledger-review", "Submission passes intake validation and is ready for ledger review."
    return "fix-submission", "Submission exists but failed intake validation."


def build_operator_checklist(
    skill_dir: Path,
    ledger: dict[str, Any],
    template_results: list[dict[str, Any]],
    submission_results: list[dict[str, Any]],
    submissions_dir: Path,
) -> list[dict[str, Any]]:
    templates_by_key = first_by_key(template_results)
    submissions_by_key = first_by_key(submission_results)
    checklist = []
    for entry in ledger.get("entries", []):
        key = str(entry.get("key", ""))
        template_path = skill_dir / "evidence" / "world_class" / "templates" / f"{key}.intake.json"
        submission_path = submissions_dir / f"{key}.json"
        template_result = templates_by_key.get(key)
        submission_result = submissions_by_key.get(key)
        readiness, blocking_reason = checklist_readiness(entry, template_result, submission_result)
        submissions_dir_arg = shell_path(submissions_dir, skill_dir)
        checklist.append(
            {
                "evidence_key": key,
                "label": entry.get("label", key),
                "category": entry.get("category", "external"),
                "owner": entry.get("owner", "release reviewer"),
                "readiness": readiness,
                "blocking_reason": blocking_reason,
                "template_status": template_result.get("status", "missing") if template_result else "missing",
                "submission_status": submission_result.get("status", "missing") if submission_result else "missing",
                "template_path": rel_path(template_path, skill_dir),
                "submission_path": rel_path(submission_path, skill_dir),
                "commands": {
                    "prepare_submission": (
                        "python3 scripts/yao.py world-class-submission-kit . "
                        f"--evidence-key {shlex.quote(key)} --output-dir {shell_path(submission_path.parent, skill_dir)}"
                    ),
                    "validate_intake": f"python3 scripts/yao.py world-class-intake . --submissions-dir {submissions_dir_arg}",
                    "refresh_ledger": "python3 scripts/yao.py world-class-ledger .",
                    "guard_claim": "python3 scripts/yao.py world-class-claim-guard .",
                },
                "must_collect": {
                    "provenance_requirements": entry.get("provenance_requirements", []),
                    "success_checks": entry.get("success_checks", []),
                    "evidence_artifacts": entry.get("evidence_artifacts", []),
                    "privacy_contract": entry.get("privacy_contract", []),
                },
                "anti_overclaim": entry.get("anti_overclaim", {}),
                "next_action": entry.get("next_action", ""),
            }
        )
    return checklist


def build_intake(skill_dir: Path, generated_at: str, submissions_dir: Path | None = None) -> dict[str, Any]:
    ledger = build_ledger(skill_dir, generated_at)
    entries = ledger.get("entries", [])
    keys = [str(entry.get("key", "")) for entry in entries]
    schema_path = skill_dir / "evidence" / "world_class" / "intake.schema.json"
    template_results = []
    for key, path in template_paths(skill_dir, keys).items():
        entry = find_entry(entries, key) or {"key": key, "category": "external"}
        payload = load_json(path)
        if not payload:
            template_results.append(
                {
                    "path": rel_path(path, skill_dir),
                    "evidence_key": key,
                    "status": "fail",
                    "template_only": True,
                    "errors": ["template missing or invalid JSON"],
                }
            )
            continue
        template_results.append(validate_payload(payload, entry, path=path, root=skill_dir, template_expected=True))

    submissions_dir = submissions_dir or (skill_dir / "evidence" / "world_class" / "submissions")
    submission_results = []
    for path in submission_paths(submissions_dir):
        payload = load_json(path)
        key = str(payload.get("evidence_key", ""))
        entry = find_entry(entries, key)
        if not payload or entry is None:
            submission_results.append(
                {
                    "path": rel_path(path, skill_dir),
                    "evidence_key": key or "unknown",
                    "status": "fail",
                    "template_only": False,
                    "errors": ["submission missing, invalid JSON, or unknown evidence_key"],
                }
            )
            continue
        submission_results.append(validate_payload(payload, entry, path=path, root=skill_dir, template_expected=False))

    template_pass_count = sum(1 for item in template_results if item["status"] == "pass")
    valid_submission_count = sum(1 for item in submission_results if item["status"] == "pass")
    invalid_submission_count = sum(1 for item in submission_results if item["status"] == "fail")
    schema_exists = schema_path.exists()
    intake_ready = schema_exists and template_pass_count == len(keys) and invalid_submission_count == 0
    operator_checklist = build_operator_checklist(skill_dir, ledger, template_results, submission_results, submissions_dir)
    ready_checklist_count = sum(1 for item in operator_checklist if item["readiness"] in {"accepted", "ready-for-ledger-review"})
    return {
        "schema_version": "1.0",
        "ok": intake_ready,
        "generated_at": generated_at,
        "skill_dir": rel_path(skill_dir, ROOT),
        "summary": {
            "schema_present": schema_exists,
            "ledger_entry_count": len(keys),
            "template_count": len(template_results),
            "template_pass_count": template_pass_count,
            "submission_count": len(submission_results),
            "valid_submission_count": valid_submission_count,
            "invalid_submission_count": invalid_submission_count,
            "operator_checklist_count": len(operator_checklist),
            "operator_checklist_ready_count": ready_checklist_count,
            "ready_for_external_collection": intake_ready,
            "ready_for_ledger_review": valid_submission_count > 0 and invalid_submission_count == 0,
            "ready_to_claim_world_class": ledger.get("summary", {}).get("ready_to_claim_world_class") is True,
            "overclaim_guard_active": True,
            "decision": (
                "fix-intake"
                if not intake_ready
                else ("intake-ready-for-ledger-review" if valid_submission_count else "awaiting-submissions")
            ),
        },
        "schema": rel_path(schema_path, skill_dir),
        "templates": template_results,
        "submissions": submission_results,
        "operator_checklist": operator_checklist,
        "source_ledger": {
            "json": "reports/world_class_evidence_ledger.json",
            "markdown": "reports/world_class_evidence_ledger.md",
            "pending_count": ledger.get("summary", {}).get("pending_count", 0),
        },
        "artifacts": {
            "json": "reports/world_class_evidence_intake.json",
            "markdown": "reports/world_class_evidence_intake.md",
        },
    }


def render_table(items: list[dict[str, Any]]) -> list[str]:
    lines = ["| Evidence | Status | Path | Errors |", "| --- | --- | --- | --- |"]
    if not items:
        lines.append("| `none` | `n/a` | none | none |")
        return lines
    for item in items:
        errors = "; ".join(item.get("errors", [])) or "none"
        safe_errors = errors.replace("|", "\\|")
        lines.append(f"| `{item['evidence_key']}` | `{item['status']}` | `{item['path']}` | {safe_errors} |")
    return lines


def render_operator_checklist(items: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Evidence | Readiness | Submission | Next action |",
        "| --- | --- | --- | --- |",
    ]
    if not items:
        lines.append("| `none` | `accepted` | none | none |")
        return lines
    for item in items:
        action = str(item.get("next_action", "")).replace("|", "\\|")
        lines.append(
            f"| `{item['evidence_key']}` | `{item['readiness']}` | `{item['submission_status']}` | {action} |"
        )
    for item in items:
        lines.extend(["", f"### {item['label']}", ""])
        lines.append(f"- readiness: `{item['readiness']}`")
        lines.append(f"- blocking reason: {item['blocking_reason']}")
        lines.append(f"- owner: {item['owner']}")
        lines.append(f"- template: `{item['template_path']}`")
        lines.append(f"- submission: `{item['submission_path']}`")
        lines.extend(["", "#### Commands", ""])
        commands = item.get("commands", {})
        for label in ["prepare_submission", "validate_intake", "refresh_ledger", "guard_claim"]:
            if commands.get(label):
                lines.append(f"- {label}: `{commands[label]}`")
        must_collect = item.get("must_collect", {})
        lines.extend(["", "#### Must Collect", ""])
        for label in ["provenance_requirements", "success_checks", "evidence_artifacts", "privacy_contract"]:
            values = must_collect.get(label, [])
            if values:
                lines.append(f"- {label}:")
                lines.extend(f"  - {value}" for value in values)
    return lines


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# World-Class Evidence Intake",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- decision: `{summary['decision']}`",
        f"- schema present: `{str(summary['schema_present']).lower()}`",
        f"- templates: `{summary['template_pass_count']}` / `{summary['template_count']}`",
        f"- submissions: `{summary['valid_submission_count']}` valid / `{summary['submission_count']}` total",
        f"- invalid submissions: `{summary['invalid_submission_count']}`",
        f"- operator checklist: `{summary['operator_checklist_ready_count']}` ready / `{summary['operator_checklist_count']}` total",
        f"- ready for external collection: `{str(summary['ready_for_external_collection']).lower()}`",
        f"- ready for ledger review: `{str(summary['ready_for_ledger_review']).lower()}`",
        f"- ready to claim world-class: `{str(summary['ready_to_claim_world_class']).lower()}`",
        f"- overclaim guard active: `{str(summary['overclaim_guard_active']).lower()}`",
        "",
        "This report validates the intake contract for human and external evidence. A valid intake packet means the evidence is ready for ledger review; it does not by itself make a world-class claim true.",
        "",
        "## Templates",
        "",
        *render_table(report["templates"]),
        "",
        "## Submissions",
        "",
        *render_table(report["submissions"]),
        "",
        "## Operator Checklist",
        "",
        *render_operator_checklist(report["operator_checklist"]),
        "",
        "## Boundary",
        "",
        "- Templates and planned work do not count as accepted evidence.",
        "- Local command-runner output does not count as provider-backed model evidence.",
        "- Metadata fallback does not count as native permission enforcement.",
        "- Pending reviewer work does not count as human adjudication.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate world-class evidence intake packets.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--submissions-dir")
    parser.add_argument("--output-json", default="reports/world_class_evidence_intake.json")
    parser.add_argument("--output-md", default="reports/world_class_evidence_intake.md")
    parser.add_argument("--generated-at", default=date.today().isoformat())
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    submissions_dir = Path(args.submissions_dir).resolve() if args.submissions_dir else None
    report = build_intake(skill_dir, args.generated_at, submissions_dir)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    if not output_json.is_absolute():
        output_json = skill_dir / output_json
    if not output_md.is_absolute():
        output_md = skill_dir / output_md
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
