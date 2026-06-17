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
            str(ROOT / "scripts" / "render_world_class_preflight.py"),
            str(ROOT),
            "--generated-at",
            "2026-06-13",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    submission_review_proc = subprocess.run(
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
        check=False,
    )
    assert submission_review_proc.returncode in {0, 2}, submission_review_proc.stderr
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
    assert payload["summary"]["release_lock_ready"] == (payload["git_status"]["source_dirty"] is False), payload
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
    assert "source_tree_dirty" in payload["summary"], payload
    assert "generated_tree_dirty" in payload["summary"], payload
    assert payload["summary"]["source_changed_file_count"] == payload["git_status"]["source_changed_file_count"], payload
    assert payload["summary"]["generated_changed_file_count"] == payload["git_status"][
        "generated_changed_file_count"
    ], payload
    assert payload["git_status"]["available"] is True, payload
    assert payload["git_status"]["scope"] == "generation-time status before this report is written", payload
    assert isinstance(payload["git_status"]["generated_dirty_prefixes"], list), payload
    assert payload["release_lock"]["status_scope"] == "generation-time status before this report is written", payload
    assert payload["release_lock"]["commit"] == payload["commit"], payload
    assert payload["release_lock"]["source_changed_file_count"] == payload["git_status"][
        "source_changed_file_count"
    ], payload
    assert payload["release_lock"]["generated_changed_file_count"] == payload["git_status"][
        "generated_changed_file_count"
    ], payload
    assert payload["evidence_bundle"]["algorithm"] == "sha256(path,label,exists,artifact_sha256)", payload
    assert payload["evidence_bundle"]["artifact_count"] == payload["summary"]["required_artifact_count"], payload
    assert payload["evidence_bundle"]["existing_count"] == payload["summary"]["required_artifact_count"], payload
    assert payload["evidence_bundle"]["missing_count"] == 0, payload
    assert payload["evidence_bundle"]["missing_paths"] == [], payload
    assert payload["summary"]["provider_evidence_complete"] is True, payload
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
    expected_beta_ready = (
        payload["summary"]["reproducibility_ready"]
        and payload["summary"]["release_lock_ready"]
        and payload["summary"]["provider_evidence_complete"]
    )
    assert payload["summary"]["beta_test_ready"] is expected_beta_ready, payload
    assert payload["summary"]["beta_test_blocker_count"] == len(payload["beta_test_release"]["blockers"]), payload
    assert payload["summary"]["beta_test_deferred_evidence_count"] == len(
        payload["beta_test_release"]["allowed_deferred_evidence"]
    ), payload
    assert payload["beta_test_release"]["ready"] is expected_beta_ready, payload["beta_test_release"]
    assert "beta/public test release" in payload["beta_test_release"]["scope"], payload["beta_test_release"]
    assert "Human blind-review" in payload["beta_test_release"]["policy"], payload["beta_test_release"]
    assert "do not claim world-class" in payload["beta_test_release"]["required_wording"], payload[
        "beta_test_release"
    ]
    deferred_keys = {item["key"] for item in payload["beta_test_release"]["allowed_deferred_evidence"]}
    assert "human-adjudication" in deferred_keys, payload["beta_test_release"]
    assert not any("human blind-review" in item for item in payload["beta_test_release"]["blockers"]), payload[
        "beta_test_release"
    ]
    assert payload["summary"]["public_claim_ready"] is False, payload
    minimum_blockers = 3 if payload["summary"]["release_lock_ready"] else 4
    assert payload["summary"]["public_claim_blocker_count"] >= minimum_blockers, payload
    assert payload["public_claim"]["ready"] is False, payload["public_claim"]
    if payload["summary"]["release_lock_ready"]:
        assert not any("release lock" in item for item in payload["public_claim"]["blockers"]), payload["public_claim"]
    else:
        assert any("release lock" in item for item in payload["public_claim"]["blockers"]), payload["public_claim"]
    assert not any("provider-backed model holdout evidence is incomplete" in item for item in payload["public_claim"]["blockers"]), payload["public_claim"]
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
    assert artifacts["reports/world_class_evidence_preflight.json"]["exists"], artifacts
    assert artifacts["reports/world_class_submission_review.json"]["exists"], artifacts
    assert artifacts["reports/world_class_operator_runbook.json"]["exists"], artifacts
    assert artifacts["reports/world_class_operator_runbook.md"]["exists"], artifacts
    assert artifacts["reports/world_class_operator_runbook.html"]["exists"], artifacts
    assert artifacts["reports/world_class_claim_guard.json"]["exists"], artifacts
    assert artifacts["reports/python_compatibility.json"]["exists"], artifacts
    assert any(command["command"] == "make ci-test" for command in payload["reproduction_commands"]), payload
    assert any(command["command"] == "python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions" for command in payload["reproduction_commands"]), payload
    assert any(command["command"] == "python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions" for command in payload["reproduction_commands"]), payload
    assert any(command["command"] == "python3 scripts/yao.py world-class-preflight . --submissions-dir evidence/world_class/submissions" for command in payload["reproduction_commands"]), payload
    assert any(command["command"] == "python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions" for command in payload["reproduction_commands"]), payload
    assert any(command["command"] == "python3 scripts/yao.py world-class-runbook . --submissions-dir evidence/world_class/submissions" for command in payload["reproduction_commands"]), payload
    assert any(command["command"] == "python3 scripts/yao.py world-class-claim-guard ." for command in payload["reproduction_commands"]), payload
    assert any(command["command"] == "python3 scripts/yao.py python-compat ." for command in payload["reproduction_commands"]), payload
    assert any(command["command"] == "python3 scripts/yao.py evidence-consistency ." for command in payload["reproduction_commands"]), payload
    assert any("Provider-backed model holdout source evidence is complete" in item for item in payload["limitations"]), payload["limitations"]
    markdown = output_md.read_text(encoding="utf-8")
    assert "Benchmark Reproducibility" in markdown, markdown
    assert "Evidence bundle SHA256" in markdown, markdown
    assert "release lock ready" in markdown, markdown
    assert "Source tree dirty at generation" in markdown, markdown
    assert "Generated evidence dirty at generation" in markdown, markdown
    assert "source changed files at generation" in markdown, markdown
    assert "generated changed files at generation" in markdown, markdown
    assert "world-class source checks" in markdown, markdown
    assert "beta test ready" in markdown, markdown
    assert "## Beta Test Boundary" in markdown, markdown
    assert "human-adjudication" in markdown, markdown
    assert "do not claim world-class" in markdown, markdown
    assert "public claim ready: `false`" in markdown, markdown
    assert "## Public Claim Boundary" in markdown, markdown
    assert "provider-backed model holdout evidence is incomplete" not in markdown, markdown
    assert "Provider-backed model holdout source evidence is complete" in markdown, markdown
    assert "world-class source checks are not all accepted" in markdown, markdown
    assert "## Release Lock" in markdown, markdown
    assert "## Evidence Bundle" in markdown, markdown
    assert "reports/benchmark_methodology.md" in markdown, markdown
    assert "reports/world_class_evidence_preflight.json" in markdown, markdown
    assert "reports/world_class_operator_runbook.html" in markdown, markdown
    assert "python3 scripts/yao.py world-class-preflight . --submissions-dir evidence/world_class/submissions" in markdown, markdown
    assert "python3 scripts/yao.py world-class-runbook . --submissions-dir evidence/world_class/submissions" in markdown, markdown
    assert "python3 scripts/yao.py evidence-consistency ." in markdown, markdown
    assert "make ci-test" in markdown, markdown
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
