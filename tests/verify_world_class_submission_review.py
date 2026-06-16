#!/usr/bin/env python3
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_world_class_submission_review.py"
TMP = ROOT / "tests" / "tmp_world_class_submission_review"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def provider_submission(*, valid: bool = True) -> dict:
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
                "sha256": sha256_file(ROOT / "reports" / "output_execution_runs.json") if valid else "example-only",
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
            "ledger_reviewer_approved": valid,
        },
    }


def run_review(*extra: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
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
        check=check,
    )


def main() -> None:
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True, exist_ok=True)

    output_json = TMP / "world_class_submission_review.json"
    output_md = TMP / "world_class_submission_review.md"
    default_proc = run_review("--output-json", str(output_json), "--output-md", str(output_md))
    payload = json.loads(default_proc.stdout)
    assert payload["schema_version"] == "1.0", payload
    assert payload["ok"] is True, payload
    summary = payload["summary"]
    assert payload["report_contract"]["contract"] == "world-class-submission-review", payload
    assert payload["report_contract"]["top_level_mirrors_summary"] is True, payload
    for field in payload["report_contract"]["summary_fields"]:
        assert payload[field] == summary[field], (field, payload[field], summary[field])
    assert summary["decision"] == "awaiting-submissions", summary
    assert summary["review_item_count"] == 4, summary
    assert summary["awaiting_submission_count"] == 4, summary
    assert summary["ready_for_ledger_review_count"] == 0, summary
    assert summary["valid_packet_source_incomplete_count"] == 0, summary
    assert summary["source_check_count"] >= 13, summary
    assert summary["source_pass_count"] + summary["source_blocked_count"] == summary["source_check_count"], summary
    assert summary["source_blocked_count"] >= 6, summary
    assert summary["review_counts_submission_as_completion"] is False, summary
    assert payload["ready_to_claim_world_class"] is False, payload
    assert payload["review_item_count"] == 4, payload
    assert payload["awaiting_submission_count"] == 4, payload
    assert payload["source_blocked_count"] == summary["source_blocked_count"], payload
    provider_item = {item["evidence_key"]: item for item in payload["items"]}["provider-holdout"]
    assert provider_item["review_state"] == "awaiting-submission", provider_item
    assert provider_item["submission_status"] == "missing", provider_item
    assert provider_item["source_accepted"] is False, provider_item
    provider_source = {item["field"]: item for item in provider_item["source_checklist"]}
    assert provider_source["model_executed_count"]["status"] == "blocked", provider_source
    assert provider_source["timing_observed_count"]["status"] == "pass", provider_source
    assert provider_source["token_observed_count"]["status"] == "blocked", provider_source
    markdown = output_md.read_text(encoding="utf-8")
    assert "World-Class Submission Review" in markdown, markdown
    assert "review counts submission as completion: `false`" in markdown, markdown
    assert "Provider model run: 0 / >0 => blocked" in markdown, markdown
    assert "`provider-holdout`" in markdown, markdown

    submissions = TMP / "valid_submissions"
    submissions.mkdir()
    (submissions / "provider-holdout.json").write_text(
        json.dumps(provider_submission(valid=True), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    # The kit manifest must not be treated as an evidence packet.
    (submissions / "submission_manifest.json").write_text(
        json.dumps({"schema_version": "1.0", "not": "an evidence packet"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    submitted_proc = run_review(
        "--submissions-dir",
        str(submissions),
        "--output-json",
        str(TMP / "submitted_review.json"),
        "--output-md",
        str(TMP / "submitted_review.md"),
        check=False,
    )
    assert submitted_proc.returncode == 2, submitted_proc.stdout
    submitted_payload = json.loads(submitted_proc.stdout)
    submitted_summary = submitted_payload["summary"]
    assert submitted_payload["ok"] is False, submitted_payload
    assert submitted_summary["decision"] == "fix-submissions", submitted_summary
    assert submitted_summary["valid_packet_source_incomplete_count"] == 0, submitted_summary
    assert submitted_summary["awaiting_submission_count"] == 3, submitted_summary
    assert submitted_summary["invalid_submission_count"] == 1, submitted_summary
    assert submitted_summary["source_pass_count"] + submitted_summary["source_blocked_count"] == submitted_summary["source_check_count"], submitted_summary
    assert submitted_summary["source_blocked_count"] >= 6, submitted_summary
    submitted_provider = {item["evidence_key"]: item for item in submitted_payload["items"]}["provider-holdout"]
    assert submitted_provider["review_state"] == "fix-submission", submitted_provider
    assert submitted_provider["intake_status"] == "fail", submitted_provider
    assert submitted_provider["submission_status"] == "invalid-contract", submitted_provider
    assert submitted_provider["artifact_ref_count"] == 1, submitted_provider
    assert submitted_provider["source_accepted"] is False, submitted_provider
    assert any("summary.model_executed_count must be >0" in error for error in submitted_provider["intake_errors"]), submitted_provider
    assert "model_executed_count" in submitted_provider["observed_state"], submitted_provider
    submitted_source = {item["field"]: item for item in submitted_provider["source_checklist"]}
    assert submitted_source["model_executed_count"]["status"] == "blocked", submitted_source
    assert submitted_source["timing_observed_count"]["status"] == "pass", submitted_source

    invalid_dir = TMP / "invalid_submissions"
    invalid_dir.mkdir()
    (invalid_dir / "provider-holdout.json").write_text(
        json.dumps(provider_submission(valid=False), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    invalid_proc = run_review(
        "--submissions-dir",
        str(invalid_dir),
        "--output-json",
        str(TMP / "invalid_review.json"),
        "--output-md",
        str(TMP / "invalid_review.md"),
        check=False,
    )
    assert invalid_proc.returncode == 2, invalid_proc.stdout
    invalid_payload = json.loads(invalid_proc.stdout)
    assert invalid_payload["ok"] is False, invalid_payload
    assert invalid_payload["summary"]["decision"] == "fix-submissions", invalid_payload["summary"]
    invalid_provider = {item["evidence_key"]: item for item in invalid_payload["items"]}["provider-holdout"]
    assert invalid_provider["review_state"] == "fix-submission", invalid_provider
    assert invalid_provider["intake_errors"], invalid_provider
    assert any("sha256" in error for error in invalid_provider["intake_errors"]), invalid_provider
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
