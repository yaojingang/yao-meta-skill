#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def assert_root_world_class_commands_are_current() -> None:
    root_json = ROOT / "reports" / "review-viewer.json"
    root_html = ROOT / "reports" / "review-viewer.html"
    agent_docs = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert root_json.exists(), root_json
    assert root_html.exists(), root_html
    json_text = root_json.read_text(encoding="utf-8")
    assert 'python3 scripts/yao.py world-class-intake ."' not in json_text, root_json
    assert "world-class-intake . --submissions-dir evidence/world_class/submissions" in json_text, root_json
    for fragment in (
        'python3 scripts/render_skill_os2_coverage.py . --generated-at "$GENERATED_AT"',
        'python3 scripts/render_benchmark_reproducibility.py . --generated-at "$GENERATED_AT"',
        "python3 scripts/render_review_viewer.py .",
        "release_lock_ready: false",
    ):
        assert fragment in agent_docs, fragment


def main() -> None:
    assert_root_world_class_commands_are_current()
    tmp_root = ROOT / "tests" / "tmp_review_viewer"
    if tmp_root.exists():
        subprocess.run(["rm", "-rf", str(tmp_root)], check=True)
    tmp_root.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "init_skill.py"),
            "review-viewer-demo",
            "--description",
            "Turn rough requests into a reusable review package.",
            "--output-dir",
            str(tmp_root),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    skill_dir = tmp_root / "review-viewer-demo"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "render_review_viewer.py"), str(skill_dir)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)
    html_path = Path(payload["artifacts"]["html"])
    json_path = Path(payload["artifacts"]["json"])
    assert html_path.exists(), html_path
    assert json_path.exists(), json_path
    html_text = html_path.read_text(encoding="utf-8")
    css_contract = (ROOT / "assets" / "review-viewer.css").read_text(encoding="utf-8").strip()
    assert css_contract in html_text, html_text[:500]
    assert 'rel="stylesheet"' not in html_text, html_text[:500]
    assert "Architecture at a glance" in html_text, html_text[:500]
    assert "Compare view" in html_text, html_text[:500]
    assert "Variant diff studio" in html_text, html_text[:900]
    assert "Evidence readiness" in html_text, html_text[:1200]
    assert "Output risk profile" in html_text, html_text[:1600]
    assert "Artifact design profile" in html_text, html_text[:2200]
    assert "Visual quality gates" in html_text, html_text[:2400]
    assert "Prompt quality profile" in html_text, html_text[:2600]
    assert "RTF to skill mapping" in html_text, html_text[:2800]
    assert "Reference coach" in html_text, html_text[:900]
    assert "Reference synthesis" in html_text, html_text[:1200]
    assert "Top three next moves" in html_text, html_text[:500]
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
