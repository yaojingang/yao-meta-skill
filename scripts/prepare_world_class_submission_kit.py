#!/usr/bin/env python3
import argparse
import hashlib
import json
import shlex
from datetime import date
from pathlib import Path
from typing import Any

from render_world_class_evidence_intake import build_intake
from world_class_evidence_contract import DISALLOWED_REAL_ARTIFACTS
from world_class_repair_checklist import build_repair_checklist, summarize_repair_checklist
from world_class_source_checks import build_source_checklist, summarize_source_checklist
from world_class_submission_matrix import build_evidence_matrix, summarize_evidence_matrix
from world_class_submission_kit_rendering import render_html, render_readme


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Prepares editable world-class evidence intake packets without counting drafts as accepted evidence."


def rel_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def shell_path(path: Path, root: Path) -> str:
    return shlex.quote(rel_path(path, root))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def has_glob_pattern(value: str) -> bool:
    return any(token in value for token in ("*", "?", "["))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def requested_checklist_items(intake: dict[str, Any], evidence_keys: list[str]) -> list[dict[str, Any]]:
    items = intake.get("operator_checklist", [])
    if not evidence_keys:
        return items
    requested = set(evidence_keys)
    return [item for item in items if item.get("evidence_key") in requested]


def template_result_by_key(intake: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("evidence_key")): item for item in intake.get("templates", [])}


def artifact_rows_by_key_and_path(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    ready: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = str(row.get("evidence_key", ""))
        path = str(row.get("path", ""))
        if key and path and row.get("artifact_ref_ready"):
            ready[(key, path)] = row
    return ready


def template_artifact_ref_paths(skill_dir: Path, item: dict[str, Any]) -> set[str]:
    template_path = skill_dir / str(item.get("template_path", ""))
    errors: list[str] = []
    payload = load_template_payload(template_path, errors)
    if payload is None:
        return set()
    refs = payload.get("artifact_refs", [])
    if not isinstance(refs, list):
        return set()
    paths: set[str] = set()
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        path = str(ref.get("path", "")).strip()
        if path:
            paths.add(path)
    return paths


def load_template_payload(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        errors.append("template file is not valid JSON")
        return None
    return payload if isinstance(payload, dict) else None


def prefill_artifact_refs(
    payload: dict[str, Any],
    evidence_key: str,
    ready_rows: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, int]:
    refs = payload.get("artifact_refs", [])
    stats = {
        "prefilled_artifact_ref_count": 0,
        "unfilled_artifact_ref_count": 0,
    }
    if not isinstance(refs, list):
        return stats
    for ref in refs:
        if not isinstance(ref, dict):
            stats["unfilled_artifact_ref_count"] += 1
            continue
        path = str(ref.get("path", "")).strip()
        row = ready_rows.get((evidence_key, path))
        if row and row.get("sha256"):
            ref["sha256"] = row["sha256"]
            ref["contains_raw_content"] = False
            stats["prefilled_artifact_ref_count"] += 1
        else:
            stats["unfilled_artifact_ref_count"] += 1
    return stats


def copy_template(
    skill_dir: Path,
    output_dir: Path,
    item: dict[str, Any],
    template_results: dict[str, dict[str, Any]],
    ready_rows: dict[tuple[str, str], dict[str, Any]],
    overwrite: bool,
    prefill_artifacts: bool,
) -> dict[str, Any]:
    key = str(item.get("evidence_key", ""))
    template_result = template_results.get(key, {})
    template_path = skill_dir / str(item.get("template_path", ""))
    output_path = output_dir / f"{key}.json"
    errors: list[str] = []

    if template_result.get("status") != "pass":
        errors.append("template failed intake validation")
    if not template_path.exists():
        errors.append("template file is missing")

    if errors:
        return {
            "evidence_key": key,
            "status": "skipped",
            "template_path": rel_path(template_path, skill_dir),
            "output_path": rel_path(output_path, skill_dir),
            "prefilled_artifact_ref_count": 0,
            "unfilled_artifact_ref_count": 0,
            "errors": errors,
        }

    if output_path.exists() and not overwrite:
        return {
            "evidence_key": key,
            "status": "exists",
            "template_path": rel_path(template_path, skill_dir),
            "output_path": rel_path(output_path, skill_dir),
            "prefilled_artifact_ref_count": 0,
            "unfilled_artifact_ref_count": 0,
            "errors": [],
        }

    payload = load_template_payload(template_path, errors)
    if errors or payload is None:
        return {
            "evidence_key": key,
            "status": "skipped",
            "template_path": rel_path(template_path, skill_dir),
            "output_path": rel_path(output_path, skill_dir),
            "prefilled_artifact_ref_count": 0,
            "unfilled_artifact_ref_count": 0,
            "errors": errors or ["template file is not a JSON object"],
        }

    prefill_stats = (
        prefill_artifact_refs(payload, key, ready_rows)
        if prefill_artifacts
        else {"prefilled_artifact_ref_count": 0, "unfilled_artifact_ref_count": 0}
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, payload)
    return {
        "evidence_key": key,
        "status": "written",
        "template_path": rel_path(template_path, skill_dir),
        "output_path": rel_path(output_path, skill_dir),
        **prefill_stats,
        "errors": [],
    }


def artifact_row(skill_dir: Path, evidence_key: str, pattern: str, path: Path, status: str) -> dict[str, Any]:
    exists = path.exists()
    is_file = exists and path.is_file()
    relative = rel_path(path, skill_dir) if exists else pattern
    contains_raw_content = relative in DISALLOWED_REAL_ARTIFACTS
    digest = sha256_file(path) if is_file and not contains_raw_content else ""
    row_status = status if status else ("ready" if is_file else "missing")
    if contains_raw_content:
        row_status = "raw-content-disallowed"
    return {
        "evidence_key": evidence_key,
        "source_pattern": pattern,
        "path": relative,
        "status": row_status,
        "exists": exists,
        "is_file": is_file,
        "sha256": digest,
        "artifact_ref_ready": bool(is_file and digest and not contains_raw_content),
        "copy_path": relative if is_file else "",
        "copy_sha256": digest,
        "contains_raw_content": contains_raw_content,
        "concrete_reference_required": has_glob_pattern(pattern),
    }


def with_artifact_role(row: dict[str, Any], submission_ref_paths: set[str]) -> dict[str, Any]:
    is_submission_ref = str(row.get("path", "")) in submission_ref_paths
    return {
        **row,
        "artifact_role": "submission-ref" if is_submission_ref else "supporting-evidence",
        "submission_ref_required": is_submission_ref,
    }


def artifact_checklist_for_item(skill_dir: Path, item: dict[str, Any]) -> list[dict[str, Any]]:
    key = str(item.get("evidence_key", ""))
    must_collect = item.get("must_collect", {}) if isinstance(item.get("must_collect", {}), dict) else {}
    artifacts = must_collect.get("evidence_artifacts", [])
    if not isinstance(artifacts, list):
        return []
    submission_ref_paths = template_artifact_ref_paths(skill_dir, item)
    rows: list[dict[str, Any]] = []
    for artifact in artifacts:
        pattern = str(artifact or "").strip()
        if not pattern:
            continue
        if Path(pattern).is_absolute() or ".." in Path(pattern).parts:
            rows.append(
                with_artifact_role(
                    {
                        "evidence_key": key,
                        "source_pattern": pattern,
                        "path": pattern,
                        "status": "unsafe-path",
                        "exists": False,
                        "is_file": False,
                        "sha256": "",
                        "artifact_ref_ready": False,
                        "copy_path": "",
                        "copy_sha256": "",
                        "contains_raw_content": False,
                        "concrete_reference_required": True,
                    },
                    submission_ref_paths,
                )
            )
            continue
        if has_glob_pattern(pattern):
            matches = sorted(path for path in skill_dir.glob(pattern) if path.is_file())
            if not matches:
                rows.append(
                    with_artifact_role(
                        {
                            "evidence_key": key,
                            "source_pattern": pattern,
                            "path": pattern,
                            "status": "glob-no-match",
                            "exists": False,
                            "is_file": False,
                            "sha256": "",
                            "artifact_ref_ready": False,
                            "copy_path": "",
                            "copy_sha256": "",
                            "contains_raw_content": False,
                            "concrete_reference_required": True,
                        },
                        submission_ref_paths,
                    )
                )
                continue
            for match in matches:
                rows.append(with_artifact_role(artifact_row(skill_dir, key, pattern, match, "ready"), submission_ref_paths))
            continue
        rows.append(with_artifact_role(artifact_row(skill_dir, key, pattern, skill_dir / pattern, ""), submission_ref_paths))
    return rows


def build_artifact_checklist(skill_dir: Path, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        rows.extend(artifact_checklist_for_item(skill_dir, item))
    return rows


def build_handoff_steps(
    commands: dict[str, str],
    *,
    files: list[dict[str, Any]],
    source_blocked_count: int,
    invalid_draft_count: int,
) -> list[dict[str, Any]]:
    drafts_ready = bool(files) and invalid_draft_count == 0
    return [
        {
            "step_id": "prepare-drafts",
            "label": "Prepare editable drafts",
            "status": "ready" if drafts_ready else "fix-required",
            "command": commands["prepare_submission"],
            "completion_signal": "JSON drafts, submission_manifest.json, README.md, and index.html are present.",
            "counts_as_completion": False,
            "blocking_condition": "One or more drafts were skipped or failed template validation." if invalid_draft_count else "",
        },
        {
            "step_id": "collect-source",
            "label": "Collect real external or human evidence",
            "status": "blocked" if source_blocked_count else "ready",
            "command": "",
            "completion_signal": "Source aggregate reports satisfy the required provider, human, native, or telemetry checks.",
            "counts_as_completion": False,
            "blocking_condition": (
                f"{source_blocked_count} source check(s) still block ledger review."
                if source_blocked_count
                else ""
            ),
        },
        {
            "step_id": "edit-submission",
            "label": "Edit submission packet",
            "status": "manual",
            "command": "",
            "completion_signal": "template_only is false only after real evidence exists; ledger_reviewer_approved, ledger_reviewer, and ledger_reviewed_at stay unset until reviewer approval.",
            "counts_as_completion": False,
            "blocking_condition": "Raw prompts, outputs, transcripts, credentials, or private content must not be included.",
        },
        {
            "step_id": "validate-intake",
            "label": "Validate intake contract",
            "status": "pending",
            "command": commands["validate_intake"],
            "completion_signal": "world_class_evidence_intake reports valid submissions and no invalid packets before reviewer approval.",
            "counts_as_completion": False,
            "blocking_condition": "A valid packet is ready for ledger review but is not accepted evidence by itself.",
        },
        {
            "step_id": "review-submission",
            "label": "Review submission queue",
            "status": "pending",
            "command": commands["review_submission"],
            "completion_signal": "world_class_submission_review shows ready-for-ledger-review before reviewer identity, timestamp, and approval are set.",
            "counts_as_completion": False,
            "blocking_condition": "Reviewer queue output is advisory and cannot accept evidence.",
        },
        {
            "step_id": "refresh-ledger",
            "label": "Refresh evidence ledger",
            "status": "pending",
            "command": commands["refresh_ledger"],
            "completion_signal": "world_class_evidence_ledger accepts the evidence entry with valid source checks.",
            "counts_as_completion": False,
            "blocking_condition": "Ledger remains the only world-class readiness source of truth.",
        },
        {
            "step_id": "guard-claim",
            "label": "Guard public claim",
            "status": "pending",
            "command": commands["guard_claim"],
            "completion_signal": "world_class_claim_guard allows the public readiness claim.",
            "counts_as_completion": False,
            "blocking_condition": "Public world-class claims stay blocked until every ledger entry is accepted.",
        },
    ]


def build_submission_kit(
    skill_dir: Path,
    output_dir: Path,
    generated_at: str,
    evidence_keys: list[str] | None = None,
    overwrite: bool = False,
    prefill_artifacts: bool = False,
    output_html: Path | None = None,
) -> dict[str, Any]:
    intake = build_intake(skill_dir, generated_at, submissions_dir=output_dir)
    items = requested_checklist_items(intake, evidence_keys or [])
    valid_keys = {str(item.get("evidence_key")) for item in intake.get("operator_checklist", [])}
    unknown_keys = sorted(set(evidence_keys or []) - valid_keys)
    template_results = template_result_by_key(intake)
    artifact_checklist = build_artifact_checklist(skill_dir, items)
    ready_rows = artifact_rows_by_key_and_path(artifact_checklist)
    files = [
        copy_template(
            skill_dir,
            output_dir,
            item,
            template_results,
            ready_rows,
            overwrite,
            prefill_artifacts,
        )
        for item in items
    ]
    source_checklist = build_source_checklist(items)
    evidence_matrix = build_evidence_matrix(items, files, artifact_checklist, source_checklist)
    repair_checklist = build_repair_checklist(items, files, artifact_checklist, source_checklist, unknown_keys)
    manifest_path = output_dir / "submission_manifest.json"
    readme_path = output_dir / "README.md"
    output_html = output_html or (output_dir / "index.html")
    written_count = sum(1 for item in files if item["status"] == "written")
    existing_count = sum(1 for item in files if item["status"] == "exists")
    skipped_count = sum(1 for item in files if item["status"] == "skipped")
    prefilled_artifact_ref_count = sum(item.get("prefilled_artifact_ref_count", 0) for item in files)
    unfilled_artifact_ref_count = sum(item.get("unfilled_artifact_ref_count", 0) for item in files)
    artifact_ready_count = sum(1 for item in artifact_checklist if item.get("artifact_ref_ready"))
    artifact_missing_count = sum(1 for item in artifact_checklist if not item.get("artifact_ref_ready"))
    artifact_glob_count = sum(1 for item in artifact_checklist if item.get("concrete_reference_required"))
    submission_ref_rows = [item for item in artifact_checklist if item.get("submission_ref_required")]
    supporting_rows = [item for item in artifact_checklist if not item.get("submission_ref_required")]
    submission_ref_ready_count = sum(1 for item in submission_ref_rows if item.get("artifact_ref_ready"))
    supporting_artifact_ready_count = sum(1 for item in supporting_rows if item.get("artifact_ref_ready"))
    source_summary = summarize_source_checklist(source_checklist)
    matrix_summary = summarize_evidence_matrix(evidence_matrix)
    repair_summary = summarize_repair_checklist(repair_checklist)
    ok = not unknown_keys and skipped_count == 0
    output_dir_arg = shell_path(output_dir, skill_dir)
    requested_key_args = " ".join(f"--evidence-key {shlex.quote(key)}" for key in (evidence_keys or []))
    prepare_command = f"python3 scripts/yao.py world-class-submission-kit . --output-dir {output_dir_arg}"
    if requested_key_args:
        prepare_command = f"{prepare_command} {requested_key_args}"
    if prefill_artifacts:
        prepare_command = f"{prepare_command} --prefill-artifacts"
    commands = {
        "prepare_submission": prepare_command,
        "validate_intake": f"python3 scripts/yao.py world-class-intake . --submissions-dir {output_dir_arg}",
        "review_submission": f"python3 scripts/yao.py world-class-submission-review . --submissions-dir {output_dir_arg}",
        "refresh_ledger": f"python3 scripts/yao.py world-class-ledger . --submissions-dir {output_dir_arg}",
        "guard_claim": "python3 scripts/yao.py world-class-claim-guard .",
    }
    handoff_steps = build_handoff_steps(
        commands,
        files=files,
        source_blocked_count=source_summary["source_blocked_count"],
        invalid_draft_count=skipped_count + len(unknown_keys),
    )
    report = {
        "schema_version": "1.0",
        "ok": ok,
        "generated_at": generated_at,
        "skill_dir": rel_path(skill_dir, ROOT),
        "output_dir": rel_path(output_dir, skill_dir),
        "summary": {
            "requested_count": len(items) + len(unknown_keys),
            "prepared_count": len(files),
            "written_count": written_count,
            "existing_count": existing_count,
            "skipped_count": skipped_count,
            "unknown_key_count": len(unknown_keys),
            "artifact_checklist_count": len(artifact_checklist),
            "artifact_ready_count": artifact_ready_count,
            "artifact_missing_count": artifact_missing_count,
            "artifact_glob_expansion_count": artifact_glob_count,
            "submission_ref_count": len(submission_ref_rows),
            "submission_ref_ready_count": submission_ref_ready_count,
            "submission_ref_missing_count": len(submission_ref_rows) - submission_ref_ready_count,
            "supporting_artifact_count": len(supporting_rows),
            "supporting_artifact_ready_count": supporting_artifact_ready_count,
            "supporting_artifact_missing_count": len(supporting_rows) - supporting_artifact_ready_count,
            "artifact_prefill_enabled": prefill_artifacts,
            "artifact_ref_prefill_count": prefilled_artifact_ref_count,
            "artifact_ref_unfilled_count": unfilled_artifact_ref_count,
            **source_summary,
            **matrix_summary,
            **repair_summary,
            "handoff_step_count": len(handoff_steps),
            "handoff_blocked_count": sum(1 for item in handoff_steps if item["status"] == "blocked"),
            "handoff_fix_required_count": sum(1 for item in handoff_steps if item["status"] == "fix-required"),
            "handoff_counts_as_completion": False,
            "drafts_count_as_evidence": False,
            "ledger_counts_submission_as_completion": False,
            "decision": "submission-kit-ready" if ok else "fix-submission-kit",
        },
        "unknown_evidence_keys": unknown_keys,
        "files": files,
        "artifact_checklist": artifact_checklist,
        "source_checklist": source_checklist,
        "evidence_matrix": evidence_matrix,
        "repair_checklist": repair_checklist,
        "operator_handoff": handoff_steps,
        "evidence_items": items,
        "commands": commands,
        "safety": {
            "template_only_drafts": True,
            "artifact_prefill_counts_as_evidence": False,
            "operator_handoff_counts_as_evidence": False,
            "real_evidence_required_before_template_only_false": True,
            "raw_content_allowed": False,
            "credentials_allowed": False,
            "drafts_count_as_evidence": False,
        },
        "artifacts": {
            "manifest": rel_path(manifest_path, skill_dir),
            "readme": rel_path(readme_path, skill_dir),
            "html": rel_path(output_html, skill_dir),
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(manifest_path, report)
    readme_path.write_text(render_readme(report), encoding="utf-8")
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(render_html(report), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare editable world-class evidence submission drafts.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--output-dir", default="evidence/world_class/submission-kit")
    parser.add_argument("--evidence-key", action="append", default=[])
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--prefill-artifacts",
        action="store_true",
        help="Insert SHA-256 digests for currently available aggregate artifacts while keeping drafts template-only.",
    )
    parser.add_argument("--generated-at", default=date.today().isoformat())
    parser.add_argument("--output-html")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = skill_dir / output_dir
    report = build_submission_kit(
        skill_dir,
        output_dir.resolve(),
        args.generated_at,
        evidence_keys=args.evidence_key,
        overwrite=args.overwrite,
        prefill_artifacts=args.prefill_artifacts,
        output_html=Path(args.output_html).resolve() if args.output_html else None,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
