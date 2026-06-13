#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_world_class_evidence_ledger.py"
TMP = ROOT / "tests" / "tmp_world_class_evidence_ledger"


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
    assert summary["ledger_entry_count"] == 4, summary
    assert summary["accepted_count"] == 0, summary
    assert summary["pending_count"] == 4, summary
    assert summary["human_pending_count"] == 1, summary
    assert summary["external_pending_count"] == 3, summary
    assert summary["overclaim_guard_active"] is True, summary
    assert summary["ready_to_claim_world_class"] is False, summary
    entries = {entry["key"]: entry for entry in payload["entries"]}
    assert set(entries) == {
        "provider-holdout",
        "human-adjudication",
        "native-permission-enforcement",
        "native-client-telemetry",
    }, entries
    assert entries["provider-holdout"]["observed_state"]["model_executed_count"] == 0, entries["provider-holdout"]
    assert entries["human-adjudication"]["observed_state"]["pending_count"] == 5, entries["human-adjudication"]
    assert entries["native-permission-enforcement"]["observed_state"]["native_enforcement_count"] == 0, entries["native-permission-enforcement"]
    assert any("summary.failure_count == 0" in check for check in entries["native-permission-enforcement"]["success_checks"]), entries["native-permission-enforcement"]
    assert entries["native-client-telemetry"]["observed_state"]["external_source_events"] == 0, entries["native-client-telemetry"]
    for entry in entries.values():
        assert entry["status"] == "pending", entry
        assert entry["success_checks"], entry
        assert entry["privacy_contract"], entry
        assert entry["anti_overclaim"]["planned_work_counts_as_evidence"] is False, entry
        assert entry["anti_overclaim"]["pending_review_counts_as_human_decision"] is False, entry
    markdown = output_md.read_text(encoding="utf-8")
    assert "World-Class Evidence Ledger" in markdown, markdown
    assert "overclaim guard active: `true`" in markdown, markdown
    assert "`provider-holdout`" in markdown, markdown
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
