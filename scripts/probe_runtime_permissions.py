#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


DEFAULT_TARGETS = ["openai", "claude", "generic", "vscode"]


def display_path(path: Path, root: Path) -> str:
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
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    return payload if isinstance(payload, dict) else {}


def expected_capabilities(skill_dir: Path) -> list[str]:
    trust = load_json(skill_dir / "reports" / "security_trust_report.json")
    governance = trust.get("permission_governance", {}) if isinstance(trust.get("permission_governance"), dict) else {}
    required = governance.get("required_capabilities", [])
    if isinstance(required, list) and required:
        return sorted(str(item) for item in required)
    summary = trust.get("summary", {}) if isinstance(trust.get("summary"), dict) else {}
    candidates = []
    if int(summary.get("network_script_count", 0) or 0):
        candidates.append("network")
    if int(summary.get("file_write_script_count", 0) or 0):
        candidates.append("file_write")
    if any(item.get("uses_subprocess") for item in trust.get("scripts", []) if isinstance(item, dict)):
        candidates.append("subprocess")
    if int(summary.get("interactive_script_count", 0) or 0):
        candidates.append("interactive")
    return sorted(candidates)


def add_check(checks: list[dict[str, Any]], failures: list[str], key: str, condition: bool, detail: str) -> None:
    checks.append({"key": key, "passed": condition, "detail": detail})
    if not condition:
        failures.append(detail)


def sorted_strings(value: Any) -> list[str]:
    return sorted(str(item) for item in value) if isinstance(value, list) else []


def probe_openai_yaml(package_dir: Path, expected: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    checks: list[dict[str, Any]] = []
    failures: list[str] = []
    path = package_dir / "targets" / "openai" / "agents" / "openai.yaml"
    payload = load_yaml(path)
    permission_contract = payload.get("compatibility", {}).get("permission_contract", {}) if payload else {}
    add_check(checks, failures, "openai-yaml-present", bool(payload), "OpenAI permission metadata YAML is readable")
    add_check(
        checks,
        failures,
        "openai-yaml-permissions",
        sorted_strings(permission_contract.get("declared_capabilities")) == expected,
        "OpenAI YAML permission contract mirrors expected capabilities",
    )
    add_check(
        checks,
        failures,
        "openai-yaml-native-flag",
        isinstance(permission_contract.get("native_enforcement"), bool),
        "OpenAI YAML declares native_enforcement as a boolean",
    )
    return checks, failures


def probe_target(skill_dir: Path, package_dir: Path, target: str, expected: list[str]) -> dict[str, Any]:
    adapter_path = package_dir / "targets" / target / "adapter.json"
    checks: list[dict[str, Any]] = []
    failures: list[str] = []
    adapter = load_json(adapter_path)
    add_check(checks, failures, "adapter-present", bool(adapter), f"{target} adapter.json is readable")

    permission_contract = adapter.get("permission_contract", {}) if adapter else {}
    target_contract = adapter.get("target_permission_contract", {}) if adapter else {}
    add_check(checks, failures, "permission-contract-present", bool(permission_contract), f"{target} adapter includes permission_contract")
    add_check(checks, failures, "target-contract-present", bool(target_contract), f"{target} adapter includes target_permission_contract")
    add_check(
        checks,
        failures,
        "source-available",
        permission_contract.get("source_available") is True,
        f"{target} permission_contract links to an available trust report",
    )
    add_check(
        checks,
        failures,
        "declared-capabilities-match",
        sorted_strings(target_contract.get("declared_capabilities")) == expected,
        f"{target} target_permission_contract mirrors expected capabilities",
    )
    add_check(
        checks,
        failures,
        "capability-counts-present",
        isinstance(target_contract.get("capability_counts"), dict),
        f"{target} target_permission_contract includes capability_counts",
    )
    add_check(
        checks,
        failures,
        "native-enforcement-boolean",
        isinstance(target_contract.get("native_enforcement"), bool),
        f"{target} target_permission_contract declares native_enforcement as a boolean",
    )
    add_check(
        checks,
        failures,
        "representation-present",
        bool(str(target_contract.get("representation", "")).strip()),
        f"{target} target_permission_contract declares where permission metadata is represented",
    )
    add_check(
        checks,
        failures,
        "operator-note-present",
        bool(str(target_contract.get("operator_note", "")).strip()),
        f"{target} target_permission_contract includes an operator_note",
    )
    add_check(
        checks,
        failures,
        "review-required-matches",
        bool(target_contract.get("review_required")) == bool(expected),
        f"{target} review_required matches whether capabilities are required",
    )

    yaml_checks: list[dict[str, Any]] = []
    yaml_failures: list[str] = []
    if target == "openai":
        yaml_checks, yaml_failures = probe_openai_yaml(package_dir, expected)
        checks.extend(yaml_checks)
        failures.extend(yaml_failures)

    native = target_contract.get("native_enforcement")
    metadata_fallback = native is False and bool(target_contract.get("representation")) and bool(target_contract.get("operator_note"))
    assurance = "native-enforced" if native is True else ("metadata-fallback-explicit" if metadata_fallback else "missing")
    residual_risks = []
    if native is False:
        residual_risks.append("Client-native permission enforcement is not provided by this target; installer or operator must honor metadata.")
    return {
        "target": target,
        "status": "pass" if not failures else "fail",
        "adapter": display_path(adapter_path, skill_dir),
        "permission_model": str(target_contract.get("permission_model", "")),
        "native_enforcement": bool(native) if isinstance(native, bool) else None,
        "metadata_fallback_explicit": metadata_fallback,
        "assurance": assurance,
        "declared_capabilities": sorted_strings(target_contract.get("declared_capabilities")),
        "checks": checks,
        "failures": failures,
        "residual_risks": residual_risks,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Runtime Permission Probes",
        "",
        "Runtime permission probes verify that generated target adapters expose high-permission capabilities and make native-enforcement limits explicit.",
        "",
        "## Summary",
        "",
        f"- OK: `{report['ok']}`",
        f"- Targets probed: `{summary['target_count']}`",
        f"- Passed: `{summary['pass_count']}`",
        f"- Failed: `{summary['fail_count']}`",
        f"- Native enforcement targets: `{summary['native_enforcement_count']}`",
        f"- Explicit metadata fallbacks: `{summary['metadata_fallback_count']}`",
        f"- Required capabilities: `{', '.join(report['expected_capabilities']) or 'none'}`",
        "",
        "| Target | Status | Assurance | Native Enforcement | Metadata Fallback | Residual Risk |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for target in report["targets"]:
        residual = "<br>".join(target["residual_risks"]) if target["residual_risks"] else "None"
        lines.append(
            f"| `{target['target']}` | `{target['status']}` | `{target['assurance']}` | "
            f"`{target['native_enforcement']}` | `{target['metadata_fallback_explicit']}` | {residual} |"
        )
    lines.extend(["", "## Failures", ""])
    lines.extend([f"- {item}" for item in report["failures"]] or ["- None"])
    lines.extend(
        [
            "",
            "## Reviewer Note",
            "",
            "A passing probe means the target contract is explicit and auditable. It does not claim that a host client enforces permissions natively.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def probe_runtime_permissions(
    skill_dir: Path,
    package_dir: Path,
    targets: list[str],
    output_json: Path,
    output_md: Path,
) -> dict[str, Any]:
    skill_dir = skill_dir.resolve()
    package_dir = package_dir.resolve()
    expected = expected_capabilities(skill_dir)
    target_results = [probe_target(skill_dir, package_dir, target, expected) for target in targets]
    failures = [failure for target in target_results for failure in target["failures"]]
    summary = {
        "target_count": len(target_results),
        "pass_count": sum(1 for item in target_results if item["status"] == "pass"),
        "fail_count": sum(1 for item in target_results if item["status"] == "fail"),
        "native_enforcement_count": sum(1 for item in target_results if item["native_enforcement"] is True),
        "metadata_fallback_count": sum(1 for item in target_results if item["metadata_fallback_explicit"]),
        "residual_risk_count": sum(len(item["residual_risks"]) for item in target_results),
        "required_capability_count": len(expected),
        "failure_count": len(failures),
    }
    report = {
        "schema_version": "1.0",
        "ok": not failures,
        "skill_dir": display_path(skill_dir, skill_dir),
        "package_dir": display_path(package_dir, skill_dir),
        "expected_capabilities": expected,
        "summary": summary,
        "targets": target_results,
        "failures": failures,
        "artifacts": {
            "json": display_path(output_json, skill_dir),
            "markdown": display_path(output_md, skill_dir),
        },
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe generated target adapters for runtime permission enforcement metadata.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--package-dir", default="dist")
    parser.add_argument("--target", action="append", choices=DEFAULT_TARGETS)
    parser.add_argument("--output-json")
    parser.add_argument("--output-md")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    report = probe_runtime_permissions(
        skill_dir,
        Path(args.package_dir).resolve(),
        args.target or DEFAULT_TARGETS,
        Path(args.output_json).resolve() if args.output_json else skill_dir / "reports" / "runtime_permission_probes.json",
        Path(args.output_md).resolve() if args.output_md else skill_dir / "reports" / "runtime_permission_probes.md",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["ok"] else 2)


if __name__ == "__main__":
    main()
