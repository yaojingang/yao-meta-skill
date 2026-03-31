#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "cross_packager.py"
EXPECTATIONS = ROOT / "evals" / "packaging_expectations.json"
SNAPSHOTS = ROOT / "tests" / "snapshots"
TMP = ROOT / "tests" / "tmp_snapshot"


def main() -> None:
    if TMP.exists():
        shutil.rmtree(TMP)
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(ROOT),
            "--platform",
            "openai",
            "--platform",
            "claude",
            "--platform",
            "generic",
            "--expectations",
            str(EXPECTATIONS),
            "--output-dir",
            str(TMP),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        raise SystemExit(proc.returncode)

    failures = []
    for name in ("openai", "claude", "generic"):
        snapshot = json.loads((SNAPSHOTS / f"{name}_adapter.json").read_text(encoding="utf-8"))
        adapter = json.loads((TMP / "targets" / name / "adapter.json").read_text(encoding="utf-8"))
        if adapter.get("platform") != snapshot["platform"]:
            failures.append(f"{name}: platform mismatch")
        if adapter.get("canonical_metadata") != snapshot["canonical_metadata"]:
            failures.append(f"{name}: canonical metadata mismatch")
        if not (TMP / snapshot["required_generated_file"]).exists():
            failures.append(f"{name}: missing generated file {snapshot['required_generated_file']}")

    report = {"ok": not failures, "failures": failures}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
