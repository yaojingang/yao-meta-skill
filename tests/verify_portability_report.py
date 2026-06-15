#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_portability_report.py"


def main() -> None:
    payload = None
    for args in ([], [str(ROOT)]):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            print(proc.stdout)
            print(proc.stderr)
            raise SystemExit(proc.returncode)
        current_payload = json.loads(proc.stdout)
        if payload is None:
            payload = current_payload
        elif current_payload != payload:
            print(json.dumps({"default": payload, "explicit": current_payload}, ensure_ascii=False, indent=2))
            raise SystemExit(2)

    assert payload is not None
    failures = []
    if payload.get("score", 0) < 95:
        failures.append(f"portability score too low: {payload.get('score')}")
    if payload.get("summary", {}).get("adapter_target_count", 0) < 3:
        failures.append("adapter target coverage too low")
    if payload.get("summary", {}).get("degradation_coverage", 0) < 3:
        failures.append("degradation coverage too low")
    if payload.get("summary", {}).get("snapshot_count", 0) < 3:
        failures.append("snapshot coverage too low")

    report = {"ok": not failures, "failures": failures, "payload": payload}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
