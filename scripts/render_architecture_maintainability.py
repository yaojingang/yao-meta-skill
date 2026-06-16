#!/usr/bin/env python3
"""Render a maintainability audit for the skill code surface."""

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent


EXCLUDED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "dist",
    ".previews",
}


def iter_python_files(skill_dir: Path) -> list[Path]:
    roots = [skill_dir / "scripts", skill_dir / "tests"]
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            rel_parts = path.relative_to(skill_dir).parts
            if any(part in EXCLUDED_PARTS for part in rel_parts):
                continue
            if len(rel_parts) >= 2 and rel_parts[0] == "tests" and rel_parts[1].startswith("tmp"):
                continue
            files.append(path)
    return sorted(files)


def rel(skill_dir: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(skill_dir.resolve()))
    except ValueError:
        return str(path)


def classify_python_file(path: Path, text: str) -> str:
    if 'SCRIPT_INTERFACE = "internal-module"' in text or "SCRIPT_INTERFACE = 'internal-module'" in text:
        return "internal-module"
    if "argparse.ArgumentParser" in text or ".add_argument(" in text or "argparse" in text:
        return "cli-script"
    if path.parts[-2:-1] == ("tests",) or "/tests/" in path.as_posix():
        return "test"
    return "module"


def recommendation_for(path: str) -> str:
    if path == "scripts/yao.py":
        return "Split command handlers by domain while keeping scripts/yao.py as the thin CLI orchestrator."
    if path == "scripts/render_review_studio.py":
        return "Move data loading and large section renderers into focused review_studio_* modules."
    if path == "scripts/render_review_viewer.py":
        return "Split viewer data assembly from HTML section rendering."
    if path.startswith("tests/"):
        return "Break broad integration assertions into focused verifier helpers when the next behavior change lands."
    return "Watch this file before adding new responsibilities; extract a helper module when one concern dominates."


def count_handlers_in_file(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.startswith("def command_"))


def command_module_paths(skill_dir: Path) -> list[Path]:
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.exists():
        return []
    paths = [scripts_dir / "yao.py"]
    paths.extend(sorted(scripts_dir.glob("yao_cli_*commands.py")))
    return [path for path in paths if path.exists()]


def count_cli_command_handlers(skill_dir: Path) -> int:
    return sum(count_handlers_in_file(path) for path in command_module_paths(skill_dir))


def build_report(skill_dir: Path, warn_lines: int, block_lines: int, trend_lines: int, generated_at: str) -> dict[str, Any]:
    files = iter_python_files(skill_dir)
    watch_lines = max(1, int(warn_lines * 0.8))
    early_watch_lines = max(1, min(trend_lines, watch_lines))
    records: list[dict[str, Any]] = []
    internal_count = 0
    cli_count = 0
    test_count = 0
    script_count = 0
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        line_count = len(text.splitlines())
        kind = classify_python_file(path, text)
        rel_path = rel(skill_dir, path)
        if kind == "internal-module":
            internal_count += 1
        if kind == "cli-script":
            cli_count += 1
        if rel_path.startswith("tests/"):
            test_count += 1
        if rel_path.startswith("scripts/"):
            script_count += 1
        severity = "pass"
        if line_count >= block_lines:
            severity = "block"
        elif line_count >= warn_lines:
            severity = "warn"
        early_watch = severity == "pass" and line_count >= early_watch_lines
        records.append(
            {
                "path": rel_path,
                "lines": line_count,
                "kind": kind,
                "severity": severity,
                "early_watch": early_watch,
                "recommendation": recommendation_for(rel_path),
            }
        )
    records.sort(key=lambda item: (-int(item["lines"]), str(item["path"])))
    hotspots = [item for item in records if item["severity"] in {"warn", "block"}]
    watchlist = [item for item in records if item["severity"] == "pass" and int(item["lines"]) >= watch_lines]
    early_watchlist = [
        item
        for item in records
        if item["severity"] == "pass" and int(item["lines"]) >= early_watch_lines and item not in watchlist
    ]
    blockers = [item for item in records if item["severity"] == "block"]
    summary = {
        "python_file_count": len(records),
        "script_file_count": script_count,
        "test_file_count": test_count,
        "internal_module_count": internal_count,
        "cli_script_count": cli_count,
        "command_handler_count": count_cli_command_handlers(skill_dir),
        "entrypoint_command_handler_count": count_handlers_in_file(skill_dir / "scripts" / "yao.py"),
        "command_module_count": len(command_module_paths(skill_dir)),
        "warn_line_threshold": warn_lines,
        "watch_line_threshold": watch_lines,
        "early_watch_line_threshold": early_watch_lines,
        "block_line_threshold": block_lines,
        "largest_file_lines": records[0]["lines"] if records else 0,
        "watchlist_count": len(watchlist),
        "early_watchlist_count": len(early_watchlist),
        "hotspot_count": len(hotspots),
        "blocker_count": len(blockers),
        "decision": "block-maintainability" if blockers else ("watch-maintainability-hotspots" if hotspots else "pass"),
    }
    return {
        "schema_version": "1.0",
        "ok": not blockers,
        "generated_at": generated_at,
        "skill_dir": ".",
        "summary": summary,
        "largest_files": records[:12],
        "watchlist": watchlist[:12],
        "early_watchlist": early_watchlist[:12],
        "hotspots": hotspots,
        "actions": [
            {
                "path": item["path"],
                "severity": item["severity"],
                "action": item["recommendation"],
            }
            for item in hotspots[:8]
        ],
        "artifacts": {
            "json": "reports/architecture_maintainability.json",
            "markdown": "reports/architecture_maintainability.md",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Architecture Maintainability",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- decision: `{summary['decision']}`",
        f"- python files: `{summary['python_file_count']}`",
        f"- scripts: `{summary['script_file_count']}`",
        f"- tests: `{summary['test_file_count']}`",
        f"- internal modules: `{summary['internal_module_count']}`",
        f"- CLI scripts: `{summary['cli_script_count']}`",
        f"- Yao CLI command handlers: `{summary['command_handler_count']}`",
        f"- entrypoint command handlers: `{summary['entrypoint_command_handler_count']}`",
        f"- command modules: `{summary['command_module_count']}`",
        f"- largest file lines: `{summary['largest_file_lines']}`",
        f"- early watch threshold lines: `{summary['early_watch_line_threshold']}`",
        f"- early watchlist: `{summary['early_watchlist_count']}`",
        f"- watch threshold lines: `{summary['watch_line_threshold']}`",
        f"- watchlist: `{summary['watchlist_count']}`",
        f"- hotspots: `{summary['hotspot_count']}`",
        f"- blockers: `{summary['blocker_count']}`",
        "",
        "This report keeps maintainability risk visible before the Meta Skill grows more gates, renderers, and CLI commands.",
        "",
        "## Hotspots",
        "",
    ]
    hotspots = report.get("hotspots", [])
    if hotspots:
        lines.extend(["| File | Lines | Kind | Severity | Recommended action |", "| --- | ---: | --- | --- | --- |"])
        for item in hotspots:
            lines.append(
                f"| `{item['path']}` | `{item['lines']}` | `{item['kind']}` | `{item['severity']}` | {item['recommendation']} |"
            )
    else:
        lines.append("No file-size hotspots found.")
    lines.extend(["", "## Watchlist", ""])
    watchlist = report.get("watchlist", [])
    if watchlist:
        lines.extend(["| File | Lines | Kind | Recommended next split |", "| --- | ---: | --- | --- |"])
        for item in watchlist:
            lines.append(f"| `{item['path']}` | `{item['lines']}` | `{item['kind']}` | {item['recommendation']} |")
    else:
        lines.append("No near-threshold files found.")
    lines.extend(["", "## Early Watchlist", ""])
    early_watchlist = report.get("early_watchlist", [])
    if early_watchlist:
        lines.extend(["| File | Lines | Kind | Recommended next split |", "| --- | ---: | --- | --- |"])
        for item in early_watchlist:
            lines.append(f"| `{item['path']}` | `{item['lines']}` | `{item['kind']}` | {item['recommendation']} |")
    else:
        lines.append("No early watch files found.")
    lines.extend(["", "## Largest Files", ""])
    if report.get("largest_files"):
        lines.extend(["| File | Lines | Kind | Severity |", "| --- | ---: | --- | --- |"])
        for item in report["largest_files"]:
            lines.append(f"| `{item['path']}` | `{item['lines']}` | `{item['kind']}` | `{item['severity']}` |")
    else:
        lines.append("No Python files found under scripts/ or tests/.")
    lines.extend(
        [
            "",
            "## Release Rule",
            "",
            "- `block` hotspots should be split before governed release.",
            "- `warn` hotspots can ship only when Review Studio keeps them visible and a reviewer accepts the modularization plan.",
            "- Do not split a file only for line count; split when a stable responsibility boundary is clear.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render architecture maintainability evidence for a skill package.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--output-json")
    parser.add_argument("--output-md")
    parser.add_argument("--warn-lines", type=int, default=900)
    parser.add_argument("--block-lines", type=int, default=1500)
    parser.add_argument("--trend-lines", type=int, default=600)
    parser.add_argument("--generated-at", default=date.today().isoformat())
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    report = build_report(skill_dir, args.warn_lines, args.block_lines, args.trend_lines, args.generated_at)
    output_json = Path(args.output_json) if args.output_json else skill_dir / "reports" / "architecture_maintainability.json"
    output_md = Path(args.output_md) if args.output_md else skill_dir / "reports" / "architecture_maintainability.md"
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["ok"] else 2)


if __name__ == "__main__":
    main()
