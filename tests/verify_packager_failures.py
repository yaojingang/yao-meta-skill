#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "cross_packager.py"
EXPECTATIONS = ROOT / "evals" / "packaging_expectations.json"
TMP = ROOT / "tests" / "tmp"


def run_case(name: str, cmd: list[str], expected_substring: str) -> dict:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    payload = {}
    if proc.stdout.strip():
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload = {"raw_stdout": proc.stdout}
    joined = proc.stdout + "\n" + proc.stderr
    passed = proc.returncode == 2 and expected_substring in joined
    return {
        "name": name,
        "passed": passed,
        "returncode": proc.returncode,
        "expected_substring": expected_substring,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "payload": payload,
    }


def main() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    cases = [
        run_case(
            "missing_interface_field",
            [
                sys.executable,
                str(SCRIPT),
                str(ROOT / "tests" / "fixtures" / "package_missing_interface_field"),
                "--platform",
                "openai",
                "--expectations",
                str(EXPECTATIONS),
                "--output-dir",
                str(TMP / "missing_interface_field"),
            ],
            "Missing required interface fields",
        ),
        run_case(
            "invalid_yaml",
            [
                sys.executable,
                str(SCRIPT),
                str(ROOT / "tests" / "fixtures" / "package_invalid_yaml"),
                "--platform",
                "openai",
                "--expectations",
                str(EXPECTATIONS),
                "--output-dir",
                str(TMP / "invalid_yaml"),
            ],
            "while scanning a quoted scalar",
        ),
        run_case(
            "unsupported_platform",
            [
                sys.executable,
                str(SCRIPT),
                str(ROOT),
                "--platform",
                "bad_target",
                "--expectations",
                str(EXPECTATIONS),
                "--output-dir",
                str(TMP / "unsupported_platform"),
            ],
            "Unsupported platform",
        ),
    ]
    report = {"ok": all(case["passed"] for case in cases), "cases": cases}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
