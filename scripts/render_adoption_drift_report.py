#!/usr/bin/env python3
import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent

ALLOWED_EVENTS = {"skill_activation", "skill_output", "script_run", "review_event"}
ADOPTION_EVENTS = {"skill_activation", "skill_output"}
ALLOWED_ACTIVATION_TYPES = {"implicit", "explicit", "manual", "unknown"}
ALLOWED_OUTCOMES = {"accepted", "edited", "rejected", "missed", "failed", "reviewed", "unknown"}
ALLOWED_FAILURE_TYPES = {
    "none",
    "wrong_trigger",
    "under_trigger",
    "bad_output",
    "missing_resource",
    "script_error",
    "review_overdue",
}
ALLOWED_FIELDS = {
    "command",
    "event",
    "skill",
    "source",
    "version",
    "activation_type",
    "outcome",
    "failure_type",
    "timestamp",
}
ALLOWED_SOURCES = {"manual", "yao_cli", "external", "unknown"}
SENSITIVE_FIELDS = {
    "prompt",
    "content",
    "input",
    "inputs",
    "output",
    "outputs",
    "transcript",
    "message",
    "messages",
    "note",
    "text",
    "raw",
}


def display_path(path: Path, root: Path = ROOT) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
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


def read_frontmatter(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    data: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def skill_defaults(skill_dir: Path) -> dict[str, str]:
    manifest = load_json(skill_dir / "manifest.json")
    frontmatter = read_frontmatter(skill_dir / "SKILL.md")
    return {
        "skill": str(manifest.get("name") or frontmatter.get("name") or skill_dir.name),
        "version": str(manifest.get("version") or frontmatter.get("version") or "0.0.0"),
    }


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_event(raw: dict[str, Any], defaults: dict[str, str], line_label: str) -> tuple[dict[str, str] | None, list[str]]:
    failures: list[str] = []
    raw_keys = set(raw.keys())
    sensitive = sorted(raw_keys & SENSITIVE_FIELDS)
    if sensitive:
        failures.append(f"{line_label}: raw content fields are not allowed in telemetry: {', '.join(sensitive)}")
    unknown = sorted(raw_keys - ALLOWED_FIELDS - SENSITIVE_FIELDS)
    if unknown:
        failures.append(f"{line_label}: unknown telemetry fields are blocked by the metadata-only contract: {', '.join(unknown)}")

    event = str(raw.get("event") or "skill_activation")
    activation_type = str(raw.get("activation_type") or "unknown")
    outcome = str(raw.get("outcome") or "unknown")
    failure_type = str(raw.get("failure_type") or "none")
    timestamp = str(raw.get("timestamp") or utc_now())
    skill = str(raw.get("skill") or defaults["skill"])
    version = str(raw.get("version") or defaults["version"])
    source = str(raw.get("source") or "manual")
    command = str(raw.get("command") or "unknown")

    if event not in ALLOWED_EVENTS:
        failures.append(f"{line_label}: unsupported event `{event}`")
    if activation_type not in ALLOWED_ACTIVATION_TYPES:
        failures.append(f"{line_label}: unsupported activation_type `{activation_type}`")
    if outcome not in ALLOWED_OUTCOMES:
        failures.append(f"{line_label}: unsupported outcome `{outcome}`")
    if failure_type not in ALLOWED_FAILURE_TYPES:
        failures.append(f"{line_label}: unsupported failure_type `{failure_type}`")
    if source not in ALLOWED_SOURCES:
        failures.append(f"{line_label}: unsupported source `{source}`")
    if not command.replace("-", "").replace("_", "").isalnum() or len(command) > 64:
        failures.append(f"{line_label}: command must use only letters, numbers, hyphens, or underscores and stay under 64 chars")

    if failures:
        return None, failures
    return {
        "command": command,
        "event": event,
        "skill": skill,
        "source": source,
        "version": version,
        "activation_type": activation_type,
        "outcome": outcome,
        "failure_type": failure_type,
        "timestamp": timestamp,
    }, []


def load_events(path: Path, defaults: dict[str, str]) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        return [], []
    events: list[dict[str, str]] = []
    failures: list[str] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            failures.append(f"line {index}: invalid JSONL event: {exc.msg}")
            continue
        if not isinstance(raw, dict):
            failures.append(f"line {index}: telemetry event must be a JSON object")
            continue
        event, event_failures = normalize_event(raw, defaults, f"line {index}")
        failures.extend(event_failures)
        if event:
            events.append(event)
    return events, failures


def append_event(path: Path, event: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def adoption_by_skill(events: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    adoption_grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for event in events:
        skill = event["skill"]
        grouped[skill]["events"] += 1
        if event["event"] in ADOPTION_EVENTS:
            adoption_grouped[skill][event["outcome"]] += 1
    rows = []
    for skill, counts in sorted(grouped.items()):
        adoption_counts = adoption_grouped[skill]
        adoption_total = sum(adoption_counts.values())
        adopted = adoption_counts["accepted"] + adoption_counts["edited"]
        rows.append(
            {
                "skill": skill,
                "events": counts["events"],
                "adoption_events": adoption_total,
                "accepted": adoption_counts["accepted"],
                "edited": adoption_counts["edited"],
                "rejected": adoption_counts["rejected"],
                "missed": adoption_counts["missed"],
                "adoption_rate": round(adopted / adoption_total * 100, 1) if adoption_total else 0,
            }
        )
    return rows


def atlas_review_overdue(skill_dir: Path) -> int:
    atlas = load_json(skill_dir / "reports" / "skill_atlas.json")
    stale = atlas.get("stale_skills", []) if isinstance(atlas.get("stale_skills"), list) else []
    return sum(
        1
        for item in stale
        if item.get("actionable", True) and "overdue" in str(item.get("reason", "")).lower()
    )


def next_candidates(summary: dict[str, Any]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    if summary["event_count"] == 0:
        candidates.append(
            {
                "signal": "no telemetry",
                "recommendation": "Start with a small metadata-only sample before using telemetry for release decisions.",
            }
        )
    if summary["missed_trigger_count"]:
        candidates.append(
            {
                "signal": "missed trigger",
                "recommendation": "Add missed prompts to trigger eval and tighten should-trigger examples.",
            }
        )
    if summary["wrong_trigger_count"]:
        candidates.append(
            {
                "signal": "wrong trigger",
                "recommendation": "Add near-neighbor should-not-trigger cases and clarify exclusions.",
            }
        )
    if summary["bad_output_count"]:
        candidates.append(
            {
                "signal": "bad output",
                "recommendation": "Convert the failed output shape into an Output Eval assertion and failure taxonomy entry.",
            }
        )
    if summary["script_error_count"]:
        candidates.append(
            {
                "signal": "script error",
                "recommendation": "Add non-interactive script smoke tests and clearer error paths.",
            }
        )
    if summary["review_overdue_count"]:
        candidates.append(
            {
                "signal": "review overdue",
                "recommendation": "Prioritize stale governed skills in Skill Atlas before creating more assets.",
            }
        )
    return candidates[:6]


def summarize(events: list[dict[str, str]], review_overdue_count: int) -> dict[str, Any]:
    adoption_events = [event for event in events if event["event"] in ADOPTION_EVENTS]
    outcomes = Counter(event["outcome"] for event in adoption_events)
    failures = Counter(event["failure_type"] for event in events if event["failure_type"] != "none")
    event_types = Counter(event["event"] for event in events)
    source_types = Counter(event.get("source", "manual") for event in events)
    command_counts = Counter(event.get("command", "unknown") for event in events if event.get("command", "unknown") != "unknown")
    adopted = outcomes["accepted"] + outcomes["edited"]
    event_count = len(events)
    adoption_sample_count = len(adoption_events)
    missed_trigger = outcomes["missed"] + failures["under_trigger"]
    bad_output = failures["bad_output"]
    script_error = failures["script_error"]
    wrong_trigger = failures["wrong_trigger"]
    risk_band = "no-data"
    if event_count:
        risk_points = missed_trigger + bad_output + script_error + wrong_trigger + review_overdue_count
        if risk_points >= 4:
            risk_band = "high"
        elif risk_points:
            risk_band = "medium"
        else:
            risk_band = "low"
    return {
        "event_count": event_count,
        "adoption_sample_count": adoption_sample_count,
        "activation_count": event_types["skill_activation"],
        "accepted_count": outcomes["accepted"],
        "edited_count": outcomes["edited"],
        "rejected_count": outcomes["rejected"],
        "missed_count": outcomes["missed"],
        "failed_count": outcomes["failed"],
        "adoption_rate": round(adopted / adoption_sample_count * 100, 1) if adoption_sample_count else 0,
        "missed_trigger_count": missed_trigger,
        "wrong_trigger_count": wrong_trigger,
        "bad_output_count": bad_output,
        "script_error_count": script_error,
        "missing_resource_count": failures["missing_resource"],
        "review_overdue_count": review_overdue_count + failures["review_overdue"],
        "risk_band": risk_band,
        "event_types": dict(sorted(event_types.items())),
        "failure_types": dict(sorted(failures.items())),
        "source_types": dict(sorted(source_types.items())),
        "command_counts": dict(sorted(command_counts.items())),
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Adoption And Drift Report",
        "",
        "Local-first, metadata-only telemetry for skill operations. Raw prompts, outputs, transcripts, and notes are not allowed in the event stream.",
        "",
        "## Summary",
        "",
        f"- Events: `{summary['event_count']}`",
        f"- Adoption samples: `{summary['adoption_sample_count']}`",
        f"- Activation events: `{summary['activation_count']}`",
        f"- Adoption rate: `{summary['adoption_rate']}`",
        f"- Missed trigger signals: `{summary['missed_trigger_count']}`",
        f"- Bad output signals: `{summary['bad_output_count']}`",
        f"- Script error signals: `{summary['script_error_count']}`",
        f"- Review overdue signals: `{summary['review_overdue_count']}`",
        f"- Risk band: `{summary['risk_band']}`",
        "",
        "## Privacy Contract",
        "",
        "- Storage is local-first.",
        "- Events are metadata-only.",
        "- Raw user prompts, model outputs, transcripts, notes, and messages are blocked.",
        "- Distributed packages should include this aggregate report, not raw `reports/telemetry_events.jsonl`.",
        "",
        "## Adoption By Skill",
        "",
        "| Skill | Events | Adoption Samples | Accepted | Edited | Rejected | Missed | Adoption Rate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report["adoption_by_skill"]:
        lines.append(
            f"| `{row['skill']}` | {row['events']} | {row['adoption_events']} | {row['accepted']} | {row['edited']} | "
            f"{row['rejected']} | {row['missed']} | {row['adoption_rate']} |"
        )
    if not report["adoption_by_skill"]:
        lines.append("| `none` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |")
    lines.extend(["", "## Next Iteration Candidates", ""])
    for item in report["next_iteration_candidates"]:
        lines.append(f"- `{item['signal']}`: {item['recommendation']}")
    if not report["next_iteration_candidates"]:
        lines.append("- No telemetry-driven iteration candidate yet.")
    lines.extend(["", "## Recent Metadata Events", ""])
    for event in report["recent_events"]:
        lines.append(
            f"- `{event['timestamp']}` `{event['skill']}` event=`{event['event']}` "
            f"source=`{event.get('source', 'manual')}` command=`{event.get('command', 'unknown')}` "
            f"activation=`{event['activation_type']}` outcome=`{event['outcome']}` failure=`{event['failure_type']}`"
        )
    if not report["recent_events"]:
        lines.append("- No metadata events captured yet.")
    if report["failures"]:
        lines.extend(["", "## Validation Failures", ""])
        lines.extend([f"- {item}" for item in report["failures"]])
    return "\n".join(lines) + "\n"


def render_report(
    skill_dir: Path,
    events_jsonl: Path | None = None,
    output_json: Path | None = None,
    output_md: Path | None = None,
    generated_at: str | None = None,
    record_event: dict[str, Any] | None = None,
) -> dict[str, Any]:
    skill_dir = skill_dir.resolve()
    reports_dir = skill_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    defaults = skill_defaults(skill_dir)
    events_jsonl = events_jsonl or reports_dir / "telemetry_events.jsonl"
    output_json = output_json or reports_dir / "adoption_drift_report.json"
    output_md = output_md or reports_dir / "adoption_drift_report.md"
    generated_at = generated_at or utc_now()
    failures: list[str] = []

    if record_event is not None:
        event, event_failures = normalize_event(record_event, defaults, "record")
        failures.extend(event_failures)
        if event:
            append_event(events_jsonl, event)

    events, load_failures = load_events(events_jsonl, defaults)
    failures.extend(load_failures)
    summary = summarize(events, atlas_review_overdue(skill_dir))
    report = {
        "ok": not failures,
        "schema_version": "2.0",
        "generated_at": generated_at,
        "skill_dir": display_path(skill_dir),
        "privacy_contract": {
            "storage": "local-first",
            "event_scope": "metadata-only",
            "raw_content_allowed": False,
            "raw_event_log_packaged": False,
            "blocked_fields": sorted(SENSITIVE_FIELDS),
        },
        "summary": summary,
        "adoption_by_skill": adoption_by_skill(events),
        "next_iteration_candidates": next_candidates(summary),
        "recent_events": events[-10:],
        "failures": failures,
        "artifacts": {
            "events_jsonl": display_path(events_jsonl),
            "json": display_path(output_json),
            "markdown": display_path(output_md),
        },
    }
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Render local-first adoption and drift telemetry for a skill package.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--events-jsonl")
    parser.add_argument("--output-json")
    parser.add_argument("--output-md")
    parser.add_argument("--generated-at")
    parser.add_argument("--record-event", choices=sorted(ALLOWED_EVENTS))
    parser.add_argument("--activation-type", choices=sorted(ALLOWED_ACTIVATION_TYPES), default="unknown")
    parser.add_argument("--outcome", choices=sorted(ALLOWED_OUTCOMES), default="unknown")
    parser.add_argument("--failure-type", choices=sorted(ALLOWED_FAILURE_TYPES), default="none")
    parser.add_argument("--source", choices=sorted(ALLOWED_SOURCES), default="manual")
    parser.add_argument("--command", default="unknown")
    parser.add_argument("--timestamp")
    parser.add_argument("--skill-name")
    parser.add_argument("--version")
    args = parser.parse_args()

    record_event = None
    if args.record_event:
        record_event = {
            "event": args.record_event,
            "activation_type": args.activation_type,
            "outcome": args.outcome,
            "failure_type": args.failure_type,
            "source": args.source,
            "command": args.command,
        }
        if args.timestamp:
            record_event["timestamp"] = args.timestamp
        if args.skill_name:
            record_event["skill"] = args.skill_name
        if args.version:
            record_event["version"] = args.version

    report = render_report(
        Path(args.skill_dir),
        events_jsonl=Path(args.events_jsonl).resolve() if args.events_jsonl else None,
        output_json=Path(args.output_json).resolve() if args.output_json else None,
        output_md=Path(args.output_md).resolve() if args.output_md else None,
        generated_at=args.generated_at,
        record_event=record_event,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
