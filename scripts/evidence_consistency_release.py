from pathlib import Path
from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_evidence_consistency.py to verify release evidence refresh instructions."

SOURCE_REFRESH_HEADER = "After source changes that affect scripts"
CLEAN_LOCK_HEADER = "For final release evidence"
CLEAN_LOCK_END = "If `reports/benchmark_reproducibility.json`"

SOURCE_REFRESH_REPORT_COMMANDS = [
    'python3 scripts/render_benchmark_reproducibility.py . --generated-at "$GENERATED_AT"',
    "python3 scripts/render_skill_overview.py .",
    "python3 scripts/render_skill_interpretation.py .",
    "python3 scripts/render_review_viewer.py .",
    'python3 scripts/render_world_class_preflight.py . --generated-at "$GENERATED_AT"',
    "python3 scripts/render_review_studio.py . --output-html reports/review-studio.html --output-json reports/review-studio.json",
    'python3 scripts/render_evidence_consistency.py . --generated-at "$GENERATED_AT"',
]
CLEAN_LOCK_REPORT_COMMANDS = list(SOURCE_REFRESH_REPORT_COMMANDS)


def section_between(text: str, start: str, end: str) -> str:
    if start not in text:
        return ""
    section = text.split(start, 1)[1]
    if end in section:
        section = section.split(end, 1)[0]
    return section


def command_presence(section: str, commands: list[str]) -> dict[str, bool]:
    return {command: command in section for command in commands}


def build_release_evidence_flow_check(skill_dir: Path) -> dict[str, Any]:
    agents_path = skill_dir / "AGENTS.md"
    agents_text = agents_path.read_text(encoding="utf-8") if agents_path.exists() else ""
    source_refresh = section_between(agents_text, SOURCE_REFRESH_HEADER, CLEAN_LOCK_HEADER)
    clean_lock = section_between(agents_text, CLEAN_LOCK_HEADER, CLEAN_LOCK_END)
    expected = {
        "AGENTS.md": True,
        "source_refresh_section": True,
        "clean_lock_section": True,
        "source_refresh_commands": {command: True for command in SOURCE_REFRESH_REPORT_COMMANDS},
        "clean_lock_commands": {command: True for command in CLEAN_LOCK_REPORT_COMMANDS},
    }
    actual = {
        "AGENTS.md": agents_path.exists(),
        "source_refresh_section": bool(source_refresh),
        "clean_lock_section": bool(clean_lock),
        "source_refresh_commands": command_presence(source_refresh, SOURCE_REFRESH_REPORT_COMMANDS),
        "clean_lock_commands": command_presence(clean_lock, CLEAN_LOCK_REPORT_COMMANDS),
    }
    return {
        "key": "release-evidence-flow-covers-first-class-reports",
        "label": "Release evidence flow covers first-class reports",
        "status": "pass" if expected == actual else "fail",
        "expected": expected,
        "actual": actual,
        "paths": [
            "AGENTS.md",
            "reports/benchmark_reproducibility.json",
            "reports/skill-overview.json",
            "reports/skill-interpretation.json",
            "reports/review-viewer.json",
            "reports/world_class_evidence_preflight.json",
            "reports/review-studio.json",
            "reports/evidence_consistency.json",
        ],
        "detail": (
            "Release refresh and clean-lock instructions must regenerate every first-class report "
            "before evidence consistency can be trusted."
        ),
    }
