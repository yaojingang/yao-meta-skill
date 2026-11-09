#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_output_risk_profile"
    if tmp_root.exists():
        subprocess.run(["rm", "-rf", str(tmp_root)], check=True)
    tmp_root.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "init_skill.py"),
            "tutorial-risk-demo",
            "--description",
            "Create Markdown tutorials with screenshots, tables, citations, and personalized section headings.",
            "--output-dir",
            str(tmp_root),
            "--intent-primary-output",
            "A polished Markdown tutorial.",
            "--intent-real-input",
            "screenshots",
            "--intent-real-input",
            "source notes",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    skill_dir = tmp_root / "tutorial-risk-demo"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "render_output_risk_profile.py"), str(skill_dir)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)
    summary = payload["summary"]
    keys = {item["key"] for item in summary["risk_families"]}
    assert "tutorial_quality" in keys, summary
    assert "markdown_readability" in keys, summary
    assert summary["output_constraints"], summary
    assert summary["self_repair_checks"], summary
    markdown = (skill_dir / "reports" / "output-risk-profile.md").read_text(encoding="utf-8")
    assert "Likely Output Mistakes" in markdown, markdown[:800]
    assert "Self-Repair Checks" in markdown, markdown[:1200]
    renamed = tmp_root / "renamed prompt screenshot data secret"
    skill_dir.rename(renamed)
    renamed_proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "render_output_risk_profile.py"), str(renamed)],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    renamed_summary = json.loads(renamed_proc.stdout)["summary"]
    assert renamed_summary["skill_name"] == "tutorial-risk-demo", renamed_summary
    assert renamed_summary == summary, (summary, renamed_summary)
    assert "Skill: `tutorial-risk-demo`" in (renamed / "reports/output-risk-profile.md").read_text()
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
