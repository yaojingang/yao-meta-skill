#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "scripts" / "yao.py"
TMP = ROOT / "tests" / "tmp_yao_cli_world_class"


def run(*args: str) -> dict:
    env = dict(os.environ)
    env["YAO_CLI_TELEMETRY"] = "0"
    env.pop("YAO_CLI_TELEMETRY_EVENTS", None)
    proc = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    payload = json.loads(proc.stdout)
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "payload": payload,
        "stderr": proc.stderr,
    }


def main() -> None:
    if TMP.exists():
        subprocess.run(["rm", "-rf", str(TMP)], check=True)
    TMP.mkdir(parents=True, exist_ok=True)

    world_class_evidence_result = run(
        "world-class-evidence",
        str(ROOT),
        "--output-json",
        str(TMP / "world_class_evidence_plan.json"),
        "--output-md",
        str(TMP / "world_class_evidence_plan.md"),
        "--generated-at",
        "2026-06-13",
    )
    assert world_class_evidence_result["ok"], world_class_evidence_result
    assert world_class_evidence_result["payload"]["summary"]["decision"] == "collect-external-evidence", world_class_evidence_result
    assert world_class_evidence_result["payload"]["summary"]["ready_to_claim_world_class"] is False, world_class_evidence_result

    world_class_ledger_result = run(
        "world-class-ledger",
        str(ROOT),
        "--output-json",
        str(TMP / "world_class_evidence_ledger.json"),
        "--output-md",
        str(TMP / "world_class_evidence_ledger.md"),
        "--generated-at",
        "2026-06-13",
    )
    assert world_class_ledger_result["ok"], world_class_ledger_result
    ledger_payload = world_class_ledger_result["payload"]
    assert ledger_payload["report_contract"]["top_level_mirrors_summary"] is True, world_class_ledger_result
    assert ledger_payload["pending_count"] == ledger_payload["summary"]["pending_count"] == 4, world_class_ledger_result
    assert ledger_payload["summary"]["missing_submission_count"] == 4, world_class_ledger_result
    assert ledger_payload["summary"]["submitted_entry_count"] == 0, world_class_ledger_result

    world_class_intake_result = run(
        "world-class-intake",
        str(ROOT),
        "--output-json",
        str(TMP / "world_class_evidence_intake.json"),
        "--output-md",
        str(TMP / "world_class_evidence_intake.md"),
        "--generated-at",
        "2026-06-14",
    )
    assert world_class_intake_result["ok"], world_class_intake_result
    intake_summary = world_class_intake_result["payload"]["summary"]
    assert intake_summary["decision"] == "awaiting-submissions", world_class_intake_result
    assert intake_summary["template_pass_count"] == 4, world_class_intake_result
    assert intake_summary["operator_checklist_count"] == 4, world_class_intake_result
    assert intake_summary["operator_checklist_ready_count"] == 0, world_class_intake_result
    assert intake_summary["ready_to_claim_world_class"] is False, world_class_intake_result
    provider_checklist = next(
        item for item in world_class_intake_result["payload"]["operator_checklist"] if item["evidence_key"] == "provider-holdout"
    )
    assert provider_checklist["readiness"] == "awaiting-submission", provider_checklist
    assert provider_checklist["commands"]["prepare_submission"] == (
        "python3 scripts/yao.py world-class-submission-kit . "
        "--evidence-key provider-holdout --output-dir evidence/world_class/submissions"
    ), provider_checklist
    assert world_class_ledger_result["payload"]["summary"]["ready_to_claim_world_class"] is False, world_class_ledger_result

    world_class_submission_kit_result = run(
        "world-class-submission-kit",
        str(ROOT),
        "--output-dir",
        str(TMP / "world_class_submission_kit"),
        "--evidence-key",
        "provider-holdout",
        "--generated-at",
        "2026-06-14",
        "--output-html",
        str(TMP / "world_class_submission_kit.html"),
    )
    kit_payload = world_class_submission_kit_result["payload"]
    assert world_class_submission_kit_result["ok"], world_class_submission_kit_result
    assert kit_payload["summary"]["decision"] == "submission-kit-ready", world_class_submission_kit_result
    assert kit_payload["summary"]["written_count"] == 1, world_class_submission_kit_result
    assert kit_payload["summary"]["drafts_count_as_evidence"] is False, world_class_submission_kit_result
    assert kit_payload["artifacts"]["html"].endswith("tests/tmp_yao_cli_world_class/world_class_submission_kit.html"), world_class_submission_kit_result
    assert (TMP / "world_class_submission_kit" / "provider-holdout.json").exists(), world_class_submission_kit_result
    assert (TMP / "world_class_submission_kit" / "submission_manifest.json").exists(), world_class_submission_kit_result
    assert (TMP / "world_class_submission_kit.html").exists(), world_class_submission_kit_result

    world_class_submission_review_result = run(
        "world-class-submission-review",
        str(ROOT),
        "--submissions-dir",
        str(TMP / "world_class_submission_kit"),
        "--output-json",
        str(TMP / "world_class_submission_review.json"),
        "--output-md",
        str(TMP / "world_class_submission_review.md"),
        "--generated-at",
        "2026-06-14",
    )
    assert not world_class_submission_review_result["ok"], world_class_submission_review_result
    assert world_class_submission_review_result["returncode"] == 2, world_class_submission_review_result
    review_payload = world_class_submission_review_result["payload"]
    assert review_payload["report_contract"]["top_level_mirrors_summary"] is True, world_class_submission_review_result
    assert review_payload["summary"]["decision"] == "fix-submissions", world_class_submission_review_result
    assert review_payload["invalid_submission_count"] == review_payload["summary"]["invalid_submission_count"] == 1, world_class_submission_review_result
    assert review_payload["items"][0]["review_state"] == "fix-submission", world_class_submission_review_result
    assert (TMP / "world_class_submission_review.md").exists(), world_class_submission_review_result

    world_class_claim_guard_result = run(
        "world-class-claim-guard",
        str(ROOT),
        "--output-json",
        str(TMP / "world_class_claim_guard.json"),
        "--output-md",
        str(TMP / "world_class_claim_guard.md"),
        "--generated-at",
        "2026-06-14",
    )
    assert world_class_claim_guard_result["ok"], world_class_claim_guard_result
    assert world_class_claim_guard_result["payload"]["summary"]["decision"] == "claim-guard-pass-evidence-pending", world_class_claim_guard_result
    assert world_class_claim_guard_result["payload"]["summary"]["violation_count"] == 0, world_class_claim_guard_result
    assert world_class_claim_guard_result["payload"]["summary"]["ledger_pending_count"] == 4, world_class_claim_guard_result

    benchmark_reproducibility_result = run(
        "benchmark-reproducibility",
        str(ROOT),
        "--output-json",
        str(TMP / "benchmark_reproducibility.json"),
        "--output-md",
        str(TMP / "benchmark_reproducibility.md"),
        "--generated-at",
        "2026-06-13",
    )
    assert benchmark_reproducibility_result["ok"], benchmark_reproducibility_result
    assert benchmark_reproducibility_result["payload"]["summary"]["reproducibility_ready"] is True, benchmark_reproducibility_result
    assert benchmark_reproducibility_result["payload"]["summary"]["world_class_ready"] is False, benchmark_reproducibility_result

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
