#!/usr/bin/env python3
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Turns redacted repeated preference patterns into proposal-only adaptation plans."

PROPOSAL_LIBRARY = {
    "language_default": {
        "title": "Keep reports Chinese-first with optional English",
        "change_type": "report-default-language",
        "risk_level": "low",
        "target_files": ["scripts/render_skill_overview.py", "references/artifact-design-doctrine.md"],
        "suggested_changes": [
            "Keep user-facing report copy Simplified Chinese by default.",
            "Expose English through the existing language switch instead of mixing languages in the default view.",
        ],
        "verification_commands": ["python3 tests/verify_skill_overview.py"],
        "rollback_plan": "Revert report language template changes and rerun the overview verifier.",
    },
    "report_ui": {
        "title": "Improve report layout, visual hierarchy, and chart readability",
        "change_type": "artifact-ui-polish",
        "risk_level": "medium",
        "target_files": ["scripts/render_skill_overview.py", "references/artifact-design-doctrine.md", "tests/verify_skill_overview.py"],
        "suggested_changes": [
            "Prefer vertical narrative sections with limited two-column layouts only when content has enough width.",
            "Keep charts inline SVG, with captions and stable responsive constraints.",
        ],
        "verification_commands": ["python3 tests/verify_skill_overview.py", "python3 tests/verify_skill_report_charts.py"],
        "rollback_plan": "Restore the previous report renderer and regenerate the demo report.",
    },
    "approval_safety": {
        "title": "Keep adaptive iteration approval-gated",
        "change_type": "privacy-governance",
        "risk_level": "low",
        "target_files": ["references/user-memory-policy.md", "references/autonomous-adaptation.md", "schemas/adaptation-proposal.schema.json"],
        "suggested_changes": [
            "Require explicit source paths for memory scans.",
            "Generate proposals before any source patching.",
            "Reserve automatic apply for a future approval ledger and rollback implementation.",
        ],
        "verification_commands": ["python3 tests/verify_adaptation_safety.py"],
        "rollback_plan": "Remove the adaptive proposal artifacts and keep feedback/adoption drift as the only iteration inputs.",
    },
    "delivery_format": {
        "title": "Make generated artifact paths explicit in CLI output",
        "change_type": "artifact-discoverability",
        "risk_level": "low",
        "target_files": ["scripts/yao.py", "README.md"],
        "suggested_changes": [
            "Include stable report paths in command output.",
            "Document which artifacts are meant for human review.",
        ],
        "verification_commands": ["python3 tests/verify_yao_cli.py"],
        "rollback_plan": "Revert CLI copy/documentation changes and keep artifact paths unchanged.",
    },
    "evidence_testing": {
        "title": "Attach tests and evidence refresh to each upgrade",
        "change_type": "quality-gate",
        "risk_level": "medium",
        "target_files": ["tests/verify_adaptation_safety.py", "scripts/render_skill_os2_coverage.py", "reports/skill_os2_coverage.json"],
        "suggested_changes": [
            "Add focused verifier coverage for every new adaptive behavior.",
            "Refresh Skill OS 2.0 coverage so planned, partial, and covered states remain visible.",
        ],
        "verification_commands": ["python3 tests/verify_adaptation_safety.py", "python3 tests/verify_skill_os2_coverage.py"],
        "rollback_plan": "Revert the new verifier and coverage status updates, then regenerate coverage reports.",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def display_path(path: Path, skill_dir: Path) -> str:
    try:
        return str(path.resolve().relative_to(skill_dir.resolve()))
    except ValueError:
        return str(path.resolve())


def resolve_output(skill_dir: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else skill_dir / path


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def proposal_id(pattern_id: str, support_count: int, target_files: list[str]) -> str:
    digest = hashlib.sha1(f"{pattern_id}:{support_count}:{','.join(target_files)}".encode("utf-8")).hexdigest()
    return f"adapt-{digest[:10]}"


def proposal_from_pattern(pattern: dict[str, Any]) -> dict[str, Any]:
    pattern_id = str(pattern.get("pattern_id") or "generic")
    spec = PROPOSAL_LIBRARY.get(
        pattern_id,
        {
            "title": "Review repeated preference pattern",
            "change_type": "manual-review",
            "risk_level": "medium",
            "target_files": ["README.md"],
            "suggested_changes": ["Review this repeated signal manually before changing skill behavior."],
            "verification_commands": ["make ci-test"],
            "rollback_plan": "Revert the approved patch and rerun the relevant verifier.",
        },
    )
    support_count = int(pattern.get("support_count") or 0)
    target_files = list(spec["target_files"])
    return {
        "proposal_id": proposal_id(pattern_id, support_count, target_files),
        "pattern_id": pattern_id,
        "title": spec["title"],
        "change_type": spec["change_type"],
        "status": "proposal-only",
        "requires_approval": True,
        "write_allowed_without_approval": False,
        "risk_level": spec["risk_level"],
        "reason": pattern.get("reason", "Repeated signal detected."),
        "support_count": support_count,
        "target_files": target_files,
        "suggested_changes": spec["suggested_changes"],
        "verification_commands": spec["verification_commands"],
        "rollback_plan": spec["rollback_plan"],
        "evidence_refs": [
            {
                "record_id": item.get("record_id", "unknown"),
                "excerpt": item.get("excerpt", ""),
            }
            for item in pattern.get("evidence", [])[:3]
            if isinstance(item, dict)
        ],
    }


def build_report(skill_dir: Path, patterns_json: Path, generated_at: str) -> dict[str, Any]:
    skill_dir = skill_dir.resolve()
    if not patterns_json.is_absolute():
        patterns_json = skill_dir / patterns_json
    patterns_payload = load_json(patterns_json)
    failures: list[str] = []
    if not patterns_payload:
        failures.append(f"Pattern report does not exist or is invalid: {display_path(patterns_json, skill_dir)}")
    elif patterns_payload.get("ok") is not True:
        failures.append("Pattern report is not ok; fix scan failures before proposal generation.")
    patterns = patterns_payload.get("patterns", []) if isinstance(patterns_payload.get("patterns"), list) else []
    proposals = [proposal_from_pattern(pattern) for pattern in patterns if isinstance(pattern, dict)] if not failures else []
    return {
        "schema_version": "1.0",
        "ok": not failures,
        "generated_at": generated_at,
        "skill_dir": display_path(skill_dir, skill_dir),
        "source_patterns": display_path(patterns_json, skill_dir),
        "summary": {
            "pattern_count": len(patterns),
            "proposal_count": len(proposals),
            "apply_supported": (ROOT / "scripts" / "apply_adaptation.py").exists(),
            "failure_count": len(failures),
        },
        "proposal_contract": {
            "proposal_only": True,
            "approval_required": True,
            "writes_repository_files": False,
            "allowlisted_targets_required": True,
            "target_file_sha256_required_for_apply": True,
            "approval_draft_supported": True,
            "rollback_required_for_apply": True,
            "apply_command_available": (ROOT / "scripts" / "apply_adaptation.py").exists(),
        },
        "proposals": proposals,
        "failures": failures,
        "artifacts": {
            "json": "reports/adaptation_proposals.json",
            "markdown": "reports/adaptation_proposals.md",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Adaptation Proposals",
        "",
        f"- Generated at: `{report['generated_at']}`",
        f"- Pattern report: `{report['source_patterns']}`",
        f"- Proposal only: `{str(report['proposal_contract']['proposal_only']).lower()}`",
        f"- Writes repository files: `{str(report['proposal_contract']['writes_repository_files']).lower()}`",
        f"- Proposals: `{report['summary']['proposal_count']}`",
        "",
    ]
    if not report["proposals"]:
        lines.append("No proposals were generated.")
    for proposal in report["proposals"]:
        lines.extend(
            [
                f"## {proposal['title']}",
                "",
                f"- ID: `{proposal['proposal_id']}`",
                f"- Status: `{proposal['status']}`",
                f"- Pattern: `{proposal['pattern_id']}`",
                f"- Risk: `{proposal['risk_level']}`",
                f"- Requires approval: `{str(proposal['requires_approval']).lower()}`",
                f"- Reason: {proposal['reason']}",
                "- Target files:",
            ]
        )
        lines.extend(f"  - `{path}`" for path in proposal["target_files"])
        lines.append("- Suggested changes:")
        lines.extend(f"  - {item}" for item in proposal["suggested_changes"])
        lines.append("- Verification:")
        lines.extend(f"  - `{item}`" for item in proposal["verification_commands"])
        lines.append(f"- Rollback: {proposal['rollback_plan']}")
        if proposal["evidence_refs"]:
            lines.append("- Redacted evidence refs:")
            lines.extend(f"  - `{item['record_id']}`: {item['excerpt']}" for item in proposal["evidence_refs"])
        lines.append("")
    if report["failures"]:
        lines.extend(["## Failures", ""])
        lines.extend(f"- {failure}" for failure in report["failures"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Create proposal-only adaptation plans from summarized user signal patterns.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--patterns-json", default="reports/user_patterns.json")
    parser.add_argument("--output-json", default="reports/adaptation_proposals.json")
    parser.add_argument("--output-md", default="reports/adaptation_proposals.md")
    parser.add_argument("--generated-at", default=utc_now())
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    report = build_report(skill_dir, Path(args.patterns_json), args.generated_at)
    if report["ok"]:
        output_json = resolve_output(skill_dir, args.output_json)
        output_md = resolve_output(skill_dir, args.output_md)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        report["artifacts"] = {
            "json": display_path(output_json, skill_dir),
            "markdown": display_path(output_md, skill_dir),
        }
        output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        output_md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
