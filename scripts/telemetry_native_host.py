#!/usr/bin/env python3
import argparse
import json
import os
import shlex
import stat
import struct
import sys
from pathlib import Path
from typing import Any, BinaryIO

from emit_telemetry_event import append_event, default_spool_path
from render_adoption_drift_report import display_path, normalize_event, skill_defaults


SCHEMA_VERSION = "1.0"
DEFAULT_HOST_NAME = "com.yao.meta_skill.telemetry"
DEFAULT_DESCRIPTION = "Yao metadata-only telemetry native messaging host"
SKILL_DIR_ENV = "YAO_TELEMETRY_SKILL_DIR"
EVENTS_ENV = "YAO_TELEMETRY_EVENTS"
MAX_MESSAGE_BYTES = 1024 * 1024


def read_native_message(stream: BinaryIO) -> dict[str, Any] | None:
    header = stream.read(4)
    if not header:
        return None
    if len(header) != 4:
        raise ValueError("native message header must be exactly 4 bytes")
    size = struct.unpack("<I", header)[0]
    if size > MAX_MESSAGE_BYTES:
        raise ValueError(f"native message is too large: {size} bytes")
    payload = stream.read(size)
    if len(payload) != size:
        raise ValueError("native message payload ended before declared length")
    message = json.loads(payload.decode("utf-8"))
    if not isinstance(message, dict):
        raise ValueError("native message must be a JSON object")
    return message


def write_native_message(stream: BinaryIO, payload: dict[str, Any]) -> None:
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    stream.write(struct.pack("<I", len(data)))
    stream.write(data)
    stream.flush()


def emit_native_message(
    skill_dir: Path,
    output_jsonl: Path,
    raw_message: dict[str, Any],
    dry_run: bool = False,
) -> dict[str, Any]:
    raw = dict(raw_message)
    raw.setdefault("source", "external")
    raw.setdefault("command", "native-messaging-host")
    event, failures = normalize_event(raw, skill_defaults(skill_dir), "native-host-message")
    if event and not failures and not dry_run:
        append_event(output_jsonl, event)
    return {
        "ok": not failures,
        "schema_version": SCHEMA_VERSION,
        "mode": "native-messaging-host",
        "skill_dir": display_path(skill_dir),
        "output_jsonl": display_path(output_jsonl),
        "dry_run": dry_run,
        "emitted": bool(event and not failures and not dry_run),
        "event": event or {},
        "failures": failures,
    }


def write_launcher(path: Path, host_script: Path, skill_dir: Path, output_jsonl: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    script = "\n".join(
        [
            "#!/bin/sh",
            "set -eu",
            (
                "exec python3 "
                f"{shlex.quote(str(host_script.resolve()))} "
                f"{shlex.quote(str(skill_dir.resolve()))} "
                "--stdio "
                f"--output-jsonl {shlex.quote(str(output_jsonl.resolve()))}"
            ),
            "",
        ]
    )
    path.write_text(script, encoding="utf-8")
    current = path.stat().st_mode
    path.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def write_manifest(
    manifest_path: Path,
    host_name: str,
    description: str,
    host_path: Path,
    allowed_origins: list[str],
) -> dict[str, Any]:
    failures: list[str] = []
    if not allowed_origins:
        failures.append("At least one --allowed-origin is required for a Chrome native messaging manifest.")
    for origin in allowed_origins:
        if not origin.startswith("chrome-extension://") or not origin.endswith("/"):
            failures.append(f"Unsupported Chrome extension origin: {origin}")
    if not host_path.exists():
        failures.append(f"Native host path does not exist: {host_path}")
    elif not os.access(host_path, os.X_OK):
        failures.append(f"Native host path must be executable: {host_path}")
    manifest = {
        "name": host_name,
        "description": description,
        "path": str(host_path.resolve()),
        "type": "stdio",
        "allowed_origins": allowed_origins,
    }
    if not failures:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": not failures,
        "schema_version": SCHEMA_VERSION,
        "manifest": manifest,
        "manifest_path": display_path(manifest_path),
        "failures": failures,
    }


def run_stdio(skill_dir: Path, output_jsonl: Path, dry_run: bool) -> int:
    while True:
        raw = read_native_message(sys.stdin.buffer)
        if raw is None:
            return 0
        response = emit_native_message(skill_dir, output_jsonl, raw, dry_run=dry_run)
        write_native_message(sys.stdout.buffer, response)


def env_default(name: str, fallback: str) -> str:
    return os.environ.get(name) or fallback


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a metadata-only telemetry native messaging host.")
    parser.add_argument("skill_dir", nargs="?", default=env_default(SKILL_DIR_ENV, "."))
    parser.add_argument("--output-jsonl", default=os.environ.get(EVENTS_ENV))
    parser.add_argument("--message-json", help="Emit one JSON object directly, useful for host smoke tests.")
    parser.add_argument("--stdio", action="store_true", help="Use Chrome/Browser Native Messaging length-prefixed stdio.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write-manifest")
    parser.add_argument("--write-launcher")
    parser.add_argument("--host-name", default=DEFAULT_HOST_NAME)
    parser.add_argument("--description", default=DEFAULT_DESCRIPTION)
    parser.add_argument("--allowed-origin", action="append", default=[])
    parser.add_argument("--host-path")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    output_jsonl = Path(args.output_jsonl).resolve() if args.output_jsonl else default_spool_path(skill_dir).resolve()
    host_script = Path(__file__).resolve()

    launcher_path = Path(args.write_launcher).resolve() if args.write_launcher else None
    if launcher_path:
        write_launcher(launcher_path, host_script, skill_dir, output_jsonl)

    if args.write_manifest:
        host_path = Path(args.host_path).resolve() if args.host_path else launcher_path or host_script
        report = write_manifest(
            Path(args.write_manifest).resolve(),
            args.host_name,
            args.description,
            host_path,
            args.allowed_origin,
        )
        if launcher_path:
            report["launcher_path"] = display_path(launcher_path)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if not report["ok"]:
            raise SystemExit(2)
        return

    if args.stdio:
        try:
            raise SystemExit(run_stdio(skill_dir, output_jsonl, args.dry_run))
        except Exception as exc:
            write_native_message(
                sys.stdout.buffer,
                {
                    "ok": False,
                    "schema_version": SCHEMA_VERSION,
                    "mode": "native-messaging-host",
                    "emitted": False,
                    "failures": [str(exc)],
                },
            )
            raise SystemExit(2)

    if args.message_json:
        try:
            message = json.loads(args.message_json)
        except json.JSONDecodeError as exc:
            print(json.dumps({"ok": False, "failures": [f"Invalid --message-json: {exc.msg}"]}, ensure_ascii=False, indent=2))
            raise SystemExit(2)
        if not isinstance(message, dict):
            print(json.dumps({"ok": False, "failures": ["--message-json must decode to a JSON object"]}, ensure_ascii=False, indent=2))
            raise SystemExit(2)
        report = emit_native_message(skill_dir, output_jsonl, message, dry_run=args.dry_run)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if not report["ok"]:
            raise SystemExit(2)
        return

    print(
        json.dumps(
            {
                "ok": False,
                "schema_version": SCHEMA_VERSION,
                "failures": ["Use --message-json, --stdio, or --write-manifest."],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    raise SystemExit(2)


if __name__ == "__main__":
    main()
