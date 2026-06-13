#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "registry_audit.py"


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_registry"
    tmp_root.mkdir(parents=True, exist_ok=True)
    output_json = tmp_root / "registry_audit.json"
    output_md = tmp_root / "registry_audit.md"
    registry_dir = tmp_root / "registry"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(ROOT),
            "--registry-dir",
            str(registry_dir),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
            "--generated-at",
            "2026-06-13",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    package = payload["package"]
    assert payload["ok"], payload
    assert payload["schema_version"] == "2.0", payload
    assert package["name"] == "yao-meta-skill", package
    assert package["version"] == "1.1.0", package
    assert package["license"] == "MIT", package
    assert package["checksums"]["package_sha256"], package
    assert package["source"]["ir_schema_version"] == "2.0.0", package
    assert "distribution" in package, package
    if (ROOT / "reports" / "package_verification.json").exists():
        assert package["distribution"]["archive_verified"], package
        assert package["checksums"]["archive_sha256"], package
    if (ROOT / "reports" / "install_simulation.json").exists():
        assert package["distribution"]["install_simulated"], package
        assert package["artifacts"]["install_simulation"].endswith("reports/install_simulation.md"), package
    if (ROOT / "reports" / "adoption_drift_report.json").exists():
        assert package["artifacts"]["adoption_drift"].endswith("reports/adoption_drift_report.md"), package
    if (ROOT / "reports" / "review_waivers.json").exists():
        assert package["artifacts"]["review_waivers"].endswith("reports/review_waivers.md"), package
    if (ROOT / "reports" / "compiled_targets.json").exists():
        assert package["artifacts"]["compiled_targets"].endswith("reports/compiled_targets.md"), package
    assert package["compatibility"]["openai"] == "pass", package
    assert package["compatibility"]["claude"] == "pass", package
    assert package["compatibility"]["generic"] == "pass", package
    assert package["compatibility"]["vscode"] == "pass", package
    assert (registry_dir / "index.json").exists(), registry_dir
    assert (registry_dir / "packages" / "yao-meta-skill.json").exists(), registry_dir
    assert output_json.exists(), output_json
    assert output_md.exists(), output_md
    assert "Registry Audit" in output_md.read_text(encoding="utf-8")

    broken = tmp_root / "broken-registry-skill"
    (broken / "reports").mkdir(parents=True, exist_ok=True)
    (broken / "agents").mkdir(parents=True, exist_ok=True)
    (broken / "SKILL.md").write_text(
        "---\nname: broken-registry-skill\ndescription: Broken registry fixture.\n---\n\n# Broken\n",
        encoding="utf-8",
    )
    (broken / "manifest.json").write_text(json.dumps({"name": "broken-registry-skill"}, indent=2), encoding="utf-8")
    (broken / "agents" / "interface.yaml").write_text(
        "interface:\n  display_name: Broken\n  short_description: Broken\n  default_prompt: Broken\ncompatibility:\n  adapter_targets: [generic]\n  trust:\n    source_tier: local\n",
        encoding="utf-8",
    )
    broken_proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(broken),
            "--registry-dir",
            str(tmp_root / "broken-registry"),
            "--output-json",
            str(tmp_root / "broken.json"),
            "--output-md",
            str(tmp_root / "broken.md"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert broken_proc.returncode == 2, broken_proc.stdout
    broken_payload = json.loads(broken_proc.stdout)
    assert not broken_payload["ok"], broken_payload
    assert any("version" in item for item in broken_payload["failures"]), broken_payload
    assert any("checksum" in item for item in broken_payload["failures"]), broken_payload

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
