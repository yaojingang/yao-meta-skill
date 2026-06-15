#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGETS = ["openai", "claude", "agent-skills", "vscode", "generic"]


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
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


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    if not path.exists():
        return {}, ""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    try:
        end_index = lines[1:].index("---") + 1
    except ValueError:
        return {}, text
    frontmatter_text = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :]).lstrip()
    if yaml is not None:
        payload = yaml.safe_load(frontmatter_text) or {}
        return payload if isinstance(payload, dict) else {}, body
    data = {}
    for line in frontmatter_text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip('"')
    return data, body


def find_skill_ir(skill_dir: Path, name: str) -> dict[str, Any]:
    direct = load_json(skill_dir / "reports" / "skill-ir.json")
    if direct:
        return direct
    return load_json(skill_dir / "skill-ir" / "examples" / f"{name}.json")


def add_check(checks: list[str], failures: list[str], condition: bool, passed: str, failed: str) -> None:
    if condition:
        checks.append(passed)
    else:
        failures.append(failed)


def relative_resource_check(skill_dir: Path, ir: dict[str, Any]) -> tuple[list[str], list[str]]:
    checks = []
    failures = []
    resources = ir.get("resources", {}) if isinstance(ir, dict) else {}
    for group in ("references", "scripts", "assets", "reports"):
        for raw_path in resources.get(group, []):
            rel = Path(str(raw_path))
            if rel.is_absolute():
                failures.append(f"{group} resource is absolute: {raw_path}")
                continue
            target = (skill_dir / rel).resolve()
            try:
                target.relative_to(skill_dir.resolve())
            except ValueError:
                failures.append(f"{group} resource escapes package: {raw_path}")
                continue
            if not target.exists():
                failures.append(f"{group} resource is missing: {raw_path}")
            else:
                checks.append(f"{group} resource resolves: {raw_path}")
    return checks, failures


def common_evidence(skill_dir: Path) -> dict[str, Any]:
    frontmatter, _ = parse_frontmatter(skill_dir / "SKILL.md")
    manifest = load_json(skill_dir / "manifest.json")
    interface_doc = load_yaml(skill_dir / "agents" / "interface.yaml")
    name = str(frontmatter.get("name") or manifest.get("name") or skill_dir.name)
    ir = find_skill_ir(skill_dir, name)
    return {
        "frontmatter": frontmatter,
        "manifest": manifest,
        "interface": interface_doc.get("interface", {}),
        "compatibility": interface_doc.get("compatibility", {}),
        "ir": ir,
        "name": name,
        "description": str(frontmatter.get("description", "")),
    }


def target_alias(target: str) -> str:
    if target in {"agent-skills", "agentskills"}:
        return "agent-skills-compatible"
    if target == "vscode":
        return "agent-skills-compatible"
    return target


def check_target(skill_dir: Path, target: str, evidence: dict[str, Any]) -> dict[str, Any]:
    checks: list[str] = []
    failures: list[str] = []
    warnings: list[str] = []
    frontmatter = evidence["frontmatter"]
    manifest = evidence["manifest"]
    interface = evidence["interface"]
    compatibility = evidence["compatibility"]
    ir = evidence["ir"]
    name = evidence["name"]
    description = evidence["description"]

    add_check(checks, failures, (skill_dir / "SKILL.md").exists(), "SKILL.md exists", "Missing SKILL.md")
    add_check(checks, failures, bool(frontmatter.get("name")), "frontmatter name exists", "Missing frontmatter name")
    add_check(checks, failures, bool(description), "frontmatter description exists", "Missing frontmatter description")
    add_check(checks, failures, len(description) <= 1024, "description length <= 1024", "description exceeds 1024 characters")
    add_check(checks, failures, re.fullmatch(r"[a-z0-9][a-z0-9_-]*", name) is not None, "name is runtime-safe", "name contains unsafe characters")

    if target in {"agent-skills", "vscode"}:
        add_check(checks, failures, bool(name), "package identity derives from skill name", "Missing package identity")
        if skill_dir.name != name:
            warnings.append(
                "source checkout directory differs from skill name; package verification must enforce archive top-level identity."
            )

    for field in ("name", "version", "owner", "status", "maturity_tier", "review_cadence"):
        add_check(checks, failures, bool(manifest.get(field)), f"manifest.{field} exists", f"Missing manifest.{field}")
    targets = [str(item) for item in manifest.get("target_platforms", [])]
    alias = target_alias(target)
    target_declared = alias in targets or target in targets
    target_message = f"manifest declares {target}" if target in targets else f"manifest declares {target} via {alias}"
    add_check(checks, failures, target_declared, target_message, f"manifest target missing: {target}")

    for field in ("display_name", "short_description", "default_prompt"):
        add_check(checks, failures, bool(interface.get(field)), f"interface.{field} exists", f"Missing interface.{field}")
    adapter_targets = [str(item) for item in compatibility.get("adapter_targets", [])]
    if target in {"openai", "claude", "generic"}:
        add_check(checks, failures, target in adapter_targets, f"adapter target declares {target}", f"adapter target missing: {target}")
    else:
        add_check(checks, failures, compatibility.get("canonical_format") == "agent-skills", "canonical format is agent-skills", "canonical format must be agent-skills")

    activation = compatibility.get("activation", {})
    execution = compatibility.get("execution", {})
    trust = compatibility.get("trust", {})
    degradation = compatibility.get("degradation", {})
    add_check(checks, failures, bool(activation.get("mode")), "activation mode exists", "Missing activation mode")
    add_check(checks, failures, bool(execution.get("context")), "execution context exists", "Missing execution context")
    add_check(checks, failures, bool(execution.get("shell")), "execution shell exists", "Missing execution shell")
    add_check(checks, failures, bool(trust.get("source_tier")), "trust source tier exists", "Missing trust source tier")
    if target in {"openai", "claude", "generic"}:
        add_check(checks, failures, bool(degradation.get(target)), f"{target} degradation note exists", f"Missing {target} degradation note")
    else:
        warnings.append(f"{target} uses canonical Agent Skills metadata; provider-native execution transforms are not implemented in v0.")

    add_check(checks, failures, ir.get("schema_version") == "2.0.0", "Skill IR schema_version is 2.0.0", "Missing or invalid Skill IR")
    add_check(checks, failures, ir.get("name") == name, "Skill IR name matches frontmatter", "Skill IR name does not match frontmatter")
    add_check(
        checks,
        failures,
        ir.get("trigger_surface", {}).get("description") == description,
        "Skill IR description matches frontmatter",
        "Skill IR description does not match frontmatter",
    )
    resource_checks, resource_failures = relative_resource_check(skill_dir, ir)
    checks.extend(resource_checks[:12])
    failures.extend(resource_failures)

    return {
        "target": target,
        "status": "pass" if not failures else "fail",
        "checks": checks,
        "failures": failures,
        "warnings": warnings,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Runtime Conformance Matrix",
        "",
        f"- Skill: `{payload['skill']}`",
        f"- Targets: `{payload['summary']['target_count']}`",
        f"- Passed: `{payload['summary']['pass_count']}`",
        f"- Failed: `{payload['summary']['fail_count']}`",
        "",
        "| Target | Status | Failures | Warnings |",
        "| --- | --- | --- | --- |",
    ]
    for target in payload["targets"]:
        failures = "<br>".join(target["failures"]) if target["failures"] else "None"
        warnings = "<br>".join(target["warnings"]) if target["warnings"] else "None"
        lines.append(f"| {target['target']} | {target['status']} | {failures} | {warnings} |")
    lines.extend(["", "## Reviewer Notes", "", "- Failed targets block release for that target.", "- Warnings identify lossy or not-yet-compiled behavior that must remain visible."])
    return "\n".join(lines).strip() + "\n"


def run_conformance(skill_dir: Path, targets: list[str], output_json: Path, output_md: Path) -> dict[str, Any]:
    skill_dir = skill_dir.resolve()
    evidence = common_evidence(skill_dir)
    target_results = [check_target(skill_dir, target, evidence) for target in targets]
    summary = {
        "target_count": len(target_results),
        "pass_count": sum(1 for item in target_results if item["status"] == "pass"),
        "fail_count": sum(1 for item in target_results if item["status"] == "fail"),
    }
    payload = {
        "ok": summary["fail_count"] == 0,
        "skill": evidence["name"],
        "targets": target_results,
        "summary": summary,
        "artifacts": {"json": display_path(output_json), "markdown": display_path(output_md)},
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run runtime conformance checks for Skill OS 2.0 targets.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--target", action="append", choices=DEFAULT_TARGETS)
    parser.add_argument("--output-json")
    parser.add_argument("--output-md")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    targets = args.target or DEFAULT_TARGETS
    payload = run_conformance(
        skill_dir,
        targets,
        Path(args.output_json).resolve() if args.output_json else skill_dir / "reports" / "conformance_matrix.json",
        Path(args.output_md).resolve() if args.output_md else skill_dir / "reports" / "conformance_matrix.md",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if payload["ok"] else 2)


if __name__ == "__main__":
    main()
