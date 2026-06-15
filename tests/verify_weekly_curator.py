#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_weekly_curator_report.py"
CLI = ROOT / "scripts" / "yao.py"
TMP = ROOT / "tests" / "tmp_weekly_curator"


def run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def seed_reports(skill_dir: Path) -> None:
    reports = skill_dir / "reports"
    write_json(
        reports / "skillops" / "daily" / "2026-06-16.json",
        {
            "ok": True,
            "generated_at": "2026-06-16T08:00:00Z",
            "opportunity_summary": {"opportunity_count": 3},
            "opportunities": [
                {
                    "opportunity_id": "skillops-aaaaaaaaaa",
                    "proposal_id": "adapt-a",
                    "pattern_id": "report_ui",
                    "title": "Improve report layout",
                    "opportunity_type": "artifact-quality",
                    "action_type": "patch_existing_skill",
                    "decision": "ready_for_approval_review",
                    "priority": "high",
                    "score": 92,
                    "risk_level": "medium",
                    "requires_approval": True,
                    "write_allowed_without_approval": False,
                    "evidence_count": 5,
                    "target_files": ["scripts/render_skill_overview.py"],
                    "verification_commands": ["python3 tests/verify_skill_overview.py"],
                    "policy_reason": "Report layout feedback maps to renderer changes.",
                },
                {
                    "opportunity_id": "skillops-bbbbbbbbbb",
                    "proposal_id": "adapt-b",
                    "pattern_id": "approval_safety",
                    "title": "Keep adaptive changes approval-gated",
                    "opportunity_type": "governance",
                    "action_type": "agents_update",
                    "decision": "proposal_review",
                    "priority": "medium",
                    "score": 78,
                    "risk_level": "low",
                    "requires_approval": True,
                    "write_allowed_without_approval": False,
                    "evidence_count": 2,
                    "target_files": ["AGENTS.md"],
                    "verification_commands": ["python3 tests/verify_adaptation_safety.py"],
                    "policy_reason": "Governance feedback maps to durable guidance.",
                },
                {
                    "opportunity_id": "skillops-cccccccccc",
                    "proposal_id": "adapt-c",
                    "pattern_id": "evidence_testing",
                    "title": "Add evidence regression",
                    "opportunity_type": "quality-gate",
                    "action_type": "add_eval",
                    "decision": "proposal_review",
                    "priority": "medium",
                    "score": 72,
                    "risk_level": "medium",
                    "requires_approval": True,
                    "write_allowed_without_approval": False,
                    "evidence_count": 2,
                    "target_files": ["tests/verify_daily_skillops.py"],
                    "verification_commands": ["python3 tests/verify_daily_skillops.py"],
                    "policy_reason": "Verification feedback maps to focused checks.",
                },
            ],
        },
    )
    write_json(
        reports / "skill_atlas.json",
        {
            "ok": True,
            "summary": {
                "skill_count": 4,
                "route_collision_count": 2,
                "actionable_route_collision_count": 1,
                "owner_gap_count": 1,
                "actionable_owner_gap_count": 0,
                "stale_count": 1,
                "actionable_stale_count": 0,
                "drift_signal_count": 1,
                "actionable_drift_signal_count": 0,
                "no_route_opportunity_count": 1,
            },
        },
    )
    write_json(reports / "benchmark_reproducibility.json", {"ok": True, "summary": {"release_lock_ready": True}})
    write_json(reports / "evidence_consistency.json", {"ok": True, "summary": {"decision": "consistent"}})
    write_json(
        reports / "world_class_evidence_ledger.json",
        {"ok": True, "summary": {"pending_count": 4, "ready_to_claim_world_class": False}},
    )


def assert_contract(payload: dict) -> None:
    assert payload["schema_version"] == "1.0", payload
    assert payload["ok"] is True, payload
    assert payload["report_contract"]["contract"] == "weekly-skillops-curator-report", payload
    assert payload["curator_contract"]["writes_source_files"] is False, payload
    assert payload["curator_contract"]["auto_patch_enabled"] is False, payload
    assert payload["curator_contract"]["approval_required_for_writes"] is True, payload
    assert payload["curator_contract"]["counts_as_world_class_evidence"] is False, payload
    for field in payload["report_contract"]["summary_fields"]:
        assert payload[field] == payload["summary"][field], field


def main() -> None:
    shutil.rmtree(TMP, ignore_errors=True)
    skill_dir = TMP / "weekly-curator-demo"
    skill_dir.mkdir(parents=True)
    seed_reports(skill_dir)
    output_json = skill_dir / "reports" / "skillops" / "weekly" / "2026-W25.json"
    output_md = skill_dir / "reports" / "skillops" / "weekly" / "2026-W25.md"

    proc = run_command(
        str(SCRIPT),
        str(skill_dir),
        "--output-json",
        str(output_json),
        "--output-md",
        str(output_md),
        "--generated-at",
        "2026-06-16T08:00:00Z",
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert_contract(payload)
    assert payload["summary"]["week_id"] == "2026-W25", payload
    assert payload["summary"]["daily_report_count"] == 1, payload
    assert payload["summary"]["unique_opportunity_count"] == 3, payload
    assert payload["summary"]["ready_for_approval_review_count"] == 1, payload
    assert payload["summary"]["proposal_review_count"] == 2, payload
    assert payload["summary"]["top_score"] == 92, payload
    assert payload["summary"]["skill_count"] == 4, payload
    assert payload["summary"]["actionable_portfolio_issue_count"] == 2, payload
    assert payload["summary"]["release_lock_ready"] is True, payload
    assert payload["summary"]["evidence_consistency_ok"] is True, payload
    assert payload["summary"]["public_world_class_ready"] is False, payload
    assert payload["summary"]["world_class_pending_count"] == 4, payload
    assert payload["opportunity_summary"]["action_type_counts"]["patch_existing_skill"] == 1, payload
    assert payload["opportunity_summary"]["action_type_counts"]["agents_update"] == 1, payload
    assert payload["opportunity_summary"]["action_type_counts"]["add_eval"] == 1, payload
    assert all(item["write_allowed_without_approval"] is False for item in payload["curator_queue"]), payload
    action_keys = {item["key"] for item in payload["actions"]}
    assert {"review-ready-opportunities", "triage-skill-library", "close-world-class-evidence"} <= action_keys, payload
    markdown = output_md.read_text(encoding="utf-8")
    assert "Weekly SkillOps Curator Report" in markdown, markdown
    assert "## Curator Queue" in markdown, markdown
    assert "counts_as_world_class_evidence: `false`" in markdown, markdown

    cli_output_json = skill_dir / "reports" / "skillops" / "weekly" / "cli.json"
    cli_output_md = skill_dir / "reports" / "skillops" / "weekly" / "cli.md"
    cli_proc = run_command(
        str(CLI),
        "weekly-curator",
        str(skill_dir),
        "--output-json",
        str(cli_output_json),
        "--output-md",
        str(cli_output_md),
        "--generated-at",
        "2026-06-16T08:00:00Z",
    )
    assert cli_proc.returncode == 0, cli_proc.stderr
    cli_payload = json.loads(cli_proc.stdout)
    assert_contract(cli_payload)
    assert cli_payload["summary"]["unique_opportunity_count"] == 3, cli_payload
    assert cli_output_json.exists(), cli_output_json
    assert cli_output_md.exists(), cli_output_md

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
