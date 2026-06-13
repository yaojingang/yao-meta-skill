#!/usr/bin/env python3
import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TMP = ROOT / "tests" / "tmp_telemetry_native_host"
HOST = ROOT / "scripts" / "telemetry_native_host.py"
YAO = ROOT / "scripts" / "yao.py"
ORIGIN = "chrome-extension://aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/"


def run(cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    payload = json.loads(proc.stdout) if proc.stdout.strip() else {}
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "payload": payload,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def pack_message(payload: dict) -> bytes:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return struct.pack("<I", len(data)) + data


def unpack_messages(data: bytes) -> list[dict]:
    messages = []
    offset = 0
    while offset < len(data):
        size = struct.unpack("<I", data[offset : offset + 4])[0]
        offset += 4
        payload = data[offset : offset + size]
        offset += size
        messages.append(json.loads(payload.decode("utf-8")))
    return messages


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "init_skill.py"),
            "telemetry-native-host-demo",
            "--description",
            "Receive metadata-only telemetry events from a Browser native messaging host.",
            "--output-dir",
            str(TMP),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    skill_dir = TMP / "telemetry-native-host-demo"
    spool = TMP / "native-spool.jsonl"

    valid = run(
        [
            sys.executable,
            str(HOST),
            str(skill_dir),
            "--output-jsonl",
            str(spool),
            "--message-json",
            json.dumps(
                {
                    "event": "skill_activation",
                    "activation_type": "explicit",
                    "outcome": "accepted",
                    "failure_type": "none",
                    "command": "chrome-native-host",
                }
            ),
        ]
    )
    assert valid["ok"], valid
    assert valid["payload"]["emitted"] is True, valid
    events = read_jsonl(spool)
    assert len(events) == 1, events
    assert events[0]["command"] == "chrome-native-host", events
    assert events[0]["source"] == "external", events

    invalid = run(
        [
            sys.executable,
            str(HOST),
            str(skill_dir),
            "--output-jsonl",
            str(spool),
            "--message-json",
            json.dumps(
                {
                    "event": "skill_activation",
                    "activation_type": "explicit",
                    "outcome": "accepted",
                    "failure_type": "none",
                    "command": "chrome-native-host",
                    "prompt": "raw prompt must not pass through native host",
                }
            ),
        ]
    )
    assert invalid["returncode"] == 2, invalid
    assert "raw content fields" in "\n".join(invalid["payload"]["failures"]), invalid
    assert len(read_jsonl(spool)) == 1, read_jsonl(spool)

    stdio_payload = pack_message(
        {
            "event": "skill_output",
            "activation_type": "manual",
            "outcome": "edited",
            "failure_type": "none",
            "command": "browser-native-host",
        }
    )
    stdio = subprocess.run(
        [
            sys.executable,
            str(HOST),
            str(skill_dir),
            "--output-jsonl",
            str(spool),
            "--stdio",
        ],
        cwd=ROOT,
        input=stdio_payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert stdio.returncode == 0, stdio.stderr
    responses = unpack_messages(stdio.stdout)
    assert len(responses) == 1, responses
    assert responses[0]["ok"], responses
    assert responses[0]["emitted"] is True, responses
    assert len(read_jsonl(spool)) == 2, read_jsonl(spool)

    manifest = TMP / "native-host-manifest.json"
    launcher = TMP / "yao-telemetry-native-host.sh"
    manifest_result = run(
        [
            sys.executable,
            str(HOST),
            str(skill_dir),
            "--output-jsonl",
            str(spool),
            "--write-launcher",
            str(launcher),
            "--write-manifest",
            str(manifest),
            "--allowed-origin",
            ORIGIN,
        ]
    )
    assert manifest_result["ok"], manifest_result
    assert manifest.exists(), manifest
    assert launcher.exists(), launcher
    assert launcher.stat().st_mode & 0o111, launcher.stat().st_mode
    manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest_payload["name"] == "com.yao.meta_skill.telemetry", manifest_payload
    assert manifest_payload["type"] == "stdio", manifest_payload
    assert manifest_payload["path"] == str(launcher.resolve()), manifest_payload
    assert manifest_payload["allowed_origins"] == [ORIGIN], manifest_payload

    manifest_without_launcher = TMP / "native-host-manifest-without-launcher.json"
    manifest_without_launcher_result = run(
        [
            sys.executable,
            str(HOST),
            str(skill_dir),
            "--write-manifest",
            str(manifest_without_launcher),
            "--allowed-origin",
            ORIGIN,
        ]
    )
    assert manifest_without_launcher_result["returncode"] == 2, manifest_without_launcher_result
    assert not manifest_without_launcher.exists(), manifest_without_launcher
    assert "must be executable" in "\n".join(manifest_without_launcher_result["payload"]["failures"])

    imported = run(
        [
            sys.executable,
            str(YAO),
            "telemetry-import",
            str(skill_dir),
            "--input-jsonl",
            str(spool),
            "--generated-at",
            "2026-06-13T12:30:00Z",
        ]
    )
    assert imported["ok"], imported
    assert imported["payload"]["imported_count"] == 2, imported
    assert imported["payload"]["adoption_drift"]["summary"]["source_types"]["external"] == 2, imported
    assert imported["payload"]["adoption_drift"]["summary"]["command_counts"]["chrome-native-host"] == 1, imported
    assert imported["payload"]["adoption_drift"]["summary"]["command_counts"]["browser-native-host"] == 1, imported

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
