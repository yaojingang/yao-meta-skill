#!/usr/bin/env python3
import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


ROOT = Path(__file__).resolve().parent.parent
COMPILER_SCHEMA_VERSION = "1.0"
COMPILER_NAME = "yao-skill-ir-compiler"


TARGET_TRANSFORMS: dict[str, dict[str, Any]] = {
    "openai": {
        "adapter_mode": "metadata-adapter",
        "generated_files": ["targets/openai/adapter.json", "targets/openai/agents/openai.yaml"],
        "metadata_mapping": {
            "display_name": "targets/openai/agents/openai.yaml::interface.display_name",
            "default_prompt": "targets/openai/agents/openai.yaml::interface.default_prompt",
            "activation": "targets/openai/agents/openai.yaml::compatibility.activation_mode",
            "execution": "targets/openai/agents/openai.yaml::compatibility.execution_context",
            "trust": "targets/openai/agents/openai.yaml::compatibility.trust_level",
            "permissions": "targets/openai/agents/openai.yaml::compatibility.permission_contract",
            "degradation": "targets/openai/agents/openai.yaml::compatibility.degradation_strategy",
        },
        "preserved_semantics": ["trigger", "workflow-counts", "resources", "eval-plan", "risk", "governance", "runtime", "trust", "permissions"],
        "unsupported_features": ["client-native script permission prompts are represented as permission contract metadata"],
    },
    "claude": {
        "adapter_mode": "neutral-source-plus-adapter",
        "generated_files": ["targets/claude/adapter.json", "targets/claude/README.md"],
        "metadata_mapping": {
            "display_name": "targets/claude/adapter.json::display_name",
            "default_prompt": "targets/claude/adapter.json::default_prompt",
            "activation": "targets/claude/adapter.json::activation_mode",
            "execution": "targets/claude/adapter.json::execution_context",
            "trust": "targets/claude/adapter.json::trust_level",
            "permissions": "targets/claude/adapter.json::target_permission_contract",
            "degradation": "targets/claude/adapter.json::degradation_strategy",
        },
        "preserved_semantics": ["trigger", "workflow-counts", "resources", "eval-plan", "risk", "governance", "runtime", "trust", "permissions"],
        "unsupported_features": ["vendor-native metadata fields are carried as adapter JSON and README notes"],
    },
    "generic": {
        "adapter_mode": "agent-skills-compatible",
        "generated_files": ["targets/generic/adapter.json"],
        "metadata_mapping": {
            "display_name": "targets/generic/adapter.json::display_name",
            "default_prompt": "targets/generic/adapter.json::default_prompt",
            "activation": "targets/generic/adapter.json::activation_mode",
            "execution": "targets/generic/adapter.json::execution_context",
            "trust": "targets/generic/adapter.json::trust_level",
            "permissions": "targets/generic/adapter.json::target_permission_contract",
            "degradation": "targets/generic/adapter.json::degradation_strategy",
        },
        "preserved_semantics": ["trigger", "workflow-counts", "resources", "eval-plan", "risk", "governance", "runtime", "trust", "permissions"],
        "unsupported_features": [],
    },
    "agent-skills-compatible": {
        "adapter_mode": "neutral-agent-skills-source",
        "generated_files": ["SKILL.md", "agents/interface.yaml"],
        "metadata_mapping": {
            "name": "SKILL.md::frontmatter.name",
            "description": "SKILL.md::frontmatter.description",
            "interface": "agents/interface.yaml",
            "manifest": "manifest.json",
        },
        "preserved_semantics": ["trigger", "workflow", "resources", "eval-plan", "risk", "governance", "runtime", "trust", "permissions"],
        "unsupported_features": [],
    },
    "agent-skills": {
        "adapter_mode": "neutral-agent-skills-source",
        "generated_files": ["SKILL.md", "agents/interface.yaml"],
        "metadata_mapping": {
            "name": "SKILL.md::frontmatter.name",
            "description": "SKILL.md::frontmatter.description",
            "interface": "agents/interface.yaml",
            "manifest": "manifest.json",
        },
        "preserved_semantics": ["trigger", "workflow", "resources", "eval-plan", "risk", "governance", "runtime", "trust", "permissions"],
        "unsupported_features": [],
    },
    "vscode": {
        "adapter_mode": "vscode-agent-skills-adapter",
        "generated_files": ["targets/vscode/adapter.json", "targets/vscode/README.md"],
        "metadata_mapping": {
            "name": "folder-name-and-SKILL.md::frontmatter.name",
            "description": "SKILL.md::frontmatter.description",
            "interface": "agents/interface.yaml",
            "permissions": "targets/vscode/adapter.json::target_permission_contract",
            "install_scope": "targets/vscode/README.md",
        },
        "preserved_semantics": ["trigger", "workflow", "resources", "eval-plan", "risk", "governance", "runtime", "trust", "permissions"],
        "unsupported_features": ["VS Code installation scope is documented but not installed by this compiler"],
    },
}


def display_path(path: Path, root: Path = ROOT) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists() or yaml is None:
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def read_frontmatter(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    if yaml is not None:
        payload = yaml.safe_load(parts[1]) or {}
        return payload if isinstance(payload, dict) else {}
    data: dict[str, Any] = {}
    for line in parts[1].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def find_skill_ir(skill_dir: Path, name: str) -> tuple[dict[str, Any], str]:
    candidates = [
        skill_dir / "reports" / "skill-ir.json",
        skill_dir / "skill-ir" / "examples" / f"{name}.json",
        skill_dir / "skill-ir" / "examples" / f"{skill_dir.name}.json",
    ]
    seen: set[Path] = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        payload = load_json(path)
        if payload:
            return payload, display_path(path, skill_dir)
    return {}, "frontmatter-fallback"


def count_list(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key, [])
    return len(value) if isinstance(value, list) else 0


def list_or_empty(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key, [])
    return [str(item) for item in value] if isinstance(value, list) else []


def resource_counts(resources: dict[str, Any]) -> dict[str, int]:
    return {key: count_list(resources, key) for key in ("references", "scripts", "assets", "reports")}


def eval_counts(eval_plan: dict[str, Any]) -> dict[str, int]:
    return {
        "trigger": count_list(eval_plan, "trigger"),
        "output": count_list(eval_plan, "output"),
        "adversarial": count_list(eval_plan, "adversarial"),
        "baseline": 1 if eval_plan.get("baseline") else 0,
    }


def scripts_with_flag(scripts: list[dict[str, Any]], flag: str) -> list[str]:
    return [str(item.get("path")) for item in scripts if item.get(flag)]


def capability(name: str, scripts: list[str], review_reason: str) -> dict[str, Any]:
    return {
        "required": bool(scripts),
        "script_count": len(scripts),
        "scripts": scripts,
        "review_reason": review_reason if scripts else "",
    }


def permission_contract(skill_dir: Path) -> dict[str, Any]:
    trust_path = skill_dir / "reports" / "security_trust_report.json"
    trust = load_json(trust_path)
    scripts = trust.get("scripts", []) if isinstance(trust.get("scripts"), list) else []
    network_scripts = scripts_with_flag(scripts, "uses_network")
    file_write_scripts = scripts_with_flag(scripts, "uses_file_write")
    subprocess_scripts = scripts_with_flag(scripts, "uses_subprocess")
    interactive_scripts = scripts_with_flag(scripts, "uses_input")
    capabilities = {
        "network": capability("network", network_scripts, "Outbound hosts must match security/network_policy.json."),
        "file_write": capability("file_write", file_write_scripts, "Scripts write local files or generated artifacts."),
        "subprocess": capability("subprocess", subprocess_scripts, "Scripts spawn local commands and need operator review."),
        "interactive": capability("interactive", interactive_scripts, "Scripts prompt for user input or credentials."),
    }
    declared = [name for name, item in capabilities.items() if item["required"]]
    help_smoke = trust.get("help_smoke", {}) if isinstance(trust.get("help_smoke"), dict) else {}
    network_policy = trust.get("network_policy", {}) if isinstance(trust.get("network_policy"), dict) else {}
    summary = trust.get("summary", {}) if isinstance(trust.get("summary"), dict) else {}
    return {
        "schema_version": "1.0",
        "source": display_path(trust_path, skill_dir) if trust else "missing-security-trust-report",
        "source_available": bool(trust),
        "declared_capabilities": declared,
        "review_required": bool(declared),
        "capabilities": capabilities,
        "network_policy": {
            "source": network_policy.get("path", "security/network_policy.json"),
            "covered_scripts": network_policy.get("covered_scripts", []),
            "missing_scripts": network_policy.get("missing_scripts", []),
            "mismatches": network_policy.get("mismatches", []),
        },
        "help_smoke": {
            "enabled": bool(help_smoke.get("enabled")),
            "checked_count": int(help_smoke.get("checked_count", 0) or 0),
            "failed_count": int(help_smoke.get("failed_count", 0) or 0),
            "failed_scripts": help_smoke.get("failed_scripts", []),
        },
        "trust_summary": {
            "secret_findings": int(summary.get("secret_findings", 0) or 0),
            "network_script_count": int(summary.get("network_script_count", len(network_scripts)) or 0),
            "file_write_script_count": int(summary.get("file_write_script_count", len(file_write_scripts)) or 0),
            "subprocess_script_count": len(subprocess_scripts),
            "interactive_script_count": int(summary.get("interactive_script_count", len(interactive_scripts)) or 0),
            "help_smoke_failed_count": int(summary.get("help_smoke_failed_count", 0) or 0),
        },
    }


TARGET_PERMISSION_MODELS = {
    "openai": {
        "model": "metadata-only",
        "native_enforcement": False,
        "representation": "targets/openai/agents/openai.yaml::compatibility.permission_contract plus adapter.json",
        "operator_note": "OpenAI target carries permission metadata for reviewer visibility; host enforcement remains outside the package.",
    },
    "claude": {
        "model": "neutral-source-plus-adapter",
        "native_enforcement": False,
        "representation": "targets/claude/adapter.json::target_permission_contract and README notes",
        "operator_note": "Claude-compatible package keeps permission intent in adapter metadata for install review.",
    },
    "generic": {
        "model": "agent-skills-compatible-metadata",
        "native_enforcement": False,
        "representation": "targets/generic/adapter.json::target_permission_contract",
        "operator_note": "Generic target exposes permission metadata for downstream clients to enforce or review.",
    },
    "vscode": {
        "model": "vscode-workspace-trust-plus-metadata",
        "native_enforcement": False,
        "representation": "targets/vscode/adapter.json::target_permission_contract and targets/vscode/README.md install notes",
        "operator_note": "VS Code target relies on project or user skill installation plus VS Code workspace trust; Yao preserves permission metadata for reviewer and installer checks.",
    },
}


TARGET_NATIVE_MODELS = {
    "openai": {
        "native_surface": "OpenAI-style interface metadata plus neutral Agent Skills source",
        "activation_policy": "Use frontmatter description for catalog routing and targets/openai/agents/openai.yaml for display name, default prompt, and compatibility metadata.",
        "resource_strategy": "Ship the neutral source tree and expose OpenAI-facing interface metadata as a generated companion file.",
        "script_strategy": "Keep scripts as local package resources; expose help-smoke and permission metadata for reviewer approval before execution.",
        "permission_enforcement": "metadata-only",
        "install_scope": "plugin or skill package consumer",
        "review_artifacts": ["targets/openai/agents/openai.yaml", "targets/openai/adapter.json", "reports/review-studio.html"],
        "fallback_behavior": "If OpenAI-native metadata is ignored, the package remains readable as neutral Agent Skills source.",
        "unsupported_native_features": [
            "client-native permission prompts",
            "provider-executed scripts",
        ],
    },
    "claude": {
        "native_surface": "Claude-compatible neutral source folder with adapter notes",
        "activation_policy": "Use SKILL.md frontmatter description as the primary activation contract and adapter.json for review metadata.",
        "resource_strategy": "Preserve the source tree directly; write target notes in targets/claude/README.md.",
        "script_strategy": "Scripts remain local package resources and must be reviewed through trust and permission reports before use.",
        "permission_enforcement": "metadata-fallback",
        "install_scope": "user or project skill directory",
        "review_artifacts": ["targets/claude/README.md", "targets/claude/adapter.json", "reports/review-studio.html"],
        "fallback_behavior": "If Claude-specific metadata is not consumed, SKILL.md and references remain the source of truth.",
        "unsupported_native_features": [
            "vendor-native permission enforcement",
            "provider-specific execution transforms",
        ],
    },
    "generic": {
        "native_surface": "Agent Skills compatible neutral package",
        "activation_policy": "Use SKILL.md name and description; consumers decide automatic or manual activation.",
        "resource_strategy": "Preserve references, scripts, assets, evals, reports, and adapter metadata as relative package resources.",
        "script_strategy": "Expose script and permission metadata for downstream clients or installers to enforce.",
        "permission_enforcement": "consumer-enforced-or-metadata-only",
        "install_scope": "generic Agent Skills compatible root",
        "review_artifacts": ["targets/generic/adapter.json", "reports/review-studio.html"],
        "fallback_behavior": "Neutral source is the runtime fallback.",
        "unsupported_native_features": [],
    },
    "agent-skills-compatible": {
        "native_surface": "Agent Skills standard source tree",
        "activation_policy": "Use SKILL.md frontmatter name and description for progressive disclosure.",
        "resource_strategy": "Keep optional directories as relative resources next to SKILL.md.",
        "script_strategy": "Scripts remain local optional resources and should advertise --help when executable.",
        "permission_enforcement": "consumer-enforced-or-metadata-only",
        "install_scope": "Agent Skills source root",
        "review_artifacts": ["SKILL.md", "agents/interface.yaml", "reports/review-studio.html"],
        "fallback_behavior": "The source tree itself is the target artifact.",
        "unsupported_native_features": [],
    },
    "agent-skills": {
        "native_surface": "Agent Skills standard source tree",
        "activation_policy": "Use SKILL.md frontmatter name and description for progressive disclosure.",
        "resource_strategy": "Keep optional directories as relative resources next to SKILL.md.",
        "script_strategy": "Scripts remain local optional resources and should advertise --help when executable.",
        "permission_enforcement": "consumer-enforced-or-metadata-only",
        "install_scope": "Agent Skills source root",
        "review_artifacts": ["SKILL.md", "agents/interface.yaml", "reports/review-studio.html"],
        "fallback_behavior": "The source tree itself is the target artifact.",
        "unsupported_native_features": [],
    },
    "vscode": {
        "native_surface": "VS Code/Copilot Agent Skills project or user scope",
        "activation_policy": "Use folder name plus SKILL.md name/description; keep description under platform limits.",
        "resource_strategy": "Install as project or user scoped skill source, preserving relative references and scripts.",
        "script_strategy": "Scripts require workspace trust and operator/client approval outside this compiler.",
        "permission_enforcement": "client-or-workspace-trust",
        "install_scope": "VS Code user or project skills directory",
        "review_artifacts": ["SKILL.md", "agents/interface.yaml", "reports/review-studio.html"],
        "fallback_behavior": "If VS Code scope is not installed, use the neutral Agent Skills source.",
        "unsupported_native_features": [
            "automatic VS Code installation",
        ],
    },
}


def target_permission_contract(target: str, permissions: dict[str, Any]) -> dict[str, Any]:
    model = TARGET_PERMISSION_MODELS.get(
        target,
        {
            "model": "metadata-only",
            "native_enforcement": False,
            "representation": "adapter metadata",
            "operator_note": "Permission semantics are preserved as metadata for reviewer visibility.",
        },
    )
    return {
        "schema_version": "1.0",
        "target": target,
        "permission_model": model["model"],
        "native_enforcement": model["native_enforcement"],
        "representation": model["representation"],
        "review_required": bool(permissions.get("review_required")),
        "declared_capabilities": permissions.get("declared_capabilities", []),
        "capability_counts": {
            name: item.get("script_count", 0)
            for name, item in permissions.get("capabilities", {}).items()
        },
        "evidence": permissions.get("source", ""),
        "operator_note": model["operator_note"],
    }


def target_native_contract(
    target: str,
    profile: dict[str, Any],
    contract: dict[str, Any],
    target_permissions: dict[str, Any],
) -> dict[str, Any]:
    model = TARGET_NATIVE_MODELS.get(
        target,
        {
            "native_surface": "adapter metadata",
            "activation_policy": "Carry activation semantics as metadata for the target consumer.",
            "resource_strategy": "Preserve neutral package resources.",
            "script_strategy": "Expose script metadata for reviewer visibility.",
            "permission_enforcement": "metadata-only",
            "install_scope": "target consumer",
            "review_artifacts": ["adapter.json", "reports/review-studio.html"],
            "fallback_behavior": "Use neutral source package.",
            "unsupported_native_features": [],
        },
    )
    return {
        "schema_version": "1.0",
        "target": target,
        "native_surface": model["native_surface"],
        "activation": {
            "policy": model["activation_policy"],
            "trigger_description": contract.get("trigger", {}).get("description", ""),
            "manual_activation_supported": True,
            "automatic_activation_note": "Depends on the target client route/catalog implementation.",
        },
        "resources": {
            "strategy": model["resource_strategy"],
            "counts": contract.get("resources", {}).get("counts", {}),
            "generated_files": profile.get("generated_files", []),
        },
        "scripts": {
            "strategy": model["script_strategy"],
            "script_count": contract.get("resources", {}).get("counts", {}).get("scripts", 0),
            "help_smoke_failed_count": contract.get("permissions", {}).get("help_smoke", {}).get("failed_count", 0),
        },
        "permissions": {
            "enforcement": model["permission_enforcement"],
            "native_enforcement": bool(target_permissions.get("native_enforcement")),
            "declared_capabilities": target_permissions.get("declared_capabilities", []),
            "review_required": bool(target_permissions.get("review_required")),
        },
        "review": {
            "artifacts": model["review_artifacts"],
            "fallback_behavior": model["fallback_behavior"],
            "unsupported_native_features": [
                *model.get("unsupported_native_features", []),
                *profile.get("unsupported_features", []),
            ],
        },
        "install_scope": model["install_scope"],
    }


def load_sources(skill_dir: Path) -> dict[str, Any]:
    skill_dir = skill_dir.resolve()
    frontmatter = read_frontmatter(skill_dir / "SKILL.md")
    manifest = load_json(skill_dir / "manifest.json")
    interface_doc = load_yaml(skill_dir / "agents" / "interface.yaml")
    name = str(frontmatter.get("name") or manifest.get("name") or skill_dir.name)
    ir, ir_source = find_skill_ir(skill_dir, name)
    return {
        "skill_dir": skill_dir,
        "frontmatter": frontmatter,
        "manifest": manifest,
        "interface_doc": interface_doc,
        "interface": interface_doc.get("interface", {}),
        "compatibility": interface_doc.get("compatibility", {}),
        "ir": ir,
        "ir_source": ir_source,
    }


def declared_targets(sources: dict[str, Any]) -> list[str]:
    ir = sources["ir"]
    compatibility = sources["compatibility"]
    manifest = sources["manifest"]
    candidates = (
        ir.get("targets")
        if isinstance(ir.get("targets"), list)
        else manifest.get("target_platforms")
        or compatibility.get("adapter_targets")
        or []
    )
    targets = []
    for item in candidates:
        value = str(item).strip()
        if value and value not in targets:
            targets.append(value)
    return targets or ["generic"]


def semantic_source(sources: dict[str, Any]) -> dict[str, Any]:
    skill_dir = sources["skill_dir"]
    frontmatter = sources["frontmatter"]
    manifest = sources["manifest"]
    interface = sources["interface"]
    compatibility = sources["compatibility"]
    ir = sources["ir"]
    trigger = ir.get("trigger_surface", {}) if isinstance(ir.get("trigger_surface"), dict) else {}
    workflow = ir.get("workflow", {}) if isinstance(ir.get("workflow"), dict) else {}
    resources = ir.get("resources", {}) if isinstance(ir.get("resources"), dict) else {}
    eval_plan = ir.get("eval_plan", {}) if isinstance(ir.get("eval_plan"), dict) else {}
    description = str(trigger.get("description") or frontmatter.get("description") or "")
    name = str(ir.get("name") or frontmatter.get("name") or manifest.get("name") or skill_dir.name)
    permissions = permission_contract(skill_dir)
    return {
        "name": name,
        "title": str(ir.get("title") or interface.get("display_name") or name),
        "version": str(manifest.get("version") or frontmatter.get("version") or "1.0.0"),
        "description": description,
        "job_to_be_done": str(ir.get("job_to_be_done") or description),
        "trigger": {
            "description": description,
            "should_trigger": list_or_empty(trigger, "should_trigger"),
            "should_not_trigger": list_or_empty(trigger, "should_not_trigger"),
            "edge_cases": list_or_empty(trigger, "edge_cases"),
        },
        "workflow": {
            "steps": list_or_empty(workflow, "steps"),
            "decision_points": list_or_empty(workflow, "decision_points"),
            "failure_modes": list_or_empty(workflow, "failure_modes"),
        },
        "resources": {
            "references": list_or_empty(resources, "references"),
            "scripts": list_or_empty(resources, "scripts"),
            "assets": list_or_empty(resources, "assets"),
            "reports": list_or_empty(resources, "reports"),
            "counts": resource_counts(resources),
        },
        "eval_plan": {
            "trigger": list_or_empty(eval_plan, "trigger"),
            "output": list_or_empty(eval_plan, "output"),
            "adversarial": list_or_empty(eval_plan, "adversarial"),
            "baseline": str(eval_plan.get("baseline") or ""),
            "counts": eval_counts(eval_plan),
        },
        "risk": ir.get("risk", {}) if isinstance(ir.get("risk"), dict) else {},
        "governance": ir.get("governance", {}) if isinstance(ir.get("governance"), dict) else {},
        "runtime": {
            "activation": compatibility.get("activation", {}) if isinstance(compatibility.get("activation"), dict) else {},
            "execution": compatibility.get("execution", {}) if isinstance(compatibility.get("execution"), dict) else {},
            "trust": compatibility.get("trust", {}) if isinstance(compatibility.get("trust"), dict) else {},
            "adapter_targets": compatibility.get("adapter_targets", []),
            "canonical_format": compatibility.get("canonical_format", "agent-skills"),
        },
        "permissions": permissions,
        "source_files_count": count_list(ir, "source_files") if ir else 0,
    }


def compile_target_contract(skill_dir: Path, target: str) -> dict[str, Any]:
    sources = load_sources(skill_dir)
    compatibility = sources["compatibility"]
    degradation = compatibility.get("degradation", {}) if isinstance(compatibility.get("degradation"), dict) else {}
    declared = declared_targets(sources)
    failures: list[str] = []
    warnings: list[str] = []
    profile = TARGET_TRANSFORMS.get(target)
    if profile is None:
        failures.append(f"Unsupported compiler target: {target}")
        profile = {
            "adapter_mode": "unsupported",
            "generated_files": [],
            "metadata_mapping": {},
            "preserved_semantics": [],
            "unsupported_features": [],
        }
    if target not in declared and not (target in {"agent-skills", "vscode"} and "agent-skills-compatible" in declared):
        warnings.append(f"Target is not declared in Skill IR or interface metadata: {target}")
    if not sources["ir"]:
        warnings.append("Skill IR is missing; compiler used frontmatter fallback")

    contract = semantic_source(sources)
    permissions = contract["permissions"]
    target_permissions = target_permission_contract(target, permissions)
    target_native = target_native_contract(target, profile, contract, target_permissions)
    contract["target"] = target
    contract["target_permission_contract"] = target_permissions
    contract["target_native_contract"] = target_native
    contract["degradation_strategy"] = degradation.get(target, degradation.get("generic", "neutral-source"))
    contract["target_runtime"] = {
        "adapter_mode": profile["adapter_mode"],
        "generated_files": profile["generated_files"],
        "metadata_mapping": profile["metadata_mapping"],
        "preserved_semantics": profile["preserved_semantics"],
        "native_surface": target_native["native_surface"],
    }

    return {
        "schema_version": COMPILER_SCHEMA_VERSION,
        "target": target,
        "status": "block" if failures else ("warn" if warnings else "pass"),
        "compiler": {
            "name": COMPILER_NAME,
            "schema_version": COMPILER_SCHEMA_VERSION,
            "source": "skill-ir" if sources["ir"] else "frontmatter-fallback",
            "ir_source": sources["ir_source"],
            "ir_schema_version": str(sources["ir"].get("schema_version") or "none"),
        },
        "source": {
            "skill_dir": display_path(sources["skill_dir"]),
            "canonical_metadata": "agents/interface.yaml" if (sources["skill_dir"] / "agents" / "interface.yaml").exists() else "missing",
            "declared_targets": declared,
        },
        "compiled_contract": contract,
        "permission_contract": permissions,
        "target_permission_contract": target_permissions,
        "target_native_contract": target_native,
        "target_transform": {
            "target": target,
            "adapter_mode": profile["adapter_mode"],
            "generated_files": profile["generated_files"],
            "metadata_mapping": profile["metadata_mapping"],
            "preserved_semantics": profile["preserved_semantics"],
            "degradation_strategy": contract["degradation_strategy"],
            "permission_representation": target_permissions["representation"],
            "native_surface": target_native["native_surface"],
            "activation_policy": target_native["activation"]["policy"],
            "resource_strategy": target_native["resources"]["strategy"],
            "script_strategy": target_native["scripts"]["strategy"],
            "permission_enforcement": target_native["permissions"]["enforcement"],
        },
        "unsupported_features": list(profile.get("unsupported_features", [])),
        "warnings": warnings,
        "failures": failures,
    }


def compile_targets(skill_dir: Path, targets: list[str] | None = None, generated_at: str | None = None) -> dict[str, Any]:
    sources = load_sources(skill_dir)
    selected = targets or declared_targets(sources)
    compiled = [compile_target_contract(skill_dir, target) for target in selected]
    failures = [failure for item in compiled for failure in item["failures"]]
    warnings = [warning for item in compiled for warning in item["warnings"]]
    return {
        "schema_version": COMPILER_SCHEMA_VERSION,
        "ok": not failures,
        "generated_at": generated_at or str(date.today()),
        "skill_dir": display_path(Path(skill_dir).resolve()),
        "summary": {
            "target_count": len(compiled),
            "pass_count": sum(1 for item in compiled if item["status"] == "pass"),
            "warn_count": sum(1 for item in compiled if item["status"] == "warn"),
            "block_count": sum(1 for item in compiled if item["status"] == "block"),
            "failure_count": len(failures),
            "warning_count": len(warnings),
        },
        "targets": compiled,
        "failures": failures,
        "warnings": warnings,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Compiled Targets",
        "",
        f"- OK: `{report['ok']}`",
        f"- Targets: `{summary['target_count']}`",
        f"- Pass: `{summary['pass_count']}`",
        f"- Warn: `{summary['warn_count']}`",
        f"- Block: `{summary['block_count']}`",
        "",
        "## Target Transforms",
        "",
        "| Target | Status | Native Surface | Adapter Mode | Permissions | Degradation | Generated Files |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["targets"]:
        transform = item["target_transform"]
        files = ", ".join(transform.get("generated_files", [])) or "none"
        permissions = ", ".join(item.get("target_permission_contract", {}).get("declared_capabilities", [])) or "none"
        lines.append(
            f"| `{item['target']}` | `{item['status']}` | {transform.get('native_surface', '')} | `{transform.get('adapter_mode', '')}` | `{permissions}` | `{transform.get('degradation_strategy', '')}` | {files} |"
        )
    lines.extend(["", "## Native Behavior Contracts", ""])
    for item in report["targets"]:
        native = item.get("target_native_contract", {})
        permissions = native.get("permissions", {})
        review = native.get("review", {})
        lines.extend(
            [
                f"### {item['target']}",
                "",
                f"- Native surface: {native.get('native_surface', '')}",
                f"- Activation: {native.get('activation', {}).get('policy', '')}",
                f"- Resources: {native.get('resources', {}).get('strategy', '')}",
                f"- Scripts: {native.get('scripts', {}).get('strategy', '')}",
                f"- Permission enforcement: `{permissions.get('enforcement', '')}`; native enforcement `{permissions.get('native_enforcement')}`",
                f"- Review artifacts: {', '.join(review.get('artifacts', [])) or 'none'}",
                "",
            ]
        )
    lines.extend(["", "## Failures", ""])
    lines.extend([f"- {item}" for item in report["failures"]] or ["- None"])
    lines.extend(["", "## Warnings", ""])
    lines.extend([f"- {item}" for item in report["warnings"]] or ["- None"])
    return "\n".join(lines).strip() + "\n"


def render_compile_report(
    skill_dir: Path,
    targets: list[str] | None = None,
    output_json: Path | None = None,
    output_md: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    skill_dir = skill_dir.resolve()
    reports = skill_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    output_json = output_json or reports / "compiled_targets.json"
    output_md = output_md or reports / "compiled_targets.md"
    report = compile_targets(skill_dir, targets=targets, generated_at=generated_at)
    report["artifacts"] = {
        "json": display_path(output_json),
        "markdown": display_path(output_md),
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile Skill IR into target-specific semantic contracts.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--target", action="append", default=[])
    parser.add_argument("--output-json")
    parser.add_argument("--output-md")
    parser.add_argument("--generated-at")
    args = parser.parse_args()

    payload = render_compile_report(
        Path(args.skill_dir),
        targets=args.target or None,
        output_json=Path(args.output_json).resolve() if args.output_json else None,
        output_md=Path(args.output_md).resolve() if args.output_md else None,
        generated_at=args.generated_at,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if payload["ok"] else 2)


if __name__ == "__main__":
    main()
