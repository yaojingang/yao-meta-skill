#!/usr/bin/env python3
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_review_studio.py"
sys.path.insert(0, str(ROOT / "scripts"))
import render_review_studio as review_studio  # noqa: E402
import review_studio_formatting as review_formatting  # noqa: E402
import review_studio_gates as review_gates  # noqa: E402
import review_studio_layout as review_layout  # noqa: E402


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_review_studio"
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    tmp_root.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "run_output_eval.py")], cwd=ROOT, check=True, capture_output=True, text=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "prepare_output_review_kit.py")], cwd=ROOT, check=True, capture_output=True, text=True)
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_output_execution.py"),
            "--runner-command",
            json.dumps(["python3", "scripts/local_output_eval_runner.py"]),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "adjudicate_output_review.py")],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "compile_skill.py"), str(ROOT), "--generated-at", "2026-06-13"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    package_dir = tmp_root / "dist"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "cross_packager.py"),
            str(ROOT),
            "--platform",
            "openai",
            "--platform",
            "claude",
            "--platform",
            "generic",
            "--platform",
            "vscode",
            "--expectations",
            str(ROOT / "evals" / "packaging_expectations.json"),
            "--output-dir",
            str(package_dir),
            "--zip",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "simulate_install.py"),
            str(ROOT),
            "--package-dir",
            str(package_dir),
            "--install-root",
            str(tmp_root / "install-root"),
            "--output-json",
            str(tmp_root / "install_simulation.json"),
            "--output-md",
            str(tmp_root / "install_simulation.md"),
            "--generated-at",
            "2026-06-13",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    (ROOT / "reports" / "install_simulation.json").write_text(
        (tmp_root / "install_simulation.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (ROOT / "reports" / "install_simulation.md").write_text(
        (tmp_root / "install_simulation.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "registry_audit.py"), str(ROOT), "--generated-at", "2026-06-13"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "render_intent_confidence.py"), str(ROOT)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "trust_check.py"), str(ROOT)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "python_compat_check.py"), str(ROOT), "--generated-at", "2026-06-13"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "render_architecture_maintainability.py"),
            str(ROOT),
            "--generated-at",
            "2026-06-13",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "render_context_reports.py")],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "render_adoption_drift_report.py"),
            str(ROOT),
            "--events-jsonl",
            str(tmp_root / "telemetry_events.jsonl"),
            "--record-event",
            "skill_activation",
            "--activation-type",
            "explicit",
            "--outcome",
            "accepted",
            "--timestamp",
            "2026-06-13T10:00:00Z",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_skill_atlas.py"),
            "--workspace-root",
            str(ROOT),
            "--output-dir",
            str(ROOT / "skill_atlas"),
            "--report-html",
            str(ROOT / "reports" / "skill_atlas.html"),
            "--report-json",
            str(ROOT / "reports" / "skill_atlas.json"),
            "--today",
            "2026-06-13",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "upgrade_check.py"),
            str(ROOT),
            "--previous-package-json",
            str(ROOT / "registry" / "examples" / "yao-meta-skill-1.0.0.json"),
            "--current-package-json",
            str(ROOT / "reports" / "registry_audit.json"),
            "--output-json",
            str(tmp_root / "upgrade_check.json"),
            "--output-md",
            str(tmp_root / "upgrade_check.md"),
            "--generated-at",
            "2026-06-13",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    (ROOT / "reports" / "upgrade_check.json").write_text(
        (tmp_root / "upgrade_check.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (ROOT / "reports" / "upgrade_check.md").write_text(
        (tmp_root / "upgrade_check.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "render_review_waivers.py"), str(ROOT), "--generated-at", "2026-06-13"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "render_review_annotations.py"),
            str(ROOT),
            "--annotations-json",
            str(tmp_root / "empty_review_annotations_input.json"),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "probe_runtime_permissions.py"),
            str(ROOT),
            "--package-dir",
            str(package_dir),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    for script_name in [
        "render_skill_os2_audit.py",
        "render_world_class_evidence_plan.py",
        "render_world_class_evidence_ledger.py",
        "render_world_class_evidence_intake.py",
        "render_world_class_submission_review.py",
        "render_world_class_operator_runbook.py",
        "render_world_class_claim_guard.py",
        "render_skill_os2_coverage.py",
    ]:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script_name), str(ROOT), "--generated-at", "2026-06-13"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    output_html = tmp_root / "review-studio.html"
    output_json = tmp_root / "review-studio.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(ROOT),
            "--output-html",
            str(output_html),
            "--output-json",
            str(output_json),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["ok"], payload
    assert payload["schema_version"] == "2.0", payload
    assert payload["summary"]["decision"] == "review", payload
    assert payload["summary"]["gate_count"] == 16, payload
    assert payload["summary"]["world_class_score"] == 91, payload
    assert payload["summary"]["warning_count"] == 3, payload
    assert payload["summary"]["blocker_count"] == 0, payload
    assert payload["summary"]["action_count"] == 3, payload
    assert payload["summary"]["annotation_count"] == 0, payload
    assert payload["summary"]["open_annotation_blocker_count"] == 0, payload
    assert payload["summary"]["action_count"] == payload["summary"]["warning_count"] + payload["summary"]["blocker_count"], payload
    assert {item["gate_key"] for item in payload["review_actions"]} == {
        "output-lab",
        "review-waivers",
        "world-class-evidence",
    }, payload
    gate_keys = {item["key"] for item in payload["gates"]}
    assert {"intent-canvas", "trigger-lab", "output-lab", "context-budget", "runtime-matrix", "trust-report", "python-compat", "architecture-maintainability", "permission-gates", "permission-runtime", "skill-atlas", "operations-loop", "review-waivers", "world-class-evidence", "registry-audit", "release-notes"} <= gate_keys, payload
    output_gate = next(item for item in payload["gates"] if item["key"] == "output-lab")
    assert output_gate["status"] == "warn", output_gate
    assert "5/5 cases" in output_gate["detail"], output_gate
    assert "file-backed 1" in output_gate["detail"], output_gate
    assert "blind A/B 5" in output_gate["detail"], output_gate
    assert "exec 10" in output_gate["detail"], output_gate
    assert "model 0" in output_gate["detail"], output_gate
    assert "reviewed 0/5" in output_gate["detail"], output_gate
    assert "review pending 5" in output_gate["detail"], output_gate
    context_gate = next(item for item in payload["gates"] if item["key"] == "context-budget")
    assert context_gate["status"] == "pass", context_gate
    initial_load = re.search(r"initial load (\d+)/1000", context_gate["detail"])
    assert initial_load, context_gate
    assert int(initial_load.group(1)) <= 1000, context_gate
    assert "deferred " in context_gate["detail"], context_gate
    assert "/120000" in context_gate["detail"], context_gate
    assert "top deferred scripts" in context_gate["detail"], context_gate
    assert "resource governance governed" in context_gate["detail"], context_gate
    assert "quality density" in context_gate["detail"], context_gate
    release_gate = next(item for item in payload["gates"] if item["key"] == "release-notes")
    assert "upgrade minor declared / minor recommended" in release_gate["detail"], release_gate
    assert "reports/upgrade_check.json" in release_gate["evidence"], release_gate
    registry_gate = next(item for item in payload["gates"] if item["key"] == "registry-audit")
    assert "install pass" in registry_gate["detail"], registry_gate
    assert "installer permissions 12 enforced / 0 failures" in registry_gate["detail"], registry_gate
    assert "reports/install_simulation.json" in registry_gate["evidence"], registry_gate
    trust_gate = next(item for item in payload["gates"] if item["key"] == "trust-report")
    assert trust_gate["status"] == "pass", trust_gate
    assert "3 network-capable scripts" in trust_gate["detail"], trust_gate
    assert "0 help smoke failures" in trust_gate["detail"], trust_gate
    python_compat_gate = next(item for item in payload["gates"] if item["key"] == "python-compat")
    assert python_compat_gate["status"] == "pass", python_compat_gate
    assert "Python 3.11" in python_compat_gate["detail"], python_compat_gate
    assert "0 compatibility issues" in python_compat_gate["detail"], python_compat_gate
    assert "0 f-string 3.11 hazards" in python_compat_gate["detail"], python_compat_gate
    assert python_compat_gate["evidence"] == "reports/python_compatibility.json", python_compat_gate
    architecture_gate = next(item for item in payload["gates"] if item["key"] == "architecture-maintainability")
    assert architecture_gate["status"] == "pass", architecture_gate
    assert "0 hotspots" in architecture_gate["detail"], architecture_gate
    assert "0 blockers" in architecture_gate["detail"], architecture_gate
    assert "CLI handlers" in architecture_gate["detail"], architecture_gate
    assert architecture_gate["evidence"] == "reports/architecture_maintainability.json", architecture_gate
    permission_gate = next(item for item in payload["gates"] if item["key"] == "permission-gates")
    assert permission_gate["status"] == "pass", permission_gate
    assert "permissions approved" in permission_gate["detail"], permission_gate
    assert "gaps 0" in permission_gate["detail"], permission_gate
    permission_runtime_gate = next(item for item in payload["gates"] if item["key"] == "permission-runtime")
    assert permission_runtime_gate["status"] == "pass", permission_runtime_gate
    assert "metadata fallback 4" in permission_runtime_gate["detail"], permission_runtime_gate
    assert "native 0" in permission_runtime_gate["detail"], permission_runtime_gate
    intent_gate = next(item for item in payload["gates"] if item["key"] == "intent-canvas")
    assert intent_gate["status"] == "pass", intent_gate
    assert "intent confidence 100/100" in intent_gate["detail"], intent_gate
    atlas_gate = next(item for item in payload["gates"] if item["key"] == "skill-atlas")
    assert atlas_gate["status"] == "pass", atlas_gate
    assert "actionable route collisions" in atlas_gate["detail"], atlas_gate
    assert "actionable drift" in atlas_gate["detail"], atlas_gate
    operations_gate = next(item for item in payload["gates"] if item["key"] == "operations-loop")
    assert operations_gate["status"] == "pass", operations_gate
    assert "metadata events" in operations_gate["detail"], operations_gate
    assert "risk low" in operations_gate["detail"], operations_gate
    assert "reports/adoption_drift_report.json" in operations_gate["evidence"], operations_gate
    waivers_gate = next(item for item in payload["gates"] if item["key"] == "review-waivers")
    assert waivers_gate["status"] == "warn", waivers_gate
    assert "1 warning gates still need reviewer decision" in waivers_gate["detail"], waivers_gate
    assert "reports/review_waivers.json" in waivers_gate["evidence"], waivers_gate
    world_class_gate = next(item for item in payload["gates"] if item["key"] == "world-class-evidence")
    assert world_class_gate["status"] == "warn", world_class_gate
    assert "4 pending world-class evidence entries" in world_class_gate["detail"], world_class_gate
    assert "1 human pending" in world_class_gate["detail"], world_class_gate
    assert "3 external pending" in world_class_gate["detail"], world_class_gate
    assert "overclaim guard true" in world_class_gate["detail"], world_class_gate
    assert world_class_gate["evidence"] == "reports/world_class_evidence_ledger.json", world_class_gate
    assert output_html.exists(), output_html
    assert output_json.exists(), output_json
    full_payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert full_payload["evidence_paths"]["compiled_targets"] == "reports/compiled_targets.md", full_payload["evidence_paths"]
    assert full_payload["evidence_paths"]["output_execution"] == "reports/output_execution_runs.md", full_payload["evidence_paths"]
    assert full_payload["evidence_paths"]["output_blind_review"] == "reports/output_blind_review_pack.md", full_payload["evidence_paths"]
    assert full_payload["evidence_paths"]["output_review_kit_html"] == "reports/output_review_kit.html", full_payload["evidence_paths"]
    assert full_payload["evidence_paths"]["output_review_decisions"] == "reports/output_review_decisions.json", full_payload["evidence_paths"]
    assert full_payload["evidence_paths"]["output_review_adjudication"] == "reports/output_review_adjudication.md", full_payload["evidence_paths"]
    assert full_payload["evidence_paths"]["python_compatibility"] == "reports/python_compatibility.md", full_payload["evidence_paths"]
    assert full_payload["evidence_paths"]["architecture_maintainability"] == "reports/architecture_maintainability.md", full_payload["evidence_paths"]
    if (ROOT / "reports" / "benchmark_reproducibility.md").exists():
        assert full_payload["evidence_paths"]["benchmark_reproducibility"] == "reports/benchmark_reproducibility.md", full_payload["evidence_paths"]
    if (ROOT / "reports" / "skill_os2_coverage.md").exists():
        assert full_payload["evidence_paths"]["skill_os2_coverage"] == "reports/skill_os2_coverage.md", full_payload["evidence_paths"]
    assert full_payload["evidence_paths"]["review_annotations"] == "reports/review_annotations.md", full_payload["evidence_paths"]
    if (ROOT / "reports" / "world_class_evidence_plan.md").exists():
        assert full_payload["evidence_paths"]["world_class_evidence_plan"] == "reports/world_class_evidence_plan.md", full_payload["evidence_paths"]
    if (ROOT / "reports" / "world_class_evidence_ledger.md").exists():
        assert full_payload["evidence_paths"]["world_class_evidence_ledger"] == "reports/world_class_evidence_ledger.md", full_payload["evidence_paths"]
    if (ROOT / "reports" / "world_class_evidence_intake.md").exists():
        assert full_payload["evidence_paths"]["world_class_evidence_intake"] == "reports/world_class_evidence_intake.md", full_payload["evidence_paths"]
    if (ROOT / "reports" / "world_class_submission_review.md").exists():
        assert full_payload["evidence_paths"]["world_class_submission_review"] == "reports/world_class_submission_review.md", full_payload["evidence_paths"]
    if (ROOT / "reports" / "world_class_operator_runbook.md").exists():
        assert full_payload["evidence_paths"]["world_class_operator_runbook"] == "reports/world_class_operator_runbook.md", full_payload["evidence_paths"]
    if (ROOT / "reports" / "world_class_operator_runbook.html").exists():
        assert full_payload["evidence_paths"]["world_class_operator_runbook_html"] == "reports/world_class_operator_runbook.html", full_payload["evidence_paths"]
    if (ROOT / "reports" / "world_class_claim_guard.md").exists():
        assert full_payload["evidence_paths"]["world_class_claim_guard"] == "reports/world_class_claim_guard.md", full_payload["evidence_paths"]
    assert full_payload["data"]["output_blind_review"]["summary"]["pair_count"] == 5, full_payload["data"]["output_blind_review"]
    assert full_payload["data"]["output_execution"]["summary"]["command_executed_count"] == 10, full_payload["data"]["output_execution"]
    assert full_payload["data"]["output_execution"]["summary"]["recorded_fixture_count"] == 0, full_payload["data"]["output_execution"]
    assert full_payload["data"]["output_execution"]["summary"]["model_executed_count"] == 0, full_payload["data"]["output_execution"]
    assert full_payload["data"]["output_review_adjudication"]["summary"]["pending_count"] == 5, full_payload["data"]["output_review_adjudication"]
    assert full_payload["data"]["output_review_adjudication"]["summary"]["answer_revealed_count"] == 0, full_payload["data"]["output_review_adjudication"]
    assert full_payload["data"]["output_review_adjudication"]["summary"]["pending_answer_hidden_count"] == 5, full_payload["data"]["output_review_adjudication"]
    assert full_payload["data"]["output_review_adjudication"]["summary"]["reviewer_checklist_count"] == 5, full_payload["data"]["output_review_adjudication"]
    assert full_payload["data"]["output_review_adjudication"]["summary"]["reviewer_checklist_pending_count"] == 5, full_payload["data"]["output_review_adjudication"]
    assert full_payload["data"]["output_review_adjudication"]["summary"]["reviewer_checklist_ready_count"] == 0, full_payload["data"]["output_review_adjudication"]
    assert all(not item["expected_revealed"] for item in full_payload["data"]["output_review_adjudication"]["pairs"]), full_payload["data"]["output_review_adjudication"]
    benchmark_summary = full_payload["data"]["benchmark_reproducibility"]["summary"]
    assert benchmark_summary["reproducibility_ready"] is True, benchmark_summary
    assert benchmark_summary["release_lock_ready"] == (benchmark_summary["working_tree_dirty"] is False), benchmark_summary
    assert benchmark_summary["public_claim_ready"] is False, benchmark_summary
    assert benchmark_summary["public_claim_blocker_count"] >= 3, benchmark_summary
    public_claim = full_payload["data"]["benchmark_reproducibility"]["public_claim"]
    assert public_claim["ready"] is False, public_claim
    assert any("provider-backed model holdout evidence is incomplete" in item for item in public_claim["blockers"]), public_claim
    assert any("human blind-review adjudication is incomplete" in item for item in public_claim["blockers"]), public_claim
    output_review_checklist = full_payload["data"]["output_review_adjudication"]["reviewer_checklist"]
    assert len(output_review_checklist) == 5, output_review_checklist
    assert all(not item["answer_key_visible"] for item in output_review_checklist), output_review_checklist
    assert output_review_checklist[0]["commands"]["adjudicate"] == "python3 scripts/yao.py output-review", output_review_checklist[0]
    assert full_payload["data"]["review_annotations"]["summary"]["annotation_count"] == 0, full_payload["data"]["review_annotations"]
    waiver_summary = full_payload["data"]["review_waivers"]["summary"]
    assert waiver_summary["waiver_candidate_count"] == 2, waiver_summary
    assert waiver_summary["waiverable_open_count"] == 1, waiver_summary
    assert waiver_summary["non_waivable_count"] == 1, waiver_summary
    waiver_candidates = {item["gate_key"]: item for item in full_payload["data"]["review_waivers"]["waiver_candidates"]}
    assert waiver_candidates["output-lab"]["waiver_allowed"] is True, waiver_candidates
    assert waiver_candidates["output-lab"]["status"] == "needs-reviewer-decision", waiver_candidates
    assert waiver_candidates["output-lab"]["risk_summary"] == "review pending 5; model-executed 0; output failures 0", waiver_candidates
    assert "review-waivers . --add-waiver" in waiver_candidates["output-lab"]["suggested_command"], waiver_candidates
    assert "Does not count as provider, human, or public world-class completion evidence" in waiver_candidates["output-lab"]["world_class_boundary"], waiver_candidates
    assert waiver_candidates["world-class-evidence"]["waiver_allowed"] is False, waiver_candidates
    assert waiver_candidates["world-class-evidence"]["status"] == "cannot-waive", waiver_candidates
    assert waiver_candidates["world-class-evidence"]["risk_summary"] == "4 pending evidence entries; 1 human pending; 3 external pending", waiver_candidates
    assert "Non-waivable completion boundary" in waiver_candidates["world-class-evidence"]["world_class_boundary"], waiver_candidates
    assert full_payload["data"]["compiled_targets"]["summary"]["target_count"] >= 4, full_payload["data"]["compiled_targets"]
    assert full_payload["data"]["compiled_targets"]["summary"]["block_count"] == 0, full_payload["data"]["compiled_targets"]
    assert full_payload["data"]["runtime_permissions"]["summary"]["metadata_fallback_count"] == 4, full_payload["data"]["runtime_permissions"]
    assert full_payload["evidence_paths"]["runtime_permissions"] == "reports/runtime_permission_probes.md", full_payload["evidence_paths"]
    assert full_payload["data"]["python_compatibility"]["summary"]["target_python"] == "3.11", full_payload["data"]["python_compatibility"]
    assert full_payload["data"]["python_compatibility"]["summary"]["issue_count"] == 0, full_payload["data"]["python_compatibility"]
    assert full_payload["data"]["architecture_maintainability"]["summary"]["hotspot_count"] == 0, full_payload["data"]["architecture_maintainability"]
    assert full_payload["data"]["architecture_maintainability"]["summary"]["blocker_count"] == 0, full_payload["data"]["architecture_maintainability"]
    action_keys = {item["gate_key"] for item in full_payload["review_actions"]}
    assert action_keys == {"output-lab", "review-waivers", "world-class-evidence"}, full_payload["review_actions"]
    world_class_action = next(item for item in full_payload["review_actions"] if item["gate_key"] == "world-class-evidence")
    assert {item["path"] for item in world_class_action["source_refs"]} >= {
        "reports/world_class_evidence_ledger.md",
        "reports/world_class_evidence_plan.md",
        "reports/world_class_evidence_intake.md",
        "reports/world_class_submission_review.md",
        "reports/world_class_claim_guard.md",
        "evidence/world_class/intake.schema.json",
        "evidence/world_class/templates/provider-holdout.intake.json",
        "evidence/world_class/templates/human-adjudication.intake.json",
        "reports/skill_os2_audit.md",
    }, world_class_action
    assert all(item["exists"] for item in world_class_action["source_refs"]), world_class_action
    assert "world-class-runbook" in world_class_action["verification_command"], world_class_action
    assert "--submissions-dir evidence/world_class/submissions" in world_class_action["verification_command"], world_class_action
    assert "reports/world_class_operator_runbook.html" in world_class_action["source_fix"], world_class_action
    assert full_payload["data"]["world_class_evidence_ledger"]["summary"]["pending_count"] == 4, full_payload["data"]["world_class_evidence_ledger"]
    assert full_payload["data"]["world_class_evidence_intake"]["summary"]["decision"] == "awaiting-submissions", full_payload["data"]["world_class_evidence_intake"]
    assert full_payload["data"]["world_class_submission_review"]["summary"]["decision"] == "awaiting-submissions", full_payload["data"]["world_class_submission_review"]
    assert full_payload["data"]["world_class_submission_review"]["summary"]["review_counts_submission_as_completion"] is False, full_payload["data"]["world_class_submission_review"]
    assert full_payload["data"]["world_class_submission_review"]["summary"]["awaiting_submission_count"] == 4, full_payload["data"]["world_class_submission_review"]
    assert full_payload["data"]["world_class_submission_review"]["summary"]["source_check_count"] >= 13, full_payload["data"]["world_class_submission_review"]
    assert full_payload["data"]["world_class_submission_review"]["summary"]["source_blocked_count"] >= 6, full_payload["data"]["world_class_submission_review"]
    assert full_payload["data"]["world_class_operator_runbook"]["summary"]["decision"] == "collect-evidence", full_payload["data"]["world_class_operator_runbook"]
    assert full_payload["data"]["world_class_operator_runbook"]["summary"]["runbook_counts_as_completion"] is False, full_payload["data"]["world_class_operator_runbook"]
    assert full_payload["data"]["world_class_operator_runbook"]["summary"]["awaiting_submission_count"] == 4, full_payload["data"]["world_class_operator_runbook"]
    assert full_payload["data"]["world_class_evidence_intake"]["summary"]["template_pass_count"] == 4, full_payload["data"]["world_class_evidence_intake"]
    assert full_payload["data"]["world_class_evidence_intake"]["summary"]["operator_checklist_count"] == 4, full_payload["data"]["world_class_evidence_intake"]
    assert full_payload["data"]["world_class_evidence_intake"]["summary"]["operator_checklist_ready_count"] == 0, full_payload["data"]["world_class_evidence_intake"]
    assert full_payload["data"]["world_class_evidence_intake"]["summary"]["ready_to_claim_world_class"] is False, full_payload["data"]["world_class_evidence_intake"]
    intake_checklist = full_payload["data"]["world_class_evidence_intake"]["operator_checklist"]
    assert len(intake_checklist) == 4, intake_checklist
    provider_checklist = next(item for item in intake_checklist if item["evidence_key"] == "provider-holdout")
    assert provider_checklist["readiness"] == "awaiting-submission", provider_checklist
    assert provider_checklist["submission_path"] == "evidence/world_class/submissions/provider-holdout.json", provider_checklist
    assert provider_checklist["commands"]["validate_intake"] == "python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions", provider_checklist
    assert provider_checklist["commands"]["submission_review"] == "python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions", provider_checklist
    assert provider_checklist["commands"]["refresh_ledger"] == "python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions", provider_checklist
    assert "provider-backed model run" in provider_checklist["must_collect"]["provenance_requirements"], provider_checklist
    assert full_payload["data"]["world_class_claim_guard"]["summary"]["decision"] == "claim-guard-pass-evidence-pending", full_payload["data"]["world_class_claim_guard"]
    assert full_payload["data"]["world_class_claim_guard"]["summary"]["violation_count"] == 0, full_payload["data"]["world_class_claim_guard"]
    assert full_payload["data"]["world_class_claim_guard"]["summary"]["ledger_pending_count"] == 4, full_payload["data"]["world_class_claim_guard"]
    if full_payload["data"]["skill_os2_coverage"]:
        assert full_payload["data"]["skill_os2_coverage"]["summary"]["local_blueprint_ready"] is True, full_payload["data"]["skill_os2_coverage"]
        assert full_payload["data"]["skill_os2_coverage"]["summary"]["public_world_class_ready"] is False, full_payload["data"]["skill_os2_coverage"]
    world_class_entries = full_payload["data"]["world_class_evidence_ledger"]["entries"]
    assert len(world_class_entries) == 4, world_class_entries
    assert {item["key"] for item in world_class_entries} == {
        "provider-holdout",
        "human-adjudication",
        "native-permission-enforcement",
        "native-client-telemetry",
    }, world_class_entries
    provider_entry = next(item for item in world_class_entries if item["key"] == "provider-holdout")
    assert provider_entry["status"] == "pending", provider_entry
    assert "reports/output_execution_runs.json summary.model_executed_count > 0" in provider_entry["success_checks"], provider_entry
    assert provider_entry["observed_state"]["model_executed_count"] == 0, provider_entry
    assert provider_entry["submission_state"]["status"] == "missing", provider_entry
    assert provider_entry["submission_state"]["ledger_counts_as_completion"] is False, provider_entry
    assert full_payload["data"]["atlas"]["summary"]["actionable_route_collision_count"] == 0, full_payload["data"]["atlas"]
    assert full_payload["data"]["atlas"]["summary"]["actionable_drift_signal_count"] == 0, full_payload["data"]["atlas"]
    assert full_payload["data"]["atlas"]["summary"]["non_actionable_issue_count"] >= 1, full_payload["data"]["atlas"]
    synthetic_actions = review_studio.build_review_actions(
        [
            {
                "key": "output-lab",
                "label": "输出实验",
                "status": "warn",
                "detail": "synthetic missing output coverage",
                "evidence": "reports/output_quality_scorecard.json",
                "link": "reports/output_quality_scorecard.md",
            }
        ],
        ROOT,
        output_html,
    )
    assert len(synthetic_actions) == 1, synthetic_actions
    assert synthetic_actions[0]["source_refs"], synthetic_actions
    assert {item["path"] for item in synthetic_actions[0]["source_refs"]} >= {
        "evals/output/cases.jsonl",
        "reports/output_quality_scorecard.md",
        "reports/output_execution_runs.md",
        "reports/output_blind_review_pack.md",
        "reports/output_review_kit.html",
        "reports/output_review_adjudication.md",
    }, synthetic_actions
    assert all(item["exists"] for item in synthetic_actions[0]["source_refs"]), synthetic_actions
    assert all(isinstance(item["line"], int) and item["line"] >= 1 for item in synthetic_actions[0]["source_refs"]), synthetic_actions
    synthetic_json = json.dumps(synthetic_actions, ensure_ascii=False)
    assert str(ROOT) not in synthetic_json, synthetic_json
    synthetic_html = review_studio.render_review_actions(synthetic_actions)
    assert "source-ref-list" in synthetic_html, synthetic_html
    assert "evals/output/cases.jsonl" in synthetic_html, synthetic_html
    html = output_html.read_text(encoding="utf-8")
    assert "Review Studio 2.0" in html, html[:400]
    assert "审查闸门" in html, html[:1200]
    assert "修复动作" in html, html[:3000]
    assert "补足 output eval 覆盖、execution evidence、blind A/B 和 reviewer adjudication。" in html, html[:9000]
    assert "resource governance governed" in html, html[:9000]
    assert "reports/output_review_kit.html" in html, html[:9000]
    assert "python3 scripts/adjudicate_output_review.py --write-template" in html, html[:9000]
    assert "对保留的 warning 写入 reviewer、理由、范围和到期时间，或修掉 warning。" in html, html[:9000]
    assert "补齐 provider、真人盲评、原生权限执行和真实客户端遥测证据" in html, html
    assert "世界证据" in html, html
    assert "证据台账" in html, html
    assert "证据入口" in html, html
    assert "入口边界" in html, html
    assert "声明守卫" in html, html
    assert "声明边界" in html, html
    assert "提交清单" in html, html
    assert "world-intake-grid" in html, html
    assert "操作命令" in html, html
    assert "收集要求" in html, html
    assert "通过条件" in html, html
    assert "evidence/world_class/submissions/provider-holdout.json" in html, html
    assert "python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions" in html, html
    assert "intake 只校验证据包格式、来源、隐私和反过度声明" in html, html
    assert "reports/world_class_evidence_intake.md" in html, html
    assert "reports/world_class_operator_runbook.html" in html, html
    assert "reports/world_class_claim_guard.md" in html, html
    assert "英文完成断言、true 状态声明或中文完成态" in html, html
    assert "world-evidence-grid" in html, html
    assert "Provider Holdout" in html, html
    assert "Native Permission Enforcement" in html, html
    assert "提交态" in html, html
    assert "status: missing" in html, html
    assert "完成定义" in html, html
    assert "证据来源" in html, html
    assert "隐私约束" in html, html
    assert "reports/output_execution_runs.json summary.model_executed_count &gt; 0" in html, html
    assert "计划、metadata fallback、待评审和本地命令不会被当成完成证据" in html, html
    assert "源证据检查" in html, html
    assert "world-source-checks" in html, html
    assert "Provider model run" in html, html
    assert "model_executed_count: 0 / &gt;0" in html, html
    assert "Token usage observed" in html, html
    assert "蓝图覆盖" in html, html
    assert "本地蓝图" in html, html
    assert "public world-class 仍以 world-class evidence ledger" in html, html
    assert "公开声明" in html, html
    assert "声明阻断" in html, html
    assert "可公开声明" in html, html
    assert "provider-backed model holdout evidence is incomplete" in html, html
    assert "human blind-review adjudication is incomplete" in html, html
    assert "审查批注" in html, html[:9000]
    assert "当前没有 reviewer 批注" in html, html[:9000]
    assert "输出实验" in html, html[:2000]
    assert "执行证据" in html, html
    assert "盲评包" in html, html[:5000]
    assert "审定报告" in html, html
    assert "评审清单" in html, html
    assert "output-review-grid" in html, html
    assert "awaiting-decision" in html, html
    assert "答案隐藏" in html, html
    assert "winner_variant" in html, html
    assert "python3 scripts/yao.py output-review" in html, html
    assert "答案揭示" in html, html
    assert "答案隐藏" in html, html
    assert "注册审计" in html, html[:3000]
    assert "包体验证" in html, html[:5000]
    assert "Upgrade" in html, html[:6000]
    assert "Compiler" in html, html[:6000]
    assert "目标编译" in html, html[:9000]
    assert "reports/compiled_targets.md" in output_json.read_text(encoding="utf-8"), output_json
    assert "Install" in html, html[:6500]
    assert "运营回路" in html, html[:7600]
    assert "人工批准" in html, html[:8200]
    assert "warning 可以被有边界地接受" in html, html
    assert "批准概况" in html, html
    assert "批准候选" in html, html
    assert "waiver-candidate-grid" in html, html
    assert "可批准 · needs-reviewer-decision" in html, html
    assert "不可批准 · cannot-waive" in html, html
    assert "review pending 5; model-executed 0; output failures 0" in html, html
    assert "4 pending evidence entries; 1 human pending; 3 external pending" in html, html
    assert "Does not count as provider, human, or public world-class completion evidence" in html, html
    assert "Non-waivable completion boundary" in html, html
    assert "python3 scripts/yao.py review-waivers . --add-waiver" in html, html
    assert "Reviewer confirms this release does not claim provider-backed or human-adjudicated output superiority" in html, html
    assert "Do not use a waiver to claim public world-class readiness" in html, html
    assert "权限批准" in html, html[:9000]
    assert "权限探针" in html, html[:9500]
    assert "Python 兼容" in html, html[:10000]
    assert "解释器边界" in html, html[:10000]
    assert "reports/python_compatibility.md" in html, html
    assert "架构维护" in html, html
    assert "Arch Debt" in html, html
    assert "reports/architecture_maintainability.md" in html, html
    assert "0 hotspots" in html, html
    assert "kv-grid" in html, html
    assert "案例数" in html, html
    assert "命令执行" in html, html
    assert "包体哈希" in html, html
    assert "{&#x27;" not in html, html
    assert "&#x27;case_count&#x27;" not in html, html
    assert "&#x27;name&#x27;" not in html, html
    assert "reports/review_waivers.md" in output_json.read_text(encoding="utf-8"), output_json
    assert "upgrade minor declared / minor recommended" in html, html[:8000]
    assert str(ROOT) not in output_json.read_text(encoding="utf-8"), output_json
    formatted = review_formatting.render_kv_grid(
        {"case_count": 5, "package_sha256": "abc123"},
        ["case_count", "package_sha256"],
        "missing",
    )
    assert "kv-grid" in formatted, formatted
    assert "案例数" in formatted, formatted
    assert "<code>abc123</code>" in formatted, formatted
    assert review_formatting.value_text({"case_count": 5}) == "案例数: 5"
    assert review_gates.min_output_cases("scaffold") == 1
    assert review_gates.min_output_cases("production") == 3
    assert review_gates.min_output_cases("governed") == 5
    assert review_gates.status_label("warn") == "关注"
    assert review_gates.weighted_score([{"key": "output-lab", "status": "pass"}]) == 100
    assert review_gates.weighted_score([{"key": "output-lab", "status": "warn"}]) == 60
    assert len(review_layout.REVIEW_STUDIO_NAV) == 16, review_layout.REVIEW_STUDIO_NAV
    assert ("#world-class", "世界证据") in review_layout.REVIEW_STUDIO_NAV, review_layout.REVIEW_STUDIO_NAV
    assert "position: sticky" in review_layout.review_studio_css(), review_layout.review_studio_css()[:400]
    assert "#overview" in review_layout.render_review_nav(), review_layout.render_review_nav()
    assert "审查总览" in review_layout.render_review_nav(), review_layout.render_review_nav()
    assert review_layout.render_review_nav([]) == ""
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
