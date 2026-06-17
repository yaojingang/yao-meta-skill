"""Shared runtime helpers for the Yao CLI."""

import json
import subprocess
import sys
from pathlib import Path


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by yao.py and command modules for shared subprocess execution and JSON payload parsing."

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


def script_path(name: str) -> str:
    return str(SCRIPTS / name)


def load_json_maybe(text: str) -> dict | None:
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def run_script(name: str, args: list[str], cwd: Path | None = None) -> dict:
    proc = subprocess.run(
        [sys.executable, script_path(name), *args],
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
    )
    payload = load_json_maybe(proc.stdout)
    return {
        "command": f"{name} {' '.join(args)}".strip(),
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "payload": payload,
    }


def allow_report_status(result: dict, *, allowed_returncodes: set[int] | None = None) -> dict:
    allowed = allowed_returncodes or {2}
    if result.get("ok") or result.get("returncode") not in allowed or result.get("payload") is None:
        return result
    normalized = dict(result)
    normalized["ok"] = True
    normalized["soft_status_returncode"] = result.get("returncode")
    normalized["soft_status_reason"] = "report generated with a non-passing evidence decision"
    return normalized


def run_adoption_drift_if_source_exists(skill_dir: Path | None = None) -> dict:
    target = (skill_dir or ROOT).resolve()
    events_path = target / "reports" / "telemetry_events.jsonl"
    if events_path.exists():
        return run_script("render_adoption_drift_report.py", [str(target)])
    return {
        "command": "render_adoption_drift_report.py skipped: missing reports/telemetry_events.jsonl",
        "returncode": 0,
        "ok": True,
        "stdout": "",
        "stderr": "",
        "payload": {
            "ok": True,
            "skipped": True,
            "reason": "raw telemetry event logs are local-only; keeping committed adoption_drift_report artifacts",
        },
    }
