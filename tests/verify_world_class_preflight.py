#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_world_class_preflight.py"
CLI = ROOT / "scripts" / "yao.py"
TMP = ROOT / "tests" / "tmp_world_class_preflight"


def run_preflight(extra_env: dict[str, str] | None = None, *extra: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.pop("OPENAI_API_KEY", None)
    env.pop("YAO_OUTPUT_EVAL_MODEL", None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(ROOT),
            "--generated-at",
            "2026-06-16",
            *extra,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )


def run_cli(*extra: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["YAO_CLI_TELEMETRY"] = "0"
    env.pop("OPENAI_API_KEY", None)
    return subprocess.run(
        [sys.executable, str(CLI), "world-class-preflight", str(ROOT), *extra],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )


def by_key(items: list[dict], key: str) -> dict:
    return next(item for item in items if item.get("evidence_key") == key)


def main() -> None:
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True, exist_ok=True)

    output_json = TMP / "world_class_evidence_preflight.json"
    output_md = TMP / "world_class_evidence_preflight.md"
    proc = run_preflight(None, "--output-json", str(output_json), "--output-md", str(output_md))
    payload = json.loads(proc.stdout)
    assert payload["schema_version"] == "1.0", payload
    assert payload["ok"] is True, payload
    summary = payload["summary"]
    assert summary["decision"] == "collection-preflight-blocked", summary
    assert summary["ready_to_claim_world_class"] is False, summary
    assert summary["preflight_counts_as_evidence"] is False, summary
    assert summary["credential_value_exposed"] is False, summary
    assert summary["evidence_item_count"] == 4, summary
    assert summary["pending_count"] == 4, summary
    assert summary["precheck_count"] >= 12, summary
    assert summary["precheck_missing_count"] >= 1, summary
    assert summary["precheck_external_required_count"] == 2, summary
    assert summary["precheck_human_required_count"] == 1, summary
    assert summary["source_check_count"] >= 13, summary
    assert summary["source_pass_count"] + summary["source_blocked_count"] == summary["source_check_count"], summary
    assert summary["source_blocked_count"] >= 6, summary
    assert payload["submissions"]["preflight_counts_submission_as_completion"] is False, payload
    assert payload["submissions"]["drafts_count_as_evidence"] is False, payload
    assert payload["submissions"]["submission_kit_command"] == (
        "python3 scripts/yao.py world-class-submission-kit . "
        "--output-dir evidence/world_class/submissions"
    ), payload["submissions"]
    submission_commands = payload["submissions"]["commands"]
    assert submission_commands["prepare_submission"] == (
        "python3 scripts/yao.py world-class-submission-kit . "
        "--output-dir evidence/world_class/submissions"
    ), submission_commands
    assert submission_commands["validate_intake"] == (
        "python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions"
    ), submission_commands
    assert submission_commands["submission_review"] == (
        "python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions"
    ), submission_commands
    assert submission_commands["refresh_ledger"] == (
        "python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions"
    ), submission_commands
    assert submission_commands["guard_claim"] == "python3 scripts/yao.py world-class-claim-guard .", submission_commands

    provider = by_key(payload["items"], "provider-holdout")
    assert provider["status"] == "blocked", provider
    assert provider["commands"]["prepare_submission"] == (
        "python3 scripts/yao.py world-class-submission-kit . "
        "--evidence-key provider-holdout --output-dir evidence/world_class/submissions"
    ), provider
    assert provider["submission_kit"]["drafts_count_as_evidence"] is False, provider
    assert provider["submission_kit"]["output_dir"] == "evidence/world_class/submissions", provider
    assert provider["submission_kit"]["draft_path"] == "evidence/world_class/submissions/provider-holdout.json", provider
    provider_checks = {item["key"]: item for item in provider["prechecks"]}
    assert provider_checks["openai-api-key"]["status"] == "missing", provider_checks
    assert provider_checks["openai-api-key"]["actual"] == "not-set", provider_checks
    assert provider_checks["openai-api-key"]["secret_value_redacted"] is True, provider_checks
    assert "sk-test-secret" not in proc.stdout, proc.stdout
    assert "OPENAI_API_KEY" in proc.stdout, proc.stdout
    assert "set OPENAI_API_KEY" not in proc.stdout.lower(), proc.stdout

    human = by_key(payload["items"], "human-adjudication")
    assert human["status"] == "ready-for-human-review", human
    human_checks = {item["key"]: item for item in human["prechecks"]}
    assert human_checks["human-reviewer"]["status"] == "human-required", human_checks
    assert "reviewer identity" in human["next_action"], human
    assert any("Record a reviewer choice" in row["next_action"] for row in human["source_checklist"]), human

    native = by_key(payload["items"], "native-permission-enforcement")
    assert native["status"] == "blocked", native
    assert any(item["status"] == "external-required" for item in native["prechecks"]), native

    markdown = output_md.read_text(encoding="utf-8")
    assert "World-Class Evidence Preflight" in markdown, markdown
    assert "ready to claim world-class: `false`" in markdown, markdown
    assert "preflight counts as evidence: `false`" in markdown, markdown
    assert "credential value exposed: `false`" in markdown, markdown
    assert "Submission Kit Handoff" in markdown, markdown
    assert "world-class-submission-kit . --output-dir evidence/world_class/submissions" in markdown, markdown
    assert "world-class-submission-kit . --evidence-key provider-holdout --output-dir evidence/world_class/submissions" in markdown, markdown
    assert "drafts count as evidence: `false`" in markdown, markdown
    assert "values are never printed" in markdown, markdown

    env_json = TMP / "preflight_with_env.json"
    env_proc = run_preflight(
        {"OPENAI_API_KEY": "sk-test-secret", "YAO_OUTPUT_EVAL_MODEL": "gpt-test"},
        "--output-json",
        str(env_json),
        "--output-md",
        str(TMP / "preflight_with_env.md"),
    )
    env_payload = json.loads(env_proc.stdout)
    env_provider = by_key(env_payload["items"], "provider-holdout")
    env_provider_checks = {item["key"]: item for item in env_provider["prechecks"]}
    assert env_provider_checks["openai-api-key"]["status"] == "pass", env_provider_checks
    assert env_provider_checks["openai-api-key"]["actual"] == "set", env_provider_checks
    assert env_provider_checks["provider-model"]["status"] == "pass", env_provider_checks
    assert "sk-test-secret" not in env_proc.stdout, env_proc.stdout
    assert env_payload["summary"]["credential_value_exposed"] is False, env_payload
    assert env_payload["summary"]["ready_to_claim_world_class"] is False, env_payload

    spaced_dir = TMP / "submission kit spaced"
    spaced_proc = run_preflight(
        None,
        "--submissions-dir",
        str(spaced_dir),
        "--output-json",
        str(TMP / "preflight_spaced.json"),
        "--output-md",
        str(TMP / "preflight_spaced.md"),
    )
    spaced_payload = json.loads(spaced_proc.stdout)
    quoted_spaced = "'tests/tmp_world_class_preflight/submission kit spaced'"
    assert quoted_spaced in spaced_payload["submissions"]["commands"]["prepare_submission"], spaced_payload["submissions"]
    assert quoted_spaced in by_key(spaced_payload["items"], "provider-holdout")["commands"]["prepare_submission"], spaced_payload["items"]

    cli_proc = run_cli(
        "--output-json",
        str(TMP / "cli_preflight.json"),
        "--output-md",
        str(TMP / "cli_preflight.md"),
        "--generated-at",
        "2026-06-16",
    )
    cli_payload = json.loads(cli_proc.stdout)
    assert cli_payload["summary"]["decision"] == "collection-preflight-blocked", cli_payload
    assert cli_payload["summary"]["preflight_counts_as_evidence"] is False, cli_payload
    assert (TMP / "cli_preflight.md").exists(), cli_payload

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
