#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_prompt_quality_profile"
    if tmp_root.exists():
        subprocess.run(["rm", "-rf", str(tmp_root)], check=True)
    tmp_root.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "init_skill.py"),
            "prompt-quality-demo",
            "--description",
            "Create reusable RTF prompt templates that teach users how to analyze product feedback.",
            "--output-dir",
            str(tmp_root),
            "--intent-job",
            "Turn rough product-feedback goals into a reusable prompt and teaching workflow.",
            "--intent-real-input",
            "user goal",
            "--intent-real-input",
            "feedback examples",
            "--intent-primary-output",
            "A reusable RTF prompt contract with quality checks.",
            "--intent-standard",
            "clarity",
            "--intent-standard",
            "practicality",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    skill_dir = tmp_root / "prompt-quality-demo"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "render_prompt_quality_profile.py"), str(skill_dir)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)
    summary = payload["summary"]
    markdown = Path(payload["artifacts"]["markdown"]).read_text(encoding="utf-8")

    assert payload["ok"], payload
    assert summary["relevance"] == "prompt-heavy", summary
    assert summary["primary_task_family"]["key"] == "prompt_engineering", summary
    assert summary["complexity"]["band"] in {"medium", "complex", "expert"}, summary
    assert set(summary["rtf_to_skill"].keys()) == {"role", "task", "format"}, summary
    assert {item["key"] for item in summary["quality_matrix"]} == {
        "completeness",
        "clarity",
        "consistency",
        "practicality",
        "specificity",
    }, summary
    assert summary["overall_quality_score"] >= 80, summary
    assert "Prompt Quality Profile" in markdown, markdown[:300]
    assert "Need Model" in markdown, markdown[:800]
    assert "RTF To Skill Mapping" in markdown, markdown[:1200]
    assert "Quality Matrix" in markdown, markdown[:1600]

    renamed = tmp_root / "renamed prompt screenshot data secret"
    skill_dir.rename(renamed)
    renamed_proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "render_prompt_quality_profile.py"), str(renamed)],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    renamed_summary = json.loads(renamed_proc.stdout)["summary"]
    assert renamed_summary["skill_name"] == "prompt-quality-demo", renamed_summary
    assert renamed_summary == summary, (summary, renamed_summary)
    assert "Skill: `prompt-quality-demo`" in (renamed / "reports/prompt-quality-profile.md").read_text()

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
