#!/usr/bin/env python3
import argparse
import json
import shlex
from pathlib import Path
from typing import Any

from render_adoption_drift_report import (
    ALLOWED_ACTIVATION_TYPES,
    ALLOWED_EVENTS,
    ALLOWED_FAILURE_TYPES,
    ALLOWED_OUTCOMES,
    ALLOWED_SOURCES,
    display_path,
    normalize_event,
    skill_defaults,
)


def default_spool_path(skill_dir: Path) -> Path:
    return skill_dir / ".yao" / "telemetry_spool" / "external_events.jsonl"


def append_event(path: Path, event: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def import_command(skill_dir: Path, output_jsonl: Path) -> str:
    return shlex.join(
        [
            "python3",
            "scripts/yao.py",
            "telemetry-import",
            display_path(skill_dir),
            "--input-jsonl",
            display_path(output_jsonl),
        ]
    )


def emit_event(
    skill_dir: Path,
    output_jsonl: Path | None = None,
    event_name: str = "script_run",
    activation_type: str = "manual",
    outcome: str = "unknown",
    failure_type: str = "none",
    source: str = "external",
    command: str = "external-client",
    timestamp: str | None = None,
    skill_name: str | None = None,
    version: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    skill_dir = skill_dir.resolve()
    output_jsonl = (output_jsonl or default_spool_path(skill_dir)).resolve()
    raw_event: dict[str, Any] = {
        "event": event_name,
        "activation_type": activation_type,
        "outcome": outcome,
        "failure_type": failure_type,
        "source": source,
        "command": command,
    }
    if timestamp:
        raw_event["timestamp"] = timestamp
    if skill_name:
        raw_event["skill"] = skill_name
    if version:
        raw_event["version"] = version
    event, failures = normalize_event(raw_event, skill_defaults(skill_dir), "emit")
    if event and not failures and not dry_run:
        append_event(output_jsonl, event)
    return {
        "ok": not failures,
        "schema_version": "1.0",
        "skill_dir": display_path(skill_dir),
        "output_jsonl": display_path(output_jsonl),
        "dry_run": dry_run,
        "emitted": bool(event and not failures and not dry_run),
        "event": event or {},
        "failures": failures,
        "artifacts": {
            "spool_jsonl": display_path(output_jsonl),
            "import_command": import_command(skill_dir, output_jsonl),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit one metadata-only telemetry event for later import.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--output-jsonl")
    parser.add_argument("--event", choices=sorted(ALLOWED_EVENTS), default="script_run")
    parser.add_argument("--activation-type", choices=sorted(ALLOWED_ACTIVATION_TYPES), default="manual")
    parser.add_argument("--outcome", choices=sorted(ALLOWED_OUTCOMES), default="unknown")
    parser.add_argument("--failure-type", choices=sorted(ALLOWED_FAILURE_TYPES), default="none")
    parser.add_argument("--source", choices=sorted(ALLOWED_SOURCES), default="external")
    parser.add_argument("--command", default="external-client")
    parser.add_argument("--timestamp")
    parser.add_argument("--skill-name")
    parser.add_argument("--version")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    report = emit_event(
        Path(args.skill_dir),
        output_jsonl=Path(args.output_jsonl) if args.output_jsonl else None,
        event_name=args.event,
        activation_type=args.activation_type,
        outcome=args.outcome,
        failure_type=args.failure_type,
        source=args.source,
        command=args.command,
        timestamp=args.timestamp,
        skill_name=args.skill_name,
        version=args.version,
        dry_run=args.dry_run,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
