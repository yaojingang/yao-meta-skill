#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
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
    assert "Architecture at a glance" in html_text, html_text[:500]
    assert "Compare view" in html_text, html_text[:500]
    assert "Top three next moves" in html_text, html_text[:500]
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
