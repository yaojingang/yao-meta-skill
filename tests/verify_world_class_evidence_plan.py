#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_world_class_evidence_plan.py"
TMP = ROOT / "tests" / "tmp_world_class_evidence"


def main() -> None:
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True, exist_ok=True)
    output_json = TMP / "world_class_evidence_plan.json"
    output_md = TMP / "world_class_evidence_plan.md"
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
    assert payload["summary"]["decision"] == "collect-external-evidence", payload
    assert payload["summary"]["ready_to_claim_world_class"] is False, payload
    assert payload["summary"]["task_count"] == 4, payload
    assert payload["summary"]["human_task_count"] == 1, payload
    assert payload["summary"]["external_task_count"] == 3, payload
    assert payload["artifacts"]["ledger"] == "reports/world_class_evidence_ledger.md", payload
    tasks = {item["key"]: item for item in payload["tasks"]}
    assert set(tasks) == {
        "provider-holdout",
        "human-adjudication",
        "native-permission-enforcement",
        "native-client-telemetry",
    }, tasks
    assert any("--provider-runner openai" in command for command in tasks["provider-holdout"]["runbook"]), tasks["provider-holdout"]
    assert any("output_review_decisions.json" in command for command in tasks["human-adjudication"]["runbook"]), tasks["human-adjudication"]
    assert any("runtime-permissions" in command for command in tasks["native-permission-enforcement"]["runbook"]), tasks["native-permission-enforcement"]
    assert any("summary.failure_count == 0" in check for check in tasks["native-permission-enforcement"]["success_checks"]), tasks["native-permission-enforcement"]
    assert any("telemetry_native_host.py" in command for command in tasks["native-client-telemetry"]["runbook"]), tasks["native-client-telemetry"]
    for task in tasks.values():
        assert task["success_checks"], task
        assert task["evidence_artifacts"], task
        assert task["privacy_contract"], task
    markdown = output_md.read_text(encoding="utf-8")
    assert "World-Class Evidence Plan" in markdown, markdown
    assert "`provider-holdout`" in markdown, markdown
    assert "ready to claim world-class: `false`" in markdown, markdown
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
