#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "scripts" / "yao.py"


def run(*args: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "payload": payload,
        "stderr": proc.stderr,
    }


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_cli"
    if tmp_root.exists():
        subprocess.run(["rm", "-rf", str(tmp_root)], check=True)
    tmp_root.mkdir(parents=True, exist_ok=True)

    init_result = run("init", "cli-demo-skill", "--description", "CLI demo skill.", "--output-dir", str(tmp_root))
    assert init_result["ok"], init_result
    created = Path(init_result["payload"]["root"])
    assert (created / "SKILL.md").exists(), created
    assert (created / "README.md").exists(), created
    assert (created / "reports" / "skill-overview.html").exists(), created
    assert (created / "reports" / "reference-scan.md").exists(), created

    validate_result = run("validate", str(created))
    assert validate_result["ok"], validate_result
    assert len(validate_result["payload"]["steps"]) == 4, validate_result

    skill_report_result = run("skill-report", str(created))
    assert skill_report_result["ok"], skill_report_result
    assert skill_report_result["payload"]["artifacts"]["html"].endswith("reports/skill-overview.html"), skill_report_result

    reference_scan_result = run(
        "reference-scan",
        str(created),
        "--reference",
        "World Class Method::method::Borrow the smallest repeatable evaluation loop.::Do not copy heavy ceremony.",
    )
    assert reference_scan_result["ok"], reference_scan_result
    assert reference_scan_result["payload"]["artifacts"]["markdown"].endswith("reports/reference-scan.md"), reference_scan_result

    optimize_result = run("optimize-description", "--target", "root")
    assert optimize_result["ok"], optimize_result
    assert optimize_result["payload"]["winner"]["label"] == "Current", optimize_result

    promote_result = run("promote-check")
    assert promote_result["ok"], promote_result
    assert promote_result["payload"]["summary"]["blocked"] == 0, promote_result

    review_result = run("review", "--target", "root")
    assert review_result["ok"], review_result
    assert review_result["payload"]["artifacts"]["review_md"].endswith("reports/iteration_bundles/yao-meta-skill/review.md")

    snapshot_result = run("release-snapshot", "--target", "root", "--label", "cli-smoke")
    assert snapshot_result["ok"], snapshot_result
    assert snapshot_result["payload"]["artifacts"]["snapshot_json"].endswith("cli-smoke.json"), snapshot_result

    flow_result = run("workspace-flow", "--target", "root", "--label", "cli-flow")
    assert flow_result["ok"], flow_result
    assert flow_result["payload"]["artifacts"][0]["snapshot"]["artifacts"]["snapshot_md"].endswith("cli-flow.md"), flow_result

    report_result = run("report")
    assert report_result["ok"], report_result
    assert "iteration_ledger" in report_result["payload"]["artifacts"], report_result
    assert "portability_score" in report_result["payload"]["artifacts"], report_result

    package_dir = tmp_root / "dist"
    package_result = run("package", ".", "--platform", "generic", "--output-dir", str(package_dir))
    assert package_result["ok"], package_result
    assert (package_dir / "targets" / "generic" / "adapter.json").exists(), package_dir

    test_result = run("test", "--target", "promotion-check")
    assert test_result["ok"], test_result

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
