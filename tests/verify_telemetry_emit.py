#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TMP = ROOT / "tests" / "tmp_telemetry_emit"
EMITTER = ROOT / "scripts" / "emit_telemetry_event.py"
YAO = ROOT / "scripts" / "yao.py"


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


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "init_skill.py"),
            "telemetry-emit-demo",
            "--description",
            "Emit metadata-only telemetry from an external client hook for later adoption drift import.",
            "--output-dir",
            str(TMP),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    skill_dir = TMP / "telemetry-emit-demo"
    spool = TMP / "external-spool.jsonl"

    emitted = run(
        [
            sys.executable,
            str(EMITTER),
            str(skill_dir),
            "--output-jsonl",
            str(spool),
            "--event",
            "skill_activation",
            "--activation-type",
            "explicit",
            "--outcome",
            "accepted",
            "--failure-type",
            "none",
            "--command",
            "browser-extension",
            "--timestamp",
            "2026-06-13T12:00:00Z",
        ]
    )
    assert emitted["ok"], emitted
    assert emitted["payload"]["emitted"] is True, emitted
    assert emitted["payload"]["artifacts"]["spool_jsonl"].endswith("external-spool.jsonl"), emitted
    assert "telemetry-import" in emitted["payload"]["artifacts"]["import_command"], emitted
    events = read_jsonl(spool)
    assert len(events) == 1, events
    assert events[0]["event"] == "skill_activation", events
    assert events[0]["source"] == "external", events
    assert events[0]["command"] == "browser-extension", events

    dry_run = run(
        [
            sys.executable,
            str(EMITTER),
            str(skill_dir),
            "--output-jsonl",
            str(spool),
            "--event",
            "script_run",
            "--outcome",
            "failed",
            "--failure-type",
            "script_error",
            "--command",
            "browser-extension",
            "--dry-run",
        ]
    )
    assert dry_run["ok"], dry_run
    assert dry_run["payload"]["dry_run"] is True, dry_run
    assert dry_run["payload"]["emitted"] is False, dry_run
    assert len(read_jsonl(spool)) == 1, read_jsonl(spool)

    invalid = run(
        [
            sys.executable,
            str(EMITTER),
            str(skill_dir),
            "--output-jsonl",
            str(spool),
            "--command",
            "bad/path",
        ]
    )
    assert invalid["returncode"] == 2, invalid
    assert "command must use only" in "\n".join(invalid["payload"]["failures"]), invalid
    assert len(read_jsonl(spool)) == 1, read_jsonl(spool)

    cli_emit = run(
        [
            sys.executable,
            str(YAO),
            "telemetry-emit",
            str(skill_dir),
            "--output-jsonl",
            str(spool),
            "--event",
            "skill_output",
            "--activation-type",
            "manual",
            "--outcome",
            "edited",
            "--command",
            "browser-plugin",
            "--timestamp",
            "2026-06-13T12:01:00Z",
        ]
    )
    assert cli_emit["ok"], cli_emit
    assert cli_emit["payload"]["emitted"] is True, cli_emit
    assert len(read_jsonl(spool)) == 2, read_jsonl(spool)

    imported = run(
        [
            sys.executable,
            str(YAO),
            "telemetry-import",
            str(skill_dir),
            "--input-jsonl",
            str(spool),
            "--generated-at",
            "2026-06-13T12:02:00Z",
        ]
    )
    assert imported["ok"], imported
    assert imported["payload"]["imported_count"] == 2, imported
    assert imported["payload"]["adoption_drift"]["summary"]["event_count"] == 2, imported
    assert imported["payload"]["adoption_drift"]["summary"]["source_types"]["external"] == 2, imported
    assert imported["payload"]["adoption_drift"]["summary"]["command_counts"]["browser-extension"] == 1, imported
    assert imported["payload"]["adoption_drift"]["summary"]["command_counts"]["browser-plugin"] == 1, imported

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
