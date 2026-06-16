import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "scripts" / "yao.py"
BENCHMARK_FIXTURE_DIR = ROOT / "tests" / "fixtures" / "github_benchmark_scan"

sys.path.insert(0, str(ROOT / "scripts"))
import yao as yao_cli_module  # noqa: E402
import yao_cli_adaptation_commands  # noqa: E402
import yao_cli_config  # noqa: E402
import yao_cli_distribution_commands  # noqa: E402
import yao_cli_output_commands  # noqa: E402
import yao_cli_parser  # noqa: E402
import yao_cli_parser_evidence  # noqa: E402
import yao_cli_parser_operations  # noqa: E402
import yao_cli_report_commands  # noqa: E402
import yao_cli_runtime  # noqa: E402
from yao_cli_report_refresh import refresh_root_report_consistency_inputs  # noqa: E402


def run(*args: str, input_text: str | None = None) -> dict:
    env = dict(os.environ)
    env["YAO_CLI_TELEMETRY"] = "0"
    env.pop("YAO_CLI_TELEMETRY_EVENTS", None)
    proc = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        input=input_text,
        env=env,
    )
    payload = json.loads(proc.stdout)
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "payload": payload,
        "stderr": proc.stderr,
    }


def run_with_env(extra_env: dict[str, str], *args: str) -> dict:
    env = dict(os.environ)
    env.update(extra_env)
    proc = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    payload = json.loads(proc.stdout)
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "payload": payload,
        "stderr": proc.stderr,
    }


def assert_cli_module_contracts() -> None:
    assert yao_cli_config.resolve_target("root")["title"] == "Root Description Optimization"
    assert yao_cli_config.resolve_promotion_target("root") == "yao-meta-skill"
    assert yao_cli_config.infer_archetype("Standardize team review workflow.", "")[0] == "production"
    assert yao_cli_config.infer_archetype("Govern release policy.", "")[0] == "governed"
    assert "--entry" in yao_cli_config.baseline_compare_args()
    assert "scripts/provider_output_eval_runner.py" in yao_cli_config.provider_output_runner_command("openai")
    assert "--allow-custom-base-url" in yao_cli_config.provider_output_runner_command("openai", allow_custom_base_url=True)
    for module in (
        yao_cli_parser,
        yao_cli_parser_evidence,
        yao_cli_parser_operations,
        yao_cli_runtime,
        yao_cli_adaptation_commands,
        yao_cli_distribution_commands,
        yao_cli_output_commands,
        yao_cli_report_commands,
    ):
        assert module.SCRIPT_INTERFACE == "internal-module"
    assert callable(yao_cli_module.command_review_studio)


def assert_help_surface() -> None:
    parser_help = yao_cli_module.build_parser().format_help()
    expected_help = (
        "quickstart skill-interpretation review-studio python-compat architecture-audit skill-os2-audit skill-os2-coverage "
        "world-class-evidence world-class-ledger world-class-intake world-class-preflight world-class-submission-kit world-class-submission-review world-class-runbook world-class-claim-guard "
        "benchmark-reproducibility evidence-consistency output-review-kit output-review-import adapt-scan adapt-propose adapt-apply telemetry-import telemetry-emit telemetry-hooks weekly-curator --record-cli-telemetry"
    ).split()
    assert all(item in parser_help for item in expected_help), parser_help


def assert_created_skill_reports(created: Path) -> None:
    expected_reports = [
        "intent-dialogue.md", "intent-confidence.md", "skill-overview.html", "skill-interpretation.html",
        "skill-interpretation.json", "review-studio.html", "review-studio.json", "review-viewer.html",
        "reference-scan.md", "reference-synthesis.md", "output-risk-profile.md", "artifact-design-profile.md",
        "prompt-quality-profile.md", "system-model.md", "skill-ir.json", "compiled_targets.md",
        "compiled_targets.json", "iteration-directions.md", "adoption_drift_report.md",
        "adoption_drift_report.json", "review_waivers.md", "review_waivers.json", "review_annotations.md",
        "review_annotations.json",
    ]
    assert all((created / "reports" / path).exists() for path in expected_reports), created


def assert_creation_report_view(report_view: dict) -> None:
    assert report_view["html_report"].endswith("reports/skill-overview.html"), report_view
    assert report_view["interpretation_report"].endswith("reports/skill-interpretation.html"), report_view
    assert Path(report_view["html_report"]).exists(), report_view
    assert Path(report_view["interpretation_report"]).exists(), report_view
    assert report_view["review_studio"].endswith("reports/review-studio.html"), report_view
    assert Path(report_view["review_studio"]).exists(), report_view
    assert "Skill 已创建完成" in report_view["message"], report_view
    assert "reports/skill-interpretation.html" in report_view["message"], report_view
    assert "Review Studio 2.0" in report_view["message"], report_view
    assert "目标编译" in report_view["message"], report_view
    assert "reports/compiled_targets.md" in report_view["message"], report_view
    assert "概述、指标、原理、触发边界、输入输出、目标编译、质量评估、风险治理、包体资产和升级路线" in report_view["message"], report_view
    assert "默认使用中文简体" in report_view["message"], report_view
    assert "切换英文版" in report_view["message"], report_view
