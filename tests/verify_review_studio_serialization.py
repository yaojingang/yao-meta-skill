#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="yao-review-studio-serialization-") as directory:
        skill = Path(directory) / "external-skill"
        (skill / "agents").mkdir(parents=True)
        quoted_outputs = {}
        for case, frontmatter_date, interface_date, expected_date in [
            ("quoted", '"2026-09-03"', '"2026-09-03"', "2026-09-03"),
            ("frontmatter-date", "2026-09-03", '"2026-09-03"', "2026-09-03"),
            ("interface-date", '"2026-09-03"', "2026-09-03", "2026-09-03"),
            ("timestamps", "2026-09-03T03:03:07Z", "2026-09-03T03:03:07Z", "2026-09-03 03:03:07+00:00"),
        ]:
            skill_text = (
                "---\nname: serialization-fixture\n"
                "description: Generate repeatable reports from structured review inputs.\n"
                f"created_at: {frontmatter_date}\n"
                "metadata:\n  enabled: true\n  retries: 3\n  labels: [fixture]\n"
                "---\n\n# Serialization fixture\n\nProduce a reusable review report.\n"
            )
            interface_text = f"governance:\n  reviewed_at: {interface_date}\n"
            (skill / "SKILL.md").write_text(skill_text, encoding="utf-8")
            (skill / "agents/interface.yaml").write_text(interface_text, encoding="utf-8")
            for entrypoint, arguments in [
                ("renderer", [ROOT / "scripts/render_review_studio.py", skill]),
                ("cli", [ROOT / "scripts/yao.py", "review-studio", skill]),
            ]:
                proc = subprocess.run(
                    [sys.executable, *map(str, arguments)], cwd=ROOT, capture_output=True, text=True
                )
                assert proc.returncode == 0, (case, entrypoint, proc.stdout, proc.stderr)
                stdout = json.loads(proc.stdout)
                json_text = (skill / "reports/review-studio.json").read_text(encoding="utf-8")
                html_text = (skill / "reports/review-studio.html").read_text(encoding="utf-8")
                report = json.loads(json_text)
                assert report["ok"] is True and report["gate_contract"]["ok"] is True, report
                assert report["summary"]["gate_count"] > 0, report["summary"]
                assert stdout == {key: value for key, value in report.items() if key != "data"}, stdout
                assert report["data"]["frontmatter"]["created_at"] == expected_date, report["data"]["frontmatter"]
                assert report["data"]["interface"]["governance"]["reviewed_at"] == expected_date, report["data"]["interface"]
                assert report["data"]["frontmatter"]["metadata"] == {
                    "enabled": True, "retries": 3, "labels": ["fixture"]
                }, report["data"]["frontmatter"]
                assert "<html" in html_text and "serialization-fixture" in html_text, html_text[:1000]
                assert (skill / "SKILL.md").read_text(encoding="utf-8") == skill_text
                assert (skill / "agents/interface.yaml").read_text(encoding="utf-8") == interface_text
                outputs = (proc.stdout, json_text, html_text)
                if case == "quoted":
                    quoted_outputs[entrypoint] = outputs
                elif case != "timestamps":
                    assert outputs == quoted_outputs[entrypoint], (case, entrypoint)
    print("Review Studio serialization checks passed: 4 inputs across renderer and CLI.")


if __name__ == "__main__":
    main()
