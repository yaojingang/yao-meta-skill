#!/usr/bin/env python3
import argparse
import json
import shutil
from datetime import date
from pathlib import Path
from typing import Any

from render_world_class_evidence_intake import build_intake


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Prepares editable world-class evidence intake packets without counting drafts as accepted evidence."


def rel_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def requested_checklist_items(intake: dict[str, Any], evidence_keys: list[str]) -> list[dict[str, Any]]:
    items = intake.get("operator_checklist", [])
    if not evidence_keys:
        return items
    requested = set(evidence_keys)
    return [item for item in items if item.get("evidence_key") in requested]


def template_result_by_key(intake: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("evidence_key")): item for item in intake.get("templates", [])}


def copy_template(
    skill_dir: Path,
    output_dir: Path,
    item: dict[str, Any],
    template_results: dict[str, dict[str, Any]],
    overwrite: bool,
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
            "errors": errors,
        }

    if output_path.exists() and not overwrite:
        return {
            "evidence_key": key,
            "status": "exists",
            "template_path": rel_path(template_path, skill_dir),
            "output_path": rel_path(output_path, skill_dir),
            "errors": [],
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template_path, output_path)
    return {
        "evidence_key": key,
        "status": "written",
        "template_path": rel_path(template_path, skill_dir),
        "output_path": rel_path(output_path, skill_dir),
        "errors": [],
    }


def render_readme(report: dict[str, Any]) -> str:
    commands = report["commands"]
    lines = [
        "# World-Class Evidence Submission Kit",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "This kit contains editable drafts for human and external evidence packets. Drafts are not accepted evidence.",
        "",
        "## Workflow",
        "",
        "1. Run the real provider, human review, native permission, or native client telemetry work first.",
        "2. Edit the matching JSON draft with only aggregate artifact references and provenance metadata.",
        "3. Set `template_only` to `false` only after real evidence exists.",
        "4. Set attestation booleans truthfully; do not include credentials, raw prompts, raw outputs, transcripts, notes, or private user content.",
        "5. Validate the packet before asking the ledger reviewer to accept it.",
        "",
        "## Commands",
        "",
        f"- validate intake: `{commands['validate_intake']}`",
        f"- refresh ledger: `{commands['refresh_ledger']}`",
        f"- guard public claims: `{commands['guard_claim']}`",
        "",
        "## Drafts",
        "",
        "| Evidence | Draft | Status |",
        "| --- | --- | --- |",
    ]
    for item in report["files"]:
        lines.append(f"| `{item['evidence_key']}` | `{item['output_path']}` | `{item['status']}` |")
    lines.extend(
        [
            "",
            "## Anti-Overclaim",
            "",
            "- This kit never marks ledger evidence as accepted.",
            "- Planned work, metadata fallback, pending review, and local command-runner output remain non-evidence.",
            "- A valid intake packet means ready for ledger review, not world-class completion.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_submission_kit(
    skill_dir: Path,
    output_dir: Path,
    generated_at: str,
    evidence_keys: list[str] | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    intake = build_intake(skill_dir, generated_at, submissions_dir=output_dir)
    items = requested_checklist_items(intake, evidence_keys or [])
    valid_keys = {str(item.get("evidence_key")) for item in intake.get("operator_checklist", [])}
    unknown_keys = sorted(set(evidence_keys or []) - valid_keys)
    template_results = template_result_by_key(intake)
    files = [copy_template(skill_dir, output_dir, item, template_results, overwrite) for item in items]
    manifest_path = output_dir / "submission_manifest.json"
    readme_path = output_dir / "README.md"
    written_count = sum(1 for item in files if item["status"] == "written")
    existing_count = sum(1 for item in files if item["status"] == "exists")
    skipped_count = sum(1 for item in files if item["status"] == "skipped")
    ok = not unknown_keys and skipped_count == 0
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
            "drafts_count_as_evidence": False,
            "ledger_counts_submission_as_completion": False,
            "decision": "submission-kit-ready" if ok else "fix-submission-kit",
        },
        "unknown_evidence_keys": unknown_keys,
        "files": files,
        "commands": {
            "validate_intake": f"python3 scripts/yao.py world-class-intake . --submissions-dir {rel_path(output_dir, skill_dir)}",
            "refresh_ledger": f"python3 scripts/yao.py world-class-ledger . --submissions-dir {rel_path(output_dir, skill_dir)}",
            "guard_claim": "python3 scripts/yao.py world-class-claim-guard .",
        },
        "safety": {
            "template_only_drafts": True,
            "real_evidence_required_before_template_only_false": True,
            "raw_content_allowed": False,
            "credentials_allowed": False,
            "drafts_count_as_evidence": False,
        },
        "artifacts": {
            "manifest": rel_path(manifest_path, skill_dir),
            "readme": rel_path(readme_path, skill_dir),
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(manifest_path, report)
    readme_path.write_text(render_readme(report), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare editable world-class evidence submission drafts.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--output-dir", default="evidence/world_class/submission-kit")
    parser.add_argument("--evidence-key", action="append", default=[])
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--generated-at", default=date.today().isoformat())
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
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
