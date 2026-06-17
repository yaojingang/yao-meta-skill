#!/usr/bin/env python3
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_world_class_operator_runbook.py"
CLI = ROOT / "scripts" / "yao.py"
TMP = ROOT / "tests" / "tmp_world_class_operator_runbook"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def provider_submission() -> dict:
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
                "contains_raw_content": False,
                "sha256": sha256_file(ROOT / "reports" / "output_execution_runs.json"),
            }
        ],
        "provenance": {"provider": "deepseek", "model": "deepseek-v4-flash", "credential_material_committed": False},
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
            "ledger_reviewer_approved": True,
            "ledger_reviewer": "Yao ledger reviewer",
            "ledger_reviewed_at": "2026-06-14",
        },
    }


def run_direct(*extra: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(ROOT), "--generated-at", "2026-06-14", *extra],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def run_cli(*extra: str) -> dict:
    env = dict(os.environ)
    env["YAO_CLI_TELEMETRY"] = "0"
    env.pop("YAO_CLI_TELEMETRY_EVENTS", None)
    proc = subprocess.run(
        [sys.executable, str(CLI), *extra],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    return json.loads(proc.stdout)


def main() -> None:
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True, exist_ok=True)
    empty_submissions = TMP / "empty-submissions"
    empty_submissions.mkdir()
    output_json = TMP / "world_class_operator_runbook.json"
    output_md = TMP / "world_class_operator_runbook.md"
    output_html = TMP / "world_class_operator_runbook.html"
    payload = run_direct(
        "--output-json",
        str(output_json),
        "--output-md",
        str(output_md),
        "--output-html",
        str(output_html),
        "--submissions-dir",
        str(empty_submissions),
    )
    assert payload["schema_version"] == "1.0", payload
    assert payload["ok"] is True, payload
    summary = payload["summary"]
    assert summary["decision"] == "collect-evidence", summary
    assert summary["evidence_item_count"] == 4, summary
    assert summary["pending_count"] == 4, summary
    assert summary["awaiting_submission_count"] == 4, summary
    assert summary["ready_for_ledger_review_count"] == 0, summary
    assert summary["valid_packet_source_incomplete_count"] == 0, summary
    assert summary["invalid_submission_count"] == 0, summary
    assert summary["source_check_count"] >= 13, summary
    assert summary["source_pass_count"] + summary["source_blocked_count"] == summary["source_check_count"], summary
    assert summary["source_blocked_count"] >= 6, summary
    assert summary["repair_checklist_count"] >= summary["source_blocked_count"], summary
    assert summary["phase_queue_count"] == 2, summary
    assert summary["phase_queue_blocked_count"] == 2, summary
    assert summary["phase_queue_row_count"] == summary["repair_checklist_count"], summary
    assert summary["phase_queue_next_phase"] == "unblock-access", summary
    assert summary["phase_queue_counts_as_completion"] is False, summary
    assert summary["coordination_step_count"] == 6, summary
    assert summary["coordination_user_required_step_count"] == 6, summary
    assert summary["coordination_pending_evidence_keys"] == [
        "human-adjudication",
        "native-client-telemetry",
        "native-permission-enforcement",
        "provider-holdout",
    ], summary
    assert summary["coordination_counts_as_completion"] is False, summary
    assert summary["release_gate_ready"] is False, summary
    assert summary["release_gate_blocked_count"] == 4, summary
    assert summary["release_gate_check_count"] == 5, summary
    assert summary["release_gate_counts_as_completion"] is False, summary
    assert summary["ready_to_claim_world_class"] is False, summary
    assert summary["runbook_counts_as_completion"] is False, summary
    assert payload["repair_checklist"], payload
    assert len(payload["phase_queue"]) == summary["phase_queue_count"], payload["phase_queue"]
    assert sum(item["row_count"] for item in payload["phase_queue"]) == summary["phase_queue_row_count"], payload[
        "phase_queue"
    ]
    items = {item["evidence_key"]: item for item in payload["items"]}
    assert set(items) == {
        "provider-holdout",
        "human-adjudication",
        "native-permission-enforcement",
        "native-client-telemetry",
    }, items
    coordination_plan = payload["coordination_plan"]
    assert len(coordination_plan) == summary["coordination_step_count"], coordination_plan
    assert all(step["counts_as_completion"] is False for step in coordination_plan), coordination_plan
    coordination_by_key = {step["evidence_key"]: step for step in coordination_plan if step["evidence_key"]}
    assert set(coordination_by_key) == set(items), coordination_by_key
    assert "output-exec . --provider-runner <openai|deepseek>" in coordination_by_key["provider-holdout"]["command"], (
        coordination_by_key
    )
    assert "output-review-kit" in coordination_by_key["human-adjudication"]["command"], coordination_by_key
    assert "runtime-permissions" in coordination_by_key["native-permission-enforcement"]["command"], (
        coordination_by_key
    )
    assert "telemetry-import" in coordination_by_key["native-client-telemetry"]["command"], coordination_by_key
    assert payload["release_gate"]["ready"] is False, payload["release_gate"]
    assert payload["release_gate"]["blocked_count"] == summary["release_gate_blocked_count"], payload["release_gate"]
    assert payload["release_gate"]["check_count"] == summary["release_gate_check_count"], payload["release_gate"]
    assert payload["release_gate"]["counts_as_completion"] is False, payload["release_gate"]
    release_checks = {item["key"]: item for item in payload["release_gate"]["checks"]}
    assert release_checks["world_class_ledger_ready"]["passed"] is False, release_checks
    assert release_checks["claim_guard_clean"]["passed"] is False, release_checks
    assert release_checks["benchmark_public_claim_ready"]["passed"] is False, release_checks
    assert release_checks["review_studio_clean"]["passed"] is False, release_checks
    assert release_checks["evidence_consistency_clean"]["passed"] is True, release_checks
    provider = items["provider-holdout"]
    assert provider["review_state"] == "awaiting-submission", provider
    assert provider["source_accepted"] is True, provider
    assert provider["blocked_source_check_count"] == 0, provider
    assert provider["repair_blocked_count"] == 1, provider
    assert provider["repair_counts_as_completion"] is False, provider
    assert provider["phase_queue_blocked_count"] == 1, provider
    assert provider["phase_queue_counts_as_completion"] is False, provider
    assert [item["phase"] for item in provider["phase_queue"]] == ["unblock-access"], provider
    assert any("--provider-runner openai" in step for step in provider["execution_runbook"]), provider
    assert any("--provider-runner deepseek" in step for step in provider["execution_runbook"]), provider
    assert not any("<redacted>" in step or "OPENAI_API_KEY=" in step for step in provider["execution_runbook"]), provider
    assert provider["next_source_actions"] == [], provider
    assert provider["commands"]["prepare_submission"].startswith("python3 scripts/yao.py world-class-submission-kit"), provider
    assert "world-class-intake" in provider["commands"]["validate_intake"], provider
    assert "world-class-submission-review" in provider["commands"]["review_queue"], provider
    assert "world-class-ledger" in provider["commands"]["refresh_ledger"], provider
    assert "world-class-claim-guard" in provider["commands"]["guard_claim"], provider
    assert "provider-backed model run" in provider["must_collect"]["provenance_requirements"], provider
    assert "reports/output_execution_runs.json summary.model_executed_count > 0" in provider["must_collect"]["success_checks"], provider
    provider_source = {item["field"]: item for item in provider["source_checklist"]}
    assert provider_source["model_executed_count"]["status"] == "pass", provider_source
    assert provider_source["timing_observed_count"]["status"] == "pass", provider_source
    assert provider_source["token_observed_count"]["status"] == "pass", provider_source
    human = items["human-adjudication"]
    human_source = {item["field"]: item for item in human["source_checklist"]}
    assert human["observed_state"]["raw_content_allowed"] is False, human
    assert human_source["raw_content_allowed"]["status"] == "pass", human_source
    markdown = output_md.read_text(encoding="utf-8")
    assert "World-Class Operator Runbook" in markdown, markdown
    assert "runbook counts as completion: `false`" in markdown, markdown
    assert "phase queue counts as completion: `false`" in markdown, markdown
    assert "coordination counts as completion: `false`" in markdown, markdown
    assert "release gate counts as completion: `false`" in markdown, markdown
    assert "## Coordination Plan" in markdown, markdown
    assert "`review-and-release-gate`" in markdown, markdown
    assert "## Release Gate" in markdown, markdown
    assert "world-class-claim-guard" in markdown, markdown
    assert "## Phase Queue" in markdown, markdown
    assert "| `unblock-access` | `blocked` |" in markdown, markdown
    assert "Valid intake means ready for submission review; ledger review still requires passing source evidence." in markdown, markdown
    assert "| Evidence | Ledger | Intake | Review | Blocked checks | Next source action | Owner |" in markdown, markdown
    assert "| `provider-holdout` | `pending` | `awaiting-submission` | `awaiting-submission` | `0` | none | operator with provider credentials |" in markdown, markdown
    assert "Source Runbook" in markdown, markdown
    assert "### Phase Queue" in markdown, markdown
    assert "--provider-runner openai" in markdown, markdown
    assert "--provider-runner deepseek" in markdown, markdown
    assert "<redacted>" not in markdown, markdown
    assert "OPENAI_API_KEY=<redacted>" not in markdown, markdown
    assert "### Next Source Actions" in markdown, markdown
    assert "| Token usage observed | `10` | `>0` | `pass` |" in markdown, markdown
    assert "Source Evidence Snapshot" in markdown, markdown
    assert "| Check | Current | Expected | Status | Next action |" in markdown, markdown
    assert "| Provider model run | `10` | `>0` | `pass` | Run provider-backed output-exec with real credentials. |" in markdown, markdown
    html = output_html.read_text(encoding="utf-8")
    assert "World-Class Operator Runbook" in html, html[:400]
    assert "ledger and claim guard" in html, html
    assert "position:sticky" in html, html
    assert "<span>Ready</span><strong>0</strong>" in html, html
    assert "<span>Invalid</span><strong>0</strong>" in html, html
    assert f"<span>Queue</span><strong>{summary['phase_queue_blocked_count']}/{summary['phase_queue_count']}</strong>" in html, html
    assert f"<span>Blocked</span><strong>{summary['source_blocked_count']}</strong>" in html, html
    assert "<dt>Blocked</dt><dd><code>0</code></dd>" in html, html
    assert "<dt>Queue</dt><dd><code>1</code></dd>" in html, html
    assert "Phase Queue" in html, html
    assert "Coordination Plan" in html, html
    assert "Release Gate" in html, html
    assert "review-and-release-gate" in html, html
    assert "blocked-until-evidence-accepted" in html, html
    assert "Next Source Actions" in html, html
    assert "Source Runbook" in html, html
    assert "--provider-runner openai" in html, html
    assert "--provider-runner deepseek" in html, html
    assert "&lt;redacted&gt;" not in html and "<redacted>" not in html, html
    assert "OPENAI_API_KEY=&lt;redacted&gt;" not in html, html
    assert "Source Evidence Snapshot" in html, html
    assert "model_executed_count" in html, html
    assert "model_executed_count: 10 / &gt;0" in html, html
    assert "raw_content_allowed: False / false" in html, html
    assert "<script" not in html.lower(), html
    assert "http://" not in html and "https://" not in html, html

    cli_payload = run_cli(
        "world-class-runbook",
        str(ROOT),
        "--output-json", str(TMP / "cli_runbook.json"),
        "--output-md", str(TMP / "cli_runbook.md"),
        "--output-html", str(TMP / "cli_runbook.html"),
        "--generated-at", "2026-06-14",
    )
    assert cli_payload["summary"]["decision"] == "collect-evidence", cli_payload
    assert cli_payload["artifacts"]["html"].endswith("tests/tmp_world_class_operator_runbook/cli_runbook.html"), cli_payload

    submissions = TMP / "valid_submissions"
    submissions.mkdir()
    (submissions / "provider-holdout.json").write_text(
        json.dumps(provider_submission(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    submitted = run_direct(
        "--submissions-dir", str(submissions),
        "--output-json", str(TMP / "submitted_runbook.json"),
        "--output-md", str(TMP / "submitted_runbook.md"),
        "--output-html", str(TMP / "submitted_runbook.html"),
    )
    submitted_summary = submitted["summary"]
    assert submitted_summary["awaiting_submission_count"] == 3, submitted_summary
    assert submitted_summary["valid_packet_source_incomplete_count"] == 0, submitted_summary
    assert submitted_summary["invalid_submission_count"] == 0, submitted_summary
    assert submitted_summary["accepted_count"] == 1, submitted_summary
    assert submitted_summary["ready_for_ledger_review_count"] == 0, submitted_summary
    assert submitted_summary["source_pass_count"] + submitted_summary["source_blocked_count"] == submitted_summary["source_check_count"], submitted_summary
    assert submitted_summary["source_blocked_count"] >= 6, submitted_summary
    assert submitted_summary["phase_queue_count"] == 2, submitted_summary
    assert submitted_summary["phase_queue_blocked_count"] == 2, submitted_summary
    assert submitted_summary["phase_queue_counts_as_completion"] is False, submitted_summary
    assert submitted_summary["ready_to_claim_world_class"] is False, submitted_summary
    submitted_provider = {item["evidence_key"]: item for item in submitted["items"]}["provider-holdout"]
    assert submitted_provider["ledger_status"] == "accepted", submitted_provider
    assert submitted_provider["intake_readiness"] == "ready-for-ledger-review", submitted_provider
    assert submitted_provider["review_state"] == "accepted", submitted_provider
    assert submitted_provider["source_accepted"] is True, submitted_provider
    assert submitted_provider["blocked_source_check_count"] == 0, submitted_provider
    assert submitted_provider["phase_queue_blocked_count"] == 0, submitted_provider
    assert submitted_provider["next_source_actions"] == [], submitted_provider
    assert "tests/tmp_world_class_operator_runbook/valid_submissions" in submitted_provider["commands"]["validate_intake"], submitted_provider
    assert "tests/tmp_world_class_operator_runbook/valid_submissions" in submitted_provider["commands"]["review_queue"], submitted_provider
    assert "tests/tmp_world_class_operator_runbook/valid_submissions" in submitted_provider["commands"]["refresh_ledger"], submitted_provider
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
