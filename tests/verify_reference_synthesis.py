#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "scripts" / "yao.py"
BENCHMARK_FIXTURE_DIR = ROOT / "tests" / "fixtures" / "github_benchmark_scan"


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_reference_synthesis"
    if tmp_root.exists():
        subprocess.run(["rm", "-rf", str(tmp_root)], check=True)

    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "init",
            "reference-synthesis-demo",
            "--description",
            "Turn repeated release notes into a portable governed release skill.",
            "--output-dir",
            str(tmp_root),
            "--mode",
            "governed",
            "--archetype",
            "governed",
            "--github-query",
            "release workflow evaluation portability",
            "--github-fixture-dir",
            str(BENCHMARK_FIXTURE_DIR),
            "--user-reference",
            "Minimal vibe helper::taste::Keep the first pass fast, minimal, and lightweight.::Do not add review, governance, or approval steps.",
            "--intent-job",
            "Turn repeated release notes into a portable governed release skill.",
            "--intent-real-input",
            "release notes",
            "--intent-real-input",
            "changelog snippets",
            "--intent-primary-output",
            "A governed release packet.",
            "--intent-exclusion",
            "Do not publish blog posts.",
            "--intent-constraint",
            "portability",
            "--intent-standard",
            "consistency",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    skill_dir = Path(payload["root"])
    synthesis_path = skill_dir / "reports" / "reference-synthesis.json"
    assert synthesis_path.exists(), synthesis_path
    synthesis = json.loads(synthesis_path.read_text(encoding="utf-8"))
    assert len(synthesis["github_benchmarks"]) == 3, synthesis
    assert len(synthesis["source_tracks"]) == 3, synthesis
    assert synthesis["synthesis"]["borrow_now"], synthesis
    assert synthesis["synthesis"]["recommendation"]["summary"], synthesis
    assert synthesis["synthesis"]["visibility"]["mode"] == "explicit", synthesis
    assert "design_conflict" in synthesis["synthesis"]["visibility"]["reasons"], synthesis
    assert synthesis["synthesis"]["conflicts"], synthesis
    markdown = (skill_dir / "reports" / "reference-synthesis.md").read_text(encoding="utf-8")
    assert "Curated World-Class Pattern Tracks" in markdown, markdown[:600]
    assert "Borrow Now" in markdown, markdown[:900]
    assert "Default Recommendation" in markdown, markdown[:1200]
    assert "Conflict Check" in markdown, markdown[:1500]
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
