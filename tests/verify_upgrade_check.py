#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "upgrade_check.py"
PREVIOUS = ROOT / "registry" / "examples" / "yao-meta-skill-1.0.0.json"


def run(cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    payload = {}
    if proc.stdout.strip():
        payload = json.loads(proc.stdout)
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "payload": payload,
    }


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_upgrade_check"
    tmp_root.mkdir(parents=True, exist_ok=True)
    output_json = tmp_root / "upgrade_check.json"
    output_md = tmp_root / "upgrade_check.md"
    result = run(
        [
            sys.executable,
            str(SCRIPT),
            str(ROOT),
            "--previous-package-json",
            str(PREVIOUS),
            "--current-package-json",
            str(ROOT / "reports" / "registry_audit.json"),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
            "--generated-at",
            "2026-06-13",
        ]
    )
    payload = result["payload"]
    assert result["ok"], result
    assert payload["ok"], payload
    assert payload["summary"]["declared_bump"] == "minor", payload
    assert payload["summary"]["recommended_bump"] == "minor", payload
    assert "agent-skills-compatible" in payload["upgrade_diff"]["added_targets"], payload
    assert "vscode" in payload["upgrade_diff"]["added_targets"], payload
    assert output_json.exists(), output_json
    assert "Upgrade Check" in output_md.read_text(encoding="utf-8"), output_md

    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    current = json.loads((ROOT / "reports" / "registry_audit.json").read_text(encoding="utf-8"))["package"]
    current["version"] = "1.1.0"
    current["targets"] = ["openai", "claude"]
    current["compatibility"] = {"openai": "pass", "claude": "fail"}
    bad_current = tmp_root / "bad-current.json"
    bad_current.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
    bad = run(
        [
            sys.executable,
            str(SCRIPT),
            str(ROOT),
            "--previous-package-json",
            str(PREVIOUS),
            "--current-package-json",
            str(bad_current),
            "--output-json",
            str(tmp_root / "bad.json"),
            "--output-md",
            str(tmp_root / "bad.md"),
            "--generated-at",
            "2026-06-13",
        ]
    )
    bad_payload = bad["payload"]
    assert bad["returncode"] == 2, bad
    assert not bad_payload["ok"], bad_payload
    assert bad_payload["summary"]["recommended_bump"] == "major", bad_payload
    assert any("Version bump is insufficient" in item for item in bad_payload["failures"]), bad_payload

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
