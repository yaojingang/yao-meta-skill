#!/usr/bin/env python3
import argparse
import json
import shutil
import zipfile
from pathlib import Path
import yaml

from compile_skill import compile_target_contract


def display_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def read_simple_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def read_frontmatter(skill_md: Path) -> dict:
    if not skill_md.exists():
        raise FileNotFoundError(f"Missing required file: {skill_md}")
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    return yaml.safe_load(parts[1]) or {}


def read_interface(skill_dir: Path) -> dict:
    path = skill_dir / "agents" / "interface.yaml"
    if not path.exists():
        return {}
    raw = read_simple_yaml(path)
    return raw


def find_skill_ir(skill_dir: Path, name: str) -> tuple[dict, str]:
    candidates = [
        skill_dir / "reports" / "skill-ir.json",
        skill_dir / "skill-ir" / "examples" / f"{name}.json",
        skill_dir / "skill-ir" / "examples" / f"{skill_dir.name}.json",
    ]
    seen = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        payload = read_json(path)
        if payload:
            return payload, display_path(path, skill_dir)
    return {}, "frontmatter-fallback"


def require_fields(payload: dict, fields: list[str], label: str) -> None:
    missing = [field for field in fields if not payload.get(field)]
    if missing:
        raise ValueError(f"Missing required {label} fields: {', '.join(missing)}")


def require_target_degradation(
    degradation: dict,
    targets: list[str],
) -> None:
    missing = [target for target in targets if not degradation.get(target)]
    if missing:
        raise ValueError(f"Missing degradation entries for targets: {', '.join(missing)}")


def count_list(payload: dict, key: str) -> int:
    value = payload.get(key, [])
    return len(value) if isinstance(value, list) else 0


def resource_counts(resources: dict) -> dict:
    return {
        "references": count_list(resources, "references"),
        "scripts": count_list(resources, "scripts"),
        "assets": count_list(resources, "assets"),
        "reports": count_list(resources, "reports"),
    }


def eval_counts(eval_plan: dict) -> dict:
    return {
        "trigger": count_list(eval_plan, "trigger"),
        "output": count_list(eval_plan, "output"),
        "adversarial": count_list(eval_plan, "adversarial"),
        "baseline": 1 if eval_plan.get("baseline") else 0,
    }


def build_semantic_contract(
    *,
    skill_dir: Path,
    platform: str,
    frontmatter: dict,
    interface: dict,
    compatibility: dict,
    manifest: dict,
    ir: dict,
    ir_source: str,
) -> dict:
    trigger_surface = ir.get("trigger_surface", {}) if isinstance(ir.get("trigger_surface"), dict) else {}
    workflow = ir.get("workflow", {}) if isinstance(ir.get("workflow"), dict) else {}
    resources = ir.get("resources", {}) if isinstance(ir.get("resources"), dict) else {}
    eval_plan = ir.get("eval_plan", {}) if isinstance(ir.get("eval_plan"), dict) else {}

    frontmatter_name = str(frontmatter.get("name") or manifest.get("name") or skill_dir.name)
    frontmatter_description = str(frontmatter.get("description") or "")
    ir_name = str(ir.get("name") or "") if ir else ""
    ir_description = str(trigger_surface.get("description") or "") if ir else ""
    name = ir_name or frontmatter_name
    description = ir_description or frontmatter_description
    job = str(ir.get("job_to_be_done") or description)
    targets = ir.get("targets") if isinstance(ir.get("targets"), list) else compatibility.get("adapter_targets", [])
    target_values = [str(item) for item in targets]
    adapter_targets = [str(item) for item in compatibility.get("adapter_targets", [])]

    semantic_contract = {
        "name": name,
        "description": description,
        "job_to_be_done": job,
        "trigger_description": description,
        "should_trigger_count": count_list(trigger_surface, "should_trigger"),
        "should_not_trigger_count": count_list(trigger_surface, "should_not_trigger"),
        "edge_case_count": count_list(trigger_surface, "edge_cases"),
        "workflow_step_count": count_list(workflow, "steps"),
        "decision_point_count": count_list(workflow, "decision_points"),
        "failure_mode_count": count_list(workflow, "failure_modes"),
        "resource_counts": resource_counts(resources),
        "eval_counts": eval_counts(eval_plan),
        "risk": ir.get("risk", {}) if isinstance(ir.get("risk"), dict) else {},
        "governance": ir.get("governance", {}) if isinstance(ir.get("governance"), dict) else {},
        "targets": target_values,
        "source_files_count": count_list(ir, "source_files") if ir else 0,
    }
    alias_declared = (
        platform in {"agent-skills", "vscode"} and "agent-skills-compatible" in target_values
    )
    semantic_parity = {
        "source": "skill-ir" if ir else "frontmatter-fallback",
        "ir_source": ir_source,
        "name_matches_ir": bool(ir) and frontmatter_name == name,
        "description_matches_ir": bool(ir) and frontmatter_description == description,
        "platform_declared_in_ir": platform in target_values
        or (platform == "generic" and "agent-skills-compatible" in target_values)
        or alias_declared,
        "platform_declared_in_interface": platform in adapter_targets,
        "display_name_present": bool(interface.get("display_name")),
        "default_prompt_present": bool(interface.get("default_prompt")),
    }
    return {
        "name": name,
        "description": description,
        "job_to_be_done": job,
        "ir_source": ir_source,
        "ir_schema_version": str(ir.get("schema_version") or "none"),
        "semantic_contract": semantic_contract,
        "semantic_parity": semantic_parity,
    }


def build_manifest(skill_dir: Path, platform: str) -> dict:
    frontmatter = read_frontmatter(skill_dir / "SKILL.md")
    manifest = read_json(skill_dir / "manifest.json")
    interface_doc = read_interface(skill_dir)
    interface = interface_doc.get("interface", {})
    compatibility = interface_doc.get("compatibility", {})
    activation = compatibility.get("activation", {})
    execution = compatibility.get("execution", {})
    trust = compatibility.get("trust", {})
    degradation = compatibility.get("degradation", {})
    require_fields(frontmatter, ["name", "description"], "frontmatter")
    require_fields(interface, ["display_name", "short_description", "default_prompt"], "interface")
    require_fields(compatibility, ["canonical_format", "adapter_targets"], "compatibility")
    require_fields(activation, ["mode"], "compatibility.activation")
    require_fields(execution, ["context", "shell"], "compatibility.execution")
    require_fields(
        trust,
        ["source_tier", "remote_inline_execution", "remote_metadata_policy"],
        "compatibility.trust",
    )
    require_target_degradation(degradation, compatibility.get("adapter_targets", []))
    ir, ir_source = find_skill_ir(skill_dir, str(frontmatter.get("name") or manifest.get("name") or skill_dir.name))
    semantic = build_semantic_contract(
        skill_dir=skill_dir,
        platform=platform,
        frontmatter=frontmatter,
        interface=interface,
        compatibility=compatibility,
        manifest=manifest,
        ir=ir,
        ir_source=ir_source,
    )
    compiled = compile_target_contract(skill_dir, platform)
    if compiled.get("failures"):
        raise ValueError(f"Compiler failed for {platform}: {'; '.join(compiled['failures'])}")
    return {
        "name": semantic["name"],
        "description": semantic["description"],
        "version": manifest.get("version") or frontmatter.get("version", "1.0.0"),
        "platform": platform,
        "skill_root": skill_dir.name,
        "job_to_be_done": semantic["job_to_be_done"],
        "ir_source": semantic["ir_source"],
        "ir_schema_version": semantic["ir_schema_version"],
        "semantic_contract": semantic["semantic_contract"],
        "semantic_parity": semantic["semantic_parity"],
        "compiler": compiled["compiler"],
        "compiled_contract": compiled["compiled_contract"],
        "permission_contract": compiled["permission_contract"],
        "target_permission_contract": compiled["target_permission_contract"],
        "target_native_contract": compiled["target_native_contract"],
        "target_transform": compiled["target_transform"],
        "unsupported_features": compiled["unsupported_features"],
        "compiler_warnings": compiled["warnings"],
        "display_name": interface.get("display_name", skill_dir.name),
        "short_description": interface.get("short_description", ""),
        "default_prompt": interface.get("default_prompt", ""),
        "canonical_metadata": "agents/interface.yaml",
        "canonical_format": compatibility.get("canonical_format", "agent-skills"),
        "adapter_targets": compatibility.get("adapter_targets", []),
        "activation_mode": activation.get("mode", "manual"),
        "activation_paths": activation.get("paths", []),
        "execution_context": execution.get("context", "inline"),
        "shell": execution.get("shell", "bash"),
        "trust_level": trust.get("source_tier", "local"),
        "remote_inline_execution": trust.get("remote_inline_execution", "forbid"),
        "remote_metadata_policy": trust.get("remote_metadata_policy", "allow-metadata-only"),
        "degradation_strategy": degradation.get(platform, "neutral-source"),
        "portability_profile": {
            "activation_mode": activation.get("mode", "manual"),
            "activation_paths": activation.get("paths", []),
            "execution_context": execution.get("context", "inline"),
            "shell": execution.get("shell", "bash"),
            "source_tier": trust.get("source_tier", "local"),
            "remote_inline_execution": trust.get("remote_inline_execution", "forbid"),
            "remote_metadata_policy": trust.get("remote_metadata_policy", "allow-metadata-only"),
            "degradation_strategy": degradation.get(platform, "neutral-source"),
        },
    }


PLATFORM_CONTRACTS = {
    "openai": {
        "required_fields": [
            "name",
            "description",
            "version",
            "display_name",
            "short_description",
            "default_prompt",
            "job_to_be_done",
            "ir_source",
            "ir_schema_version",
            "semantic_contract",
            "semantic_parity",
            "canonical_metadata",
            "canonical_format",
            "activation_mode",
            "execution_context",
            "shell",
            "trust_level",
            "remote_inline_execution",
            "degradation_strategy",
            "portability_profile",
            "permission_contract",
            "target_permission_contract",
            "target_native_contract",
        ],
        "required_files": ["targets/openai/adapter.json", "targets/openai/agents/openai.yaml"],
        "field_mapping": {
            "display_name": "interface.display_name",
            "short_description": "interface.short_description",
            "default_prompt": "interface.default_prompt",
            "execution_context": "compatibility.execution.context",
            "shell": "compatibility.execution.shell",
        },
    },
    "claude": {
        "required_fields": [
            "name",
            "description",
            "version",
            "display_name",
            "short_description",
            "default_prompt",
            "job_to_be_done",
            "ir_source",
            "ir_schema_version",
            "semantic_contract",
            "semantic_parity",
            "canonical_metadata",
            "canonical_format",
            "activation_mode",
            "execution_context",
            "shell",
            "trust_level",
            "remote_inline_execution",
            "degradation_strategy",
            "portability_profile",
            "permission_contract",
            "target_permission_contract",
            "target_native_contract",
        ],
        "required_files": ["targets/claude/adapter.json", "targets/claude/README.md"],
        "field_mapping": {
            "display_name": "adapter.display_name",
            "short_description": "adapter.short_description",
            "default_prompt": "adapter.default_prompt",
            "execution_context": "compatibility.execution.context",
            "shell": "compatibility.execution.shell",
        },
    },
    "generic": {
        "required_fields": [
            "name",
            "description",
            "version",
            "display_name",
            "short_description",
            "default_prompt",
            "job_to_be_done",
            "ir_source",
            "ir_schema_version",
            "semantic_contract",
            "semantic_parity",
            "canonical_metadata",
            "canonical_format",
            "activation_mode",
            "execution_context",
            "shell",
            "trust_level",
            "remote_inline_execution",
            "degradation_strategy",
            "portability_profile",
            "permission_contract",
            "target_permission_contract",
            "target_native_contract",
        ],
        "required_files": ["targets/generic/adapter.json"],
        "field_mapping": {
            "display_name": "adapter.display_name",
            "short_description": "adapter.short_description",
            "default_prompt": "adapter.default_prompt",
            "execution_context": "compatibility.execution.context",
            "shell": "compatibility.execution.shell",
        },
    },
    "vscode": {
        "required_fields": [
            "name",
            "description",
            "version",
            "display_name",
            "short_description",
            "default_prompt",
            "job_to_be_done",
            "ir_source",
            "ir_schema_version",
            "semantic_contract",
            "semantic_parity",
            "compiler",
            "compiled_contract",
            "permission_contract",
            "target_permission_contract",
            "target_native_contract",
            "target_transform",
            "canonical_metadata",
            "canonical_format",
            "activation_mode",
            "execution_context",
            "shell",
            "trust_level",
            "remote_inline_execution",
            "degradation_strategy",
            "portability_profile",
        ],
        "required_files": ["targets/vscode/adapter.json", "targets/vscode/README.md"],
        "field_mapping": {
            "name": "SKILL.md::frontmatter.name and folder name",
            "description": "SKILL.md::frontmatter.description",
            "display_name": "agents/interface.yaml::interface.display_name",
            "execution_context": "compatibility.execution.context",
            "permissions": "adapter.target_permission_contract",
        },
    },
}

EXCLUDED_ARCHIVE_PARTS = {".git", "__pycache__", ".venv", "venv", "node_modules", "dist"}


def should_skip_archive_path(rel_path: Path) -> bool:
    parts = rel_path.parts
    if any(part in EXCLUDED_ARCHIVE_PARTS for part in parts):
        return True
    if parts == ("reports", "telemetry_events.jsonl"):
        return True
    if parts and parts[0] == "tests" and any(part.startswith("tmp") for part in parts[1:]):
        return True
    return False


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def write_yaml_file(path: Path, payload: dict) -> None:
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def safe_output_dir(skill_dir: Path, requested_output_dir: Path, cwd: Path) -> Path:
    skill_dir = skill_dir.resolve()
    cwd = cwd.resolve()
    requested_output_dir = requested_output_dir.expanduser()
    candidate = requested_output_dir if requested_output_dir.is_absolute() else cwd / requested_output_dir
    if candidate.is_symlink():
        raise ValueError(f"Refusing symlink output directory: {candidate}")
    out_dir = candidate.resolve()
    home = Path.home().resolve()
    filesystem_root = Path(out_dir.anchor).resolve()

    dangerous_exact = {filesystem_root, home, cwd, skill_dir, skill_dir.parent.resolve()}
    if out_dir in dangerous_exact or out_dir in skill_dir.parents:
        raise ValueError(f"Refusing dangerous output directory: {out_dir}")
    if out_dir.exists() and not out_dir.is_dir():
        raise ValueError(f"Output path exists but is not a directory: {out_dir}")
    if not (is_relative_to(out_dir, cwd) or is_relative_to(out_dir, skill_dir)):
        raise ValueError(f"Output directory must stay under the current workspace or skill directory: {out_dir}")
    return out_dir


def write_adapter(skill_dir: Path, out_dir: Path, platform: str) -> Path:
    target_dir = out_dir / "targets" / platform
    target_dir.mkdir(parents=True, exist_ok=True)
    if platform not in PLATFORM_CONTRACTS:
        raise ValueError(f"Unsupported platform: {platform}")
    payload = build_manifest(skill_dir, platform)
    if platform == "openai":
        meta_dir = target_dir / "agents"
        meta_dir.mkdir(parents=True, exist_ok=True)
        write_yaml_file(
            meta_dir / "openai.yaml",
            {
                "interface": {
                    "display_name": payload["display_name"],
                    "short_description": payload["short_description"],
                    "default_prompt": payload["default_prompt"],
                },
                "compatibility": {
                    "canonical_format": payload["canonical_format"],
                    "activation_mode": payload["activation_mode"],
                    "execution_context": payload["execution_context"],
                    "shell": payload["shell"],
                    "trust_level": payload["trust_level"],
                    "remote_inline_execution": payload["remote_inline_execution"],
                    "permission_contract": {
                        "review_required": payload["target_permission_contract"]["review_required"],
                        "declared_capabilities": payload["target_permission_contract"]["declared_capabilities"],
                        "native_enforcement": payload["target_permission_contract"]["native_enforcement"],
                        "representation": payload["target_permission_contract"]["representation"],
                    },
                    "native_contract": {
                        "native_surface": payload["target_native_contract"]["native_surface"],
                        "activation_policy": payload["target_native_contract"]["activation"]["policy"],
                        "resource_strategy": payload["target_native_contract"]["resources"]["strategy"],
                        "permission_enforcement": payload["target_native_contract"]["permissions"]["enforcement"],
                        "review_artifacts": payload["target_native_contract"]["review"]["artifacts"],
                    },
                    "degradation_strategy": payload["degradation_strategy"],
                },
            },
        )
        payload["install_hint"] = f"Use the packaged skill and include targets/openai/agents/openai.yaml when the client expects OpenAI-style interface metadata."
    elif platform == "claude":
        notes = target_dir / "README.md"
        native = payload["target_native_contract"]
        notes.write_text(
            f"# Claude-Compatible Package\n\nUse `{skill_dir.name}` with its neutral source files. This target does not require vendor metadata by default.\n\n"
            f"Native surface: {native['native_surface']}.\n\n"
            f"Activation: {native['activation']['policy']}\n\n"
            f"Resources: {native['resources']['strategy']}\n\n"
            f"Scripts: {native['scripts']['strategy']}\n\n"
            f"Permission metadata is preserved in `adapter.json` under `target_permission_contract` and `target_native_contract` for reviewer visibility.\n",
            encoding="utf-8",
        )
        payload["install_hint"] = f"Use the packaged skill directly; this target relies on SKILL.md and optional neutral metadata."
    elif platform == "vscode":
        notes = target_dir / "README.md"
        native = payload["target_native_contract"]
        notes.write_text(
            f"# VS Code / Copilot Agent Skills Package\n\n"
            f"Install `{skill_dir.name}` as a VS Code user or project scoped Agent Skill. Keep the folder name aligned with `SKILL.md` frontmatter name.\n\n"
            f"Native surface: {native['native_surface']}.\n\n"
            f"Activation: {native['activation']['policy']}\n\n"
            f"Resources: {native['resources']['strategy']}\n\n"
            f"Scripts: {native['scripts']['strategy']}\n\n"
            f"Permission model: {payload['target_permission_contract']['permission_model']}. "
            "Review `target_permission_contract`, workspace trust, and `reports/security_trust_report.md` before running scripts.\n\n"
            "This adapter does not perform automatic VS Code installation; it preserves the reviewed source package plus install notes.\n",
            encoding="utf-8",
        )
        payload["install_hint"] = (
            "Install the package as a VS Code user or project scoped Agent Skill; use targets/vscode/README.md for scope and trust notes."
        )
    else:
        payload["install_hint"] = f"Use {skill_dir.name} as an Agent Skills compatible package."
    path = target_dir / "adapter.json"
    payload["contract"] = PLATFORM_CONTRACTS.get(platform, PLATFORM_CONTRACTS["generic"])
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def make_zip(skill_dir: Path, out_dir: Path) -> Path:
    zip_path = out_dir / f"{skill_dir.name}.zip"
    skill_root = skill_dir.resolve()
    out_root = out_dir.resolve()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in skill_dir.rglob("*"):
            if path.is_symlink() or not path.is_file():
                continue
            resolved = path.resolve()
            if not is_relative_to(resolved, skill_root):
                continue
            if is_relative_to(resolved, out_root):
                continue
            rel_path = path.relative_to(skill_dir)
            if should_skip_archive_path(rel_path):
                continue
            zf.write(path, arcname=str(path.relative_to(skill_dir.parent)))
    return zip_path


def copy_manifest(skill_dir: Path, out_dir: Path) -> Path:
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(build_manifest(skill_dir, "generic"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest_path


def load_expectations(path: Path | None) -> dict:
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def validate_exports(out_dir: Path, expectations: dict) -> dict:
    failures = []
    required_targets = expectations.get("required_targets", [])
    required_fields = expectations.get("required_fields", [])
    required_by_target = {
        key[: -len("_required_files")]: value
        for key, value in expectations.items()
        if key.endswith("_required_files")
    }

    for target in required_targets:
        adapter_path = out_dir / "targets" / target / "adapter.json"
        if not adapter_path.exists():
            failures.append(f"missing adapter for target: {target}")
            continue
        payload = json.loads(adapter_path.read_text(encoding="utf-8"))
        for field in required_fields:
            if field not in payload:
                failures.append(f"missing field '{field}' in {adapter_path.relative_to(out_dir)}")
        for rel in required_by_target.get(target, []):
            if not (out_dir / rel).exists():
                failures.append(f"missing file: {rel}")
    return {"ok": not failures, "failures": failures}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate lightweight cross-platform packaging artifacts.")
    parser.add_argument("skill_dir", help="Path to the skill directory")
    parser.add_argument("--platform", action="append", default=[], help="Target platform: openai, claude, generic, vscode")
    parser.add_argument("--output-dir", default="dist", help="Output directory")
    parser.add_argument("--expectations", help="JSON file describing packaging expectations")
    parser.add_argument("--zip", action="store_true", help="Create a zip package")
    args = parser.parse_args()

    generated = []
    failures = []
    try:
        skill_dir = Path(args.skill_dir).resolve()
        out_dir = safe_output_dir(skill_dir, Path(args.output_dir), Path.cwd())
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True)
        manifest = copy_manifest(skill_dir, out_dir)
        generated.append(str(manifest))
        for platform in (args.platform or ["generic"]):
            generated.append(str(write_adapter(skill_dir, out_dir, platform)))
        if args.zip:
            generated.append(str(make_zip(skill_dir, out_dir)))
    except (FileNotFoundError, ValueError, yaml.YAMLError) as exc:
        failures.append(str(exc))

    expectations = load_expectations(Path(args.expectations).resolve()) if args.expectations else {}
    validation = validate_exports(out_dir, expectations) if expectations and not failures else None
    report = {
        "output_dir": str(out_dir) if "out_dir" in locals() else str(Path(args.output_dir).resolve()),
        "generated": generated,
        "contracts": PLATFORM_CONTRACTS,
        "validation": validation,
        "failure_handling": {
            "missing_required_file": "exit with code 2 when expectations are provided and validation fails",
            "missing_required_field": "exit with code 2 when expectations are provided and validation fails",
            "invalid_yaml_or_frontmatter": "exit with code 2 when parsing fails",
            "unsupported_platform": "exit with code 2 when the platform is not defined in PLATFORM_CONTRACTS",
        },
        "failures": failures,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if failures or (validation and not validation["ok"]):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
