#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TMP = ROOT / "tests" / "tmp_adoption_drift"
SCRIPT = ROOT / "scripts" / "render_adoption_drift_report.py"


def run(cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    payload = json.loads(proc.stdout) if proc.stdout.strip() else {}
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "payload": payload,
        "stderr": proc.stderr,
    }


def record(skill_dir: Path, *args: str) -> dict:
    return run([sys.executable, str(SCRIPT), str(skill_dir), *args])


def main() -> None:
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "init_skill.py"),
            "telemetry-demo",
            "--description",
            "Turn repeated operational signals into a reusable telemetry demo skill.",
            "--output-dir",
            str(TMP),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    skill_dir = TMP / "telemetry-demo"

    assert record(
        skill_dir,
        "--record-event",
        "skill_activation",
        "--activation-type",
        "explicit",
        "--outcome",
        "accepted",
        "--timestamp",
        "2026-06-13T10:00:00Z",
    )["ok"]
    assert record(
        skill_dir,
        "--record-event",
        "skill_activation",
        "--activation-type",
        "implicit",
        "--outcome",
        "edited",
        "--timestamp",
        "2026-06-13T10:01:00Z",
    )["ok"]
    assert record(
        skill_dir,
        "--record-event",
        "skill_activation",
        "--activation-type",
        "implicit",
        "--outcome",
        "missed",
        "--failure-type",
        "under_trigger",
        "--timestamp",
        "2026-06-13T10:02:00Z",
    )["ok"]
    assert record(
        skill_dir,
        "--record-event",
        "skill_output",
        "--outcome",
        "rejected",
        "--failure-type",
        "bad_output",
        "--timestamp",
        "2026-06-13T10:03:00Z",
    )["ok"]
    final = record(
        skill_dir,
        "--record-event",
        "script_run",
        "--outcome",
        "failed",
        "--failure-type",
        "script_error",
        "--source",
        "yao_cli",
        "--command",
        "validate",
        "--timestamp",
        "2026-06-13T10:04:00Z",
    )
    assert final["ok"], final
    summary = final["payload"]["summary"]
    assert summary["event_count"] == 5, summary
    assert summary["adoption_sample_count"] == 4, summary
    assert summary["adoption_rate"] == 50.0, summary
    assert summary["missed_trigger_count"] == 2, summary
    assert summary["bad_output_count"] == 1, summary
    assert summary["script_error_count"] == 1, summary
    assert summary["risk_band"] == "high", summary
    assert summary["source_types"]["yao_cli"] == 1, summary
    assert summary["command_counts"]["validate"] == 1, summary
    assert final["payload"]["privacy_contract"]["raw_content_allowed"] is False, final
    assert final["payload"]["next_iteration_candidates"], final
    markdown = (skill_dir / "reports" / "adoption_drift_report.md").read_text(encoding="utf-8")
    assert "metadata-only telemetry" in markdown, markdown
    assert "Raw user prompts" in markdown, markdown
    assert "source=`yao_cli` command=`validate`" in markdown, markdown

    unsafe_events = TMP / "unsafe_events.jsonl"
    unsafe_events.write_text(
        json.dumps(
            {
                "event": "skill_activation",
                "outcome": "accepted",
                "prompt": "raw prompt must not be stored",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    unsafe = run(
        [
            sys.executable,
            str(SCRIPT),
            str(skill_dir),
            "--events-jsonl",
            str(unsafe_events),
            "--output-json",
            str(TMP / "unsafe.json"),
            "--output-md",
            str(TMP / "unsafe.md"),
        ]
    )
    assert unsafe["returncode"] == 2, unsafe
    assert not unsafe["payload"]["ok"], unsafe
    assert "raw content fields" in unsafe["payload"]["failures"][0], unsafe

    root_events = ROOT / "reports" / "telemetry_events.jsonl"
    original_root_events = root_events.read_text(encoding="utf-8") if root_events.exists() else None
    root_events.write_text(
        json.dumps(
            {
                "event": "skill_activation",
                "skill": "yao-meta-skill",
                "version": "1.1.0",
                "activation_type": "explicit",
                "outcome": "accepted",
                "failure_type": "none",
                "timestamp": "2026-06-13T10:05:00Z",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    try:
        package_dir = TMP / "dist"
        package = run(
            [
                sys.executable,
                str(ROOT / "scripts" / "cross_packager.py"),
                str(ROOT),
                "--platform",
                "generic",
                "--output-dir",
                str(package_dir),
                "--zip",
            ]
        )
        assert package["ok"], package
        with zipfile.ZipFile(package_dir / "yao-meta-skill.zip") as archive:
            names = archive.namelist()
        assert "yao-meta-skill/reports/telemetry_events.jsonl" not in names, names
    finally:
        if original_root_events is not None:
            root_events.write_text(original_root_events, encoding="utf-8")
        elif root_events.exists():
            root_events.unlink()

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
