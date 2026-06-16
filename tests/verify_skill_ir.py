#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "export_skill_ir.py"


def main() -> None:
    output_path = ROOT / "tests" / "tmp_skill_ir" / "yao-meta-skill.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(ROOT),
            "--output-json",
            str(output_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    result = json.loads(proc.stdout)
    assert result["ok"], result
    assert result["summary"]["name"] == "yao-meta-skill", result
    assert result["summary"]["trigger_samples"] >= 3, result
    assert output_path.exists(), output_path

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "2.0.0", payload
    assert payload["name"] == "yao-meta-skill", payload
    assert payload["job_to_be_done"], payload
    assert payload["trigger_surface"]["description"], payload
    assert payload["trigger_surface"]["should_trigger"], payload
    assert payload["trigger_surface"]["should_not_trigger"], payload
    assert payload["trigger_surface"]["edge_cases"], payload
    assert payload["workflow"]["steps"], payload
    assert payload["workflow"]["decision_points"], payload
    assert any("`Governed`" in item for item in payload["workflow"]["decision_points"]), payload["workflow"]["decision_points"]
    assert payload["resources"]["references"], payload
    assert payload["resources"]["scripts"], payload
    expected_scripts = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "scripts").rglob("*")
        if path.is_file() and path.suffix in {".py", ".sh", ".js", ".ts"}
    }
    actual_scripts = set(payload["resources"]["scripts"])
    assert expected_scripts <= actual_scripts, sorted(expected_scripts - actual_scripts)
    assert "assets/skill-overview.css" in payload["resources"]["assets"], payload["resources"]["assets"]
    assert "assets/skill-overview.js" in payload["resources"]["assets"], payload["resources"]["assets"]
    assert "assets/review-studio.css" in payload["resources"]["assets"], payload["resources"]["assets"]
    assert "assets/review-viewer.css" in payload["resources"]["assets"], payload["resources"]["assets"]
    assert payload["resources"]["reports"], payload
    assert "evals/trigger_cases.json" in payload["eval_plan"]["trigger"], payload["eval_plan"]
    assert payload["risk"]["trust_boundary"] == "external", payload
    assert payload["governance"]["maturity"] == "governed", payload
    assert "openai" in payload["targets"], payload

    validate_proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(ROOT), "--validate-only"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    validate_result = json.loads(validate_proc.stdout)
    assert validate_result["ok"], validate_result

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
