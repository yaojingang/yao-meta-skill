#!/usr/bin/env python3
import argparse
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from review_studio_gates import REVIEW_STUDIO_GATE_KEYS


ROOT = Path(__file__).resolve().parent.parent
NON_WAIVABLE_GATE_KEYS = {"review-waivers", "world-class-evidence"}
WAIVERABLE_GATE_KEYS = REVIEW_STUDIO_GATE_KEYS - NON_WAIVABLE_GATE_KEYS
KNOWN_GATE_KEYS = WAIVERABLE_GATE_KEYS
VALID_DECISIONS = {"accepted-risk", "false-positive", "temporary-exception"}
MIN_REASON_CHARS = 20


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def today_from(value: str | None) -> date:
    if not value:
        return date.today()
    return date.fromisoformat(value[:10])


def parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value[:10])
    except (TypeError, ValueError):
        return None


def waiver_id(entry: dict[str, Any]) -> str:
    raw = "|".join(
        [
            str(entry.get("gate_key", "")),
            str(entry.get("reviewer", "")),
            str(entry.get("created_at", "")),
            str(entry.get("reason", "")),
        ]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def normalize_waiver(entry: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "id": str(entry.get("id") or ""),
        "gate_key": str(entry.get("gate_key") or ""),
        "decision": str(entry.get("decision") or "accepted-risk"),
        "reviewer": str(entry.get("reviewer") or ""),
        "reason": str(entry.get("reason") or ""),
        "created_at": str(entry.get("created_at") or ""),
        "expires_at": str(entry.get("expires_at") or ""),
        "evidence": str(entry.get("evidence") or ""),
        "scope": str(entry.get("scope") or "current-release"),
    }
    normalized["id"] = normalized["id"] or waiver_id(normalized)
    return normalized


def add_waiver(existing: list[dict[str, Any]], args: argparse.Namespace, today: date) -> list[dict[str, Any]]:
    created_at = args.created_at or today.isoformat()
    entry = normalize_waiver(
        {
            "gate_key": args.gate_key,
            "decision": args.decision,
            "reviewer": args.reviewer,
            "reason": args.reason,
            "created_at": created_at,
            "expires_at": args.expires_at,
            "evidence": args.evidence or "",
            "scope": args.scope,
        }
    )
    return [*existing, entry]


def validate_waivers(waivers: list[dict[str, Any]], today: date) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    normalized = []
    failures = []
    warnings = []
    seen_ids = set()

    for index, raw in enumerate(waivers, start=1):
        entry = normalize_waiver(raw)
        entry_failures = []
        entry_warnings = []
        if entry["id"] in seen_ids:
            entry_failures.append("duplicate waiver id")
        seen_ids.add(entry["id"])
        if entry["gate_key"] not in KNOWN_GATE_KEYS:
            entry_failures.append(f"unknown gate_key: {entry['gate_key'] or '<empty>'}")
        if entry["decision"] not in VALID_DECISIONS:
            entry_failures.append(f"invalid decision: {entry['decision'] or '<empty>'}")
        if not entry["reviewer"]:
            entry_failures.append("reviewer is required")
        if len(entry["reason"]) < MIN_REASON_CHARS:
            entry_failures.append(f"reason must be at least {MIN_REASON_CHARS} characters")
        created_at = parse_date(entry["created_at"])
        if created_at is None:
            entry_failures.append("created_at must be ISO date")
        expires_at = parse_date(entry["expires_at"])
        if expires_at is None:
            entry_failures.append("expires_at must be ISO date")
        elif expires_at < today:
            entry_warnings.append("waiver is expired")
        entry["status"] = "invalid" if entry_failures else ("expired" if entry_warnings else "active")
        entry["validation"] = {"failures": entry_failures, "warnings": entry_warnings}
        normalized.append(entry)
        failures.extend([f"waiver {index} ({entry['id']}): {item}" for item in entry_failures])
        warnings.extend([f"waiver {index} ({entry['id']}): {item}" for item in entry_warnings])

    return normalized, failures, warnings


def output_lab_candidate(skill_dir: Path, covered_gate_keys: set[str], today: date) -> dict[str, Any] | None:
    output_quality = load_json(skill_dir / "reports" / "output_quality_scorecard.json").get("summary", {})
    output_execution = load_json(skill_dir / "reports" / "output_execution_runs.json").get("summary", {})
    output_review = load_json(skill_dir / "reports" / "output_review_adjudication.json").get("summary", {})
    if not output_quality and not output_execution and not output_review:
        return None
    pending = int(output_review.get("pending_count", 0) or 0)
    model_executed = int(output_execution.get("model_executed_count", 0) or 0)
    failure_count = int(output_quality.get("failure_count", 0) or 0)
    if pending == 0 and model_executed > 0 and failure_count == 0:
        return None
    status = "covered" if "output-lab" in covered_gate_keys else "needs-reviewer-decision"
    return {
        "gate_key": "output-lab",
        "label": "Output Lab",
        "status": status,
        "waiver_allowed": True,
        "decision_options": sorted(VALID_DECISIONS),
        "risk_summary": (
            f"review pending {pending}; model-executed {model_executed}; "
            f"output failures {failure_count}"
        ),
        "required_review": [
            "Reviewer confirms this release does not claim provider-backed or human-adjudicated output superiority.",
            "Reviewer names the release scope and expiry date.",
            "Reviewer links output_review_adjudication or output_execution evidence.",
        ],
        "suggested_evidence": "reports/output_review_adjudication.md",
        "suggested_command": (
            "python3 scripts/yao.py review-waivers . --add-waiver "
            "--gate-key output-lab --reviewer \"<reviewer>\" "
            "--reason \"Output Lab has pending human/provider evidence; accepted only for this bounded review scope.\" "
            f"--expires-at {(today + timedelta(days=365)).isoformat()} "
            "--evidence reports/output_review_adjudication.md"
        ),
        "world_class_boundary": "Does not count as provider, human, or public world-class completion evidence.",
    }


def world_class_boundary(skill_dir: Path) -> dict[str, Any] | None:
    ledger_summary = load_json(skill_dir / "reports" / "world_class_evidence_ledger.json").get("summary", {})
    if not ledger_summary:
        return None
    pending = int(ledger_summary.get("pending_count", 0) or 0)
    if pending == 0 and ledger_summary.get("ready_to_claim_world_class") is True:
        return None
    return {
        "gate_key": "world-class-evidence",
        "label": "World-Class Evidence",
        "status": "cannot-waive",
        "waiver_allowed": False,
        "risk_summary": (
            f"{pending} pending evidence entries; "
            f"{ledger_summary.get('human_pending_count', 0)} human pending; "
            f"{ledger_summary.get('external_pending_count', 0)} external pending"
        ),
        "required_review": [
            "Do not use a waiver to claim public world-class readiness.",
            "Either submit accepted ledger evidence or state that this release does not claim world-class completion.",
            "Keep claim guard active until ledger summary.ready_to_claim_world_class is true.",
        ],
        "suggested_evidence": "reports/world_class_evidence_ledger.md",
        "suggested_command": (
            "python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions "
            "&& python3 scripts/yao.py world-class-claim-guard ."
        ),
        "world_class_boundary": "Non-waivable completion boundary.",
    }


def build_waiver_candidates(skill_dir: Path, covered_gate_keys: list[str], today: date) -> list[dict[str, Any]]:
    covered = set(covered_gate_keys)
    candidates = []
    output_candidate = output_lab_candidate(skill_dir, covered, today)
    if output_candidate:
        candidates.append(output_candidate)
    world_boundary = world_class_boundary(skill_dir)
    if world_boundary:
        candidates.append(world_boundary)
    return candidates


def render_report(
    skill_dir: Path,
    waivers_json: Path | None = None,
    output_json: Path | None = None,
    output_md: Path | None = None,
    generated_at: str | None = None,
    add_args: argparse.Namespace | None = None,
) -> dict[str, Any]:
    skill_dir = skill_dir.resolve()
    reports = skill_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    output_json = output_json or reports / "review_waivers.json"
    output_md = output_md or reports / "review_waivers.md"
    source_json = waivers_json or output_json
    today = today_from(generated_at)
    payload = load_json(source_json)
    raw_waivers = payload.get("waivers", []) if isinstance(payload.get("waivers", []), list) else []
    if add_args is not None:
        raw_waivers = add_waiver(raw_waivers, add_args, today)
    waivers, failures, warnings = validate_waivers(raw_waivers, today)
    active = [item for item in waivers if item["status"] == "active"]
    expired = [item for item in waivers if item["status"] == "expired"]
    invalid = [item for item in waivers if item["status"] == "invalid"]
    covered_gate_keys = sorted({item["gate_key"] for item in active})
    waiver_candidates = build_waiver_candidates(skill_dir, covered_gate_keys, today)
    waiverable_open = [
        item for item in waiver_candidates if item["waiver_allowed"] and item["status"] != "covered"
    ]
    non_waivable = [item for item in waiver_candidates if not item["waiver_allowed"]]
    report = {
        "schema_version": "1.0",
        "ok": not failures,
        "skill_dir": display_path(skill_dir),
        "generated_at": generated_at or today.isoformat(),
        "summary": {
            "waiver_count": len(waivers),
            "active_count": len(active),
            "expired_count": len(expired),
            "invalid_count": len(invalid),
            "covered_gate_count": len(covered_gate_keys),
            "covered_gate_keys": covered_gate_keys,
            "waiver_candidate_count": len(waiver_candidates),
            "waiverable_open_count": len(waiverable_open),
            "non_waivable_count": len(non_waivable),
        },
        "policy": {
            "blocker_waivers_allowed": False,
            "minimum_reason_chars": MIN_REASON_CHARS,
            "expires_required": True,
            "review_studio_gate_keys": sorted(REVIEW_STUDIO_GATE_KEYS),
            "known_gate_keys": sorted(KNOWN_GATE_KEYS),
            "waiverable_gate_keys": sorted(WAIVERABLE_GATE_KEYS),
            "non_waivable_gate_keys": sorted(NON_WAIVABLE_GATE_KEYS),
        },
        "waivers": waivers,
        "waiver_candidates": waiver_candidates,
        "failures": failures,
        "warnings": warnings,
        "artifacts": {
            "json": display_path(output_json),
            "markdown": display_path(output_md),
        },
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Review Waivers",
        "",
        f"- OK: `{report['ok']}`",
        f"- Waivers: `{summary['waiver_count']}`",
        f"- Active: `{summary['active_count']}`",
        f"- Expired: `{summary['expired_count']}`",
        f"- Invalid: `{summary['invalid_count']}`",
        f"- Covered gates: `{', '.join(summary['covered_gate_keys']) or 'none'}`",
        f"- Waiver candidates: `{summary['waiver_candidate_count']}`",
        f"- Open waiverable candidates: `{summary['waiverable_open_count']}`",
        f"- Non-waivable boundaries: `{summary['non_waivable_count']}`",
        "",
        "## Policy",
        "",
        "- Blocker waivers allowed: `False`",
        f"- Minimum reason chars: `{report['policy']['minimum_reason_chars']}`",
        "- Expiry is required for every waiver.",
        "- World-class evidence completion cannot be waived; it can only be proven by accepted ledger evidence.",
        f"- Review Studio gates: `{', '.join(report['policy']['review_studio_gate_keys'])}`",
        f"- Waiverable gates: `{', '.join(report['policy']['waiverable_gate_keys'])}`",
        f"- Non-waivable gates: `{', '.join(report['policy']['non_waivable_gate_keys'])}`",
        "",
        "## Waivers",
        "",
    ]
    if not report["waivers"]:
        lines.append("- None")
    else:
        lines.extend(["| ID | Gate | Decision | Reviewer | Status | Expires | Reason |", "| --- | --- | --- | --- | --- | --- | --- |"])
        for item in report["waivers"]:
            reason = str(item["reason"]).replace("|", "\\|")
            lines.append(
                f"| `{item['id']}` | `{item['gate_key']}` | `{item['decision']}` | {item['reviewer']} | `{item['status']}` | `{item['expires_at']}` | {reason} |"
            )
    lines.extend(["", "## Candidate Actions", ""])
    candidates = report.get("waiver_candidates", [])
    if not candidates:
        lines.append("- None")
    else:
        lines.extend(["| Gate | Status | Waiver | Risk | Evidence |", "| --- | --- | --- | --- | --- |"])
        for item in candidates:
            risk = str(item.get("risk_summary", "")).replace("|", "\\|")
            lines.append(
                f"| `{item['gate_key']}` | `{item['status']}` | `{str(item['waiver_allowed']).lower()}` | {risk} | `{item.get('suggested_evidence', '')}` |"
            )
        for item in candidates:
            lines.extend(["", f"### {item['label']}", ""])
            lines.append(f"- gate: `{item['gate_key']}`")
            lines.append(f"- status: `{item['status']}`")
            lines.append(f"- waiver allowed: `{str(item['waiver_allowed']).lower()}`")
            lines.append(f"- risk: {item['risk_summary']}")
            lines.append(f"- evidence: `{item.get('suggested_evidence', '')}`")
            lines.append(f"- verification: `{item.get('suggested_command', '')}`")
            lines.append(f"- world-class boundary: {item.get('world_class_boundary', '')}")
            lines.extend(["", "#### Required Review", ""])
            lines.extend(f"- {review}" for review in item.get("required_review", []))
    lines.extend(["", "## Failures", ""])
    lines.extend([f"- {item}" for item in report["failures"]] or ["- None"])
    lines.extend(["", "## Warnings", ""])
    lines.extend([f"- {item}" for item in report["warnings"]] or ["- None"])
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render or update Review Studio waiver evidence.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--waivers-json")
    parser.add_argument("--output-json")
    parser.add_argument("--output-md")
    parser.add_argument("--generated-at")
    parser.add_argument("--add-waiver", action="store_true")
    parser.add_argument("--gate-key", choices=sorted(KNOWN_GATE_KEYS))
    parser.add_argument("--decision", choices=sorted(VALID_DECISIONS), default="accepted-risk")
    parser.add_argument("--reviewer")
    parser.add_argument("--reason")
    parser.add_argument("--expires-at")
    parser.add_argument("--created-at")
    parser.add_argument("--evidence")
    parser.add_argument("--scope", default="current-release")
    args = parser.parse_args()

    add_args = None
    if args.add_waiver:
        required = {
            "--gate-key": args.gate_key,
            "--reviewer": args.reviewer,
            "--reason": args.reason,
            "--expires-at": args.expires_at,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            print(json.dumps({"ok": False, "failures": [f"Missing required fields for --add-waiver: {', '.join(missing)}"]}, ensure_ascii=False, indent=2))
            raise SystemExit(2)
        add_args = args

    payload = render_report(
        Path(args.skill_dir),
        waivers_json=Path(args.waivers_json).resolve() if args.waivers_json else None,
        output_json=Path(args.output_json).resolve() if args.output_json else None,
        output_md=Path(args.output_md).resolve() if args.output_md else None,
        generated_at=args.generated_at,
        add_args=add_args,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if payload["ok"] else 2)


if __name__ == "__main__":
    main()
