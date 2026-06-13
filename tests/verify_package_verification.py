#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TMP = ROOT / "tests" / "tmp_package_verification"
PACKAGER = ROOT / "scripts" / "cross_packager.py"
VERIFIER = ROOT / "scripts" / "verify_package.py"
EXPECTATIONS = ROOT / "evals" / "packaging_expectations.json"


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


def build_package(out_dir: Path) -> dict:
    return run(
        [
            sys.executable,
            str(PACKAGER),
            str(ROOT),
            "--platform",
            "openai",
            "--platform",
            "claude",
            "--platform",
            "generic",
            "--platform",
            "vscode",
            "--expectations",
            str(EXPECTATIONS),
            "--output-dir",
            str(out_dir),
            "--zip",
        ]
    )


def verify_package(out_dir: Path, output_json: Path, output_md: Path) -> dict:
    return run(
        [
            sys.executable,
            str(VERIFIER),
            str(ROOT),
            "--package-dir",
            str(out_dir),
            "--expectations",
            str(EXPECTATIONS),
            "--registry-json",
            str(ROOT / "reports" / "registry_audit.json"),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
            "--require-zip",
            "--generated-at",
            "2026-06-13",
        ]
    )


def main() -> None:
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True, exist_ok=True)

    valid_dir = TMP / "dist"
    build = build_package(valid_dir)
    assert build["ok"], build
    valid = verify_package(valid_dir, TMP / "package_verification.json", TMP / "package_verification.md")
    payload = valid["payload"]
    assert valid["ok"], valid
    assert payload["ok"], payload
    assert payload["summary"]["target_count"] == 4, payload
    assert payload["summary"]["adapter_count"] == 4, payload
    assert payload["summary"]["archive_present"], payload
    assert payload["summary"]["archive_sha256"], payload
    assert not payload["failures"], payload
    assert (TMP / "package_verification.md").exists(), TMP

    unsafe_dir = TMP / "unsafe-dist"
    shutil.copytree(valid_dir, unsafe_dir)
    with zipfile.ZipFile(unsafe_dir / "yao-meta-skill.zip", "a", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("../evil.txt", "bad")
    unsafe = verify_package(unsafe_dir, TMP / "unsafe.json", TMP / "unsafe.md")
    assert unsafe["returncode"] == 2, unsafe
    unsafe_payload = unsafe["payload"]
    assert not unsafe_payload["ok"], unsafe_payload
    assert any("Archive has no absolute or parent-traversal entries" in item for item in unsafe_payload["failures"]), unsafe_payload

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
