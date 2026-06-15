#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "python_compat_check.py"
TMP = ROOT / "tests" / "tmp_python_compat"


def run_check(*extra: str, check: bool = True, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(ROOT),
            "--generated-at",
            "2026-06-14",
            *extra,
        ],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
    )


def main() -> None:
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True, exist_ok=True)
    output_json = TMP / "python_compatibility.json"
    output_md = TMP / "python_compatibility.md"
    proc = run_check("--output-json", str(output_json), "--output-md", str(output_md))
    payload = json.loads(proc.stdout)
    assert payload["schema_version"] == "1.0", payload
    assert payload["ok"] is True, payload
    assert payload["summary"]["target_python"] == "3.11", payload
    assert payload["summary"]["file_count"] >= 50, payload["summary"]
    assert payload["summary"]["issue_count"] == 0, payload["summary"]
    assert payload["summary"]["fstring_311_violation_count"] == 0, payload["summary"]
    markdown = output_md.read_text(encoding="utf-8")
    assert "Python Compatibility" in markdown, markdown
    assert "f-string 3.11 violations" in markdown, markdown

    safe = TMP / "safe.py"
    safe.write_text(
        "value = 'x|y'\n"
        "escaped = value.replace('|', '\\\\|')\n"
        "result = f'{escaped}'\n",
        encoding="utf-8",
    )
    safe_proc = run_check(
        "--path",
        safe.relative_to(ROOT).as_posix(),
        "--output-json",
        str(TMP / "safe_python_compatibility.json"),
        "--output-md",
        str(TMP / "safe_python_compatibility.md"),
        check=True,
        cwd=TMP,
    )
    safe_payload = json.loads(safe_proc.stdout)
    assert safe_payload["summary"]["file_count"] == 1, safe_payload
    assert safe_payload["summary"]["issue_count"] == 0, safe_payload

    unsafe = TMP / "unsafe.py"
    unsafe.write_text(
        "value = 'x|y'\n"
        "result = f\"{value.replace('|', '\\\\|')}\"\n",
        encoding="utf-8",
    )
    unsafe_proc = run_check(
        "--path",
        unsafe.relative_to(ROOT).as_posix(),
        "--output-json",
        str(TMP / "unsafe_python_compatibility.json"),
        "--output-md",
        str(TMP / "unsafe_python_compatibility.md"),
        check=False,
        cwd=TMP,
    )
    assert unsafe_proc.returncode == 2, unsafe_proc.stdout
    unsafe_payload = json.loads(unsafe_proc.stdout)
    assert unsafe_payload["ok"] is False, unsafe_payload
    assert unsafe_payload["summary"]["decision"] == "block-python-compat", unsafe_payload
    assert unsafe_payload["summary"]["file_count"] == 1, unsafe_payload
    assert unsafe_payload["summary"]["fstring_311_violation_count"] >= 1, unsafe_payload
    assert any(item["rule"] == "fstring-expression-backslash" for item in unsafe_payload["issues"]), unsafe_payload["issues"]
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
