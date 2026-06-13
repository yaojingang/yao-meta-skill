#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path
import yaml


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "cross_packager.py"
TRUST_SCRIPT = ROOT / "scripts" / "trust_check.py"
EXPECTATIONS = ROOT / "evals" / "packaging_expectations.json"
SNAPSHOTS = ROOT / "tests" / "snapshots"
TMP = ROOT / "tests" / "tmp_snapshot"


def main() -> None:
    if TMP.exists():
        shutil.rmtree(TMP)
    trust_proc = subprocess.run(
        [sys.executable, str(TRUST_SCRIPT), str(ROOT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if trust_proc.returncode != 0:
        print(trust_proc.stdout)
        print(trust_proc.stderr)
        raise SystemExit(trust_proc.returncode)
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(ROOT),
            "--platform",
            "openai",
            "--platform",
            "claude",
            "--platform",
            "generic",
            "--platform",
            "vscode",
            "--expectations",
            str(EXPECTATIONS),
            "--output-dir",
            str(TMP),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        raise SystemExit(proc.returncode)

    failures = []
    for name in ("openai", "claude", "generic", "vscode"):
        snapshot = json.loads((SNAPSHOTS / f"{name}_adapter.json").read_text(encoding="utf-8"))
        adapter = json.loads((TMP / "targets" / name / "adapter.json").read_text(encoding="utf-8"))
        if adapter.get("platform") != snapshot["platform"]:
            failures.append(f"{name}: platform mismatch")
        if adapter.get("canonical_metadata") != snapshot["canonical_metadata"]:
            failures.append(f"{name}: canonical metadata mismatch")
        for field in snapshot.get("required_fields", []):
            if field not in adapter:
                failures.append(f"{name}: missing required adapter field {field}")
        if adapter.get("ir_source") != "skill-ir/examples/yao-meta-skill.json":
            failures.append(f"{name}: adapter is not sourced from root Skill IR")
        if adapter.get("ir_schema_version") != "2.0.0":
            failures.append(f"{name}: missing Skill IR schema version")
        contract = adapter.get("semantic_contract", {})
        if contract.get("name") != "yao-meta-skill":
            failures.append(f"{name}: semantic contract name mismatch")
        if contract.get("trigger_description") != adapter.get("description"):
            failures.append(f"{name}: trigger description is not adapter description")
        if contract.get("job_to_be_done") != adapter.get("job_to_be_done"):
            failures.append(f"{name}: job-to-be-done not carried into adapter")
        if contract.get("resource_counts", {}).get("references", 0) <= 0:
            failures.append(f"{name}: semantic contract does not include reference counts")
        if contract.get("eval_counts", {}).get("output", 0) <= 0:
            failures.append(f"{name}: semantic contract does not include output eval counts")
        parity = adapter.get("semantic_parity", {})
        if parity.get("source") != "skill-ir":
            failures.append(f"{name}: semantic parity source is not skill-ir")
        if parity.get("name_matches_ir") is not True:
            failures.append(f"{name}: frontmatter name does not match Skill IR")
        if parity.get("description_matches_ir") is not True:
            failures.append(f"{name}: frontmatter description does not match Skill IR")
        compiler = adapter.get("compiler", {})
        if compiler.get("name") != "yao-skill-ir-compiler":
            failures.append(f"{name}: missing compiler provenance")
        compiled = adapter.get("compiled_contract", {})
        if compiled.get("target") != name:
            failures.append(f"{name}: compiled contract target mismatch")
        if compiled.get("trigger", {}).get("description") != adapter.get("description"):
            failures.append(f"{name}: compiled trigger description is not adapter description")
        permission = adapter.get("permission_contract", {})
        if permission.get("source") != "reports/security_trust_report.json":
            failures.append(f"{name}: permission contract is not sourced from trust report")
        if "file_write" not in permission.get("declared_capabilities", []):
            failures.append(f"{name}: permission contract does not carry file_write capability")
        if permission.get("help_smoke", {}).get("failed_count") != 0:
            failures.append(f"{name}: permission contract reports help smoke failures")
        target_permission = adapter.get("target_permission_contract", {})
        if target_permission.get("target") != name:
            failures.append(f"{name}: target permission contract target mismatch")
        if not target_permission.get("representation"):
            failures.append(f"{name}: target permission contract lacks representation")
        if target_permission.get("capability_counts", {}).get("file_write", 0) <= 0:
            failures.append(f"{name}: target permission contract lacks file_write count")
        native = adapter.get("target_native_contract", {})
        if native.get("target") != name:
            failures.append(f"{name}: target native contract target mismatch")
        if not native.get("native_surface"):
            failures.append(f"{name}: target native contract lacks native surface")
        if not native.get("activation", {}).get("policy"):
            failures.append(f"{name}: target native contract lacks activation policy")
        if not native.get("resources", {}).get("strategy"):
            failures.append(f"{name}: target native contract lacks resource strategy")
        if not native.get("scripts", {}).get("strategy"):
            failures.append(f"{name}: target native contract lacks script strategy")
        if not native.get("permissions", {}).get("enforcement"):
            failures.append(f"{name}: target native contract lacks permission enforcement")
        if not native.get("review", {}).get("artifacts"):
            failures.append(f"{name}: target native contract lacks review artifacts")
        transform = adapter.get("target_transform", {})
        if transform.get("target") != name:
            failures.append(f"{name}: target transform target mismatch")
        if not transform.get("generated_files"):
            failures.append(f"{name}: target transform does not declare generated files")
        if not transform.get("permission_representation"):
            failures.append(f"{name}: target transform does not declare permission representation")
        if transform.get("native_surface") != native.get("native_surface"):
            failures.append(f"{name}: target transform native surface does not match native contract")
        if transform.get("activation_policy") != native.get("activation", {}).get("policy"):
            failures.append(f"{name}: target transform activation policy does not match native contract")
        if not (TMP / snapshot["required_generated_file"]).exists():
            failures.append(f"{name}: missing generated file {snapshot['required_generated_file']}")
        if name == "openai":
            meta = yaml.safe_load((TMP / "targets" / "openai" / "agents" / "openai.yaml").read_text(encoding="utf-8")) or {}
            compatibility = meta.get("compatibility", {})
            for field in ("canonical_format", "activation_mode", "execution_context", "shell", "trust_level", "remote_inline_execution", "degradation_strategy"):
                if not compatibility.get(field):
                    failures.append(f"{name}: missing portability metadata in generated openai.yaml: {field}")
            yaml_permission = compatibility.get("permission_contract", {})
            if "file_write" not in yaml_permission.get("declared_capabilities", []):
                failures.append(f"{name}: generated openai.yaml does not carry permission capabilities")
            native_yaml = compatibility.get("native_contract", {})
            if native_yaml.get("native_surface") != native.get("native_surface"):
                failures.append(f"{name}: generated openai.yaml does not carry native surface")
        if name == "claude":
            readme = (TMP / "targets" / "claude" / "README.md").read_text(encoding="utf-8")
            if "Native surface:" not in readme or "Activation:" not in readme:
                failures.append(f"{name}: generated README does not describe native behavior")
        if name == "vscode":
            readme = (TMP / "targets" / "vscode" / "README.md").read_text(encoding="utf-8")
            if "VS Code / Copilot Agent Skills Package" not in readme or "workspace trust" not in readme:
                failures.append(f"{name}: generated README does not describe VS Code install and trust behavior")

    report = {"ok": not failures, "failures": failures}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
