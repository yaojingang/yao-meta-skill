#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INTAKE_SCRIPT = ROOT / "scripts" / "render_world_class_evidence_intake.py"
KIT_SCRIPT = ROOT / "scripts" / "prepare_world_class_submission_kit.py"
TMP = ROOT / "tests" / "tmp_world_class_submission_kit"


def run_intake(*extra: str) -> dict:
    extra_args = list(extra)
    if "--output-json" not in extra_args:
        extra_args.extend(["--output-json", str(TMP / "last_intake.json")])
    if "--output-md" not in extra_args:
        extra_args.extend(["--output-md", str(TMP / "last_intake.md")])
    proc = subprocess.run(
        [
            sys.executable,
            str(INTAKE_SCRIPT),
            str(ROOT),
            "--generated-at",
            "2026-06-14",
            *extra_args,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def run_kit(*extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(KIT_SCRIPT),
            str(ROOT),
            "--generated-at",
            "2026-06-14",
            *extra,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def assert_documented_submission_commands() -> None:
    expected_fragments = [
        'SUBMISSIONS_DIR="${SUBMISSIONS_DIR:-evidence/world_class/submissions}"',
        'world-class-preflight . --submissions-dir "$SUBMISSIONS_DIR"',
        'world-class-submission-kit . --output-dir "$SUBMISSIONS_DIR"',
        'world-class-submission-kit . --output-dir "$SUBMISSIONS_DIR" --prefill-artifacts',
        'world-class-intake . --submissions-dir "$SUBMISSIONS_DIR"',
        'world-class-submission-review . --submissions-dir "$SUBMISSIONS_DIR"',
        'world-class-ledger . --submissions-dir "$SUBMISSIONS_DIR"',
    ]
    for relative_path in ("README.md", "evidence/world_class/README.md"):
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for fragment in expected_fragments:
            assert fragment in text, (relative_path, fragment)
        assert "/tmp/yao-world-class-submission-kit" not in text, relative_path


def main() -> None:
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True, exist_ok=True)
    assert_documented_submission_commands()

    kit_dir = TMP / "submission_kit"
    kit_proc = run_kit("--output-dir", str(kit_dir), "--evidence-key", "provider-holdout")
    kit_payload = json.loads(kit_proc.stdout)
    assert kit_payload["ok"] is True, kit_payload
    assert kit_payload["summary"]["decision"] == "submission-kit-ready", kit_payload["summary"]
    assert kit_payload["summary"]["requested_count"] == 1, kit_payload["summary"]
    assert kit_payload["summary"]["written_count"] == 1, kit_payload["summary"]
    assert kit_payload["summary"]["artifact_checklist_count"] >= 1, kit_payload["summary"]
    assert kit_payload["summary"]["artifact_ready_count"] >= 1, kit_payload["summary"]
    assert kit_payload["summary"]["submission_ref_count"] == 1, kit_payload["summary"]
    assert kit_payload["summary"]["submission_ref_ready_count"] == 1, kit_payload["summary"]
    assert kit_payload["summary"]["supporting_artifact_count"] >= 1, kit_payload["summary"]
    assert kit_payload["summary"]["supporting_artifact_ready_count"] >= 1, kit_payload["summary"]
    assert kit_payload["summary"]["source_check_count"] == 3, kit_payload["summary"]
    assert kit_payload["summary"]["source_pass_count"] == 1, kit_payload["summary"]
    assert kit_payload["summary"]["source_blocked_count"] == 2, kit_payload["summary"]
    assert kit_payload["summary"]["evidence_matrix_count"] == 1, kit_payload["summary"]
    assert kit_payload["summary"]["evidence_matrix_collect_source_count"] == 1, kit_payload["summary"]
    assert kit_payload["summary"]["evidence_matrix_submission_ref_count"] == 1, kit_payload["summary"]
    assert kit_payload["summary"]["evidence_matrix_submission_ref_ready_count"] == 1, kit_payload["summary"]
    assert kit_payload["summary"]["evidence_matrix_supporting_artifact_count"] >= 1, kit_payload["summary"]
    assert kit_payload["summary"]["evidence_matrix_supporting_artifact_ready_count"] >= 1, kit_payload["summary"]
    assert kit_payload["summary"]["evidence_matrix_counts_as_completion"] == 0, kit_payload["summary"]
    assert kit_payload["summary"]["repair_checklist_count"] == 2, kit_payload["summary"]
    assert kit_payload["summary"]["repair_blocked_count"] == 2, kit_payload["summary"]
    assert kit_payload["summary"]["repair_ready_count"] == 0, kit_payload["summary"]
    assert kit_payload["summary"]["repair_phase_counts"] == {"collect-source": 2}, kit_payload["summary"]
    assert kit_payload["summary"]["phase_queue_count"] == 1, kit_payload["summary"]
    assert kit_payload["summary"]["phase_queue_blocked_count"] == 1, kit_payload["summary"]
    assert kit_payload["summary"]["phase_queue_row_count"] == 2, kit_payload["summary"]
    assert kit_payload["summary"]["phase_queue_next_phase"] == "collect-source", kit_payload["summary"]
    assert kit_payload["summary"]["phase_queue_next_action_id"] == "provider-holdout-source-check-model_executed_count", kit_payload["summary"]
    assert "output-exec --provider-runner openai" in kit_payload["summary"]["phase_queue_next_command"], kit_payload["summary"]
    assert kit_payload["summary"]["phase_queue_counts_as_completion"] is False, kit_payload["summary"]
    assert kit_payload["summary"]["next_repair_action_id"] == "provider-holdout-source-check-model_executed_count", kit_payload["summary"]
    assert kit_payload["summary"]["next_repair_phase"] == "collect-source", kit_payload["summary"]
    assert kit_payload["summary"]["next_repair_owner"] == "operator with provider credentials", kit_payload["summary"]
    assert "output-exec --provider-runner openai" in kit_payload["summary"]["next_repair_command"], kit_payload["summary"]
    assert kit_payload["summary"]["repair_counts_as_completion"] is False, kit_payload["summary"]
    assert kit_payload["summary"]["handoff_step_count"] == 7, kit_payload["summary"]
    assert kit_payload["summary"]["handoff_blocked_count"] == 1, kit_payload["summary"]
    assert kit_payload["summary"]["handoff_fix_required_count"] == 0, kit_payload["summary"]
    assert kit_payload["summary"]["handoff_counts_as_completion"] is False, kit_payload["summary"]
    assert kit_payload["summary"]["drafts_count_as_evidence"] is False, kit_payload["summary"]
    assert kit_payload["safety"]["template_only_drafts"] is True, kit_payload["safety"]
    assert kit_payload["safety"]["raw_content_allowed"] is False, kit_payload["safety"]
    assert kit_payload["safety"]["operator_handoff_counts_as_evidence"] is False, kit_payload["safety"]
    assert "review_submission" in kit_payload["commands"], kit_payload["commands"]
    assert kit_payload["files"][0]["output_path"].endswith(
        f"tests/{TMP.name}/submission_kit/provider-holdout.json"
    ), kit_payload["files"]

    assert len(kit_payload["evidence_matrix"]) == 1, kit_payload["evidence_matrix"]
    matrix_row = kit_payload["evidence_matrix"][0]
    assert matrix_row["evidence_key"] == "provider-holdout", matrix_row
    assert matrix_row["stage"] == "collect-source", matrix_row
    assert matrix_row["draft_status"] == "written", matrix_row
    assert matrix_row["artifact_ready_count"] >= 1, matrix_row
    assert matrix_row["artifact_total_count"] >= matrix_row["artifact_ready_count"], matrix_row
    assert matrix_row["submission_ref_ready_count"] == 1, matrix_row
    assert matrix_row["submission_ref_total_count"] == 1, matrix_row
    assert matrix_row["supporting_artifact_ready_count"] >= 1, matrix_row
    assert matrix_row["supporting_artifact_total_count"] >= matrix_row["supporting_artifact_ready_count"], matrix_row
    assert matrix_row["source_pass_count"] == 1, matrix_row
    assert matrix_row["source_check_count"] == 3, matrix_row
    assert matrix_row["source_blocked_count"] == 2, matrix_row
    assert matrix_row["counts_as_completion"] is False, matrix_row
    assert "real credentials" in matrix_row["next_action"], matrix_row

    repair_rows = {item["target"]: item for item in kit_payload["repair_checklist"]}
    assert set(repair_rows) == {"model_executed_count", "token_observed_count"}, repair_rows
    assert repair_rows["model_executed_count"]["repair_type"] == "source-check", repair_rows
    assert repair_rows["model_executed_count"]["action_id"] == "provider-holdout-source-check-model_executed_count", repair_rows
    assert repair_rows["model_executed_count"]["phase"] == "collect-source", repair_rows
    assert repair_rows["model_executed_count"]["priority"] == 40, repair_rows
    assert repair_rows["model_executed_count"]["owner"] == "operator with provider credentials", repair_rows
    assert "output-exec --provider-runner openai" in repair_rows["model_executed_count"][
        "verification_command"
    ], repair_rows
    assert repair_rows["model_executed_count"]["status"] == "blocked", repair_rows
    assert repair_rows["model_executed_count"]["counts_as_completion"] is False, repair_rows
    assert "real credentials" in repair_rows["model_executed_count"]["next_action"], repair_rows
    assert "does not satisfy" in repair_rows["token_observed_count"]["blocking_reason"], repair_rows

    assert len(kit_payload["phase_queue"]) == 1, kit_payload["phase_queue"]
    queue_row = kit_payload["phase_queue"][0]
    assert queue_row["phase"] == "collect-source", queue_row
    assert queue_row["status"] == "blocked", queue_row
    assert queue_row["row_count"] == 2, queue_row
    assert queue_row["blocked_count"] == 2, queue_row
    assert queue_row["owners"] == ["operator with provider credentials"], queue_row
    assert queue_row["evidence_keys"] == ["provider-holdout"], queue_row
    assert queue_row["counts_as_completion"] is False, queue_row
    assert queue_row["rows"] == kit_payload["repair_checklist"], queue_row

    handoff_steps = {item["step_id"]: item for item in kit_payload["operator_handoff"]}
    assert list(handoff_steps) == [
        "prepare-drafts",
        "collect-source",
        "edit-submission",
        "validate-intake",
        "review-submission",
        "refresh-ledger",
        "guard-claim",
    ], handoff_steps
    assert handoff_steps["prepare-drafts"]["status"] == "ready", handoff_steps
    assert handoff_steps["collect-source"]["status"] == "blocked", handoff_steps
    assert handoff_steps["collect-source"]["counts_as_completion"] is False, handoff_steps
    assert "source check" in handoff_steps["collect-source"]["blocking_condition"], handoff_steps
    assert "world-class-submission-review" in handoff_steps["review-submission"]["command"], handoff_steps
    assert all(item["counts_as_completion"] is False for item in kit_payload["operator_handoff"]), handoff_steps

    artifact_rows = {item["path"]: item for item in kit_payload["artifact_checklist"]}
    assert "reports/output_execution_runs.json" in artifact_rows, artifact_rows
    assert artifact_rows["reports/output_execution_runs.json"]["artifact_ref_ready"] is True, artifact_rows
    assert artifact_rows["reports/output_execution_runs.json"]["artifact_role"] == "submission-ref", artifact_rows
    assert artifact_rows["reports/output_execution_runs.json"]["submission_ref_required"] is True, artifact_rows
    assert len(artifact_rows["reports/output_execution_runs.json"]["sha256"]) == 64, artifact_rows
    assert artifact_rows["reports/output_execution_runs.json"]["contains_raw_content"] is False, artifact_rows
    assert artifact_rows["reports/output_execution_runs.md"]["artifact_role"] == "supporting-evidence", artifact_rows
    assert artifact_rows["reports/output_execution_runs.md"]["submission_ref_required"] is False, artifact_rows

    source_rows = {item["field"]: item for item in kit_payload["source_checklist"]}
    assert source_rows["model_executed_count"]["status"] == "blocked", source_rows
    assert source_rows["model_executed_count"]["actual"] == 0, source_rows
    assert source_rows["timing_observed_count"]["status"] == "pass", source_rows
    assert source_rows["token_observed_count"]["status"] == "blocked", source_rows

    kit_draft = json.loads((kit_dir / "provider-holdout.json").read_text(encoding="utf-8"))
    assert kit_draft["template_only"] is True, kit_draft
    assert kit_draft["attestation"]["real_external_or_human_evidence"] is False, kit_draft
    assert kit_draft["attestation"]["ledger_reviewer_approved"] is False, kit_draft
    assert kit_draft["attestation"]["ledger_reviewer"] == "", kit_draft
    assert kit_draft["attestation"]["ledger_reviewed_at"] == "", kit_draft
    assert "sha256" not in kit_draft["artifact_refs"][0], kit_draft
    assert kit_draft["provenance"]["run_command"] == (
        "python3 scripts/yao.py output-exec --provider-runner openai --timeout-seconds 60"
    ), kit_draft
    assert kit_draft["provenance"]["credential_env"] == "OPENAI_API_KEY", kit_draft
    assert "<redacted>" not in json.dumps(kit_draft), kit_draft

    kit_manifest = json.loads((kit_dir / "submission_manifest.json").read_text(encoding="utf-8"))
    assert kit_manifest["summary"]["ledger_counts_submission_as_completion"] is False, kit_manifest["summary"]
    assert kit_manifest["summary"]["artifact_prefill_enabled"] is False, kit_manifest["summary"]
    assert kit_manifest["summary"]["artifact_ref_prefill_count"] == 0, kit_manifest["summary"]
    assert kit_manifest["artifact_checklist"] == kit_payload["artifact_checklist"], kit_manifest["artifact_checklist"]
    assert kit_manifest["source_checklist"] == kit_payload["source_checklist"], kit_manifest["source_checklist"]
    assert kit_manifest["repair_checklist"] == kit_payload["repair_checklist"], kit_manifest["repair_checklist"]
    assert kit_manifest["phase_queue"] == kit_payload["phase_queue"], kit_manifest["phase_queue"]
    assert kit_manifest["artifacts"]["html"].endswith(
        f"tests/{TMP.name}/submission_kit/index.html"
    ), kit_manifest["artifacts"]

    kit_readme = (kit_dir / "README.md").read_text(encoding="utf-8")
    assert "Drafts are not accepted evidence." in kit_readme, kit_readme
    assert "Execution Runbook" in kit_readme, kit_readme
    assert "output-exec --provider-runner openai" in kit_readme, kit_readme
    assert "<redacted>" not in kit_readme, kit_readme
    assert "validate intake" in kit_readme, kit_readme
    assert "Artifact Checklist" in kit_readme, kit_readme
    assert "Evidence Matrix" in kit_readme, kit_readme
    assert "Phase Queue" in kit_readme, kit_readme
    assert "This queue groups repair rows by execution phase" in kit_readme, kit_readme
    assert "Repair Checklist" in kit_readme, kit_readme
    assert "Operator Handoff" in kit_readme, kit_readme
    assert "Handoff rows are procedural" in kit_readme, kit_readme
    assert "ledger_reviewed_at" in kit_readme, kit_readme
    assert "`review-submission`" in kit_readme, kit_readme
    assert "Submission refs" in kit_readme, kit_readme
    assert "Supporting assets" in kit_readme, kit_readme
    assert "`submission-ref`" in kit_readme, kit_readme
    assert "`supporting-evidence`" in kit_readme, kit_readme
    assert "`collect-source`" in kit_readme, kit_readme
    assert "Queue rows are procedural guidance only" in kit_readme, kit_readme
    assert "Matrix rows are guidance only" in kit_readme, kit_readme
    assert "Repair rows are procedural guidance and do not count as completion evidence." in kit_readme, kit_readme
    assert "Source Evidence Snapshot" in kit_readme, kit_readme
    assert "model_executed_count" in kit_readme, kit_readme
    assert "reports/output_execution_runs.json" in kit_readme, kit_readme
    assert "Provider model run" in kit_readme, kit_readme

    kit_html = (kit_dir / "index.html").read_text(encoding="utf-8")
    assert "<title>World-Class Evidence Submission Kit</title>" in kit_html, kit_html
    assert "Drafts are not accepted evidence" in kit_html, kit_html
    assert "provider-holdout" in kit_html, kit_html
    assert "Artifact Checklist" in kit_html, kit_html
    assert "Evidence Matrix" in kit_html, kit_html
    assert "Phase Queue" in kit_html, kit_html
    assert "queue-card blocked" in kit_html, kit_html
    assert "<dt>Phase</dt><dd><code>collect-source</code></dd>" in kit_html, kit_html
    assert "<dt>Rows</dt><dd>2/2 blocked</dd>" in kit_html, kit_html
    assert "Repair Checklist" in kit_html, kit_html
    assert "<dt>Priority</dt>" in kit_html, kit_html
    assert "<dt>Phase</dt>" in kit_html, kit_html
    assert "<dt>Owner</dt>" in kit_html, kit_html
    assert "collect-source" in kit_html, kit_html
    assert "operator with provider credentials" in kit_html, kit_html
    assert "output-exec --provider-runner openai" in kit_html, kit_html
    assert "Operator Handoff" in kit_html, kit_html
    assert "handoff-card blocked" in kit_html, kit_html
    assert "does not count as completion" in kit_html, kit_html
    assert "matrix-card collect-source" in kit_html, kit_html
    assert "repair-card blocked" in kit_html, kit_html
    assert (
        f"<dt>Submission refs</dt><dd>{matrix_row['submission_ref_ready_count']}/{matrix_row['submission_ref_total_count']} ready</dd>"
        in kit_html
    ), kit_html
    assert (
        f"<dt>Supporting assets</dt><dd>{matrix_row['supporting_artifact_ready_count']}/{matrix_row['supporting_artifact_total_count']} ready</dd>"
        in kit_html
    ), kit_html
    assert "<dt>Source</dt><dd>1/3 pass</dd>" in kit_html, kit_html
    assert "Source Evidence Snapshot" in kit_html, kit_html
    assert "<dt>Field</dt><dd><code>model_executed_count</code></dd>" in kit_html, kit_html
    assert "<h3>model_executed_count</h3>" in kit_html, kit_html
    assert "<dt>Current</dt><dd><code>0</code></dd>" in kit_html, kit_html
    assert "<dt>Expected</dt><dd><code>&gt;0</code></dd>" in kit_html, kit_html
    assert "World-Class Evidence Submission Kit" in kit_html, kit_html
    assert "Execution Runbook" in kit_html, kit_html
    assert "output-exec --provider-runner openai" in kit_html, kit_html
    assert "&lt;redacted&gt;" not in kit_html and "<redacted>" not in kit_html, kit_html
    assert "Do not include credentials, raw prompts, raw outputs, transcripts, notes, or private user content." in kit_html, kit_html
    assert "Rows marked submission-ref are the paths expected in artifact_refs" in kit_html, kit_html

    prefilled_kit_dir = TMP / "prefilled_submission_kit"
    prefilled_proc = run_kit(
        "--output-dir",
        str(prefilled_kit_dir),
        "--evidence-key",
        "provider-holdout",
        "--prefill-artifacts",
    )
    prefilled_payload = json.loads(prefilled_proc.stdout)
    assert prefilled_payload["summary"]["artifact_prefill_enabled"] is True, prefilled_payload["summary"]
    assert prefilled_payload["summary"]["artifact_ref_prefill_count"] == 1, prefilled_payload["summary"]
    assert prefilled_payload["summary"]["artifact_ref_unfilled_count"] == 0, prefilled_payload["summary"]
    assert prefilled_payload["summary"]["drafts_count_as_evidence"] is False, prefilled_payload["summary"]
    assert prefilled_payload["safety"]["artifact_prefill_counts_as_evidence"] is False, prefilled_payload["safety"]
    assert prefilled_payload["files"][0]["prefilled_artifact_ref_count"] == 1, prefilled_payload["files"]
    prefilled_draft = json.loads((prefilled_kit_dir / "provider-holdout.json").read_text(encoding="utf-8"))
    assert prefilled_draft["template_only"] is True, prefilled_draft
    assert prefilled_draft["attestation"]["real_external_or_human_evidence"] is False, prefilled_draft
    assert prefilled_draft["attestation"]["ledger_reviewer_approved"] is False, prefilled_draft
    assert len(prefilled_draft["artifact_refs"][0]["sha256"]) == 64, prefilled_draft
    assert prefilled_draft["artifact_refs"][0]["contains_raw_content"] is False, prefilled_draft
    prefilled_readme = (prefilled_kit_dir / "README.md").read_text(encoding="utf-8")
    assert "Optional artifact prefill only inserts SHA-256 digests" in prefilled_readme, prefilled_readme
    assert "does not mark a draft as real evidence" in prefilled_readme, prefilled_readme
    prefilled_html = (prefilled_kit_dir / "index.html").read_text(encoding="utf-8")
    assert "artifact prefill only inserts local SHA-256 digests" in prefilled_html, prefilled_html
    assert "<dt>Prefill</dt><dd>1 artifact refs</dd>" in prefilled_html, prefilled_html

    native_kit_dir = TMP / "native_permission_kit"
    native_kit_proc = run_kit("--output-dir", str(native_kit_dir), "--evidence-key", "native-permission-enforcement")
    native_kit_payload = json.loads(native_kit_proc.stdout)
    native_rows = {item["path"]: item for item in native_kit_payload["artifact_checklist"]}
    assert native_kit_payload["summary"]["artifact_glob_expansion_count"] >= 1, native_kit_payload["summary"]
    if "dist/targets/openai/adapter.json" in native_rows:
        assert native_rows["dist/targets/openai/adapter.json"]["source_pattern"] == "dist/targets/*/adapter.json", native_rows
        assert native_rows["dist/targets/openai/adapter.json"]["artifact_ref_ready"] is True, native_rows
        assert len(native_rows["dist/targets/openai/adapter.json"]["sha256"]) == 64, native_rows
    else:
        glob_rows = [
            item for item in native_kit_payload["artifact_checklist"]
            if item["source_pattern"] == "dist/targets/*/adapter.json"
        ]
        assert len(glob_rows) == 1, glob_rows
        assert glob_rows[0]["status"] == "glob-no-match", glob_rows[0]
        assert glob_rows[0]["artifact_ref_ready"] is False, glob_rows[0]
        assert glob_rows[0]["concrete_reference_required"] is True, glob_rows[0]
    native_readme = (native_kit_dir / "README.md").read_text(encoding="utf-8")
    assert "Glob patterns are expanded into concrete files" in native_readme, native_readme

    draft_intake = run_intake("--submissions-dir", str(kit_dir))
    assert draft_intake["ok"] is False, draft_intake
    assert draft_intake["summary"]["submission_count"] == 1, draft_intake["summary"]
    assert draft_intake["summary"]["invalid_submission_count"] == 1, draft_intake["summary"]
    assert draft_intake["submissions"][0]["evidence_key"] == "provider-holdout", draft_intake["submissions"]
    assert all(item["evidence_key"] != "unknown" for item in draft_intake["submissions"]), draft_intake["submissions"]

    spaced_kit_dir = TMP / "submission kit spaced"
    spaced_kit_proc = run_kit("--output-dir", str(spaced_kit_dir), "--evidence-key", "provider-holdout")
    spaced_kit_payload = json.loads(spaced_kit_proc.stdout)
    quoted_spaced_dir = f"'tests/{TMP.name}/submission kit spaced'"
    assert quoted_spaced_dir in spaced_kit_payload["commands"]["validate_intake"], spaced_kit_payload["commands"]
    assert quoted_spaced_dir in spaced_kit_payload["commands"]["refresh_ledger"], spaced_kit_payload["commands"]
    spaced_readme = (spaced_kit_dir / "README.md").read_text(encoding="utf-8")
    assert quoted_spaced_dir in spaced_readme, spaced_readme

    existing_proc = run_kit("--output-dir", str(kit_dir), "--evidence-key", "provider-holdout")
    existing_payload = json.loads(existing_proc.stdout)
    assert existing_payload["summary"]["existing_count"] == 1, existing_payload["summary"]
    assert existing_payload["files"][0]["status"] == "exists", existing_payload["files"]
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
