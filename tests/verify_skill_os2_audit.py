#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_skill_os2_audit.py"
TMP = ROOT / "tests" / "tmp_skill_os2_audit"


def main() -> None:
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True, exist_ok=True)
    output_json = TMP / "skill_os2_audit.json"
    output_md = TMP / "skill_os2_audit.md"
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
    assert payload["summary"]["decision"] == "continue-iteration", payload
    assert payload["summary"]["world_class_ready"] is False, payload
    assert payload["summary"]["missing_count"] == 0, payload
    assert payload["summary"]["pass_count"] >= 10, payload
    assert payload["summary"]["human_required_count"] >= 1, payload
    assert payload["summary"]["external_required_count"] >= 3, payload
    items = {item["key"]: item for item in payload["items"]}
    assert items["skill-ir"]["status"] == "pass", items["skill-ir"]
    assert items["target-compiler"]["status"] == "pass", items["target-compiler"]
    assert items["output-eval-lab"]["status"] == "pass", items["output-eval-lab"]
    assert items["provider-holdout"]["status"] == "external_required", items["provider-holdout"]
    assert items["human-adjudication"]["status"] == "human_required", items["human-adjudication"]
    assert items["native-permission-enforcement"]["status"] == "external_required", items["native-permission-enforcement"]
    assert items["native-client-telemetry"]["status"] == "external_required", items["native-client-telemetry"]
    assert any(entry["path"] == "scripts/provider_output_eval_runner.py" and entry["exists"] for entry in items["provider-holdout"]["evidence"])
    assert any(entry["path"] == "scripts/telemetry_native_host.py" and entry["exists"] for entry in items["native-client-telemetry"]["evidence"])
    markdown = output_md.read_text(encoding="utf-8")
    assert "Skill OS 2.0 Audit" in markdown, markdown
    assert "`provider-holdout`" in markdown, markdown
    assert "`human-adjudication`" in markdown, markdown
    assert "`native-client-telemetry`" in markdown, markdown
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
