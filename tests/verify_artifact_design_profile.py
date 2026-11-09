#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_artifact_design_profile"
    if tmp_root.exists():
        subprocess.run(["rm", "-rf", str(tmp_root)], check=True)
    tmp_root.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "init_skill.py"),
            "visual-report-demo",
            "--description",
            "Create polished HTML reports and Markdown tutorials with screenshots, comparison tables, and reviewer notes.",
            "--output-dir",
            str(tmp_root),
            "--intent-primary-output",
            "A polished HTML report and Markdown tutorial.",
            "--intent-real-input",
            "screenshots",
            "--intent-real-input",
            "comparison data",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    skill_dir = tmp_root / "visual-report-demo"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "render_artifact_design_profile.py"), str(skill_dir)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)
    summary = payload["summary"]
    keys = {item["key"] for item in summary["artifact_families"]}
    assert "report" in keys, summary
    assert "tutorial" in keys, summary
    assert summary["quality_gates"], summary
    assert summary["layout_patterns"], summary
    assert any("parchment" in item for item in summary["anti_patterns"]), summary
    markdown = (skill_dir / "reports" / "artifact-design-profile.md").read_text(encoding="utf-8")
    assert "Artifact Design Profile" in markdown, markdown[:500]
    assert "Quality Gates" in markdown, markdown[:1200]
    assert "Do not copy Kami" in markdown, markdown[:2000]
    renamed = tmp_root / "renamed prompt screenshot data secret"
    skill_dir.rename(renamed)
    renamed_proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "render_artifact_design_profile.py"), str(renamed)],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    renamed_summary = json.loads(renamed_proc.stdout)["summary"]
    assert renamed_summary["skill_name"] == "visual-report-demo", renamed_summary
    assert renamed_summary == summary, (summary, renamed_summary)
    assert "Skill: `visual-report-demo`" in (renamed / "reports/artifact-design-profile.md").read_text()
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
