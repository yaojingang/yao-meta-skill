#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_architecture_maintainability.py"


def main() -> None:
    tmp = ROOT / "tests" / "tmp_architecture_maintainability"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)

    output_json = tmp / "architecture_maintainability.json"
    output_md = tmp / "architecture_maintainability.md"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(ROOT),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
            "--generated-at",
            "2026-06-14",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["ok"], payload
    assert payload["summary"]["decision"] == "watch-maintainability-hotspots", payload["summary"]
    assert payload["summary"]["hotspot_count"] == 2, payload["summary"]
    assert payload["summary"]["blocker_count"] == 0, payload["summary"]
    assert 30 <= payload["summary"]["command_handler_count"] < 50, payload["summary"]
    assert payload["summary"]["largest_file_lines"] >= 900, payload["summary"]
    assert payload["largest_files"][0]["path"] == "scripts/yao.py", payload["largest_files"][0]
    assert payload["largest_files"][0]["severity"] == "warn", payload["largest_files"][0]
    hotspot_paths = {item["path"] for item in payload["hotspots"]}
    assert {"scripts/yao.py", "scripts/render_review_viewer.py"} <= hotspot_paths, hotspot_paths
    assert "scripts/render_review_studio.py" not in hotspot_paths, hotspot_paths
    assert output_json.exists(), output_json
    markdown = output_md.read_text(encoding="utf-8")
    assert "# Architecture Maintainability" in markdown, markdown
    assert "Split command handlers by domain" in markdown, markdown
    assert "Do not split a file only for line count" in markdown, markdown

    blocker_proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(ROOT),
            "--output-json",
            str(tmp / "architecture_blocker.json"),
            "--output-md",
            str(tmp / "architecture_blocker.md"),
            "--warn-lines",
            "10",
            "--block-lines",
            "100",
            "--generated-at",
            "2026-06-14",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert blocker_proc.returncode == 2, blocker_proc.stdout
    blocker_payload = json.loads(blocker_proc.stdout)
    assert blocker_payload["ok"] is False, blocker_payload
    assert blocker_payload["summary"]["blocker_count"] > 0, blocker_payload["summary"]
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
