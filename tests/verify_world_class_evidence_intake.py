#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_world_class_evidence_intake.py"
KIT_SCRIPT = ROOT / "scripts" / "prepare_world_class_submission_kit.py"
TMP = ROOT / "tests" / "tmp_world_class_evidence_intake"


def run_intake(*extra: str) -> dict:
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(ROOT),
            "--generated-at",
            "2026-06-14",
            *extra,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def run_kit(*extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(KIT_SCRIPT),
            str(ROOT),
            "--generated-at",
            "2026-06-14",
            *extra,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def provider_submission(*, valid: bool) -> dict:
    return {
        "schema_version": "1.0",
        "evidence_key": "provider-holdout",
        "template_only": False,
        "category": "external",
        "source_type": "provider-output-eval",
        "submitted_by": "Yao provider operator",
        "submitted_at": "2026-06-14",
        "summary": "Aggregate provider-backed holdout evidence for ledger review.",
        "artifact_refs": [
            {
                "path": "reports/output_execution_runs.json",
                "kind": "aggregate-report",
                "contains_raw_content": not valid,
                "sha256": "example-only",
            }
        ],
        "provenance": {
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "credential_material_committed": False,
        },
        "privacy": {
            "raw_user_content_included": False,
            "raw_provider_prompt_included": False,
            "credentials_included": False,
            "secrets_included": False,
        },
        "anti_overclaim": {
            "planned_work_counts_as_evidence": False,
            "metadata_fallback_counts_as_native_enforcement": False,
            "pending_review_counts_as_human_decision": False,
            "local_command_runner_counts_as_provider_model": False,
        },
        "attestation": {
            "real_external_or_human_evidence": valid,
            "reviewer_or_operator_identity_present": valid,
            "artifact_refs_reviewed": valid,
            "privacy_contract_satisfied": valid,
        },
    }


def main() -> None:
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True, exist_ok=True)
    default_json = TMP / "world_class_evidence_intake.json"
    default_md = TMP / "world_class_evidence_intake.md"
    payload = run_intake("--output-json", str(default_json), "--output-md", str(default_md))
    assert payload["schema_version"] == "1.0", payload
    assert payload["ok"] is True, payload
    summary = payload["summary"]
    assert summary["decision"] == "awaiting-submissions", summary
    assert summary["schema_present"] is True, summary
    assert summary["ledger_entry_count"] == 4, summary
    assert summary["template_count"] == 4, summary
    assert summary["template_pass_count"] == 4, summary
    assert summary["submission_count"] == 0, summary
    assert summary["valid_submission_count"] == 0, summary
    assert summary["invalid_submission_count"] == 0, summary
    assert summary["operator_checklist_count"] == 4, summary
    assert summary["operator_checklist_ready_count"] == 0, summary
    assert summary["ready_for_external_collection"] is True, summary
    assert summary["ready_for_ledger_review"] is False, summary
    assert summary["ready_to_claim_world_class"] is False, summary
    assert summary["overclaim_guard_active"] is True, summary
    assert {item["evidence_key"] for item in payload["templates"]} == {
        "provider-holdout",
        "human-adjudication",
        "native-permission-enforcement",
        "native-client-telemetry",
    }, payload["templates"]
    assert all(item["status"] == "pass" and item["template_only"] is True for item in payload["templates"]), payload["templates"]
    checklist = {item["evidence_key"]: item for item in payload["operator_checklist"]}
    assert set(checklist) == {
        "provider-holdout",
        "human-adjudication",
        "native-permission-enforcement",
        "native-client-telemetry",
    }, checklist
    assert checklist["provider-holdout"]["readiness"] == "awaiting-submission", checklist["provider-holdout"]
    assert checklist["provider-holdout"]["template_path"] == "evidence/world_class/templates/provider-holdout.intake.json", checklist["provider-holdout"]
    assert checklist["provider-holdout"]["submission_path"] == "evidence/world_class/submissions/provider-holdout.json", checklist["provider-holdout"]
    assert checklist["provider-holdout"]["commands"]["prepare_submission"] == (
        "python3 scripts/yao.py world-class-submission-kit . "
        "--evidence-key provider-holdout --output-dir evidence/world_class/submissions"
    ), checklist["provider-holdout"]
    assert checklist["provider-holdout"]["commands"]["validate_intake"] == "python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions", checklist["provider-holdout"]
    assert "provider-backed model run" in checklist["provider-holdout"]["must_collect"]["provenance_requirements"], checklist["provider-holdout"]
    assert "reports/output_execution_runs.json summary.model_executed_count > 0" in checklist["provider-holdout"]["must_collect"]["success_checks"], checklist["provider-holdout"]
    assert checklist["provider-holdout"]["anti_overclaim"]["local_command_runner_counts_as_provider_model"] is False, checklist["provider-holdout"]
    markdown = default_md.read_text(encoding="utf-8")
    assert "World-Class Evidence Intake" in markdown, markdown
    assert "ready to claim world-class: `false`" in markdown, markdown
    assert "Operator Checklist" in markdown, markdown
    assert "operator checklist: `0` ready / `4` total" in markdown, markdown
    assert "`evidence/world_class/submissions/provider-holdout.json`" in markdown, markdown
    assert "`python3 scripts/yao.py world-class-submission-kit . --evidence-key provider-holdout --output-dir evidence/world_class/submissions`" in markdown, markdown
    assert "`python3 scripts/yao.py world-class-ledger .`" in markdown, markdown
    assert "Templates and planned work do not count as accepted evidence." in markdown, markdown

    kit_dir = TMP / "submission_kit"
    kit_proc = run_kit("--output-dir", str(kit_dir), "--evidence-key", "provider-holdout")
    kit_payload = json.loads(kit_proc.stdout)
    assert kit_payload["ok"] is True, kit_payload
    assert kit_payload["summary"]["decision"] == "submission-kit-ready", kit_payload["summary"]
    assert kit_payload["summary"]["requested_count"] == 1, kit_payload["summary"]
    assert kit_payload["summary"]["written_count"] == 1, kit_payload["summary"]
    assert kit_payload["summary"]["drafts_count_as_evidence"] is False, kit_payload["summary"]
    assert kit_payload["safety"]["template_only_drafts"] is True, kit_payload["safety"]
    assert kit_payload["safety"]["raw_content_allowed"] is False, kit_payload["safety"]
    assert kit_payload["files"][0]["output_path"].endswith("tests/tmp_world_class_evidence_intake/submission_kit/provider-holdout.json"), kit_payload["files"]
    kit_draft = json.loads((kit_dir / "provider-holdout.json").read_text(encoding="utf-8"))
    assert kit_draft["template_only"] is True, kit_draft
    assert kit_draft["attestation"]["real_external_or_human_evidence"] is False, kit_draft
    kit_manifest = json.loads((kit_dir / "submission_manifest.json").read_text(encoding="utf-8"))
    assert kit_manifest["summary"]["ledger_counts_submission_as_completion"] is False, kit_manifest["summary"]
    assert kit_manifest["artifacts"]["html"].endswith("tests/tmp_world_class_evidence_intake/submission_kit/index.html"), kit_manifest["artifacts"]
    kit_readme = (kit_dir / "README.md").read_text(encoding="utf-8")
    assert "Drafts are not accepted evidence." in kit_readme, kit_readme
    assert "validate intake" in kit_readme, kit_readme
    kit_html = (kit_dir / "index.html").read_text(encoding="utf-8")
    assert "<title>World-Class Evidence Submission Kit</title>" in kit_html, kit_html
    assert "Drafts are not accepted evidence" in kit_html, kit_html
    assert "provider-holdout" in kit_html, kit_html
    assert "World-Class Evidence Submission Kit" in kit_html, kit_html
    assert "Do not include credentials, raw prompts, raw outputs, transcripts, notes, or private user content." in kit_html, kit_html
    draft_intake = run_intake("--submissions-dir", str(kit_dir))
    assert draft_intake["ok"] is False, draft_intake
    assert draft_intake["summary"]["submission_count"] == 1, draft_intake["summary"]
    assert draft_intake["summary"]["invalid_submission_count"] == 1, draft_intake["summary"]
    assert draft_intake["submissions"][0]["evidence_key"] == "provider-holdout", draft_intake["submissions"]
    assert all(item["evidence_key"] != "unknown" for item in draft_intake["submissions"]), draft_intake["submissions"]

    existing_proc = run_kit("--output-dir", str(kit_dir), "--evidence-key", "provider-holdout")
    existing_payload = json.loads(existing_proc.stdout)
    assert existing_payload["summary"]["existing_count"] == 1, existing_payload["summary"]
    assert existing_payload["files"][0]["status"] == "exists", existing_payload["files"]

    valid_dir = TMP / "valid_submissions"
    valid_dir.mkdir()
    (valid_dir / "provider-holdout.json").write_text(
        json.dumps(provider_submission(valid=True), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    valid_payload = run_intake("--submissions-dir", str(valid_dir))
    assert valid_payload["ok"] is True, valid_payload
    assert valid_payload["summary"]["decision"] == "intake-ready-for-ledger-review", valid_payload["summary"]
    assert valid_payload["summary"]["valid_submission_count"] == 1, valid_payload["summary"]
    assert valid_payload["summary"]["operator_checklist_ready_count"] == 1, valid_payload["summary"]
    assert valid_payload["summary"]["ready_for_ledger_review"] is True, valid_payload["summary"]
    assert valid_payload["summary"]["ready_to_claim_world_class"] is False, valid_payload["summary"]
    assert valid_payload["submissions"][0]["status"] == "pass", valid_payload["submissions"]
    valid_checklist = {item["evidence_key"]: item for item in valid_payload["operator_checklist"]}
    assert valid_checklist["provider-holdout"]["readiness"] == "ready-for-ledger-review", valid_checklist["provider-holdout"]
    assert valid_checklist["provider-holdout"]["submission_path"].endswith("tests/tmp_world_class_evidence_intake/valid_submissions/provider-holdout.json"), valid_checklist["provider-holdout"]
    assert "tests/tmp_world_class_evidence_intake/valid_submissions" in valid_checklist["provider-holdout"]["commands"]["validate_intake"], valid_checklist["provider-holdout"]

    invalid_dir = TMP / "invalid_submissions"
    invalid_dir.mkdir()
    (invalid_dir / "provider-holdout.json").write_text(
        json.dumps(provider_submission(valid=False), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    invalid_payload = run_intake("--submissions-dir", str(invalid_dir))
    assert invalid_payload["ok"] is False, invalid_payload
    assert invalid_payload["summary"]["decision"] == "fix-intake", invalid_payload["summary"]
    assert invalid_payload["summary"]["invalid_submission_count"] == 1, invalid_payload["summary"]
    assert invalid_payload["summary"]["operator_checklist_ready_count"] == 0, invalid_payload["summary"]
    assert any("raw content" in error for error in invalid_payload["submissions"][0]["errors"]), invalid_payload["submissions"]
    assert any("attestation.real_external_or_human_evidence" in error for error in invalid_payload["submissions"][0]["errors"]), invalid_payload["submissions"]
    invalid_checklist = {item["evidence_key"]: item for item in invalid_payload["operator_checklist"]}
    assert invalid_checklist["provider-holdout"]["readiness"] == "fix-submission", invalid_checklist["provider-holdout"]
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
