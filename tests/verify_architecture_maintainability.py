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
    assert payload["summary"]["decision"] == "pass", payload["summary"]
    assert payload["summary"]["early_watch_line_threshold"] == 600, payload["summary"]
    assert payload["summary"]["watch_line_threshold"] == 720, payload["summary"]
    assert payload["summary"]["early_watchlist_count"] >= 8, payload["summary"]
    assert payload["summary"]["watchlist_count"] == 0, payload["summary"]
    assert payload["summary"]["hotspot_count"] == 0, payload["summary"]
    assert payload["summary"]["blocker_count"] == 0, payload["summary"]
    assert payload["summary"]["command_handler_count"] >= 60, payload["summary"]
    assert payload["summary"]["entrypoint_command_handler_count"] < 30, payload["summary"]
    assert payload["summary"]["command_module_count"] >= 5, payload["summary"]
    assert payload["summary"]["largest_file_lines"] < 900, payload["summary"]
    assert all(item["severity"] == "pass" for item in payload["largest_files"]), payload["largest_files"]
    assert payload["watchlist"] == [], payload["watchlist"]
    assert payload["early_watchlist"], payload["early_watchlist"]
    assert all(item["early_watch"] is True for item in payload["early_watchlist"]), payload["early_watchlist"]
    early_watch_paths = {item["path"] for item in payload["early_watchlist"]}
    assert "scripts/render_review_viewer.py" not in early_watch_paths, payload["early_watchlist"]
    assert "scripts/render_skill_os2_coverage.py" not in early_watch_paths, payload["early_watchlist"]
    renderer_lines = len((ROOT / "scripts" / "render_review_studio.py").read_text(encoding="utf-8").splitlines())
    action_module = (ROOT / "scripts" / "review_studio_actions.py").read_text(encoding="utf-8")
    action_lines = len(action_module.splitlines())
    assert renderer_lines < 650, renderer_lines
    assert action_lines < 450, action_lines
    assert 'SCRIPT_INTERFACE = "internal-module"' in action_module, action_module[:400]
    hotspot_paths = {item["path"] for item in payload["hotspots"]}
    assert "scripts/yao.py" not in hotspot_paths, hotspot_paths
    assert "scripts/render_review_studio.py" not in hotspot_paths, hotspot_paths
    assert "scripts/review_studio_actions.py" not in hotspot_paths, hotspot_paths
    assert "scripts/render_review_viewer.py" not in hotspot_paths, hotspot_paths
    assert output_json.exists(), output_json
    markdown = output_md.read_text(encoding="utf-8")
    assert "# Architecture Maintainability" in markdown, markdown
    assert "No file-size hotspots found." in markdown, markdown
    assert "No near-threshold files found." in markdown, markdown
    assert "## Early Watchlist" in markdown, markdown
    assert "- early watchlist: `8`" in markdown, markdown
    assert "scripts/render_review_viewer.py" not in markdown, markdown
    assert "scripts/render_skill_os2_coverage.py" not in markdown, markdown
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
