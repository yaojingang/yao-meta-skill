#!/usr/bin/env python3
"""Focused assertions for Review Studio world-class evidence actions."""


def assert_world_class_action(full_payload: dict) -> None:
    world_class_action = next(
        item for item in full_payload["review_actions"] if item["gate_key"] == "world-class-evidence"
    )
    assert {item["path"] for item in world_class_action["source_refs"]} >= {
        "reports/world_class_evidence_ledger.md",
        "reports/world_class_evidence_plan.md",
        "reports/world_class_evidence_intake.md",
        "reports/world_class_evidence_preflight.md",
        "reports/world_class_evidence_preflight.html",
        "reports/world_class_submission_review.md",
        "reports/world_class_claim_guard.md",
        "evidence/world_class/intake.schema.json",
        "evidence/world_class/templates/provider-holdout.intake.json",
        "evidence/world_class/templates/human-adjudication.intake.json",
        "evidence/world_class/templates/native-permission-enforcement.intake.json",
        "evidence/world_class/templates/native-client-telemetry.intake.json",
        "reports/skill_os2_audit.md",
    }, world_class_action
    assert all(item["exists"] for item in world_class_action["source_refs"]), world_class_action
    assert all("matched_pattern" in item for item in world_class_action["source_refs"]), world_class_action
    assert all("excerpt" in item for item in world_class_action["source_refs"]), world_class_action
    assert all(isinstance(item["line"], int) and item["line"] >= 1 for item in world_class_action["source_refs"]), world_class_action
    assert any(
        item["path"] == "reports/world_class_evidence_ledger.md"
        and item["matched_pattern"] == "# World-Class Evidence Ledger"
        and "World-Class Evidence Ledger" in item["excerpt"]
        for item in world_class_action["source_refs"]
    ), world_class_action
    assert "world-class-runbook" in world_class_action["verification_command"], world_class_action
    assert "--submissions-dir evidence/world_class/submissions" in world_class_action["verification_command"], world_class_action
    assert "reports/world_class_operator_runbook.html" in world_class_action["source_fix"], world_class_action
    assert {item["key"] for item in world_class_action["evidence_steps"]} == {
        "provider-holdout",
        "human-adjudication",
        "native-permission-enforcement",
        "native-client-telemetry",
    }, world_class_action

    provider_action_step = next(
        item for item in world_class_action["evidence_steps"] if item["key"] == "provider-holdout"
    )
    assert provider_action_step["status"] == "pending", provider_action_step
    provider_readiness = provider_action_step["readiness"]
    assert provider_readiness in {"fix-submission", "awaiting-submission"}, provider_action_step
    assert provider_action_step["submission_path"] == "evidence/world_class/submissions/provider-holdout.json", provider_action_step
    assert provider_action_step["template_path"] == "evidence/world_class/templates/provider-holdout.intake.json", provider_action_step
    assert provider_action_step["source_blocked_count"] == 0, provider_action_step
    assert provider_action_step["repair_blocked_count"] == 1, provider_action_step
    assert provider_action_step["repair_counts_as_completion"] is False, provider_action_step
    assert provider_action_step["phase_queue_blocked_count"] == 1, provider_action_step
    assert provider_action_step["phase_queue_counts_as_completion"] is False, provider_action_step
    provider_phase_queue = {item["phase"]: item for item in provider_action_step["phase_queue"]}
    assert set(provider_phase_queue) == {"unblock-access"}, provider_phase_queue
    assert provider_phase_queue["unblock-access"]["next_action_id"] == "provider-holdout-precheck-provider-api-key", provider_phase_queue
    assert provider_phase_queue["unblock-access"]["row_count"] == 1, provider_phase_queue
    assert "operator with provider credentials" in provider_phase_queue["unblock-access"]["owners"], provider_phase_queue
    assert provider_action_step["blocked_checks"] == [], provider_action_step
    provider_repair_rows = {item["target"]: item for item in provider_action_step["repair_rows"]}
    assert set(provider_repair_rows) == {"provider-api-key"}, provider_repair_rows
    assert provider_repair_rows["provider-api-key"]["action_id"] == "provider-holdout-precheck-provider-api-key", provider_repair_rows
    assert provider_repair_rows["provider-api-key"]["repair_type"] == "precheck", provider_repair_rows
    assert provider_repair_rows["provider-api-key"]["phase"] == "unblock-access", provider_repair_rows
    assert provider_repair_rows["provider-api-key"]["priority"] == 20, provider_repair_rows
    assert provider_repair_rows["provider-api-key"]["owner"] == "operator with provider credentials", provider_repair_rows
    assert all(item["counts_as_completion"] is False for item in provider_action_step["repair_rows"]), provider_action_step
    assert any("world-class-intake" in item["command"] for item in provider_action_step["commands"]), provider_action_step
    assert any("world-class-ledger" in item["command"] for item in provider_action_step["commands"]), provider_action_step
    assert any("output-exec --provider-runner openai" in item for item in provider_action_step["runbook"]), provider_action_step
    assert not any("<redacted>" in item or "OPENAI_API_KEY=" in item for item in provider_action_step["runbook"]), provider_action_step
    assert "provider-backed model run" in provider_action_step["provenance_requirements"], provider_action_step
    assert "reports/output_execution_runs.json summary.model_executed_count > 0" in provider_action_step["success_checks"], provider_action_step
    assert "reports/output_execution_runs.json" in provider_action_step["evidence_artifacts"], provider_action_step
    provider_role_contract = provider_action_step["artifact_role_contract"]
    assert provider_role_contract["role_source"] == "world-class-submission-kit", provider_role_contract
    assert provider_role_contract["counts_as_evidence"] is False, provider_role_contract
    assert provider_role_contract["artifact_prefill_counts_as_evidence"] is False, provider_role_contract
    assert provider_role_contract["submission_ref_total_count"] == 1, provider_role_contract
    assert provider_role_contract["submission_ref_ready_count"] == 1, provider_role_contract
    provider_role_rows = {item["role"]: item for item in provider_role_contract["roles"]}
    assert provider_role_rows["submission-ref"]["copy_to_artifact_refs"] is True, provider_role_rows
    assert provider_role_rows["supporting-evidence"]["copy_to_artifact_refs"] is False, provider_role_rows
    assert any("provider credentials" in item for item in provider_action_step["privacy_contract"]), provider_action_step

    human_action_step = next(
        item for item in world_class_action["evidence_steps"] if item["key"] == "human-adjudication"
    )
    assert human_action_step["repair_blocked_count"] >= 2, human_action_step
    assert human_action_step["phase_queue_blocked_count"] == 2, human_action_step
    human_repair_rows = {item["target"]: item for item in human_action_step["repair_rows"]}
    assert human_repair_rows["human-reviewer"]["repair_type"] == "precheck", human_repair_rows
    assert human_repair_rows["human-reviewer"]["owner"] == "human reviewer", human_repair_rows
    assert human_repair_rows["pending_count"]["repair_type"] == "source-check", human_repair_rows
    assert "output-review" in human_repair_rows["pending_count"]["verification_command"], human_repair_rows
    assert "prompt_sha256" in " ".join(human_action_step["success_checks"]), human_action_step
    assert "prompt_sha256" in " ".join(human_action_step["privacy_contract"]), human_action_step

    expected_awaiting_count = 3 if provider_readiness == "fix-submission" else 4
    expected_invalid_count = 1 if provider_readiness == "fix-submission" else 0
    expected_intake_decision = "fix-intake" if provider_readiness == "fix-submission" else "awaiting-submissions"
    expected_review_decision = "fix-submissions" if provider_readiness == "fix-submission" else "awaiting-submissions"
    assert full_payload["data"]["world_class_evidence_ledger"]["summary"]["pending_count"] == 4
    assert full_payload["data"]["world_class_evidence_intake"]["summary"]["decision"] == expected_intake_decision
    submission_review = full_payload["data"]["world_class_submission_review"]
    assert submission_review["summary"]["decision"] == expected_review_decision, submission_review
    assert submission_review["summary"]["review_counts_submission_as_completion"] is False, submission_review
    assert submission_review["summary"]["awaiting_submission_count"] == expected_awaiting_count, submission_review
    assert submission_review["summary"]["invalid_submission_count"] == expected_invalid_count, submission_review
    assert submission_review["summary"]["source_check_count"] >= 13, submission_review
    assert submission_review["summary"]["source_blocked_count"] >= 6, submission_review
    human_review_item = next(item for item in submission_review["items"] if item["evidence_key"] == "human-adjudication")
    human_review_source = {item["field"]: item for item in human_review_item["source_checklist"]}
    assert human_review_item["observed_state"]["raw_content_allowed"] is False, human_review_item
    assert human_review_item["observed_state"]["raw_content_path_count"] == 0, human_review_item
    assert human_review_source["raw_content_allowed"]["status"] == "pass", human_review_source

    runbook = full_payload["data"]["world_class_operator_runbook"]
    assert runbook["summary"]["decision"] == "collect-evidence", runbook
    assert runbook["summary"]["runbook_counts_as_completion"] is False, runbook
    assert runbook["summary"]["awaiting_submission_count"] == expected_awaiting_count, runbook
    assert runbook["summary"]["invalid_submission_count"] == expected_invalid_count, runbook
    intake = full_payload["data"]["world_class_evidence_intake"]
    assert intake["summary"]["template_pass_count"] == 4, intake
    assert intake["summary"]["operator_checklist_count"] == 4, intake
    assert intake["summary"]["operator_checklist_ready_count"] == 0, intake
    assert intake["summary"]["ready_to_claim_world_class"] is False, intake
    provider_checklist = next(item for item in intake["operator_checklist"] if item["evidence_key"] == "provider-holdout")
    assert provider_checklist["readiness"] == provider_readiness, provider_checklist
    if provider_readiness == "fix-submission":
        assert provider_checklist["submission_status"] == "fail", provider_checklist
    else:
        assert provider_checklist["submission_status"] in {"missing", "not-found", "not-submitted"}, provider_checklist
    assert provider_checklist["source_accepted"] is True, provider_checklist
    assert provider_checklist["submission_path"] == "evidence/world_class/submissions/provider-holdout.json", provider_checklist
    assert provider_checklist["commands"]["validate_intake"] == "python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions", provider_checklist
    assert provider_checklist["commands"]["submission_review"] == "python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions", provider_checklist
    assert provider_checklist["commands"]["refresh_ledger"] == "python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions", provider_checklist
    assert "provider-backed model run" in provider_checklist["must_collect"]["provenance_requirements"], provider_checklist
    assert any(
        "output-exec --provider-runner openai" in step for step in provider_checklist["must_collect"]["runbook"]
    ), provider_checklist
    assert full_payload["data"]["world_class_claim_guard"]["summary"]["decision"] == "claim-guard-pass-evidence-pending"
    assert full_payload["data"]["world_class_claim_guard"]["summary"]["violation_count"] == 0
    assert full_payload["data"]["world_class_claim_guard"]["summary"]["ledger_pending_count"] == 4
