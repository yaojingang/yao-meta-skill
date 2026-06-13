#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "compile_skill.py"
TRUST_SCRIPT = ROOT / "scripts" / "trust_check.py"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=check,
    )


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_compile_skill"
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    tmp_root.mkdir(parents=True, exist_ok=True)
    output_json = tmp_root / "compiled_targets.json"
    output_md = tmp_root / "compiled_targets.md"
    subprocess.run(
        [sys.executable, str(TRUST_SCRIPT), str(ROOT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    proc = run(
        str(ROOT),
        "--target",
        "openai",
        "--target",
        "claude",
        "--target",
        "generic",
        "--target",
        "vscode",
        "--output-json",
        str(output_json),
        "--output-md",
        str(output_md),
        "--generated-at",
        "2026-06-13",
    )
    payload = json.loads(proc.stdout)
    assert payload["ok"], payload
    assert payload["schema_version"] == "1.0", payload
    assert payload["summary"]["target_count"] == 4, payload
    assert payload["summary"]["pass_count"] == 4, payload
    assert output_json.exists(), output_json
    assert output_md.exists(), output_md
    assert "Compiled Targets" in output_md.read_text(encoding="utf-8")
    by_target = {item["target"]: item for item in payload["targets"]}
    for target in ("openai", "claude", "generic", "vscode"):
        item = by_target[target]
        assert item["compiler"]["name"] == "yao-skill-ir-compiler", item
        assert item["compiler"]["source"] == "skill-ir", item
        assert item["compiled_contract"]["name"] == "yao-meta-skill", item
        assert item["compiled_contract"]["target"] == target, item
        assert item["compiled_contract"]["trigger"]["description"], item
        assert item["compiled_contract"]["resources"]["counts"]["references"] > 0, item
        assert item["compiled_contract"]["eval_plan"]["counts"]["output"] > 0, item
        assert item["compiled_contract"]["permissions"]["source"] == "reports/security_trust_report.json", item
        assert "file_write" in item["compiled_contract"]["permissions"]["declared_capabilities"], item
        assert item["compiled_contract"]["target_permission_contract"]["target"] == target, item
        assert item["compiled_contract"]["target_permission_contract"]["representation"], item
        assert item["permission_contract"]["help_smoke"]["failed_count"] == 0, item
        assert item["target_permission_contract"]["target"] == target, item
        assert item["target_permission_contract"]["capability_counts"]["file_write"] > 0, item
        native = item["target_native_contract"]
        assert native["target"] == target, item
        assert native["native_surface"], item
        assert native["activation"]["policy"], item
        assert native["resources"]["strategy"], item
        assert native["scripts"]["strategy"], item
        assert native["permissions"]["enforcement"], item
        assert native["review"]["artifacts"], item
        assert item["compiled_contract"]["target_native_contract"]["target"] == target, item
        assert item["target_transform"]["generated_files"], item
        assert item["target_transform"]["metadata_mapping"], item
        assert item["target_transform"]["permission_representation"], item
        assert item["target_transform"]["native_surface"] == native["native_surface"], item
        assert item["target_transform"]["activation_policy"] == native["activation"]["policy"], item

    unsupported = run(str(ROOT), "--target", "unsupported-target", "--output-json", str(tmp_root / "bad.json"), "--output-md", str(tmp_root / "bad.md"), check=False)
    bad_payload = json.loads(unsupported.stdout)
    assert unsupported.returncode == 2, unsupported.stdout
    assert not bad_payload["ok"], bad_payload
    assert bad_payload["summary"]["block_count"] == 1, bad_payload
    assert bad_payload["failures"], bad_payload

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
