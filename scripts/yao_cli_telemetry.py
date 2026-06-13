#!/usr/bin/env python3
"""Metadata-only CLI telemetry helpers for yao.py."""

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from render_adoption_drift_report import append_event, normalize_event, skill_defaults, utc_now


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by yao.py to record opt-in metadata-only CLI run telemetry."

ENABLE_ENV = "YAO_CLI_TELEMETRY"
EVENTS_ENV = "YAO_CLI_TELEMETRY_EVENTS"
TRUTHY = {"1", "true", "yes", "on"}
FALSY = {"0", "false", "no", "off"}


def add_telemetry_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--record-cli-telemetry",
        action="store_true",
        help="Record metadata-only yao.py command telemetry to reports/telemetry_events.jsonl.",
    )
    parser.add_argument(
        "--no-cli-telemetry",
        action="store_true",
        help="Disable yao.py command telemetry even when YAO_CLI_TELEMETRY is enabled.",
    )
    parser.add_argument(
        "--telemetry-events-jsonl",
        help="Override the local metadata-only telemetry JSONL path.",
    )


def telemetry_enabled(args: argparse.Namespace, environ: dict[str, str] | None = None) -> bool:
    environ = environ or os.environ
    if getattr(args, "no_cli_telemetry", False):
        return False
    if getattr(args, "record_cli_telemetry", False):
        return True
    raw = environ.get(ENABLE_ENV, "").strip().lower()
    if raw in TRUTHY:
        return True
    if raw in FALSY:
        return False
    return False


def telemetry_path(root: Path, args: argparse.Namespace, environ: dict[str, str] | None = None) -> Path:
    environ = environ or os.environ
    configured = getattr(args, "telemetry_events_jsonl", None) or environ.get(EVENTS_ENV)
    if configured:
        return Path(configured).expanduser().resolve()
    return root / "reports" / "telemetry_events.jsonl"


def normalize_command_name(value: Any) -> str:
    raw = str(value or "unknown")
    lowered = raw.strip().lower()
    safe = "".join(char for char in lowered if char.isalnum() or char in {"-", "_"})
    return safe[:64] or "unknown"


def cli_event(root: Path, args: argparse.Namespace, returncode: int) -> dict[str, str]:
    defaults = skill_defaults(root)
    ok = returncode == 0
    return {
        "event": "script_run",
        "skill": defaults["skill"],
        "version": defaults["version"],
        "activation_type": "manual",
        "outcome": "accepted" if ok else "failed",
        "failure_type": "none" if ok else "script_error",
        "timestamp": utc_now(),
        "source": "yao_cli",
        "command": normalize_command_name(getattr(args, "command", "unknown")),
    }


def maybe_record_cli_event(root: Path, args: argparse.Namespace, returncode: int) -> None:
    if not telemetry_enabled(args):
        return
    path = telemetry_path(root, args)
    event, failures = normalize_event(cli_event(root, args, returncode), skill_defaults(root), "yao-cli")
    if failures or event is None:
        sys.stderr.write(f"Telemetry skipped: {'; '.join(failures)}\n")
        return
    try:
        append_event(path, event)
    except OSError as exc:
        sys.stderr.write(f"Telemetry skipped: {exc}\n")
