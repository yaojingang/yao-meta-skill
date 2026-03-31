#!/usr/bin/env python3
import argparse
import json
import shutil
import zipfile
from pathlib import Path
import yaml


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


def require_fields(payload: dict, fields: list[str], label: str) -> None:
    missing = [field for field in fields if not payload.get(field)]
    if missing:
        raise ValueError(f"Missing required {label} fields: {', '.join(missing)}")


def build_manifest(skill_dir: Path, platform: str) -> dict:
    frontmatter = read_frontmatter(skill_dir / "SKILL.md")
    interface_doc = read_interface(skill_dir)
    interface = interface_doc.get("interface", {})
    compatibility = interface_doc.get("compatibility", {})
    require_fields(frontmatter, ["name", "description"], "frontmatter")
    require_fields(interface, ["display_name", "short_description", "default_prompt"], "interface")
    return {
        "name": frontmatter.get("name", skill_dir.name),
        "description": frontmatter.get("description", ""),
        "version": frontmatter.get("version", "1.0.0"),
        "platform": platform,
        "skill_root": skill_dir.name,
        "display_name": interface.get("display_name", skill_dir.name),
        "short_description": interface.get("short_description", ""),
        "default_prompt": interface.get("default_prompt", ""),
        "canonical_metadata": "agents/interface.yaml",
        "adapter_targets": compatibility.get("adapter_targets", []),
    }


PLATFORM_CONTRACTS = {
    "openai": {
        "required_fields": ["name", "description", "version", "display_name", "short_description", "default_prompt", "canonical_metadata"],
        "required_files": ["targets/openai/adapter.json", "targets/openai/agents/openai.yaml"],
        "field_mapping": {
            "display_name": "interface.display_name",
            "short_description": "interface.short_description",
            "default_prompt": "interface.default_prompt",
        },
    },
    "claude": {
        "required_fields": ["name", "description", "version", "display_name", "short_description", "default_prompt", "canonical_metadata"],
        "required_files": ["targets/claude/adapter.json", "targets/claude/README.md"],
        "field_mapping": {
            "display_name": "adapter.display_name",
            "short_description": "adapter.short_description",
            "default_prompt": "adapter.default_prompt",
        },
    },
    "generic": {
        "required_fields": ["name", "description", "version", "display_name", "short_description", "default_prompt", "canonical_metadata"],
        "required_files": ["targets/generic/adapter.json"],
        "field_mapping": {
            "display_name": "adapter.display_name",
            "short_description": "adapter.short_description",
            "default_prompt": "adapter.default_prompt",
        },
    },
}


def write_yaml_like(path: Path, payload: dict) -> None:
    interface = payload.get("interface", {})
    lines = ["interface:"]
    for key in ("display_name", "short_description", "default_prompt"):
        value = interface.get(key, "")
        lines.append(f'  {key}: "{value}"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_adapter(skill_dir: Path, out_dir: Path, platform: str) -> Path:
    target_dir = out_dir / "targets" / platform
    target_dir.mkdir(parents=True, exist_ok=True)
    if platform not in PLATFORM_CONTRACTS:
        raise ValueError(f"Unsupported platform: {platform}")
    payload = build_manifest(skill_dir, platform)
    if platform == "openai":
        meta_dir = target_dir / "agents"
        meta_dir.mkdir(parents=True, exist_ok=True)
        write_yaml_like(
            meta_dir / "openai.yaml",
            {
                "interface": {
                    "display_name": payload["display_name"],
                    "short_description": payload["short_description"],
                    "default_prompt": payload["default_prompt"],
                }
            },
        )
        payload["install_hint"] = f"Use the packaged skill and include targets/openai/agents/openai.yaml when the client expects OpenAI-style interface metadata."
    elif platform == "claude":
        notes = target_dir / "README.md"
        notes.write_text(
            f"# Claude-Compatible Package\n\nUse `{skill_dir.name}` with its neutral source files. This target does not require vendor metadata by default.\n",
            encoding="utf-8",
        )
        payload["install_hint"] = f"Use the packaged skill directly; this target relies on SKILL.md and optional neutral metadata."
    else:
        payload["install_hint"] = f"Use {skill_dir.name} as an Agent Skills compatible package."
    path = target_dir / "adapter.json"
    payload["contract"] = PLATFORM_CONTRACTS.get(platform, PLATFORM_CONTRACTS["generic"])
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def make_zip(skill_dir: Path, out_dir: Path) -> Path:
    zip_path = out_dir / f"{skill_dir.name}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in skill_dir.rglob("*"):
            if path.is_file():
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
        "openai": expectations.get("openai_required_files", []),
        "claude": expectations.get("claude_required_files", []),
        "generic": expectations.get("generic_required_files", []),
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
    parser.add_argument("--platform", action="append", default=[], help="Target platform: openai, claude, generic")
    parser.add_argument("--output-dir", default="dist", help="Output directory")
    parser.add_argument("--expectations", help="JSON file describing packaging expectations")
    parser.add_argument("--zip", action="store_true", help="Create a zip package")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    out_dir = Path(args.output_dir).resolve()
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    manifest = copy_manifest(skill_dir, out_dir)
    generated = [str(manifest)]
    failures = []
    try:
        for platform in (args.platform or ["generic"]):
            generated.append(str(write_adapter(skill_dir, out_dir, platform)))
        if args.zip:
            generated.append(str(make_zip(skill_dir, out_dir)))
    except (FileNotFoundError, ValueError, yaml.YAMLError) as exc:
        failures.append(str(exc))

    expectations = load_expectations(Path(args.expectations).resolve()) if args.expectations else {}
    validation = validate_exports(out_dir, expectations) if expectations and not failures else None
    report = {
        "output_dir": str(out_dir),
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
