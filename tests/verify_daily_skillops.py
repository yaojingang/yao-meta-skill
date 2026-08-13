#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_daily_skillops_report.py"
CLI = ROOT / "scripts" / "yao.py"
TMP = ROOT / "tests" / "tmp_daily_skillops"
FAKE_API_SECRET = "sk-" + "1234567890abcdef"
FAKE_INLINE_TOKEN = "token=" + "abc123456789"
FAKE_LOCAL_PATH = "/Users/" + "fixture-user/private/path"


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


def seed_release_reports(skill_dir: Path) -> None:
    reports = skill_dir / "reports"
    write_json(
        reports / "skill_os2_coverage.json",
        {
            "ok": True,
            "summary": {
                "local_blueprint_ready": True,
                "public_world_class_ready": False,
                "world_class_evidence_pending_count": 4,
            },
        },
    )
    write_json(
        reports / "world_class_evidence_ledger.json",
        {
            "ok": True,
            "summary": {
                "pending_count": 4,
                "accepted_count": 0,
                "ready_to_claim_world_class": False,
            },
        },
    )
    write_json(reports / "evidence_consistency.json", {"ok": True, "checks": [{"status": "pass"}]})
    write_json(reports / "benchmark_reproducibility.json", {"ok": True, "summary": {"release_lock_ready": True}})
    write_json(
        reports / "adaptation_approval_ledger.json",
        {
            "ok": True,
            "summary": {
                "approval_count": 1,
                "pending_review_count": 1,
                "applied_count": 0,
                "rollback_count": 0,
            },
        },
    )
    write_json(
        reports / "adaptation_regression_report.json",
        {
            "ok": True,
            "summary": {
                "attempt_count": 1,
                "dry_run_count": 1,
                "applied_count": 0,
                "rollback_count": 0,
            },
        },
    )


def write_signal_source(path: Path) -> None:
    sensitive_text = (
        "报告默认中文简体，同时右上角提供英文切换；敏感内容 "
        f"{FAKE_INLINE_TOKEN}、{FAKE_API_SECRET} 和 {FAKE_LOCAL_PATH} 必须脱敏。"
    )
    path.write_text(
        "\n".join(
            [
                json.dumps({"text": sensitive_text}, ensure_ascii=False),
                json.dumps({"message": "新的 HTML 报告要双语，但默认中文简体。"}, ensure_ascii=False),
                json.dumps({"content": "报告 UI 需要 Kami 白底排版、图表模块和清晰导航。"}, ensure_ascii=False),
                json.dumps({"excerpt": "HTML 报告还是白底 Kami 风格，图表不要挤在一起。"}, ensure_ascii=False),
                json.dumps({"note": "不要自动扫描私人日志；必须由用户提供明确路径。"}, ensure_ascii=False),
                json.dumps({"body": "自适应升级需要先输出提案，授权后再修改，并能回滚。"}, ensure_ascii=False),
                json.dumps({"text": "每次升级都要有测试、证据报告和 GitHub push。"}, ensure_ascii=False),
                json.dumps({"text": "敏感内容也不能直接进入公开日报。"}, ensure_ascii=False),
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def assert_daily_contract(payload: dict) -> None:
    assert payload["schema_version"] == "1.0", payload
    assert payload["ok"] is True, payload
    assert payload["report_contract"]["contract"] == "daily-skillops-report", payload
    assert payload["report_contract"]["top_level_mirrors_summary"] is True, payload
    for field in payload["report_contract"]["summary_fields"]:
        assert payload[field] == payload["summary"][field], (field, payload.get(field), payload["summary"].get(field))
    contract = payload["operations_contract"]
    assert contract["explicit_source_required_for_scan"] is True, payload
    assert contract["implicit_private_log_scan"] is False, payload
    assert contract["raw_content_stored"] is False, payload
    assert contract["redacted_excerpts_only"] is True, payload
    assert contract["proposal_only"] is True, payload
    assert contract["approval_required_for_writes"] is True, payload
    assert contract["writes_source_files"] is False, payload
    assert contract["auto_patch_enabled"] is False, payload
    assert contract["daily_report_counts_as_world_class_evidence"] is False, payload


def main() -> None:
    shutil.rmtree(TMP, ignore_errors=True)
    skill_dir = TMP / "daily-skillops-demo"
    skill_dir.mkdir(parents=True)
    seed_release_reports(skill_dir)
    source = TMP / "curated-signals.jsonl"
    write_signal_source(source)
    source_before = source.read_text(encoding="utf-8")

    output_json = skill_dir / "reports" / "skillops" / "daily" / "2026-06-16.json"
    output_md = skill_dir / "reports" / "skillops" / "daily" / "2026-06-16.md"
    proc = run_command(
        str(SCRIPT),
        str(skill_dir),
        "--source",
        str(source),
        "--output-json",
        str(output_json),
        "--output-md",
        str(output_md),
        "--generated-at",
        "2026-06-16T08:00:00Z",
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert_daily_contract(payload)
    assert payload["summary"]["source_supplied"] is True, payload
    assert payload["summary"]["pattern_count"] >= 4, payload
    assert payload["summary"]["proposal_count"] >= 4, payload
    assert payload["summary"]["pending_review_count"] == 1, payload
    assert payload["summary"]["world_class_pending_count"] == 4, payload
    assert payload["summary"]["public_world_class_ready"] is False, payload
    assert payload["summary"]["release_lock_ready"] is True, payload
    assert payload["summary"]["evidence_consistency_ok"] is True, payload
    assert payload["opportunity_summary"]["opportunity_count"] >= 4, payload
    assert payload["opportunity_summary"]["top_score"] >= 70, payload
    assert payload["decision_policy"]["writes_source_files"] is False, payload
    assert payload["decision_policy"]["auto_patch_enabled"] is False, payload
    action_types = {item["action_type"] for item in payload["opportunities"]}
    assert {"patch_existing_skill", "agents_update"} <= action_types, payload["opportunities"]
    assert action_types <= set(payload["decision_policy"]["action_types"]), payload["opportunities"]
    assert all(item["write_allowed_without_approval"] is False for item in payload["opportunities"]), payload[
        "opportunities"
    ]
    action_keys = {item["key"] for item in payload["actions"]}
    assert {"review-adaptation-proposals", "resolve-pending-approvals", "close-world-class-evidence"} <= action_keys, payload
    assert output_json.exists(), output_json
    assert output_md.exists(), output_md
    assert (skill_dir / "reports" / "user_patterns.json").exists(), skill_dir
    assert (skill_dir / "reports" / "adaptation_proposals.json").exists(), skill_dir
    assert source.read_text(encoding="utf-8") == source_before, source

    serialized = json.dumps(payload, ensure_ascii=False)
    assert FAKE_API_SECRET not in serialized, serialized
    assert FAKE_INLINE_TOKEN not in serialized, serialized
    assert FAKE_LOCAL_PATH not in serialized, serialized
    assert "[REDACTED_SECRET]" in serialized, serialized
    assert "[LOCAL_PATH]" in serialized, serialized
    markdown = output_md.read_text(encoding="utf-8")
    assert "Daily SkillOps Report" in markdown, markdown
    assert "does not scan private logs" in markdown, markdown
    assert "daily_report_counts_as_world_class_evidence: `false`" in markdown, markdown
    assert "## Opportunities" in markdown, markdown
    assert "ready for approval review" in markdown, markdown

    cli_dir = TMP / "cli-daily-skillops-demo"
    cli_dir.mkdir(parents=True)
    seed_release_reports(cli_dir)
    cli_output_json = cli_dir / "reports" / "skillops" / "daily" / "cli.json"
    cli_output_md = cli_dir / "reports" / "skillops" / "daily" / "cli.md"
    cli_proc = run_command(
        str(CLI),
        "daily-skillops",
        str(cli_dir),
        "--source",
        str(source),
        "--output-json",
        str(cli_output_json),
        "--output-md",
        str(cli_output_md),
        "--generated-at",
        "2026-06-16T08:00:00Z",
    )
    assert cli_proc.returncode == 0, cli_proc.stderr
    cli_payload = json.loads(cli_proc.stdout)
    assert_daily_contract(cli_payload)
    assert cli_payload["summary"]["proposal_count"] >= 4, cli_payload
    assert cli_output_json.exists(), cli_output_json
    assert cli_output_md.exists(), cli_output_md

    history_source = TMP / ".zsh_history"
    history_source.write_text("报告默认中文\n报告默认中文\n", encoding="utf-8")
    history_proc = run_command(str(SCRIPT), str(skill_dir), "--source", str(history_source))
    assert history_proc.returncode == 2, history_proc.stdout
    history_payload = json.loads(history_proc.stdout)
    assert history_payload["ok"] is False, history_payload
    assert any("Refusing private history source" in item for item in history_payload["failures"]), history_payload

    no_refresh_dir = TMP / "no-refresh-daily-skillops-demo"
    no_refresh_dir.mkdir(parents=True)
    seed_release_reports(no_refresh_dir)
    write_json(
        no_refresh_dir / "reports" / "user_patterns.json",
        {"ok": True, "summary": {"pattern_count": 0}, "patterns": []},
    )
    no_refresh_output_json = no_refresh_dir / "reports" / "skillops" / "daily" / "no-refresh.json"
    no_refresh_proc = run_command(
        str(SCRIPT),
        str(no_refresh_dir),
        "--source",
        str(source),
        "--no-refresh-source-reports",
        "--output-json",
        str(no_refresh_output_json),
        "--generated-at",
        "2026-06-16T08:00:00Z",
    )
    assert no_refresh_proc.returncode == 0, no_refresh_proc.stderr
    no_refresh_payload = json.loads(no_refresh_proc.stdout)
    assert_daily_contract(no_refresh_payload)
    assert no_refresh_payload["summary"]["source_supplied"] is True, no_refresh_payload
    assert no_refresh_payload["summary"]["pattern_count"] >= 4, no_refresh_payload
    assert no_refresh_payload["summary"]["proposal_count"] >= 4, no_refresh_payload
    assert no_refresh_payload["opportunity_summary"]["opportunity_count"] >= 4, no_refresh_payload
    assert not (no_refresh_dir / "reports" / "adaptation_proposals.json").exists(), no_refresh_dir

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
