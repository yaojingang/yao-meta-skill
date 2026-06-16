#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from output_review_privacy import BLOCKED_DECISION_FIELDS  # noqa: E402

OUTPUT_EVAL = ROOT / "scripts" / "run_output_eval.py"
ADJUDICATOR = ROOT / "scripts" / "adjudicate_output_review.py"
IMPORTER = ROOT / "scripts" / "import_output_review_decisions.py"
CLI = ROOT / "scripts" / "yao.py"


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=check,
    )


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def adjudicate_payload(
    tmp_root: Path,
    blind_pack_json: Path,
    answer_key_json: Path,
    name: str,
    decisions: dict,
) -> tuple[subprocess.CompletedProcess[str], dict]:
    decisions_path = tmp_root / f"{name}_decisions.json"
    write_json(decisions_path, decisions)
    proc = run(
        [
            str(ADJUDICATOR),
            "--blind-pack",
            str(blind_pack_json),
            "--answer-key",
            str(answer_key_json),
            "--decisions",
            str(decisions_path),
            "--output-json",
            str(tmp_root / f"{name}_adjudication.json"),
            "--output-md",
            str(tmp_root / f"{name}_adjudication.md"),
        ],
        check=False,
    )
    return proc, json.loads(proc.stdout)


def main() -> None:
    assert {"api_key", "raw_provider_prompt", "expected_winner_role"} <= BLOCKED_DECISION_FIELDS

    tmp_root = ROOT / "tests" / "tmp_output_review_adjudication"
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    tmp_root.mkdir(parents=True, exist_ok=True)

    scorecard_json = tmp_root / "output_quality_scorecard.json"
    scorecard_md = tmp_root / "output_quality_scorecard.md"
    blind_pack_json = tmp_root / "output_blind_review_pack.json"
    blind_pack_md = tmp_root / "output_blind_review_pack.md"
    answer_key_json = tmp_root / "output_blind_answer_key.json"

    run(
        [
            str(OUTPUT_EVAL),
            "--cases",
            str(ROOT / "evals" / "output" / "cases.jsonl"),
            "--output-json",
            str(scorecard_json),
            "--output-md",
            str(scorecard_md),
            "--blind-pack-json",
            str(blind_pack_json),
            "--blind-pack-md",
            str(blind_pack_md),
            "--blind-answer-key-json",
            str(answer_key_json),
        ]
    )

    pending_json = tmp_root / "pending_adjudication.json"
    pending_md = tmp_root / "pending_adjudication.md"
    pending_proc = run(
        [
            str(ADJUDICATOR),
            "--blind-pack",
            str(blind_pack_json),
            "--answer-key",
            str(answer_key_json),
            "--decisions",
            str(tmp_root / "missing_decisions.json"),
            "--output-json",
            str(pending_json),
            "--output-md",
            str(pending_md),
        ]
    )
    pending_payload = json.loads(pending_proc.stdout)
    assert pending_payload["ok"], pending_payload
    assert pending_payload["summary"]["pair_count"] == 5, pending_payload
    assert pending_payload["summary"]["judgment_count"] == 0, pending_payload
    assert pending_payload["summary"]["pending_count"] == 5, pending_payload
    assert pending_payload["summary"]["agreement_rate"] is None, pending_payload
    assert pending_payload["summary"]["needs_review"], pending_payload
    assert pending_payload["summary"]["answer_revealed_count"] == 0, pending_payload
    assert pending_payload["summary"]["pending_answer_hidden_count"] == 5, pending_payload
    assert pending_payload["summary"]["reviewer_checklist_count"] == 5, pending_payload
    assert pending_payload["summary"]["reviewer_checklist_pending_count"] == 5, pending_payload
    assert pending_payload["summary"]["reviewer_checklist_ready_count"] == 0, pending_payload
    assert pending_payload["summary"]["reviewer_checklist_invalid_count"] == 0, pending_payload
    assert pending_payload["summary"]["reviewer_metadata_present"] is False, pending_payload
    assert pending_payload["summary"]["reason_required"] is True, pending_payload
    assert pending_payload["summary"]["ready_for_human_evidence"] is False, pending_payload
    assert all(not item["expected_winner_variant"] and not item["expected_revealed"] for item in pending_payload["pairs"]), pending_payload
    assert all("prompt" not in item and len(item["prompt_sha256"]) == 64 for item in pending_payload["pairs"]), pending_payload
    checklist = {item["case_id"]: item for item in pending_payload["reviewer_checklist"]}
    assert checklist["skill-package-contract"]["readiness"] == "awaiting-decision", checklist["skill-package-contract"]
    assert checklist["skill-package-contract"]["answer_key_visible"] is False, checklist["skill-package-contract"]
    assert "prompt" not in checklist["skill-package-contract"] and len(checklist["skill-package-contract"]["prompt_sha256"]) == 64, checklist["skill-package-contract"]
    assert checklist["skill-package-contract"]["decisions_path"].endswith("tests/tmp_output_review_adjudication/missing_decisions.json"), checklist["skill-package-contract"]
    assert checklist["skill-package-contract"]["commands"]["write_template"] == "python3 scripts/adjudicate_output_review.py --write-template", checklist["skill-package-contract"]
    assert checklist["skill-package-contract"]["commands"]["import_decisions"].startswith("python3 scripts/yao.py output-review-import"), checklist["skill-package-contract"]
    assert checklist["skill-package-contract"]["required_fields"]["winner_variant"].startswith("A or B"), checklist["skill-package-contract"]
    assert checklist["skill-package-contract"]["required_fields"]["reason"].startswith("Required rationale"), checklist["skill-package-contract"]
    assert "reviewer" in checklist["skill-package-contract"]["required_fields"], checklist["skill-package-contract"]
    assert "reviewed_at" in checklist["skill-package-contract"]["required_fields"], checklist["skill-package-contract"]
    assert "No reviewer decisions recorded yet" in pending_md.read_text(encoding="utf-8"), pending_md
    pending_text = pending_md.read_text(encoding="utf-8")
    assert "| skill-package-contract | pending | hidden | pending |" in pending_text, pending_text
    assert "| skill-package-contract | pending | A | pending |" not in pending_text, pending_text
    assert "Reviewer Checklist" in pending_text, pending_text
    assert "Reviewer checklist: `0` ready / `5` total" in pending_text, pending_text
    assert "answer key visible: `false`" in pending_text, pending_text
    assert "Ready for human evidence: `false`" in pending_text, pending_text

    template_path = tmp_root / "output_review_decisions.json"
    template_proc = run(
        [
            str(ADJUDICATOR),
            "--blind-pack",
            str(blind_pack_json),
            "--answer-key",
            str(answer_key_json),
            "--decisions",
            str(template_path),
            "--output-json",
            str(tmp_root / "template_adjudication.json"),
            "--output-md",
            str(tmp_root / "template_adjudication.md"),
            "--write-template",
        ]
    )
    template_payload = json.loads(template_proc.stdout)
    assert template_payload["ok"], template_payload
    assert template_payload["template_written"], template_payload
    template = json.loads(template_path.read_text(encoding="utf-8"))
    assert len(template["decisions"]) == 5, template
    assert all(item["winner_variant"] == "" for item in template["decisions"]), template

    answer_key = json.loads(answer_key_json.read_text(encoding="utf-8"))
    decisions = {
        "schema_version": "1.0",
        "reviewer": "Yao QA",
        "reviewed_at": "2026-06-13",
        "decisions": [
            {
                "case_id": item["case_id"],
                "winner_variant": item["expected_winner_variant"],
                "confidence": 0.9,
                "reason": "Matches the rubric better.",
            }
            for item in answer_key["answers"]
        ],
    }
    filled_path = tmp_root / "filled_decisions.json"
    filled_path.write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    filled_proc = run(
        [
            str(ADJUDICATOR),
            "--blind-pack",
            str(blind_pack_json),
            "--answer-key",
            str(answer_key_json),
            "--decisions",
            str(filled_path),
            "--output-json",
            str(tmp_root / "filled_adjudication.json"),
            "--output-md",
            str(tmp_root / "filled_adjudication.md"),
        ]
    )
    filled_payload = json.loads(filled_proc.stdout)
    assert filled_payload["ok"], filled_payload
    assert filled_payload["summary"]["judgment_count"] == 5, filled_payload
    assert filled_payload["summary"]["pending_count"] == 0, filled_payload
    assert filled_payload["summary"]["agreement_count"] == 5, filled_payload
    assert filled_payload["summary"]["agreement_rate"] == 100.0, filled_payload
    assert filled_payload["summary"]["answer_revealed_count"] == 5, filled_payload
    assert filled_payload["summary"]["pending_answer_hidden_count"] == 0, filled_payload
    assert filled_payload["summary"]["reviewer_checklist_ready_count"] == 5, filled_payload
    assert filled_payload["summary"]["reviewer_checklist_pending_count"] == 0, filled_payload
    assert filled_payload["summary"]["reviewer_metadata_present"] is True, filled_payload
    assert filled_payload["summary"]["ready_for_human_evidence"] is True, filled_payload
    assert all(item["status"] == "match" for item in filled_payload["pairs"]), filled_payload
    assert all(item["expected_winner_variant"] in {"A", "B"} and item["expected_revealed"] for item in filled_payload["pairs"]), filled_payload
    assert all("prompt" not in item and len(item["prompt_sha256"]) == 64 for item in filled_payload["pairs"]), filled_payload
    filled_checklist = {item["case_id"]: item for item in filled_payload["reviewer_checklist"]}
    assert all(item["readiness"] == "adjudicated" and item["answer_key_visible"] and "prompt" not in item and len(item["prompt_sha256"]) == 64 for item in filled_checklist.values()), filled_checklist

    import_source = tmp_root / "reviewer_source.json"
    import_source.write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    imported_path = tmp_root / "imported_decisions.json"
    imported_proc = run(
        [
            str(IMPORTER),
            "--input",
            str(import_source),
            "--blind-pack",
            str(blind_pack_json),
            "--output-json",
            str(imported_path),
            "--run-adjudication",
            "--answer-key",
            str(answer_key_json),
            "--adjudication-json",
            str(tmp_root / "imported_adjudication.json"),
            "--adjudication-md",
            str(tmp_root / "imported_adjudication.md"),
        ]
    )
    imported_payload = json.loads(imported_proc.stdout)
    assert imported_payload["ok"], imported_payload
    assert imported_payload["summary"]["canonical_written"] is True, imported_payload
    assert imported_payload["summary"]["adjudication_run"] is True, imported_payload
    assert imported_payload["summary"]["adjudication_pending_count"] == 0, imported_payload
    imported_decisions = json.loads(imported_path.read_text(encoding="utf-8"))
    assert imported_decisions["import_contract"]["raw_content_allowed"] is False, imported_decisions
    assert imported_decisions["import_contract"]["answer_key_fields_allowed"] is False, imported_decisions
    assert imported_decisions["import_contract"]["answer_key_opened_by_importer"] is False, imported_decisions
    assert imported_decisions["reviewer"] == "Yao QA", imported_decisions

    no_reason_source = tmp_root / "no_reason_source.json"
    write_json(
        no_reason_source,
        {
            "reviewer": "Yao QA",
            "reviewed_at": "2026-06-13",
            "decisions": [
                {
                    "case_id": answer_key["answers"][0]["case_id"],
                    "winner_variant": answer_key["answers"][0]["expected_winner_variant"],
                    "confidence": 0.8,
                }
            ],
        },
    )
    no_reason_import_proc = run(
        [
            str(IMPORTER),
            "--input",
            str(no_reason_source),
            "--blind-pack",
            str(blind_pack_json),
            "--output-json",
            str(tmp_root / "no_reason_decisions.json"),
        ],
        check=False,
    )
    no_reason_import_payload = json.loads(no_reason_import_proc.stdout)
    assert no_reason_import_proc.returncode == 2, no_reason_import_payload
    assert any("reason is required for imported human decisions" in failure for failure in no_reason_import_payload["failures"]), no_reason_import_payload
    assert not (tmp_root / "no_reason_decisions.json").exists(), no_reason_import_payload

    cli_import_proc = run(
        [
            str(CLI),
            "output-review-import",
            "--input",
            str(import_source),
            "--blind-pack",
            str(blind_pack_json),
            "--output-json",
            str(tmp_root / "cli_imported_decisions.json"),
            "--run-adjudication",
            "--answer-key",
            str(answer_key_json),
            "--adjudication-json",
            str(tmp_root / "cli_imported_adjudication.json"),
            "--adjudication-md",
            str(tmp_root / "cli_imported_adjudication.md"),
        ]
    )
    cli_import_payload = json.loads(cli_import_proc.stdout)
    assert cli_import_payload["ok"], cli_import_payload
    assert cli_import_payload["summary"]["canonical_written"] is True, cli_import_payload
    assert cli_import_payload["summary"]["adjudication_pending_count"] == 0, cli_import_payload

    jsonl_source = tmp_root / "reviewer_source.jsonl"
    jsonl_source.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in decisions["decisions"]) + "\n", encoding="utf-8")
    jsonl_proc = run(
        [
            str(IMPORTER),
            "--input",
            str(jsonl_source),
            "--blind-pack",
            str(blind_pack_json),
            "--output-json",
            str(tmp_root / "jsonl_decisions.json"),
            "--reviewer",
            "Yao QA",
            "--reviewed-at",
            "2026-06-13",
        ]
    )
    jsonl_payload = json.loads(jsonl_proc.stdout)
    assert jsonl_payload["ok"], jsonl_payload
    assert jsonl_payload["summary"]["completed_decision_count"] == 5, jsonl_payload

    csv_source = tmp_root / "reviewer_source.csv"
    csv_source.write_text(
        "case_id,winner_variant,confidence,reason\n"
        + "\n".join(
            f"{item['case_id']},{item['expected_winner_variant']},0.8,CSV reviewer choice"
            for item in answer_key["answers"]
        )
        + "\n",
        encoding="utf-8",
    )
    csv_proc = run(
        [
            str(IMPORTER),
            "--input",
            str(csv_source),
            "--blind-pack",
            str(blind_pack_json),
            "--output-json",
            str(tmp_root / "csv_decisions.json"),
            "--reviewer",
            "Yao QA",
            "--reviewed-at",
            "2026-06-13",
        ]
    )
    csv_payload = json.loads(csv_proc.stdout)
    assert csv_payload["ok"], csv_payload
    assert csv_payload["summary"]["completed_decision_count"] == 5, csv_payload

    private_source = tmp_root / "private_source.json"
    private_source.write_text(
        json.dumps(
            {
                "reviewer": "Yao QA",
                "reviewed_at": "2026-06-13",
                "decisions": [
                    {
                        "case_id": answer_key["answers"][0]["case_id"],
                        "winner_variant": "A",
                        "prompt": "raw prompt must not be imported",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    private_proc = run(
        [
            str(IMPORTER),
            "--input",
            str(private_source),
            "--blind-pack",
            str(blind_pack_json),
            "--output-json",
            str(tmp_root / "private_decisions.json"),
        ],
        check=False,
    )
    private_payload = json.loads(private_proc.stdout)
    assert private_proc.returncode == 2, private_payload
    assert private_payload["ok"] is False, private_payload
    assert any("forbidden raw or answer-key fields" in failure for failure in private_payload["failures"]), private_payload
    assert not (tmp_root / "private_decisions.json").exists(), private_payload

    nested_private_source = tmp_root / "nested_private_source.json"
    nested_private_source.write_text(
        json.dumps(
            {
                "reviewer": "Yao QA",
                "reviewed_at": "2026-06-13",
                "decisions": [
                    {
                        "case_id": answer_key["answers"][0]["case_id"],
                        "winner_variant": "A",
                        "metadata": {"Raw_Output": "nested raw output must not be imported"},
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    nested_private_proc = run(
        [
            str(IMPORTER),
            "--input",
            str(nested_private_source),
            "--blind-pack",
            str(blind_pack_json),
            "--output-json",
            str(tmp_root / "nested_private_decisions.json"),
        ],
        check=False,
    )
    nested_private_payload = json.loads(nested_private_proc.stdout)
    assert nested_private_proc.returncode == 2, nested_private_payload
    assert nested_private_payload["ok"] is False, nested_private_payload
    assert any("decision #1.metadata.Raw_Output" in failure for failure in nested_private_payload["failures"]), nested_private_payload
    assert not (tmp_root / "nested_private_decisions.json").exists(), nested_private_payload

    credential_source = tmp_root / "credential_source.json"
    credential_source.write_text(
        json.dumps(
            {
                "reviewer": "Yao QA",
                "reviewed_at": "2026-06-13",
                "decisions": [
                    {
                        "case_id": answer_key["answers"][0]["case_id"],
                        "winner_variant": "A",
                        "metadata": {"API_KEY": "credential material must not be imported"},
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    credential_proc = run(
        [
            str(IMPORTER),
            "--input",
            str(credential_source),
            "--blind-pack",
            str(blind_pack_json),
            "--output-json",
            str(tmp_root / "credential_decisions.json"),
        ],
        check=False,
    )
    credential_payload = json.loads(credential_proc.stdout)
    assert credential_proc.returncode == 2, credential_payload
    assert credential_payload["ok"] is False, credential_payload
    assert any("decision #1.metadata.API_KEY" in failure for failure in credential_payload["failures"]), credential_payload
    assert not (tmp_root / "credential_decisions.json").exists(), credential_payload

    unknown_case = tmp_root / "unknown_case.json"
    unknown_case.write_text(
        json.dumps(
            {
                "reviewer": "Yao QA",
                "reviewed_at": "2026-06-13",
                "decisions": [{"case_id": "unknown", "winner_variant": "A"}],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    unknown_proc = run(
        [
            str(IMPORTER),
            "--input",
            str(unknown_case),
            "--blind-pack",
            str(blind_pack_json),
            "--output-json",
            str(tmp_root / "unknown_decisions.json"),
        ],
        check=False,
    )
    unknown_payload = json.loads(unknown_proc.stdout)
    assert unknown_proc.returncode == 2, unknown_payload
    assert any("unknown case_id" in failure for failure in unknown_payload["failures"]), unknown_payload

    invalid = {
        "schema_version": "1.0",
        "reviewer": "Yao QA",
        "reviewed_at": "2026-06-13",
        "decisions": [
            {
                "case_id": answer_key["answers"][0]["case_id"],
                "winner_variant": "C",
                "confidence": 0.9,
                "reason": "Invalid variant should fail validation.",
            }
        ],
    }
    invalid_path = tmp_root / "invalid_decisions.json"
    invalid_path.write_text(json.dumps(invalid, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    invalid_proc = run(
        [
            str(ADJUDICATOR),
            "--blind-pack",
            str(blind_pack_json),
            "--answer-key",
            str(answer_key_json),
            "--decisions",
            str(invalid_path),
            "--output-json",
            str(tmp_root / "invalid_adjudication.json"),
            "--output-md",
            str(tmp_root / "invalid_adjudication.md"),
        ],
        check=False,
    )
    assert invalid_proc.returncode == 2, invalid_proc.stdout
    invalid_payload = json.loads(invalid_proc.stdout)
    assert not invalid_payload["ok"], invalid_payload
    assert invalid_payload["summary"]["invalid_decision_count"] == 1, invalid_payload
    assert invalid_payload["summary"]["answer_revealed_count"] == 0, invalid_payload
    assert invalid_payload["summary"]["reviewer_checklist_invalid_count"] == 1, invalid_payload
    assert invalid_payload["pairs"][0]["expected_winner_variant"] == "", invalid_payload
    assert invalid_payload["pairs"][0]["expected_revealed"] is False, invalid_payload
    invalid_checklist = {item["case_id"]: item for item in invalid_payload["reviewer_checklist"]}
    assert invalid_checklist[answer_key["answers"][0]["case_id"]]["readiness"] == "fix-decision", invalid_checklist
    assert invalid_checklist[answer_key["answers"][0]["case_id"]]["answer_key_visible"] is False, invalid_checklist
    assert invalid_payload["failures"], invalid_payload

    no_reason_direct = {
        "schema_version": "1.0",
        "reviewer": "Yao QA",
        "reviewed_at": "2026-06-13",
        "decisions": [
            {
                "case_id": answer_key["answers"][0]["case_id"],
                "winner_variant": answer_key["answers"][0]["expected_winner_variant"],
                "confidence": 0.9,
                "reason": "",
            }
        ],
    }
    no_reason_proc, no_reason_payload = adjudicate_payload(
        tmp_root, blind_pack_json, answer_key_json, "no_reason", no_reason_direct
    )
    assert no_reason_proc.returncode == 2, no_reason_proc.stdout
    assert no_reason_payload["summary"]["invalid_decision_count"] == 1, no_reason_payload
    assert no_reason_payload["summary"]["answer_revealed_count"] == 0, no_reason_payload
    assert no_reason_payload["summary"]["ready_for_human_evidence"] is False, no_reason_payload
    assert no_reason_payload["pairs"][0]["expected_winner_variant"] == "", no_reason_payload
    assert no_reason_payload["pairs"][0]["expected_revealed"] is False, no_reason_payload
    assert any("reason is required before answer key can be revealed" in failure for failure in no_reason_payload["failures"]), no_reason_payload

    missing_metadata = {
        "schema_version": "1.0",
        "decisions": [
            {
                "case_id": answer_key["answers"][0]["case_id"],
                "winner_variant": answer_key["answers"][0]["expected_winner_variant"],
                "confidence": 0.9,
                "reason": "Visible rubric-based rationale.",
            }
        ],
    }
    missing_metadata_proc, missing_metadata_payload = adjudicate_payload(
        tmp_root, blind_pack_json, answer_key_json, "missing_metadata", missing_metadata
    )
    assert missing_metadata_proc.returncode == 2, missing_metadata_proc.stdout
    assert missing_metadata_payload["summary"]["reviewer_metadata_present"] is False, missing_metadata_payload
    assert missing_metadata_payload["summary"]["invalid_decision_count"] == 1, missing_metadata_payload
    assert missing_metadata_payload["summary"]["answer_revealed_count"] == 0, missing_metadata_payload
    assert missing_metadata_payload["summary"]["ready_for_human_evidence"] is False, missing_metadata_payload
    assert any("reviewer and reviewed_at are required" in failure for failure in missing_metadata_payload["failures"]), missing_metadata_payload

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
