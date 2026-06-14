#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "trust_check.py"


INTERFACE = """interface:
  display_name: "Trust Demo"
  short_description: "Trust check demo"
  default_prompt: "Use trust demo."
compatibility:
  canonical_format: "agent-skills"
  adapter_targets:
    - "generic"
  activation:
    mode: "manual"
    paths: []
  execution:
    context: "inline"
    shell: "bash"
  trust:
    source_tier: "local"
    remote_inline_execution: "forbid"
    remote_metadata_policy: "allow-metadata-only"
  degradation:
    generic: "neutral-source"
"""


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_trust"
    shutil.rmtree(tmp_root, ignore_errors=True)
    tmp_root.mkdir(parents=True, exist_ok=True)
    output_json = tmp_root / "security_trust_report.json"
    output_md = tmp_root / "security_trust_report.md"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(ROOT),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["ok"], payload
    assert payload["summary"]["secret_findings"] == 0, payload
    assert payload["summary"]["package_hash_scope"] == "source-contract-without-generated-reports", payload
    assert payload["summary"]["package_hash_file_count"] == payload["summary"]["scanned_files"], payload
    assert payload["summary"]["package_sha256"], payload
    assert payload["summary"]["internal_module_count"] >= 3, payload
    assert payload["summary"]["network_script_count"] == 3, payload
    assert payload["summary"]["network_policy_covered_count"] == payload["summary"]["network_script_count"], payload
    assert payload["summary"]["network_policy_missing_count"] == 0, payload
    assert payload["summary"]["permission_required_count"] >= 3, payload
    assert payload["summary"]["permission_approved_count"] == payload["summary"]["permission_required_count"], payload
    assert payload["summary"]["permission_missing_count"] == 0, payload
    assert payload["summary"]["permission_invalid_count"] == 0, payload
    assert payload["summary"]["permission_expired_count"] == 0, payload
    assert payload["summary"]["help_smoke_checked_count"] > 0, payload
    assert payload["summary"]["help_smoke_failed_count"] == 0, payload
    assert payload["help_smoke"]["enabled"], payload["help_smoke"]
    assert payload["help_smoke"]["checked_count"] == payload["help_smoke"]["passed_count"], payload["help_smoke"]
    assert payload["help_smoke"]["failed_scripts"] == [], payload["help_smoke"]
    assert payload["help_smoke"]["skipped_count"] == payload["summary"]["internal_module_count"], payload["help_smoke"]
    assert payload["network_policy"]["present"], payload["network_policy"]
    assert payload["network_policy"]["missing_scripts"] == [], payload["network_policy"]
    assert payload["network_policy"]["mismatches"] == [], payload["network_policy"]
    assert payload["permission_governance"]["present"], payload["permission_governance"]
    assert {"network", "file_write", "subprocess"} <= set(payload["permission_governance"]["approved_capabilities"]), payload["permission_governance"]
    assert payload["permission_governance"]["missing_capabilities"] == [], payload["permission_governance"]
    assert payload["permission_governance"]["invalid_capabilities"] == [], payload["permission_governance"]
    assert payload["permission_governance"]["expired_capabilities"] == [], payload["permission_governance"]
    assert "scripts/check_update.py" in payload["network_policy"]["covered_scripts"], payload["network_policy"]
    assert "scripts/github_benchmark_scan.py" in payload["network_policy"]["covered_scripts"], payload["network_policy"]
    assert "scripts/provider_output_eval_runner.py" in payload["network_policy"]["covered_scripts"], payload["network_policy"]
    script_map = {item["path"]: item for item in payload["scripts"]}
    for internal_module in [
        "scripts/review_studio_formatting.py",
        "scripts/review_studio_gates.py",
        "scripts/review_studio_layout.py",
        "scripts/skill_report_charts.py",
        "scripts/skill_report_layout.py",
        "scripts/skill_report_metrics.py",
        "scripts/skill_report_model.py",
        "scripts/world_class_evidence_contract.py",
        "scripts/world_class_source_checks.py",
        "scripts/yao_cli_config.py",
        "scripts/yao_cli_parser.py",
        "scripts/yao_cli_telemetry.py",
    ]:
        assert script_map[internal_module]["interface"] == "internal-module", script_map[internal_module]
        assert script_map[internal_module]["interface_declared"], script_map[internal_module]
    warning_text = "\n".join(payload["warnings"])
    assert "review_studio_formatting.py" not in warning_text, payload["warnings"]
    assert "review_studio_gates.py" not in warning_text, payload["warnings"]
    assert "review_studio_layout.py" not in warning_text, payload["warnings"]
    assert "skill_report_charts.py" not in warning_text, payload["warnings"]
    assert "skill_report_layout.py" not in warning_text, payload["warnings"]
    assert "skill_report_metrics.py" not in warning_text, payload["warnings"]
    assert "skill_report_model.py" not in warning_text, payload["warnings"]
    assert "world_class_evidence_contract.py" not in warning_text, payload["warnings"]
    assert "world_class_source_checks.py" not in warning_text, payload["warnings"]
    assert "yao_cli_config.py" not in warning_text, payload["warnings"]
    assert "yao_cli_parser.py" not in warning_text, payload["warnings"]
    assert "yao_cli_telemetry.py" not in warning_text, payload["warnings"]
    assert "render_context_reports.py" not in warning_text, payload["warnings"]
    assert "render_social_preview.py" not in warning_text, payload["warnings"]
    assert "Network-capable scripts require bounded host policy" not in warning_text, payload["warnings"]
    assert "CLI help smoke failed" not in warning_text, payload["warnings"]
    assert "Permission approvals" not in warning_text, payload["warnings"]
    assert output_json.exists(), output_json
    assert output_md.exists(), output_md
    assert "Security Trust Report" in output_md.read_text(encoding="utf-8")
    assert "Package hash scope" in output_md.read_text(encoding="utf-8")

    secret_skill = tmp_root / "secret-skill"
    (secret_skill / "agents").mkdir(parents=True, exist_ok=True)
    (secret_skill / "scripts").mkdir(parents=True, exist_ok=True)
    (secret_skill / "SKILL.md").write_text(
        "---\nname: secret-skill\ndescription: Secret demo.\n---\n\n# Secret\n",
        encoding="utf-8",
    )
    (secret_skill / "agents" / "interface.yaml").write_text(INTERFACE, encoding="utf-8")
    (secret_skill / "scripts" / "leaky.py").write_text(
        "TOKEN = 'ghp_1234567890abcdefghijklmnopqrstuv'\n",
        encoding="utf-8",
    )
    secret_proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(secret_skill)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert secret_proc.returncode == 2, secret_proc.stdout
    secret_payload = json.loads(secret_proc.stdout)
    assert not secret_payload["ok"], secret_payload
    assert secret_payload["summary"]["secret_findings"] == 1, secret_payload
    assert secret_payload["secrets"][0]["type"] == "github_token", secret_payload

    network_skill = tmp_root / "network-skill"
    (network_skill / "agents").mkdir(parents=True, exist_ok=True)
    (network_skill / "scripts").mkdir(parents=True, exist_ok=True)
    (network_skill / "SKILL.md").write_text(
        "---\nname: network-skill\ndescription: Network demo.\n---\n\n# Network\n",
        encoding="utf-8",
    )
    (network_skill / "agents" / "interface.yaml").write_text(INTERFACE, encoding="utf-8")
    (network_skill / "scripts" / "probe.py").write_text(
        "from urllib.request import urlopen\n\nurlopen('https://example.com/status')\n",
        encoding="utf-8",
    )
    missing_policy_proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(network_skill)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    missing_policy_payload = json.loads(missing_policy_proc.stdout)
    assert missing_policy_payload["summary"]["network_script_count"] == 1, missing_policy_payload
    assert missing_policy_payload["summary"]["network_policy_missing_count"] == 1, missing_policy_payload
    assert any("Network-capable scripts require bounded host policy" in item for item in missing_policy_payload["warnings"]), missing_policy_payload

    (network_skill / "security").mkdir(parents=True, exist_ok=True)
    (network_skill / "security" / "network_policy.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "scripts": {
                    "scripts/probe.py": {
                        "purpose": "Test policy coverage.",
                        "allowed_hosts": ["example.com"],
                        "allowed_path_prefixes": ["/"],
                        "requires_https": True,
                        "custom_url_policy": "not supported",
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    covered_policy_proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(network_skill)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    covered_policy_payload = json.loads(covered_policy_proc.stdout)
    assert covered_policy_payload["summary"]["network_policy_covered_count"] == 1, covered_policy_payload
    assert covered_policy_payload["summary"]["network_policy_missing_count"] == 0, covered_policy_payload
    assert not any("Network-capable scripts require bounded host policy" in item for item in covered_policy_payload["warnings"]), covered_policy_payload
    assert covered_policy_payload["summary"]["permission_missing_count"] == 1, covered_policy_payload
    assert covered_policy_payload["permission_governance"]["missing_capabilities"] == ["network"], covered_policy_payload
    assert any("Permission approvals missing: network" in item for item in covered_policy_payload["warnings"]), covered_policy_payload

    (network_skill / "security" / "permission_policy.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "capabilities": {
                    "network": {
                        "decision": "approved",
                        "reviewer": "Yao Team",
                        "scope": "Test network probe.",
                        "reason": "Network access is bounded to example.com for this isolated test fixture.",
                        "expires_at": "2026-09-30",
                        "target_enforcement": {
                            "openai": "metadata-only",
                            "claude": "adapter metadata",
                            "generic": "adapter metadata",
                            "vscode": "workspace trust note",
                        },
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    approved_policy_proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(network_skill)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    approved_policy_payload = json.loads(approved_policy_proc.stdout)
    assert approved_policy_payload["summary"]["permission_approved_count"] == 1, approved_policy_payload
    assert approved_policy_payload["summary"]["permission_missing_count"] == 0, approved_policy_payload
    assert not any("Permission approvals missing" in item for item in approved_policy_payload["warnings"]), approved_policy_payload

    help_smoke_skill = tmp_root / "help-smoke-skill"
    (help_smoke_skill / "agents").mkdir(parents=True, exist_ok=True)
    (help_smoke_skill / "scripts").mkdir(parents=True, exist_ok=True)
    (help_smoke_skill / "SKILL.md").write_text(
        "---\nname: help-smoke-skill\ndescription: Help smoke demo.\n---\n\n# Help Smoke\n",
        encoding="utf-8",
    )
    (help_smoke_skill / "agents" / "interface.yaml").write_text(INTERFACE, encoding="utf-8")
    (help_smoke_skill / "scripts" / "bad_help.py").write_text(
        "import argparse\n\nraise RuntimeError('help import failed')\n",
        encoding="utf-8",
    )
    help_smoke_proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(help_smoke_skill)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    help_smoke_payload = json.loads(help_smoke_proc.stdout)
    assert help_smoke_payload["summary"]["help_smoke_checked_count"] == 1, help_smoke_payload
    assert help_smoke_payload["summary"]["help_smoke_failed_count"] == 1, help_smoke_payload
    assert help_smoke_payload["help_smoke"]["failed_scripts"] == ["scripts/bad_help.py"], help_smoke_payload
    assert any("CLI help smoke failed: scripts/bad_help.py" in item for item in help_smoke_payload["warnings"]), help_smoke_payload

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
