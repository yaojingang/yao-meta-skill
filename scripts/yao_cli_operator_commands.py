"""Operator UX commands for installation, docs sync, and PR review evidence."""

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from yao_cli_runtime import ROOT


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by yao.py for operator-facing install, localized docs, and PR review diagnostics."


DEFAULT_DOC_PAIRS = [
    {
        "key": "skill-os-2-upgrade",
        "source": "## Skill OS 2.0 Upgrade",
        "localized": "## Skill OS 2.0 升级",
    },
    {
        "key": "from-1-to-2",
        "source": "## From 1.0 to 2.0",
        "localized": "## 从 1.0 到 2.0",
    },
    {
        "key": "use-cases",
        "source": "## 2.0 Use Cases",
        "localized": "## 2.0 使用场景",
    },
    {
        "key": "operator-ux",
        "source": "## Operator UX Commands",
        "localized": "## Operator UX 命令",
    },
    {
        "key": "architecture",
        "source": "## Architecture",
        "localized": "## 架构图",
    },
    {
        "key": "benchmark",
        "source": "## Weighted Quality Benchmark",
        "localized": "## 加权质量评测",
    },
    {
        "key": "claim-boundary",
        "source": 'Current posture: the repository is ready for beta and external testing',
        "localized": "当前发布口径：仓库已经适合进入测试版和外部试用",
    },
]


def _expand(path: str) -> Path:
    return Path(path).expanduser().resolve()


def _display(path: Path) -> str:
    try:
        return str(path.relative_to(Path.home()))
    except ValueError:
        return str(path)


def _skill_path_status(root: Path, skill_name: str, expected_source: Path) -> dict[str, Any]:
    path = root / skill_name
    exists = path.exists()
    resolved = path.resolve() if exists or path.is_symlink() else path
    has_skill_md = (path / "SKILL.md").exists()
    return {
        "root": str(root),
        "path": str(path),
        "exists": exists,
        "is_symlink": path.is_symlink(),
        "resolved": str(resolved),
        "has_skill_md": has_skill_md,
        "points_to_expected_source": resolved == expected_source,
    }


def _recommend_install_status(codex: dict[str, Any], agents: dict[str, Any], disabled: dict[str, Any]) -> list[str]:
    recommendations = []
    if codex["has_skill_md"]:
        recommendations.append("Codex/Cortex can discover this skill through .codex/skills; restart the app if the list looks stale.")
    if agents["has_skill_md"]:
        recommendations.append("The skill is also active under .agents/skills; expect a duplicate entry when this repo is open.")
    if not codex["has_skill_md"] and not agents["has_skill_md"] and disabled["has_skill_md"]:
        recommendations.append("Only the disabled mirror exists; run make sync-active-install or add a .codex/skills symlink to activate it.")
    if not codex["has_skill_md"] and not agents["has_skill_md"] and not disabled["has_skill_md"]:
        recommendations.append("No active or disabled install was found for this skill name.")
    if codex["has_skill_md"] and not codex["points_to_expected_source"]:
        recommendations.append("The .codex/skills entry points somewhere else; inspect the symlink before editing or syncing.")
    if not recommendations:
        recommendations.append("No action required.")
    return recommendations


def command_install_status(args: argparse.Namespace) -> int:
    skill_name = args.skill_name
    expected_source = _expand(args.expected_source)
    codex_root = _expand(args.codex_root)
    agents_root = _expand(args.agents_root)
    disabled_root = _expand(args.disabled_root)

    codex = _skill_path_status(codex_root, skill_name, expected_source)
    agents = _skill_path_status(agents_root, skill_name, expected_source)
    disabled = _skill_path_status(disabled_root, skill_name, expected_source)
    active_locations = [name for name, item in (("codex", codex), ("agents", agents)) if item["has_skill_md"]]
    report = {
        "ok": True,
        "skill_name": skill_name,
        "expected_source": str(expected_source),
        "summary": {
            "codex_active": codex["has_skill_md"],
            "agents_active": agents["has_skill_md"],
            "disabled_mirror": disabled["has_skill_md"],
            "active_location_count": len(active_locations),
            "duplicate_active": len(active_locations) > 1,
            "active_locations": active_locations,
        },
        "locations": {
            "codex": codex,
            "agents": agents,
            "disabled": disabled,
        },
        "recommendations": _recommend_install_status(codex, agents, disabled),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def _load_pairs(raw_pairs: list[str]) -> list[dict[str, str]]:
    if not raw_pairs:
        return DEFAULT_DOC_PAIRS
    pairs = []
    for raw in raw_pairs:
        parts = raw.split("::")
        if len(parts) != 3:
            raise ValueError("--pair must use key::source-marker::localized-marker")
        pairs.append({"key": parts[0], "source": parts[1], "localized": parts[2]})
    return pairs


def _write_json(path: str | None, payload: dict[str, Any]) -> None:
    if not path:
        return
    target = _expand(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_docs_sync_md(path: str | None, payload: dict[str, Any]) -> None:
    if not path:
        return
    target = _expand(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Localized Docs Sync Check",
        "",
        f"- ok: `{str(payload['ok']).lower()}`",
        f"- source: `{payload['source']}`",
        f"- localized: `{payload['localized']}`",
        f"- checked: `{payload['summary']['checked_count']}`",
        f"- missing: `{payload['summary']['missing_count']}`",
        f"- skipped: `{payload['summary']['skipped_count']}`",
        "",
        "## Pairs",
        "",
    ]
    for item in payload["pairs"]:
        lines.append(f"- `{item['key']}`: `{item['status']}`")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def command_localized_doc_sync_check(args: argparse.Namespace) -> int:
    source_path = _expand(args.source)
    localized_path = _expand(args.localized)
    try:
        pairs = _load_pairs(args.pair)
    except ValueError as exc:
        report = {
            "ok": False,
            "source": str(source_path),
            "localized": str(localized_path),
            "summary": {"checked_count": 0, "missing_count": 0, "skipped_count": 0},
            "pairs": [],
            "missing": [],
            "failures": [str(exc)],
        }
        _write_json(args.output_json, report)
        _write_docs_sync_md(args.output_md, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2
    missing_paths = [str(path) for path in (source_path, localized_path) if not path.exists()]
    if missing_paths:
        report = {
            "ok": False,
            "source": str(source_path),
            "localized": str(localized_path),
            "summary": {"checked_count": 0, "missing_count": 0, "skipped_count": 0},
            "pairs": [],
            "missing": [],
            "failures": [f"Missing docs file: {path}" for path in missing_paths],
        }
        _write_json(args.output_json, report)
        _write_docs_sync_md(args.output_md, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2
    source_text = source_path.read_text(encoding="utf-8")
    localized_text = localized_path.read_text(encoding="utf-8")
    results = []
    for pair in pairs:
        source_present = pair["source"] in source_text
        localized_present = pair["localized"] in localized_text
        if not source_present:
            status = "skipped-source-missing"
        elif localized_present:
            status = "pass"
        else:
            status = "missing-localized-marker"
        results.append(
            {
                **pair,
                "source_present": source_present,
                "localized_present": localized_present,
                "status": status,
            }
        )
    missing = [item for item in results if item["status"] == "missing-localized-marker"]
    checked = [item for item in results if item["source_present"]]
    report = {
        "ok": not missing,
        "source": str(source_path),
        "localized": str(localized_path),
        "summary": {
            "checked_count": len(checked),
            "missing_count": len(missing),
            "skipped_count": len(results) - len(checked),
        },
        "pairs": results,
        "missing": missing,
    }
    _write_json(args.output_json, report)
    _write_docs_sync_md(args.output_md, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


def _run_gh(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *args], capture_output=True, text=True)


def _gh_available() -> bool:
    return shutil.which("gh") is not None


def _review_depth(changed_files: int, changed_lines: int) -> str:
    if changed_files <= 5 and changed_lines < 100:
        return "quick"
    if changed_files <= 10 and changed_lines < 500:
        return "standard"
    return "deep"


def _check_summary(checks: list[dict[str, Any]]) -> dict[str, Any]:
    pending = []
    failed = []
    passed = []
    for item in checks:
        name = str(item.get("name") or item.get("workflowName") or "check")
        status = str(item.get("status") or "").upper()
        conclusion = str(item.get("conclusion") or "").upper()
        if status and status != "COMPLETED":
            pending.append(name)
        elif conclusion in {"SUCCESS", "SKIPPED", "NEUTRAL"}:
            passed.append(name)
        else:
            failed.append(name)
    return {
        "present": bool(checks),
        "passed_count": len(passed),
        "pending_count": len(pending),
        "failed_count": len(failed),
        "passed": passed,
        "pending": pending,
        "failed": failed,
    }


def _pr_decision(view: dict[str, Any], checks: dict[str, Any], require_checks: bool) -> str:
    if view.get("state") != "OPEN":
        return "not-open"
    if view.get("isDraft"):
        return "draft"
    if view.get("mergeable") not in {"MERGEABLE", "UNKNOWN"}:
        return "not-mergeable"
    if checks["failed_count"]:
        return "fix-failing-checks"
    if checks["pending_count"]:
        return "wait-for-checks"
    if require_checks and not checks["present"]:
        return "checks-required"
    if not checks["present"]:
        return "local-verification-required"
    return "mergeable-after-review"


def _write_pr_review_md(path: str | None, payload: dict[str, Any]) -> None:
    if not path:
        return
    target = _expand(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# PR Review Report",
        "",
        f"- ok: `{str(payload['ok']).lower()}`",
        f"- PR: `{payload['pr']}`",
        f"- repo: `{payload.get('repo') or 'current'}`",
        f"- decision: `{payload['decision']}`",
        f"- review depth: `{payload['review_depth']}`",
        f"- changed files: `{payload['summary']['changed_files']}`",
        f"- additions: `{payload['summary']['additions']}`",
        f"- deletions: `{payload['summary']['deletions']}`",
        f"- checks present: `{str(payload['checks']['present']).lower()}`",
        "",
        "## Files",
        "",
    ]
    for path_item in payload["files"]:
        lines.append(f"- `{path_item}`")
    lines.extend(["", "## Suggested Commands", ""])
    for command in payload["suggested_commands"]:
        lines.append(f"- `{command}`")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def command_pr_review_report(args: argparse.Namespace) -> int:
    if not _gh_available():
        report = {
            "ok": False,
            "pr": args.pr,
            "repo": args.repo,
            "decision": "missing-gh-cli",
            "failures": ["GitHub CLI `gh` is not available on PATH."],
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    fields = ",".join(
        [
            "number",
            "title",
            "state",
            "isDraft",
            "mergeable",
            "author",
            "baseRefName",
            "headRefName",
            "url",
            "additions",
            "deletions",
            "changedFiles",
            "commits",
            "statusCheckRollup",
            "reviewDecision",
            "maintainerCanModify",
        ]
    )
    view_args = ["pr", "view", args.pr, "--json", fields]
    diff_args = ["pr", "diff", args.pr, "--name-only"]
    if args.repo:
        view_args.extend(["--repo", args.repo])
        diff_args.extend(["--repo", args.repo])
    view_proc = _run_gh(view_args)
    if view_proc.returncode != 0:
        report = {
            "ok": False,
            "pr": args.pr,
            "repo": args.repo,
            "decision": "gh-pr-view-failed",
            "returncode": view_proc.returncode,
            "stderr": view_proc.stderr.strip(),
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2
    view = json.loads(view_proc.stdout)
    diff_proc = _run_gh(diff_args)
    files = [line.strip() for line in diff_proc.stdout.splitlines() if line.strip()] if diff_proc.returncode == 0 else []
    checks = _check_summary(view.get("statusCheckRollup") or [])
    changed_lines = int(view.get("additions") or 0) + int(view.get("deletions") or 0)
    depth = _review_depth(int(view.get("changedFiles") or len(files)), changed_lines)
    decision = _pr_decision(view, checks, args.require_checks)
    report = {
        "ok": decision not in {"missing-gh-cli", "gh-pr-view-failed", "checks-required", "fix-failing-checks", "not-mergeable", "draft", "not-open"},
        "pr": str(view.get("number", args.pr)),
        "repo": args.repo,
        "url": view.get("url", ""),
        "title": view.get("title", ""),
        "state": view.get("state", ""),
        "mergeable": view.get("mergeable", ""),
        "decision": decision,
        "review_depth": depth,
        "summary": {
            "changed_files": int(view.get("changedFiles") or len(files)),
            "additions": int(view.get("additions") or 0),
            "deletions": int(view.get("deletions") or 0),
            "commit_count": len(view.get("commits") or []),
            "maintainer_can_modify": bool(view.get("maintainerCanModify")),
        },
        "checks": checks,
        "files": files,
        "suggested_commands": [
            f"gh pr view {args.pr}{' --repo ' + args.repo if args.repo else ''} --json number,title,state,mergeable,statusCheckRollup",
            f"gh pr diff {args.pr}{' --repo ' + args.repo if args.repo else ''} --name-only",
            f"git fetch origin pull/{args.pr}/head:refs/tmp/pr-{args.pr}",
            f"git diff --check origin/main...refs/tmp/pr-{args.pr}",
        ],
    }
    _write_json(args.output_json, report)
    _write_pr_review_md(args.output_md, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2
