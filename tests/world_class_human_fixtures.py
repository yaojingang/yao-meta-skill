#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

from world_class_evidence_contract import validate_payload


ROOT = Path(__file__).resolve().parent.parent
TMP = ROOT / "tests" / "tmp_world_class_evidence_intake"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def human_submission(skill_root: Path, *, reviewer: str = "Yao QA") -> dict:
    return {
        "schema_version": "1.0",
        "evidence_key": "human-adjudication",
        "template_only": False,
        "category": "human",
        "source_type": "blind-ab-review",
        "submitted_by": reviewer,
        "submitted_at": "2026-06-14",
        "summary": "Completed blind A/B reviewer decisions for ledger review.",
        "artifact_refs": [
            {
                "path": "reports/output_review_adjudication.json",
                "kind": "adjudication-report",
                "contains_raw_content": False,
                "sha256": sha256_file(skill_root / "reports" / "output_review_adjudication.json"),
            },
            {
                "path": "reports/output_review_decisions.json",
                "kind": "review-decisions",
                "contains_raw_content": False,
                "sha256": sha256_file(skill_root / "reports" / "output_review_decisions.json"),
            },
        ],
        "provenance": {
            "reviewer": reviewer,
            "blind_pack_path": "reports/output_blind_review_pack.md",
            "answer_key_opened_after_decisions": True,
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
            "ledger_reviewer_approved": True,
            "ledger_reviewer": "Yao ledger reviewer",
            "ledger_reviewed_at": "2026-06-14",
        },
    }


def human_pairs(*, complete: bool) -> list[dict]:
    if complete:
        return [
            {
                "case_id": "case-a",
                "status": "match",
                "expected_revealed": True,
                "reviewer_winner_variant": "A",
                "confidence": 0.9,
                "reason": "Variant A follows the rubric.",
            },
            {
                "case_id": "case-b",
                "status": "disagree",
                "expected_revealed": True,
                "reviewer_winner_variant": "B",
                "confidence": 0.8,
                "reason": "Variant B handles the boundary.",
            },
        ]
    return [
        {
            "case_id": "case-a",
            "status": "match",
            "expected_revealed": True,
            "reviewer_winner_variant": "A",
            "confidence": 0.9,
            "reason": "Variant A follows the rubric.",
        },
        {
            "case_id": "case-b",
            "status": "pending",
            "expected_revealed": False,
            "reviewer_winner_variant": "",
            "confidence": None,
            "reason": "",
        },
    ]


def write_human_artifacts(skill_root: Path, *, complete: bool = True, reviewer: str = "Yao QA") -> None:
    reviewed_at = "2026-06-14"
    summary = {
        "pair_count": 2,
        "judgment_count": 2 if complete else 1,
        "pending_count": 0 if complete else 1,
        "agreement_count": 2 if complete else 1,
        "disagreement_count": 0,
        "invalid_decision_count": 0,
        "answer_revealed_count": 2 if complete else 1,
        "pending_answer_hidden_count": 0 if complete else 1,
        "agreement_rate": 100.0,
        "needs_review": not complete,
        "failure_count": 0,
    }
    decisions = [
        {"case_id": "case-a", "winner_variant": "A", "confidence": 0.9, "reason": "Variant A follows the rubric."},
        {
            "case_id": "case-b",
            "winner_variant": "B" if complete else "",
            "confidence": 0.8 if complete else None,
            "reason": "Variant B handles the boundary." if complete else "",
        },
    ]
    write_json(
        skill_root / "reports" / "output_review_adjudication.json",
        {
            "schema_version": "1.0",
            "ok": True,
            "summary": summary,
            "reviewer": reviewer,
            "reviewed_at": reviewed_at,
            "pairs": human_pairs(complete=complete),
            "failures": [],
        },
    )
    write_json(
        skill_root / "reports" / "output_review_decisions.json",
        {
            "schema_version": "1.0",
            "reviewer": reviewer,
            "reviewed_at": reviewed_at,
            "decisions": decisions,
        },
    )


def assert_human_submission_error(skill_root: Path, entry: dict, expected_error: str) -> None:
    result = validate_payload(
        human_submission(skill_root),
        entry,
        path=skill_root / "evidence" / "world_class" / "submissions" / "human-adjudication.json",
        root=skill_root,
        template_expected=False,
    )
    assert result["status"] == "fail", result
    assert any(expected_error in error for error in result["errors"]), result["errors"]


def assert_human_contract_artifact_validation() -> None:
    entry = {"key": "human-adjudication", "category": "human"}
    skill_root = TMP / "human_contract_root"
    write_human_artifacts(skill_root, complete=True)
    valid_result = validate_payload(
        human_submission(skill_root),
        entry,
        path=skill_root / "evidence" / "world_class" / "submissions" / "human-adjudication.json",
        root=skill_root,
        template_expected=False,
    )
    assert valid_result["status"] == "pass", valid_result
    assert valid_result["artifact_integrity"]["required_artifact_verified_count"] == 2, valid_result

    wrong_kind_submission = human_submission(skill_root)
    wrong_kind_submission["artifact_refs"][1]["kind"] = "aggregate-report"
    wrong_kind_result = validate_payload(
        wrong_kind_submission,
        entry,
        path=skill_root / "evidence" / "world_class" / "submissions" / "human-adjudication.json",
        root=skill_root,
        template_expected=False,
    )
    assert wrong_kind_result["status"] == "fail", wrong_kind_result
    assert any("kind must be review-decisions" in error for error in wrong_kind_result["errors"]), wrong_kind_result["errors"]

    write_human_artifacts(skill_root, complete=False)
    pending_result = validate_payload(
        human_submission(skill_root),
        entry,
        path=skill_root / "evidence" / "world_class" / "submissions" / "human-adjudication.json",
        root=skill_root,
        template_expected=False,
    )
    assert pending_result["status"] == "fail", pending_result
    assert any("summary.pending_count must be 0" in error for error in pending_result["errors"]), pending_result["errors"]
    assert any("summary.judgment_count must equal" in error for error in pending_result["errors"]), pending_result["errors"]
    assert any("summary.needs_review must be false" in error for error in pending_result["errors"]), pending_result["errors"]
    assert any("A/B winner_variant" in error for error in pending_result["errors"]), pending_result["errors"]

    write_human_artifacts(skill_root, complete=True, reviewer="Yao QA")
    mismatch_result = validate_payload(
        human_submission(skill_root, reviewer="Different Reviewer"),
        entry,
        path=skill_root / "evidence" / "world_class" / "submissions" / "human-adjudication.json",
        root=skill_root,
        template_expected=False,
    )
    assert mismatch_result["status"] == "fail", mismatch_result
    assert any("provenance.reviewer must match decisions.reviewer" in error for error in mismatch_result["errors"]), mismatch_result["errors"]

    write_human_artifacts(skill_root, complete=True, reviewer="Yao QA")
    forged_decisions = json.loads((skill_root / "reports" / "output_review_decisions.json").read_text(encoding="utf-8"))
    forged_decisions["decisions"][1]["case_id"] = "unknown-case"
    write_json(skill_root / "reports" / "output_review_decisions.json", forged_decisions)
    assert_human_submission_error(skill_root, entry, "case_id set must match adjudication pairs")

    write_human_artifacts(skill_root, complete=True, reviewer="Yao QA")
    forged_decisions = json.loads((skill_root / "reports" / "output_review_decisions.json").read_text(encoding="utf-8"))
    forged_decisions["decisions"][0]["confidence"] = 1.2
    write_json(skill_root / "reports" / "output_review_decisions.json", forged_decisions)
    assert_human_submission_error(skill_root, entry, "confidence must be between 0 and 1")

    write_human_artifacts(skill_root, complete=True, reviewer="Yao QA")
    forged_decisions = json.loads((skill_root / "reports" / "output_review_decisions.json").read_text(encoding="utf-8"))
    forged_decisions["decisions"][0]["expected_winner_variant"] = "A"
    write_json(skill_root / "reports" / "output_review_decisions.json", forged_decisions)
    assert_human_submission_error(skill_root, entry, "answer-key fields")

    write_human_artifacts(skill_root, complete=True, reviewer="Yao QA")
    forged_decisions = json.loads((skill_root / "reports" / "output_review_decisions.json").read_text(encoding="utf-8"))
    forged_decisions["decisions"][0]["metadata"] = {"raw_output": "verbatim model answer must not ship"}
    write_json(skill_root / "reports" / "output_review_decisions.json", forged_decisions)
    assert_human_submission_error(skill_root, entry, "decisions[1].metadata.raw_output")

    write_human_artifacts(skill_root, complete=True, reviewer="Yao QA")
    forged_decisions = json.loads((skill_root / "reports" / "output_review_decisions.json").read_text(encoding="utf-8"))
    forged_decisions["decisions"][0]["metadata"] = {"API_KEY": "credential material must not ship"}
    write_json(skill_root / "reports" / "output_review_decisions.json", forged_decisions)
    assert_human_submission_error(skill_root, entry, "decisions[1].metadata.API_KEY")
