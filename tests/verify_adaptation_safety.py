#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "scripts" / "yao.py"
SCAN_SCRIPT = ROOT / "scripts" / "summarize_user_signals.py"
PROPOSE_SCRIPT = ROOT / "scripts" / "propose_adaptation.py"
APPLY_SCRIPT = ROOT / "scripts" / "apply_adaptation.py"
TMP = ROOT / "tests" / "tmp_adaptation_safety"


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> None:
    shutil.rmtree(TMP, ignore_errors=True)
    skill_dir = TMP / "adaptive-demo-skill"
    reports_dir = skill_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    source = TMP / "curated-user-signals.jsonl"
    source.write_text(
        "\n".join(
            [
                json.dumps({"text": "报告默认中文简体，同时右上角提供英文切换。"}, ensure_ascii=False),
                json.dumps({"message": "新的 HTML 报告要双语，但默认中文简体。"}, ensure_ascii=False),
                json.dumps({"content": "报告 UI 需要 Kami 白底排版、图表模块和清晰导航。"}, ensure_ascii=False),
                json.dumps({"excerpt": "HTML 报告还是白底 Kami 风格，图表不要挤在一起。"}, ensure_ascii=False),
                json.dumps({"note": "不要自动扫描私人日志；必须由用户提供明确路径。"}, ensure_ascii=False),
                json.dumps({"body": "自适应升级需要先输出提案，授权后再修改，并能回滚。"}, ensure_ascii=False),
                json.dumps({"text": "隐私证据里也要保护 token=abc123456789、sk-1234567890abcdef 和 /Users/laoyao/private/path。"}, ensure_ascii=False),
                json.dumps({"text": "PDF 只提过一次，不能当作稳定偏好。"}, ensure_ascii=False),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    scan_proc = run_script(
        str(SCAN_SCRIPT),
        str(skill_dir),
        "--source",
        str(source),
        "--generated-at",
        "2026-06-15T00:00:00Z",
    )
    assert scan_proc.returncode == 0, scan_proc.stderr
    scan_payload = json.loads(scan_proc.stdout)
    assert scan_payload["ok"], scan_payload
    assert scan_payload["privacy_contract"]["local_only"] is True, scan_payload
    assert scan_payload["privacy_contract"]["implicit_private_log_scan"] is False, scan_payload
    assert scan_payload["privacy_contract"]["raw_content_stored"] is False, scan_payload
    assert scan_payload["privacy_contract"]["writes_repository_files"] is False, scan_payload
    assert scan_payload["source"]["path"].startswith("[external-explicit-source]/"), scan_payload
    pattern_ids = {item["pattern_id"] for item in scan_payload["patterns"]}
    assert {"language_default", "report_ui", "approval_safety"} <= pattern_ids, scan_payload
    serialized = json.dumps(scan_payload, ensure_ascii=False)
    assert "sk-1234567890abcdef" not in serialized, serialized
    assert "token=abc123456789" not in serialized, serialized
    assert "/Users/laoyao/private" not in serialized, serialized
    assert "[REDACTED_SECRET]" in serialized, serialized
    assert "[LOCAL_PATH]" in serialized, serialized
    assert (reports_dir / "user_patterns.json").exists(), reports_dir
    assert (reports_dir / "user_patterns.md").exists(), reports_dir

    propose_proc = run_script(
        str(PROPOSE_SCRIPT),
        str(skill_dir),
        "--generated-at",
        "2026-06-15T00:00:00Z",
    )
    assert propose_proc.returncode == 0, propose_proc.stderr
    proposal_payload = json.loads(propose_proc.stdout)
    assert proposal_payload["ok"], proposal_payload
    assert proposal_payload["summary"]["apply_supported"] is True, proposal_payload
    assert proposal_payload["proposal_contract"]["proposal_only"] is True, proposal_payload
    assert proposal_payload["proposal_contract"]["writes_repository_files"] is False, proposal_payload
    assert proposal_payload["proposal_contract"]["apply_command_available"] is True, proposal_payload
    assert proposal_payload["proposal_contract"]["target_file_sha256_required_for_apply"] is True, proposal_payload
    assert proposal_payload["proposal_contract"]["approval_draft_supported"] is True, proposal_payload
    assert proposal_payload["summary"]["proposal_count"] >= 3, proposal_payload
    assert all(item["status"] == "proposal-only" for item in proposal_payload["proposals"]), proposal_payload
    assert all(item["requires_approval"] is True for item in proposal_payload["proposals"]), proposal_payload
    assert all(item["write_allowed_without_approval"] is False for item in proposal_payload["proposals"]), proposal_payload
    assert any(
        any("tests/verify_adaptation_safety.py" in command for command in item["verification_commands"])
        for item in proposal_payload["proposals"]
    ), proposal_payload
    assert (reports_dir / "adaptation_proposals.json").exists(), reports_dir
    assert (reports_dir / "adaptation_proposals.md").exists(), reports_dir

    template_proc = run_script(str(APPLY_SCRIPT), str(skill_dir), "--write-template", "--generated-at", "2026-06-15T00:00:00Z")
    assert template_proc.returncode == 0, template_proc.stderr
    template_payload = json.loads(template_proc.stdout)
    assert template_payload["summary"]["apply_supported"] is True, template_payload
    assert template_payload["summary"]["attempt_count"] == 0, template_payload
    assert template_payload["apply_contract"]["target_file_sha256_required"] is True, template_payload
    assert template_payload["apply_contract"]["approval_draft_supported"] is True, template_payload
    assert (reports_dir / "adaptation_approval_ledger.json").exists(), reports_dir
    assert (reports_dir / "adaptation_regression_report.json").exists(), reports_dir

    missing_source_proc = run_script(str(SCAN_SCRIPT), str(skill_dir))
    assert missing_source_proc.returncode != 0, missing_source_proc

    history_source = TMP / ".zsh_history"
    history_source.write_text("报告默认中文\n报告默认中文\n", encoding="utf-8")
    history_proc = run_script(str(SCAN_SCRIPT), str(skill_dir), "--source", str(history_source))
    assert history_proc.returncode == 2, history_proc.stdout
    history_payload = json.loads(history_proc.stdout)
    assert history_payload["ok"] is False, history_payload
    assert any("Refusing private history source" in item for item in history_payload["failures"]), history_payload

    cli_skill_dir = TMP / "cli-adaptive-demo-skill"
    cli_skill_dir.mkdir(parents=True, exist_ok=True)
    cli_source = TMP / "cli-user-signals.jsonl"
    cli_source.write_text(
        "\n".join(
            [
                json.dumps({"text": "报告默认中文简体，同时提供英文切换。"}, ensure_ascii=False),
                json.dumps({"text": "新的 HTML 报告还是默认中文简体，并保留英文版。"}, ensure_ascii=False),
                json.dumps({"text": "报告 UI 要保持 Kami 白底排版和图表模块。"}, ensure_ascii=False),
                json.dumps({"text": "HTML 报告的图表和白底 Kami 排版都要清晰。"}, ensure_ascii=False),
                json.dumps({"text": "自适应升级必须先生成提案，授权后再修改。"}, ensure_ascii=False),
                json.dumps({"text": "不要默认扫描私人日志，要由用户提供明确路径。"}, ensure_ascii=False),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    cli_scan = run_script(
        str(CLI),
        "adapt-scan",
        str(cli_skill_dir),
        "--source",
        str(cli_source),
        "--generated-at",
        "2026-06-15T00:00:00Z",
    )
    assert cli_scan.returncode == 0, cli_scan.stderr
    cli_scan_payload = json.loads(cli_scan.stdout)
    assert cli_scan_payload["summary"]["pattern_count"] >= 3, cli_scan_payload
    assert cli_scan_payload["privacy_contract"]["writes_repository_files"] is False, cli_scan_payload
    assert (cli_skill_dir / "reports" / "user_patterns.json").exists(), cli_skill_dir
    cli_propose = run_script(
        str(CLI),
        "adapt-propose",
        str(cli_skill_dir),
        "--generated-at",
        "2026-06-15T00:00:00Z",
    )
    assert cli_propose.returncode == 0, cli_propose.stderr
    cli_proposal_payload = json.loads(cli_propose.stdout)
    assert cli_proposal_payload["summary"]["proposal_count"] >= 3, cli_proposal_payload
    assert cli_proposal_payload["summary"]["apply_supported"] is True, cli_proposal_payload
    assert cli_proposal_payload["proposal_contract"]["proposal_only"] is True, cli_proposal_payload
    assert cli_proposal_payload["proposal_contract"]["writes_repository_files"] is False, cli_proposal_payload
    assert cli_proposal_payload["proposal_contract"]["apply_command_available"] is True, cli_proposal_payload
    assert cli_proposal_payload["proposal_contract"]["target_file_sha256_required_for_apply"] is True, cli_proposal_payload
    assert cli_proposal_payload["proposal_contract"]["approval_draft_supported"] is True, cli_proposal_payload

    policy_path = cli_skill_dir / "references" / "user-memory-policy.md"
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    policy_path.write_text("old policy\n", encoding="utf-8")
    verifier = cli_skill_dir / "tests" / "check_policy.py"
    verifier.parent.mkdir(parents=True, exist_ok=True)
    verifier.write_text(
        "from pathlib import Path\n"
        "assert 'approved adaptive note' in Path('references/user-memory-policy.md').read_text(encoding='utf-8')\n",
        encoding="utf-8",
    )
    approval_proposal = next(
        item for item in cli_proposal_payload["proposals"] if item["pattern_id"] == "approval_safety"
    )
    patch_text = (
        "diff --git a/references/user-memory-policy.md b/references/user-memory-policy.md\n"
        "--- a/references/user-memory-policy.md\n"
        "+++ b/references/user-memory-policy.md\n"
        "@@ -1 +1,2 @@\n"
        " old policy\n"
        "+approved adaptive note\n"
    )
    patch_path = TMP / "approved-adaptation.patch"
    patch_path.write_text(patch_text, encoding="utf-8")
    ledger_path = cli_skill_dir / "reports" / "adaptation_approval_ledger.json"
    prepare_proc = run_script(
        str(CLI),
        "adapt-apply",
        str(cli_skill_dir),
        "--proposal-id",
        approval_proposal["proposal_id"],
        "--patch-file",
        str(patch_path),
        "--generated-at",
        "2026-06-15T00:00:00Z",
        "--today",
        "2026-06-15",
        "--prepare-approval",
    )
    assert prepare_proc.returncode == 0, prepare_proc.stdout
    prepare_payload = json.loads(prepare_proc.stdout)
    assert prepare_payload["summary"]["approval_draft_count"] == 1, prepare_payload
    assert prepare_payload["approval_draft"]["decision"] == "pending-review", prepare_payload
    assert prepare_payload["approval_draft"]["patch_sha256"] == sha256_text(patch_text), prepare_payload
    assert prepare_payload["approval_draft"]["target_file_sha256"] == {
        "references/user-memory-policy.md": sha256_text("old policy\n"),
    }, prepare_payload
    approval_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert approval_ledger["summary"]["pending_review_count"] == 1, approval_ledger
    approval_ledger["entries"][0].update(
        {
            "decision": "approved",
            "reviewer": "qa-reviewer",
            "reason": "Fixture validates approval-gated adaptive apply.",
            "approved_at": "2026-06-15",
            "expires_at": "2026-12-31",
            "verification_commands": ["python3 tests/check_policy.py"],
            "rollback_plan": "git apply -R approved-adaptation.patch",
        }
    )
    ledger_path.write_text(json.dumps(approval_ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    policy_path.write_text("changed outside approval\n", encoding="utf-8")
    stale_proc = run_script(
        str(CLI),
        "adapt-apply",
        str(cli_skill_dir),
        "--proposal-id",
        approval_proposal["proposal_id"],
        "--patch-file",
        str(patch_path),
        "--output-json",
        str(cli_skill_dir / "reports" / "stale_baseline_regression.json"),
        "--output-md",
        str(cli_skill_dir / "reports" / "stale_baseline_regression.md"),
        "--generated-at",
        "2026-06-15T00:00:00Z",
        "--today",
        "2026-06-15",
    )
    assert stale_proc.returncode == 2, stale_proc.stdout
    stale_payload = json.loads(stale_proc.stdout)
    assert any("baseline sha256" in item for item in stale_payload["failures"]), stale_payload
    assert "approved adaptive note" not in policy_path.read_text(encoding="utf-8"), policy_path
    policy_path.write_text("old policy\n", encoding="utf-8")
    dry_run = run_script(
        str(CLI),
        "adapt-apply",
        str(cli_skill_dir),
        "--proposal-id",
        approval_proposal["proposal_id"],
        "--patch-file",
        str(patch_path),
        "--generated-at",
        "2026-06-15T00:00:00Z",
        "--today",
        "2026-06-15",
    )
    assert dry_run.returncode == 0, dry_run.stderr
    dry_payload = json.loads(dry_run.stdout)
    assert dry_payload["summary"]["dry_run_count"] == 1, dry_payload
    assert dry_payload["summary"]["applied_count"] == 0, dry_payload
    refreshed_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert refreshed_ledger["summary"]["approval_count"] == 1, refreshed_ledger
    assert refreshed_ledger["summary"]["pending_review_count"] == 0, refreshed_ledger
    assert "approved adaptive note" not in policy_path.read_text(encoding="utf-8"), policy_path

    apply_proc = run_script(
        str(CLI),
        "adapt-apply",
        str(cli_skill_dir),
        "--proposal-id",
        approval_proposal["proposal_id"],
        "--patch-file",
        str(patch_path),
        "--generated-at",
        "2026-06-15T00:00:00Z",
        "--today",
        "2026-06-15",
        "--apply",
        "--run-verification",
    )
    assert apply_proc.returncode == 0, apply_proc.stderr
    apply_payload = json.loads(apply_proc.stdout)
    assert apply_payload["summary"]["applied_count"] == 1, apply_payload
    assert apply_payload["summary"]["regression_run_count"] == 1, apply_payload
    assert apply_payload["summary"]["regression_pass_count"] == 1, apply_payload
    assert "approved adaptive note" in policy_path.read_text(encoding="utf-8"), policy_path

    policy_path.write_text("old policy\n", encoding="utf-8")
    failing_verifier = cli_skill_dir / "tests" / "failing_policy.py"
    failing_verifier.write_text(
        "from pathlib import Path\n"
        "assert 'impossible verifier token' in Path('references/user-memory-policy.md').read_text(encoding='utf-8')\n",
        encoding="utf-8",
    )
    rollback_patch = (
        "diff --git a/references/user-memory-policy.md b/references/user-memory-policy.md\n"
        "--- a/references/user-memory-policy.md\n"
        "+++ b/references/user-memory-policy.md\n"
        "@@ -1 +1,2 @@\n"
        " old policy\n"
        "+rolled back adaptive note\n"
    )
    rollback_patch_path = TMP / "rollback-adaptation.patch"
    rollback_patch_path.write_text(rollback_patch, encoding="utf-8")
    approval_ledger["entries"][0]["patch_sha256"] = sha256_text(rollback_patch)
    approval_ledger["entries"][0]["verification_commands"] = ["python3 tests/failing_policy.py"]
    ledger_path.write_text(json.dumps(approval_ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rollback_proc = run_script(
        str(CLI),
        "adapt-apply",
        str(cli_skill_dir),
        "--proposal-id",
        approval_proposal["proposal_id"],
        "--patch-file",
        str(rollback_patch_path),
        "--output-json",
        str(cli_skill_dir / "reports" / "rollback_adaptation_regression.json"),
        "--output-md",
        str(cli_skill_dir / "reports" / "rollback_adaptation_regression.md"),
        "--today",
        "2026-06-15",
        "--apply",
        "--run-verification",
    )
    assert rollback_proc.returncode == 2, rollback_proc.stdout
    rollback_payload = json.loads(rollback_proc.stdout)
    assert rollback_payload["summary"]["applied_count"] == 0, rollback_payload
    assert rollback_payload["summary"]["rollback_count"] == 1, rollback_payload
    assert rollback_payload["attempts"][0]["status"] == "failed-rolled-back", rollback_payload
    assert rollback_payload["attempts"][0]["rollback_result"]["ok"] is True, rollback_payload
    assert "rolled back adaptive note" not in policy_path.read_text(encoding="utf-8"), policy_path
    assert policy_path.read_text(encoding="utf-8") == "old policy\n", policy_path

    unsafe_patch = (
        "diff --git a/README.md b/README.md\n"
        "--- a/README.md\n"
        "+++ b/README.md\n"
        "@@ -1 +1,2 @@\n"
        " old\n"
        "+unsafe\n"
    )
    unsafe_patch_path = TMP / "unsafe-adaptation.patch"
    unsafe_patch_path.write_text(unsafe_patch, encoding="utf-8")
    approval_ledger["entries"][0]["patch_sha256"] = sha256_text(unsafe_patch)
    ledger_path.write_text(json.dumps(approval_ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    unsafe_proc = run_script(
        str(CLI),
        "adapt-apply",
        str(cli_skill_dir),
        "--proposal-id",
        approval_proposal["proposal_id"],
        "--patch-file",
        str(unsafe_patch_path),
        "--output-json",
        str(cli_skill_dir / "reports" / "unsafe_adaptation_regression.json"),
        "--output-md",
        str(cli_skill_dir / "reports" / "unsafe_adaptation_regression.md"),
        "--today",
        "2026-06-15",
    )
    assert unsafe_proc.returncode == 2, unsafe_proc.stdout
    unsafe_payload = json.loads(unsafe_proc.stdout)
    assert any("outside approval target_files" in item for item in unsafe_payload["failures"]), unsafe_payload

    proposal_report_path = cli_skill_dir / "reports" / "adaptation_proposals.json"
    proposal_report = json.loads(proposal_report_path.read_text(encoding="utf-8"))
    for proposal in proposal_report["proposals"]:
        if proposal["proposal_id"] == approval_proposal["proposal_id"]:
            proposal["target_files"].append("references/new-user-memory-policy.md")
    proposal_report_path.write_text(json.dumps(proposal_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    new_file_patch = (
        "diff --git a/references/new-user-memory-policy.md b/references/new-user-memory-policy.md\n"
        "new file mode 100644\n"
        "--- /dev/null\n"
        "+++ b/references/new-user-memory-policy.md\n"
        "@@ -0,0 +1 @@\n"
        "+new approved policy\n"
    )
    new_file_patch_path = TMP / "new-file-adaptation.patch"
    new_file_patch_path.write_text(new_file_patch, encoding="utf-8")
    new_file_prepare = run_script(
        str(CLI),
        "adapt-apply",
        str(cli_skill_dir),
        "--proposal-id",
        approval_proposal["proposal_id"],
        "--patch-file",
        str(new_file_patch_path),
        "--approval-ledger",
        str(cli_skill_dir / "reports" / "new_file_approval_ledger.json"),
        "--output-json",
        str(cli_skill_dir / "reports" / "new_file_prepare_regression.json"),
        "--output-md",
        str(cli_skill_dir / "reports" / "new_file_prepare_regression.md"),
        "--generated-at",
        "2026-06-15T00:00:00Z",
        "--today",
        "2026-06-15",
        "--prepare-approval",
    )
    assert new_file_prepare.returncode == 0, new_file_prepare.stdout
    new_file_payload = json.loads(new_file_prepare.stdout)
    assert new_file_payload["approval_draft"]["target_file_sha256"] == {
        "references/new-user-memory-policy.md": "__absent__",
    }, new_file_payload
    assert not (cli_skill_dir / "references" / "new-user-memory-policy.md").exists(), cli_skill_dir
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
