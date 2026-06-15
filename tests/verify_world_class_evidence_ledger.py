#!/usr/bin/env python3
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_world_class_evidence_ledger.py"
TMP = ROOT / "tests" / "tmp_world_class_evidence_ledger"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def provider_submission(artifact_root: Path = ROOT, artifact_path: str = "reports/output_execution_runs.json") -> dict:
    return {
        "schema_version": "1.0",
        "evidence_key": "provider-holdout",
        "template_only": False,
        "category": "external",
        "source_type": "provider-output-eval",
        "submitted_by": "Yao provider operator",
        "submitted_at": "2026-06-13",
        "summary": "Aggregate provider-backed holdout evidence for ledger review.",
        "artifact_refs": [
            {
                "path": artifact_path,
                "kind": "aggregate-report",
                "contains_raw_content": False,
                "sha256": sha256_file(artifact_root / artifact_path),
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
            "real_external_or_human_evidence": True,
            "reviewer_or_operator_identity_present": True,
            "artifact_refs_reviewed": True,
            "privacy_contract_satisfied": True,
        },
    }


def main() -> None:
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True, exist_ok=True)
    output_json = TMP / "world_class_evidence_ledger.json"
    output_md = TMP / "world_class_evidence_ledger.md"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(ROOT),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
            "--generated-at",
            "2026-06-13",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["schema_version"] == "1.0", payload
    assert payload["ok"] is True, payload
    summary = payload["summary"]
    assert payload["report_contract"]["contract"] == "world-class-evidence-ledger", payload
    assert payload["report_contract"]["top_level_mirrors_summary"] is True, payload
    for field in payload["report_contract"]["summary_fields"]:
        assert payload[field] == summary[field], (field, payload[field], summary[field])
    assert summary["ledger_entry_count"] == 4, summary
    assert summary["accepted_count"] == 0, summary
    assert summary["pending_count"] == 4, summary
    assert summary["human_pending_count"] == 1, summary
    assert summary["external_pending_count"] == 3, summary
    assert summary["submitted_entry_count"] == 0, summary
    assert summary["missing_submission_count"] == 4, summary
    assert summary["invalid_submission_count"] == 0, summary
    assert summary["source_check_count"] >= 13, summary
    assert summary["source_pass_count"] + summary["source_blocked_count"] == summary["source_check_count"], summary
    assert summary["source_blocked_count"] >= 6, summary
    assert summary["submitted_but_pending_count"] == 0, summary
    assert summary["overclaim_guard_active"] is True, summary
    assert summary["ready_to_claim_world_class"] is False, summary
    assert payload["ready_to_claim_world_class"] is False, payload
    assert payload["pending_count"] == 4, payload
    assert payload["accepted_count"] == 0, payload
    assert payload["source_blocked_count"] == summary["source_blocked_count"], payload
    assert payload["artifacts"]["intake"] == "reports/world_class_evidence_intake.md", payload
    entries = {entry["key"]: entry for entry in payload["entries"]}
    assert set(entries) == {
        "provider-holdout",
        "human-adjudication",
        "native-permission-enforcement",
        "native-client-telemetry",
    }, entries
    assert entries["provider-holdout"]["observed_state"]["model_executed_count"] == 0, entries["provider-holdout"]
    assert any("output-exec --provider-runner openai" in step for step in entries["provider-holdout"]["runbook"]), entries["provider-holdout"]
    provider_source = {item["field"]: item for item in entries["provider-holdout"]["source_checklist"]}
    assert provider_source["model_executed_count"]["status"] == "blocked", provider_source
    assert provider_source["timing_observed_count"]["status"] == "pass", provider_source
    assert provider_source["token_observed_count"]["status"] == "blocked", provider_source
    assert entries["provider-holdout"]["submission_state"]["status"] == "missing", entries["provider-holdout"]
    assert entries["provider-holdout"]["submission_state"]["ledger_counts_as_completion"] is False, entries["provider-holdout"]
    assert entries["human-adjudication"]["observed_state"]["pending_count"] == 5, entries["human-adjudication"]
    assert entries["native-permission-enforcement"]["observed_state"]["native_enforcement_count"] == 0, entries["native-permission-enforcement"]
    assert entries["native-permission-enforcement"]["observed_state"]["installer_enforcement_pass_count"] >= 0, entries["native-permission-enforcement"]
    assert any("summary.failure_count == 0" in check for check in entries["native-permission-enforcement"]["success_checks"]), entries["native-permission-enforcement"]
    assert entries["native-client-telemetry"]["observed_state"]["external_source_events"] == 0, entries["native-client-telemetry"]
    for entry in entries.values():
        assert entry["status"] == "pending", entry
        assert entry["success_checks"], entry
        assert entry["privacy_contract"], entry
        assert entry["anti_overclaim"]["planned_work_counts_as_evidence"] is False, entry
        assert entry["anti_overclaim"]["pending_review_counts_as_human_decision"] is False, entry
        assert "submission_state" in entry, entry
    markdown = output_md.read_text(encoding="utf-8")
    assert "World-Class Evidence Ledger" in markdown, markdown
    assert "overclaim guard active: `true`" in markdown, markdown
    assert "submitted entries: `0`" in markdown, markdown
    assert "source checks:" in markdown, markdown
    assert "Source Runbook" in markdown, markdown
    assert "output-exec --provider-runner openai" in markdown, markdown
    assert "Source Evidence Checks" in markdown, markdown
    assert "| Provider model run | `0` | `>0` | `blocked` |" in markdown, markdown
    assert "`provider-holdout`" in markdown, markdown

    submissions = TMP / "submissions"
    submissions.mkdir()
    (submissions / "provider-holdout.json").write_text(
        json.dumps(provider_submission(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    submitted_proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(ROOT),
            "--output-json",
            str(TMP / "submitted_ledger.json"),
            "--output-md",
            str(TMP / "submitted_ledger.md"),
            "--submissions-dir",
            str(submissions),
            "--generated-at",
            "2026-06-13",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    submitted_payload = json.loads(submitted_proc.stdout)
    submitted_summary = submitted_payload["summary"]
    assert submitted_summary["submitted_entry_count"] == 1, submitted_summary
    assert submitted_summary["submitted_but_pending_count"] == 1, submitted_summary
    assert submitted_summary["accepted_count"] == 0, submitted_summary
    assert submitted_summary["source_blocked_count"] >= 6, submitted_summary
    submitted_provider = {entry["key"]: entry for entry in submitted_payload["entries"]}["provider-holdout"]
    assert submitted_provider["status"] == "pending", submitted_provider
    assert submitted_provider["submission_state"]["status"] == "submitted", submitted_provider
    assert submitted_provider["submission_state"]["artifact_sha256_verified_count"] == 1, submitted_provider
    assert submitted_provider["submission_state"]["attested_real_evidence"] is True, submitted_provider
    assert submitted_provider["submission_state"]["ledger_counts_as_completion"] is False, submitted_provider

    accepted_source_skill = TMP / "accepted_source_skill"
    (accepted_source_skill / "reports").mkdir(parents=True)
    (accepted_source_skill / "reports" / "output_execution_runs.json").write_text(
        json.dumps(
            {
                "summary": {
                    "model_executed_count": 1,
                    "timing_observed_count": 1,
                    "token_observed_count": 1,
                }
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    accepted_source_proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(accepted_source_skill),
            "--output-json",
            str(TMP / "accepted_source_without_submission.json"),
            "--output-md",
            str(TMP / "accepted_source_without_submission.md"),
            "--generated-at",
            "2026-06-13",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    accepted_source_payload = json.loads(accepted_source_proc.stdout)
    accepted_source_summary = accepted_source_payload["summary"]
    assert accepted_source_summary["source_accepted_count"] == 1, accepted_source_summary
    assert accepted_source_summary["accepted_count"] == 0, accepted_source_summary
    assert accepted_source_summary["source_accepted_without_valid_submission_count"] == 1, accepted_source_summary
    assert accepted_source_summary["source_check_count"] >= 13, accepted_source_summary
    accepted_source_provider = {
        entry["key"]: entry for entry in accepted_source_payload["entries"]
    }["provider-holdout"]
    assert accepted_source_provider["source_accepted"] is True, accepted_source_provider
    assert accepted_source_provider["status"] == "pending", accepted_source_provider
    assert accepted_source_provider["submission_state"]["status"] == "missing", accepted_source_provider
    assert all(item["status"] == "pass" for item in accepted_source_provider["source_checklist"]), accepted_source_provider

    (accepted_source_skill / "reports" / "context_budget.json").write_text(
        json.dumps({"summary": {"unrelated": True}}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    unrelated_accepted_submissions = TMP / "unrelated_accepted_submissions"
    unrelated_accepted_submissions.mkdir()
    (unrelated_accepted_submissions / "provider-holdout.json").write_text(
        json.dumps(
            provider_submission(accepted_source_skill, artifact_path="reports/context_budget.json"),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    unrelated_accepted_proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(accepted_source_skill),
            "--output-json",
            str(TMP / "unrelated_accepted_provider_ledger.json"),
            "--output-md",
            str(TMP / "unrelated_accepted_provider_ledger.md"),
            "--submissions-dir",
            str(unrelated_accepted_submissions),
            "--generated-at",
            "2026-06-13",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    unrelated_accepted_payload = json.loads(unrelated_accepted_proc.stdout)
    unrelated_accepted_summary = unrelated_accepted_payload["summary"]
    assert unrelated_accepted_summary["source_accepted_count"] == 1, unrelated_accepted_summary
    assert unrelated_accepted_summary["accepted_count"] == 0, unrelated_accepted_summary
    assert unrelated_accepted_summary["invalid_submission_count"] == 1, unrelated_accepted_summary
    unrelated_accepted_provider = {
        entry["key"]: entry for entry in unrelated_accepted_payload["entries"]
    }["provider-holdout"]
    assert unrelated_accepted_provider["source_accepted"] is True, unrelated_accepted_provider
    assert unrelated_accepted_provider["status"] == "pending", unrelated_accepted_provider
    assert unrelated_accepted_provider["submission_state"]["status"] == "invalid-contract", unrelated_accepted_provider
    assert any(
        "required evidence artifact reports/output_execution_runs.json" in error
        for error in unrelated_accepted_provider["submission_state"]["errors"]
    ), unrelated_accepted_provider

    placeholder_accepted_submissions = TMP / "placeholder_accepted_submissions"
    placeholder_accepted_submissions.mkdir()
    placeholder_submission = provider_submission(accepted_source_skill)
    placeholder_submission["submitted_by"] = "operator with provider credentials"
    placeholder_submission["submitted_at"] = "YYYY-MM-DD"
    (placeholder_accepted_submissions / "provider-holdout.json").write_text(
        json.dumps(placeholder_submission, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    placeholder_accepted_proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(accepted_source_skill),
            "--output-json",
            str(TMP / "placeholder_accepted_provider_ledger.json"),
            "--output-md",
            str(TMP / "placeholder_accepted_provider_ledger.md"),
            "--submissions-dir",
            str(placeholder_accepted_submissions),
            "--generated-at",
            "2026-06-13",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    placeholder_accepted_payload = json.loads(placeholder_accepted_proc.stdout)
    placeholder_accepted_summary = placeholder_accepted_payload["summary"]
    assert placeholder_accepted_summary["source_accepted_count"] == 1, placeholder_accepted_summary
    assert placeholder_accepted_summary["accepted_count"] == 0, placeholder_accepted_summary
    assert placeholder_accepted_summary["invalid_submission_count"] == 1, placeholder_accepted_summary
    placeholder_accepted_provider = {
        entry["key"]: entry for entry in placeholder_accepted_payload["entries"]
    }["provider-holdout"]
    assert placeholder_accepted_provider["source_accepted"] is True, placeholder_accepted_provider
    assert placeholder_accepted_provider["status"] == "pending", placeholder_accepted_provider
    assert placeholder_accepted_provider["submission_state"]["status"] == "invalid-contract", placeholder_accepted_provider
    assert any(
        "submitted_by must not use template placeholder text" in error
        for error in placeholder_accepted_provider["submission_state"]["errors"]
    ), placeholder_accepted_provider

    accepted_submissions = TMP / "accepted_submissions"
    accepted_submissions.mkdir()
    (accepted_submissions / "provider-holdout.json").write_text(
        json.dumps(provider_submission(accepted_source_skill), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    accepted_proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(accepted_source_skill),
            "--output-json",
            str(TMP / "accepted_provider_ledger.json"),
            "--output-md",
            str(TMP / "accepted_provider_ledger.md"),
            "--submissions-dir",
            str(accepted_submissions),
            "--generated-at",
            "2026-06-13",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    accepted_payload = json.loads(accepted_proc.stdout)
    accepted_summary = accepted_payload["summary"]
    assert accepted_summary["source_accepted_count"] == 1, accepted_summary
    assert accepted_summary["accepted_count"] == 1, accepted_summary
    assert accepted_summary["pending_count"] == 3, accepted_summary
    assert accepted_summary["source_accepted_without_valid_submission_count"] == 0, accepted_summary
    accepted_provider = {entry["key"]: entry for entry in accepted_payload["entries"]}["provider-holdout"]
    assert accepted_provider["status"] == "accepted", accepted_provider
    assert accepted_provider["submission_state"]["status"] == "submitted", accepted_provider
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
