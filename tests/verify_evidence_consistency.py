#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_evidence_consistency.py"
TMP = ROOT / "tests" / "tmp_evidence_consistency"
REPORT_FILES = [
    "reports/benchmark_reproducibility.json",
    "reports/skill-overview.json",
    "reports/skill-overview.html",
    "reports/skill-interpretation.json",
    "reports/skill-interpretation.html",
    "reports/adoption_drift_report.json",
    "reports/world_class_evidence_ledger.json",
    "reports/skill_os2_coverage.json",
    "reports/review-studio.json",
]


def run(cmd: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=check)


def copy_reports(dst: Path) -> None:
    for relative in REPORT_FILES:
        source = ROOT / relative
        target = dst / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def refresh_embedded_reports() -> None:
    script_names = [
        "render_benchmark_reproducibility.py",
        "render_skill_os2_coverage.py",
        "render_skill_overview.py",
        "render_skill_interpretation.py",
    ]
    for script_name in script_names:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script_name), str(ROOT)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )


def main() -> None:
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True, exist_ok=True)
    refresh_embedded_reports()
    output_json = TMP / "evidence_consistency.json"
    output_md = TMP / "evidence_consistency.md"
    proc = run(
        [
            sys.executable,
            str(SCRIPT),
            str(ROOT),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
            "--generated-at",
            "2026-06-15",
        ],
        check=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["schema_version"] == "1.0", payload
    assert payload["ok"] is True, payload
    assert payload["summary"]["decision"] == "consistent", payload
    assert payload["summary"]["fail_count"] == 0, payload
    assert payload["summary"]["check_count"] >= 26, payload
    checks = {item["key"]: item for item in payload["checks"]}
    assert checks["overview-benchmark-summary"]["status"] == "pass", checks["overview-benchmark-summary"]
    assert checks["interpretation-adoption-summary"]["status"] == "pass", checks["interpretation-adoption-summary"]
    assert checks["coverage-world-class-boundary"]["status"] == "pass", checks["coverage-world-class-boundary"]
    assert checks["review-studio-no-overclaim"]["status"] == "pass", checks["review-studio-no-overclaim"]
    markdown = output_md.read_text(encoding="utf-8")
    assert "Evidence Consistency" in markdown, markdown
    assert "decision: `consistent`" in markdown, markdown
    assert "does not create provider, human, native-client, or permission-enforcement evidence" in markdown, markdown

    drift_root = TMP / "drift-skill"
    copy_reports(drift_root)
    overview_path = drift_root / "reports" / "skill-overview.json"
    overview = json.loads(overview_path.read_text(encoding="utf-8"))
    overview["adoption_drift"]["summary"]["adoption_sample_count"] += 1
    overview_path.write_text(json.dumps(overview, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    drift_proc = run(
        [
            sys.executable,
            str(SCRIPT),
            str(drift_root),
            "--output-json",
            str(TMP / "drift.json"),
            "--output-md",
            str(TMP / "drift.md"),
            "--generated-at",
            "2026-06-15",
        ]
    )
    assert drift_proc.returncode == 2, drift_proc.stdout
    drift_payload = json.loads(drift_proc.stdout)
    drift_checks = {item["key"]: item for item in drift_payload["checks"]}
    assert drift_payload["ok"] is False, drift_payload
    assert drift_payload["summary"]["decision"] == "evidence-drift-detected", drift_payload
    assert drift_checks["overview-adoption-summary"]["status"] == "fail", drift_checks["overview-adoption-summary"]
    assert drift_checks["interpretation-adoption-summary"]["status"] == "pass", drift_checks["interpretation-adoption-summary"]
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
