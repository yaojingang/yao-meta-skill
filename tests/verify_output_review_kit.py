#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_EVAL = ROOT / "scripts" / "run_output_eval.py"
REVIEW_KIT = ROOT / "scripts" / "prepare_output_review_kit.py"
CLI = ROOT / "scripts" / "yao.py"


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=check,
    )


def assert_no_answer_key_leak(text: str) -> None:
    forbidden = [
        "output_blind_answer_key",
        "expected_winner",
        "variant_a_role",
        "variant_b_role",
        "score_winner_role",
    ]
    for needle in forbidden:
        assert needle not in text, f"review kit leaked hidden field {needle!r}"


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_output_review_kit"
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

    decisions_path = tmp_root / "output_review_decisions.json"
    kit_json = tmp_root / "output_review_kit.json"
    kit_md = tmp_root / "output_review_kit.md"
    kit_html = tmp_root / "output_review_kit.html"
    pending_proc = run(
        [
            str(REVIEW_KIT),
            "--blind-pack-json",
            str(blind_pack_json),
            "--blind-pack-md",
            str(blind_pack_md),
            "--decisions",
            str(decisions_path),
            "--output-json",
            str(kit_json),
            "--output-md",
            str(kit_md),
            "--output-html",
            str(kit_html),
            "--write-template",
        ]
    )
    pending_payload = json.loads(pending_proc.stdout)
    assert pending_payload["ok"], pending_payload
    assert pending_payload["template_written"], pending_payload
    assert pending_payload["summary"]["case_count"] == 5, pending_payload
    assert pending_payload["summary"]["pending_decision_count"] == 5, pending_payload
    assert pending_payload["summary"]["ready_for_adjudication_count"] == 0, pending_payload
    assert pending_payload["summary"]["answer_key_hidden"] is True, pending_payload
    assert pending_payload["summary"]["answer_key_path_exposed"] is False, pending_payload
    assert pending_payload["summary"]["ready_to_run_adjudication"] is False, pending_payload
    assert "answer_key" not in pending_payload["artifacts"], pending_payload["artifacts"]
    assert pending_payload["artifacts"]["reviewer_kit_html"].endswith("tests/tmp_output_review_kit/output_review_kit.html"), pending_payload["artifacts"]
    assert len(pending_payload["cases"]) == 5, pending_payload["cases"]
    first_case = pending_payload["cases"][0]
    assert first_case["variant_a"]["output"], first_case
    assert first_case["variant_b"]["output"], first_case
    assert first_case["decision_state"]["status"] == "awaiting-decision", first_case
    assert decisions_path.exists(), decisions_path

    kit_json_text = kit_json.read_text(encoding="utf-8")
    kit_md_text = kit_md.read_text(encoding="utf-8")
    kit_html_text = kit_html.read_text(encoding="utf-8")
    assert "# Output Review Kit" in kit_md_text, kit_md_text
    assert "answer key path exposed: `false`" in kit_md_text, kit_md_text
    assert "Variant A" in kit_md_text and "Variant B" in kit_md_text, kit_md_text
    assert "python3 scripts/yao.py output-review" in kit_md_text, kit_md_text
    assert "<title>Output Review Kit</title>" in kit_html_text, kit_html_text
    assert "Reviewer cockpit for output quality decisions" in kit_html_text, kit_html_text
    assert "Variant A" in kit_html_text and "Variant B" in kit_html_text, kit_html_text
    assert "Decision Template" in kit_html_text, kit_html_text
    assert_no_answer_key_leak(kit_json_text)
    assert_no_answer_key_leak(kit_md_text)
    assert_no_answer_key_leak(kit_html_text)

    cli_proc = run(
        [
            str(CLI),
            "output-review-kit",
            "--blind-pack-json",
            str(blind_pack_json),
            "--blind-pack-md",
            str(blind_pack_md),
            "--decisions",
            str(decisions_path),
            "--output-json",
            str(tmp_root / "cli_output_review_kit.json"),
            "--output-md",
            str(tmp_root / "cli_output_review_kit.md"),
            "--output-html",
            str(tmp_root / "cli_output_review_kit.html"),
        ]
    )
    cli_payload = json.loads(cli_proc.stdout)
    assert cli_payload["ok"], cli_payload
    assert cli_payload["summary"]["case_count"] == 5, cli_payload
    assert cli_payload["summary"]["answer_key_hidden"] is True, cli_payload
    assert "answer_key" not in cli_payload["artifacts"], cli_payload["artifacts"]
    assert (tmp_root / "cli_output_review_kit.html").exists(), cli_payload

    template = json.loads(decisions_path.read_text(encoding="utf-8"))
    filled = {
        "schema_version": "1.0",
        "reviewer": "Yao QA",
        "reviewed_at": "2026-06-14",
        "decisions": [
            {
                "case_id": item["case_id"],
                "winner_variant": "A",
                "confidence": 0.8,
                "reason": "Variant A is clearer against the visible rubric.",
            }
            for item in template["decisions"]
        ],
    }
    decisions_path.write_text(json.dumps(filled, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ready_proc = run(
        [
            str(REVIEW_KIT),
            "--blind-pack-json",
            str(blind_pack_json),
            "--blind-pack-md",
            str(blind_pack_md),
            "--decisions",
            str(decisions_path),
            "--output-json",
            str(tmp_root / "ready_output_review_kit.json"),
            "--output-md",
            str(tmp_root / "ready_output_review_kit.md"),
            "--output-html",
            str(tmp_root / "ready_output_review_kit.html"),
        ]
    )
    ready_payload = json.loads(ready_proc.stdout)
    assert ready_payload["ok"], ready_payload
    assert ready_payload["summary"]["ready_for_adjudication_count"] == 5, ready_payload
    assert ready_payload["summary"]["pending_decision_count"] == 0, ready_payload
    assert ready_payload["summary"]["invalid_decision_count"] == 0, ready_payload
    assert ready_payload["summary"]["reviewer_metadata_present"] is True, ready_payload
    assert ready_payload["summary"]["ready_to_run_adjudication"] is True, ready_payload
    assert all(case["decision_state"]["status"] == "ready-for-adjudication" for case in ready_payload["cases"]), ready_payload

    invalid = dict(filled)
    invalid["decisions"] = [dict(filled["decisions"][0], winner_variant="C", reason="")]
    invalid_path = tmp_root / "invalid_output_review_decisions.json"
    invalid_path.write_text(json.dumps(invalid, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    invalid_proc = run(
        [
            str(REVIEW_KIT),
            "--blind-pack-json",
            str(blind_pack_json),
            "--blind-pack-md",
            str(blind_pack_md),
            "--decisions",
            str(invalid_path),
            "--output-json",
            str(tmp_root / "invalid_output_review_kit.json"),
            "--output-md",
            str(tmp_root / "invalid_output_review_kit.md"),
            "--output-html",
            str(tmp_root / "invalid_output_review_kit.html"),
        ]
    )
    invalid_payload = json.loads(invalid_proc.stdout)
    assert invalid_payload["ok"], invalid_payload
    assert invalid_payload["summary"]["invalid_decision_count"] == 1, invalid_payload
    assert invalid_payload["summary"]["answer_key_hidden"] is True, invalid_payload
    assert invalid_payload["cases"][0]["decision_state"]["status"] == "needs-fix", invalid_payload["cases"][0]

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
