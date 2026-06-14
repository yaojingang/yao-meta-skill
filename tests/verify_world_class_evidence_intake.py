#!/usr/bin/env python3
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_world_class_evidence_intake.py"
KIT_SCRIPT = ROOT / "scripts" / "prepare_world_class_submission_kit.py"
TMP = ROOT / "tests" / "tmp_world_class_evidence_intake"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def provider_submission(*, valid: bool, artifact_path: str = "reports/output_execution_runs.json") -> dict:
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
                "path": artifact_path,
                "kind": "aggregate-report",
                "contains_raw_content": not valid,
                "sha256": sha256_file(ROOT / artifact_path) if valid else "example-only",
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


def assert_documented_submission_commands() -> None:
    expected_fragments = [
        'SUBMISSIONS_DIR="${SUBMISSIONS_DIR:-evidence/world_class/submissions}"',
        'world-class-submission-kit . --output-dir "$SUBMISSIONS_DIR"',
        'world-class-intake . --submissions-dir "$SUBMISSIONS_DIR"',
        'world-class-submission-review . --submissions-dir "$SUBMISSIONS_DIR"',
        'world-class-ledger . --submissions-dir "$SUBMISSIONS_DIR"',
    ]
    for relative_path in ("README.md", "evidence/world_class/README.md"):
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for fragment in expected_fragments:
            assert fragment in text, (relative_path, fragment)
        assert "/tmp/yao-world-class-submission-kit" not in text, relative_path


def main() -> None:
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True, exist_ok=True)
    assert_documented_submission_commands()
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
    assert summary["valid_packet_source_incomplete_count"] == 0, summary
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
    assert checklist["provider-holdout"]["commands"]["submission_review"] == "python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions", checklist["provider-holdout"]
    assert checklist["provider-holdout"]["commands"]["refresh_ledger"] == "python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions", checklist["provider-holdout"]
    assert "provider-backed model run" in checklist["provider-holdout"]["must_collect"]["provenance_requirements"], checklist["provider-holdout"]
    assert "reports/output_execution_runs.json summary.model_executed_count > 0" in checklist["provider-holdout"]["must_collect"]["success_checks"], checklist["provider-holdout"]
    assert checklist["provider-holdout"]["anti_overclaim"]["local_command_runner_counts_as_provider_model"] is False, checklist["provider-holdout"]
    assert checklist["provider-holdout"]["source_accepted"] is False, checklist["provider-holdout"]
    assert checklist["provider-holdout"]["observed_state"]["model_executed_count"] == 0, checklist["provider-holdout"]
    assert checklist["provider-holdout"]["observed_state"]["timing_observed_count"] > 0, checklist["provider-holdout"]
    markdown = default_md.read_text(encoding="utf-8")
    assert "World-Class Evidence Intake" in markdown, markdown
    assert "ready to claim world-class: `false`" in markdown, markdown
    assert "Operator Checklist" in markdown, markdown
    assert "valid packet but source incomplete: `0`" in markdown, markdown
    assert "operator checklist: `0` ready / `4` total" in markdown, markdown
    assert "0 existing / 0 sha256 verified / 0 required verified / 1 refs" in markdown, markdown
    assert "`evidence/world_class/submissions/provider-holdout.json`" in markdown, markdown
    assert "`python3 scripts/yao.py world-class-submission-kit . --evidence-key provider-holdout --output-dir evidence/world_class/submissions`" in markdown, markdown
    assert "`python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions`" in markdown, markdown
    assert "`python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions`" in markdown, markdown
    assert "Templates and planned work do not count as accepted evidence." in markdown, markdown
    assert "Real submissions must include the evidence-key critical artifact paths with verified SHA-256 digests." in markdown, markdown
    assert "Real submissions must replace template submitter, date, and provenance placeholders with concrete evidence metadata." in markdown, markdown

    kit_dir = TMP / "submission_kit"
    kit_proc = run_kit("--output-dir", str(kit_dir), "--evidence-key", "provider-holdout")
    kit_payload = json.loads(kit_proc.stdout)
    assert kit_payload["ok"] is True, kit_payload
    assert kit_payload["summary"]["decision"] == "submission-kit-ready", kit_payload["summary"]
    assert kit_payload["summary"]["requested_count"] == 1, kit_payload["summary"]
    assert kit_payload["summary"]["written_count"] == 1, kit_payload["summary"]
    assert kit_payload["summary"]["artifact_checklist_count"] >= 1, kit_payload["summary"]
    assert kit_payload["summary"]["artifact_ready_count"] >= 1, kit_payload["summary"]
    assert kit_payload["summary"]["source_check_count"] == 3, kit_payload["summary"]
    assert kit_payload["summary"]["source_pass_count"] == 1, kit_payload["summary"]
    assert kit_payload["summary"]["source_blocked_count"] == 2, kit_payload["summary"]
    assert kit_payload["summary"]["drafts_count_as_evidence"] is False, kit_payload["summary"]
    assert kit_payload["safety"]["template_only_drafts"] is True, kit_payload["safety"]
    assert kit_payload["safety"]["raw_content_allowed"] is False, kit_payload["safety"]
    assert kit_payload["files"][0]["output_path"].endswith("tests/tmp_world_class_evidence_intake/submission_kit/provider-holdout.json"), kit_payload["files"]
    artifact_rows = {item["path"]: item for item in kit_payload["artifact_checklist"]}
    assert "reports/output_execution_runs.json" in artifact_rows, artifact_rows
    assert artifact_rows["reports/output_execution_runs.json"]["artifact_ref_ready"] is True, artifact_rows
    assert len(artifact_rows["reports/output_execution_runs.json"]["sha256"]) == 64, artifact_rows
    assert artifact_rows["reports/output_execution_runs.json"]["contains_raw_content"] is False, artifact_rows
    source_rows = {item["field"]: item for item in kit_payload["source_checklist"]}
    assert source_rows["model_executed_count"]["status"] == "blocked", source_rows
    assert source_rows["model_executed_count"]["actual"] == 0, source_rows
    assert source_rows["timing_observed_count"]["status"] == "pass", source_rows
    assert source_rows["token_observed_count"]["status"] == "blocked", source_rows
    kit_draft = json.loads((kit_dir / "provider-holdout.json").read_text(encoding="utf-8"))
    assert kit_draft["template_only"] is True, kit_draft
    assert kit_draft["attestation"]["real_external_or_human_evidence"] is False, kit_draft
    kit_manifest = json.loads((kit_dir / "submission_manifest.json").read_text(encoding="utf-8"))
    assert kit_manifest["summary"]["ledger_counts_submission_as_completion"] is False, kit_manifest["summary"]
    assert kit_manifest["artifact_checklist"] == kit_payload["artifact_checklist"], kit_manifest["artifact_checklist"]
    assert kit_manifest["source_checklist"] == kit_payload["source_checklist"], kit_manifest["source_checklist"]
    assert kit_manifest["artifacts"]["html"].endswith("tests/tmp_world_class_evidence_intake/submission_kit/index.html"), kit_manifest["artifacts"]
    kit_readme = (kit_dir / "README.md").read_text(encoding="utf-8")
    assert "Drafts are not accepted evidence." in kit_readme, kit_readme
    assert "validate intake" in kit_readme, kit_readme
    assert "Artifact Checklist" in kit_readme, kit_readme
    assert "Source Evidence Snapshot" in kit_readme, kit_readme
    assert "reports/output_execution_runs.json" in kit_readme, kit_readme
    assert "Provider model run" in kit_readme, kit_readme
    kit_html = (kit_dir / "index.html").read_text(encoding="utf-8")
    assert "<title>World-Class Evidence Submission Kit</title>" in kit_html, kit_html
    assert "Drafts are not accepted evidence" in kit_html, kit_html
    assert "provider-holdout" in kit_html, kit_html
    assert "Artifact Checklist" in kit_html, kit_html
    assert "Source Evidence Snapshot" in kit_html, kit_html
    assert "<dt>Field</dt><dd><code>model_executed_count</code></dd>" in kit_html, kit_html
    assert "<dt>Current</dt><dd><code>0</code></dd>" in kit_html, kit_html
    assert "<dt>Expected</dt><dd><code>&gt;0</code></dd>" in kit_html, kit_html
    assert "World-Class Evidence Submission Kit" in kit_html, kit_html
    assert "Do not include credentials, raw prompts, raw outputs, transcripts, notes, or private user content." in kit_html, kit_html

    native_kit_dir = TMP / "native_permission_kit"
    native_kit_proc = run_kit("--output-dir", str(native_kit_dir), "--evidence-key", "native-permission-enforcement")
    native_kit_payload = json.loads(native_kit_proc.stdout)
    native_rows = {item["path"]: item for item in native_kit_payload["artifact_checklist"]}
    assert native_kit_payload["summary"]["artifact_glob_expansion_count"] >= 1, native_kit_payload["summary"]
    if "dist/targets/openai/adapter.json" in native_rows:
        assert native_rows["dist/targets/openai/adapter.json"]["source_pattern"] == "dist/targets/*/adapter.json", native_rows
        assert native_rows["dist/targets/openai/adapter.json"]["artifact_ref_ready"] is True, native_rows
        assert len(native_rows["dist/targets/openai/adapter.json"]["sha256"]) == 64, native_rows
    else:
        glob_rows = [
            item for item in native_kit_payload["artifact_checklist"]
            if item["source_pattern"] == "dist/targets/*/adapter.json"
        ]
        assert len(glob_rows) == 1, glob_rows
        assert glob_rows[0]["status"] == "glob-no-match", glob_rows[0]
        assert glob_rows[0]["artifact_ref_ready"] is False, glob_rows[0]
        assert glob_rows[0]["concrete_reference_required"] is True, glob_rows[0]
    native_readme = (native_kit_dir / "README.md").read_text(encoding="utf-8")
    assert "Glob patterns are expanded into concrete files" in native_readme, native_readme
    draft_intake = run_intake("--submissions-dir", str(kit_dir))
    assert draft_intake["ok"] is False, draft_intake
    assert draft_intake["summary"]["submission_count"] == 1, draft_intake["summary"]
    assert draft_intake["summary"]["invalid_submission_count"] == 1, draft_intake["summary"]
    assert draft_intake["submissions"][0]["evidence_key"] == "provider-holdout", draft_intake["submissions"]
    assert all(item["evidence_key"] != "unknown" for item in draft_intake["submissions"]), draft_intake["submissions"]

    spaced_kit_dir = TMP / "submission kit spaced"
    spaced_kit_proc = run_kit("--output-dir", str(spaced_kit_dir), "--evidence-key", "provider-holdout")
    spaced_kit_payload = json.loads(spaced_kit_proc.stdout)
    quoted_spaced_dir = "'tests/tmp_world_class_evidence_intake/submission kit spaced'"
    assert quoted_spaced_dir in spaced_kit_payload["commands"]["validate_intake"], spaced_kit_payload["commands"]
    assert quoted_spaced_dir in spaced_kit_payload["commands"]["refresh_ledger"], spaced_kit_payload["commands"]
    spaced_readme = (spaced_kit_dir / "README.md").read_text(encoding="utf-8")
    assert quoted_spaced_dir in spaced_readme, spaced_readme

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
    assert valid_payload["summary"]["decision"] == "source-evidence-incomplete", valid_payload["summary"]
    assert valid_payload["summary"]["valid_submission_count"] == 1, valid_payload["summary"]
    assert valid_payload["summary"]["valid_packet_source_incomplete_count"] == 1, valid_payload["summary"]
    assert valid_payload["summary"]["operator_checklist_ready_count"] == 0, valid_payload["summary"]
    assert valid_payload["summary"]["ready_for_ledger_review"] is False, valid_payload["summary"]
    assert valid_payload["summary"]["ready_to_claim_world_class"] is False, valid_payload["summary"]
    assert valid_payload["submissions"][0]["status"] == "pass", valid_payload["submissions"]
    assert valid_payload["submissions"][0]["artifact_integrity"]["artifact_existing_count"] == 1, valid_payload["submissions"]
    assert valid_payload["submissions"][0]["artifact_integrity"]["artifact_sha256_verified_count"] == 1, valid_payload["submissions"]
    valid_checklist = {item["evidence_key"]: item for item in valid_payload["operator_checklist"]}
    assert valid_checklist["provider-holdout"]["readiness"] == "source-evidence-incomplete", valid_checklist["provider-holdout"]
    assert "source evidence checks still do not pass" in valid_checklist["provider-holdout"]["blocking_reason"], valid_checklist["provider-holdout"]
    assert valid_checklist["provider-holdout"]["submission_path"].endswith("tests/tmp_world_class_evidence_intake/valid_submissions/provider-holdout.json"), valid_checklist["provider-holdout"]
    assert "tests/tmp_world_class_evidence_intake/valid_submissions" in valid_checklist["provider-holdout"]["commands"]["validate_intake"], valid_checklist["provider-holdout"]
    assert "tests/tmp_world_class_evidence_intake/valid_submissions" in valid_checklist["provider-holdout"]["commands"]["submission_review"], valid_checklist["provider-holdout"]
    assert "tests/tmp_world_class_evidence_intake/valid_submissions" in valid_checklist["provider-holdout"]["commands"]["refresh_ledger"], valid_checklist["provider-holdout"]

    placeholder_dir = TMP / "placeholder_submissions"
    placeholder_dir.mkdir()
    placeholder_submission = provider_submission(valid=True)
    placeholder_submission["submitted_by"] = "operator with provider credentials"
    placeholder_submission["submitted_at"] = "YYYY-MM-DD"
    (placeholder_dir / "provider-holdout.json").write_text(
        json.dumps(placeholder_submission, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    placeholder_payload = run_intake("--submissions-dir", str(placeholder_dir))
    assert placeholder_payload["ok"] is False, placeholder_payload
    assert placeholder_payload["summary"]["decision"] == "fix-intake", placeholder_payload["summary"]
    assert placeholder_payload["summary"]["invalid_submission_count"] == 1, placeholder_payload["summary"]
    placeholder_errors = placeholder_payload["submissions"][0]["errors"]
    assert any("submitted_by must not use template placeholder text" in error for error in placeholder_errors), placeholder_errors
    assert any("submitted_at must use YYYY-MM-DD" in error for error in placeholder_errors), placeholder_errors

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
    assert any("sha256" in error for error in invalid_payload["submissions"][0]["errors"]), invalid_payload["submissions"]
    assert any("attestation.real_external_or_human_evidence" in error for error in invalid_payload["submissions"][0]["errors"]), invalid_payload["submissions"]
    invalid_checklist = {item["evidence_key"]: item for item in invalid_payload["operator_checklist"]}
    assert invalid_checklist["provider-holdout"]["readiness"] == "fix-submission", invalid_checklist["provider-holdout"]

    unrelated_dir = TMP / "unrelated_artifact_submissions"
    unrelated_dir.mkdir()
    (unrelated_dir / "provider-holdout.json").write_text(
        json.dumps(provider_submission(valid=True, artifact_path="reports/context_budget.json"), ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    unrelated_payload = run_intake("--submissions-dir", str(unrelated_dir))
    assert unrelated_payload["ok"] is False, unrelated_payload
    assert unrelated_payload["summary"]["decision"] == "fix-intake", unrelated_payload["summary"]
    assert unrelated_payload["summary"]["invalid_submission_count"] == 1, unrelated_payload["summary"]
    unrelated_errors = unrelated_payload["submissions"][0]["errors"]
    assert any("required evidence artifact reports/output_execution_runs.json" in error for error in unrelated_errors), unrelated_errors
    assert unrelated_payload["submissions"][0]["artifact_integrity"]["artifact_sha256_verified_count"] == 1, unrelated_payload["submissions"]
    assert unrelated_payload["submissions"][0]["artifact_integrity"]["required_artifact_verified_count"] == 0, unrelated_payload["submissions"]
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
