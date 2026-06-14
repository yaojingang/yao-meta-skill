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
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "render_world_class_evidence_intake.py"),
            str(ROOT),
            "--generated-at",
            "2026-06-13",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "render_world_class_submission_review.py"),
            str(ROOT),
            "--generated-at",
            "2026-06-13",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "render_world_class_operator_runbook.py"),
            str(ROOT),
            "--generated-at",
            "2026-06-13",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "render_world_class_claim_guard.py"),
            str(ROOT),
            "--generated-at",
            "2026-06-13",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "python_compat_check.py"),
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
    assert payload["summary"]["release_lock_ready"] == (payload["git_status"]["dirty"] is False), payload
    assert payload["summary"]["methodology_complete"] is True, payload
    assert payload["summary"]["missing_artifact_count"] == 0, payload
    assert len(payload["summary"]["evidence_bundle_sha256"]) == 64, payload
    assert payload["summary"]["evidence_bundle_sha256"] == payload["evidence_bundle"]["sha256"], payload
    assert payload["summary"]["source_contract_sha256"], payload
    assert payload["summary"]["archive_sha256"], payload
    assert payload["summary"]["output_case_count"] >= 5, payload
    assert payload["summary"]["failure_disclosure_count"] >= 1, payload
    assert payload["summary"]["command_count"] >= 10, payload
    assert "working_tree_dirty" in payload["summary"], payload
    assert payload["git_status"]["available"] is True, payload
    assert payload["git_status"]["scope"] == "generation-time status before this report is written", payload
    assert payload["release_lock"]["status_scope"] == "generation-time status before this report is written", payload
    assert payload["release_lock"]["commit"] == payload["commit"], payload
    assert payload["evidence_bundle"]["algorithm"] == "sha256(path,label,exists,artifact_sha256)", payload
    assert payload["evidence_bundle"]["artifact_count"] == payload["summary"]["required_artifact_count"], payload
    assert payload["evidence_bundle"]["existing_count"] == payload["summary"]["required_artifact_count"], payload
    assert payload["evidence_bundle"]["missing_count"] == 0, payload
    assert payload["evidence_bundle"]["missing_paths"] == [], payload
    assert payload["summary"]["provider_evidence_complete"] is False, payload
    assert payload["summary"]["human_review_complete"] is False, payload
    assert payload["summary"]["world_class_ready"] is False, payload
    assert payload["summary"]["world_class_source_check_count"] >= 13, payload
    assert payload["summary"]["world_class_source_pass_count"] >= 6, payload
    assert payload["summary"]["world_class_source_blocked_count"] >= 6, payload
    assert (
        payload["summary"]["world_class_source_pass_count"]
        + payload["summary"]["world_class_source_blocked_count"]
        == payload["summary"]["world_class_source_check_count"]
    ), payload
    assert payload["summary"]["public_claim_ready"] is False, payload
    assert payload["summary"]["public_claim_blocker_count"] >= 4, payload
    assert payload["public_claim"]["ready"] is False, payload["public_claim"]
    assert any("provider-backed" in item for item in payload["public_claim"]["blockers"]), payload["public_claim"]
    assert any("human blind-review" in item for item in payload["public_claim"]["blockers"]), payload["public_claim"]
    assert any("world-class evidence" in item for item in payload["public_claim"]["blockers"]), payload["public_claim"]
    assert any("world-class source checks" in item for item in payload["public_claim"]["blockers"]), payload["public_claim"]
    assert "complete source checks" in payload["public_claim"]["policy"], payload["public_claim"]
    headings = {item["heading"]: item["exists"] for item in payload["methodology"]["sections"]}
    assert headings["## Benchmark Types"], headings
    assert headings["## Failure Disclosure"], headings
    artifacts = {item["path"]: item for item in payload["artifacts_checked"]}
    assert artifacts["reports/benchmark_methodology.md"]["exists"], artifacts
    assert artifacts["evals/failure-cases.md"]["exists"], artifacts
    assert artifacts["reports/world_class_evidence_plan.json"]["exists"], artifacts
    assert artifacts["reports/world_class_evidence_ledger.json"]["exists"], artifacts
    assert artifacts["reports/world_class_evidence_intake.json"]["exists"], artifacts
    assert artifacts["reports/world_class_submission_review.json"]["exists"], artifacts
    assert artifacts["reports/world_class_operator_runbook.json"]["exists"], artifacts
    assert artifacts["reports/world_class_operator_runbook.md"]["exists"], artifacts
    assert artifacts["reports/world_class_operator_runbook.html"]["exists"], artifacts
    assert artifacts["reports/world_class_claim_guard.json"]["exists"], artifacts
    assert artifacts["reports/python_compatibility.json"]["exists"], artifacts
    assert any(command["command"] == "make ci-test" for command in payload["reproduction_commands"]), payload
    assert any(command["command"] == "python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions" for command in payload["reproduction_commands"]), payload
    assert any(command["command"] == "python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions" for command in payload["reproduction_commands"]), payload
    assert any(command["command"] == "python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions" for command in payload["reproduction_commands"]), payload
    assert any(command["command"] == "python3 scripts/yao.py world-class-runbook . --submissions-dir evidence/world_class/submissions" for command in payload["reproduction_commands"]), payload
    assert any(command["command"] == "python3 scripts/yao.py world-class-claim-guard ." for command in payload["reproduction_commands"]), payload
    assert any(command["command"] == "python3 scripts/yao.py python-compat ." for command in payload["reproduction_commands"]), payload
    assert any("provider-backed" in item for item in payload["limitations"]), payload["limitations"]
    markdown = output_md.read_text(encoding="utf-8")
    assert "Benchmark Reproducibility" in markdown, markdown
    assert "Evidence bundle SHA256" in markdown, markdown
    assert "release lock ready" in markdown, markdown
    assert "world-class source checks" in markdown, markdown
    assert "public claim ready: `false`" in markdown, markdown
    assert "## Public Claim Boundary" in markdown, markdown
    assert "provider-backed model holdout evidence is incomplete" in markdown, markdown
    assert "world-class source checks are not all accepted" in markdown, markdown
    assert "## Release Lock" in markdown, markdown
    assert "## Evidence Bundle" in markdown, markdown
    assert "reports/benchmark_methodology.md" in markdown, markdown
    assert "reports/world_class_operator_runbook.html" in markdown, markdown
    assert "python3 scripts/yao.py world-class-runbook . --submissions-dir evidence/world_class/submissions" in markdown, markdown
    assert "make ci-test" in markdown, markdown
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
