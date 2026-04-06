#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_reference_scan.py"


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_reference_scan"
    if tmp_root.exists():
        subprocess.run(["rm", "-rf", str(tmp_root)], check=True)
    tmp_root.mkdir(parents=True, exist_ok=True)

    init_proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "init_skill.py"),
            "reference-scan-demo",
            "--description",
            "Turn a product idea into a reusable benchmarked skill.",
            "--output-dir",
            str(tmp_root),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    init_payload = json.loads(init_proc.stdout)
    created = Path(init_payload["root"])

    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(created),
            "--reference",
            "Top Method::method::Borrow a tight benchmark loop.::Avoid copying source-specific branding.",
            "--reference",
            "Portable System::portability::Borrow neutral metadata and degradation rules.::Avoid target lock-in.",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)

    md_path = Path(payload["artifacts"]["markdown"])
    json_path = Path(payload["artifacts"]["json"])
    assert md_path.exists(), md_path
    assert json_path.exists(), json_path

    report_text = md_path.read_text(encoding="utf-8")
    assert "# Reference Scan" in report_text, report_text[:200]
    assert "Top Method" in report_text, report_text[:300]
    assert "Borrow Plan" in report_text, report_text[:500]

    summary = json.loads(json_path.read_text(encoding="utf-8"))
    assert len(summary["references"]) == 2, summary

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
