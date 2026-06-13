#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_benchmark_reproducibility.py"
TMP = ROOT / "tests" / "tmp_benchmark_reproducibility"


def main() -> None:
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "render_world_class_evidence_ledger.py"),
            str(ROOT),
            "--generated-at",
            "2026-06-13",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    output_json = TMP / "benchmark_reproducibility.json"
    output_md = TMP / "benchmark_reproducibility.md"
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
    assert payload["summary"]["reproducibility_ready"] is True, payload
    assert payload["summary"]["methodology_complete"] is True, payload
    assert payload["summary"]["missing_artifact_count"] == 0, payload
    assert payload["summary"]["output_case_count"] >= 5, payload
    assert payload["summary"]["failure_disclosure_count"] >= 1, payload
    assert payload["summary"]["command_count"] >= 10, payload
    assert "working_tree_dirty" in payload["summary"], payload
    assert payload["git_status"]["available"] is True, payload
    assert payload["summary"]["provider_evidence_complete"] is False, payload
    assert payload["summary"]["human_review_complete"] is False, payload
    assert payload["summary"]["world_class_ready"] is False, payload
    headings = {item["heading"]: item["exists"] for item in payload["methodology"]["sections"]}
    assert headings["## Benchmark Types"], headings
    assert headings["## Failure Disclosure"], headings
    artifacts = {item["path"]: item for item in payload["artifacts_checked"]}
    assert artifacts["reports/benchmark_methodology.md"]["exists"], artifacts
    assert artifacts["evals/failure-cases.md"]["exists"], artifacts
    assert artifacts["reports/world_class_evidence_plan.json"]["exists"], artifacts
    assert artifacts["reports/world_class_evidence_ledger.json"]["exists"], artifacts
    assert any(command["command"] == "make ci-test" for command in payload["reproduction_commands"]), payload
    assert any(command["command"] == "python3 scripts/yao.py world-class-ledger ." for command in payload["reproduction_commands"]), payload
    assert any("provider-backed" in item for item in payload["limitations"]), payload["limitations"]
    markdown = output_md.read_text(encoding="utf-8")
    assert "Benchmark Reproducibility" in markdown, markdown
    assert "reports/benchmark_methodology.md" in markdown, markdown
    assert "make ci-test" in markdown, markdown
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
