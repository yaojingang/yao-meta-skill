#!/usr/bin/env python3
import argparse
import json
import shutil
import tempfile
import zipfile
from datetime import date, datetime
from pathlib import Path, PurePosixPath
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


ROOT = Path(__file__).resolve().parent.parent


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


def zip_names(zip_path: Path) -> list[str]:
    with zipfile.ZipFile(zip_path) as archive:
        return archive.namelist()


def unsafe_zip_entries(names: list[str]) -> list[str]:
    unsafe = []
    for name in names:
        pure = PurePosixPath(name)
        if pure.is_absolute() or ".." in pure.parts or name.startswith("\\") or (pure.parts and ":" in pure.parts[0]):
            unsafe.append(name)
    return unsafe


def top_level_dirs(names: list[str]) -> list[str]:
    roots = set()
    for name in names:
        parts = PurePosixPath(name).parts
        if parts:
            roots.add(parts[0])
    return sorted(roots)


def add_check(checks: list[dict[str, str]], failures: list[str], check_id: str, passed: bool, detail: str) -> None:
    checks.append({"id": check_id, "status": "pass" if passed else "fail", "detail": detail})
    if not passed:
        failures.append(detail)


def adapter_targets(adapter_root: Path) -> list[str]:
    targets_dir = adapter_root / "targets"
    if not targets_dir.exists():
        return []
    return sorted(path.name for path in targets_dir.iterdir() if path.is_dir())


def sorted_strings(value: Any) -> list[str]:
    return sorted(str(item) for item in value) if isinstance(value, list) else []


def parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def permission_policy_checks(
    installed_dir: Path | None,
    adapter_root: Path,
    targets: list[str],
    generated_at: str,
    checks: list[dict[str, str]],
    failures: list[str],
) -> dict[str, int]:
    installed = installed_dir is not None and installed_dir.exists() and installed_dir.is_dir()
    policy = load_json(installed_dir / "security" / "permission_policy.json") if installed else {}
    capabilities = policy.get("capabilities", {}) if isinstance(policy.get("capabilities"), dict) else {}
    generated_date = parse_date(generated_at[:10])
    enforced_count = 0
    permission_failure_start = len(failures)
    declared_capabilities: set[str] = set()

    add_check(checks, failures, "permission-policy-load", bool(capabilities), "Installed permission policy is readable")
    for target in targets:
        adapter = load_json(adapter_root / "targets" / target / "adapter.json")
        target_contract = adapter.get("target_permission_contract", {}) if isinstance(adapter, dict) else {}
        target_capabilities = sorted_strings(target_contract.get("declared_capabilities"))
        declared_capabilities.update(target_capabilities)
        add_check(
            checks,
            failures,
            f"permission-{target}-contract",
            bool(target_contract),
            f"{target} adapter exposes target permission contract for installer enforcement",
        )
        if not target_capabilities:
            continue
        for capability in target_capabilities:
            approval = capabilities.get(capability, {}) if isinstance(capabilities, dict) else {}
            enforcement = approval.get("target_enforcement", {}) if isinstance(approval.get("target_enforcement"), dict) else {}
            expires_at = str(approval.get("expires_at", "")).strip()
            expiry_date = parse_date(expires_at) if expires_at else None
            common_ok = (
                approval.get("decision") == "approved"
                and bool(str(approval.get("reviewer", "")).strip())
                and bool(str(approval.get("scope", "")).strip())
                and bool(str(approval.get("reason", "")).strip())
                and isinstance(approval.get("evidence"), list)
                and bool(approval.get("evidence"))
                and bool(enforcement)
                and expiry_date is not None
                and (generated_date is None or expiry_date >= generated_date)
            )
            add_check(
                checks,
                failures,
                f"permission-{target}-{capability}-approved",
                bool(common_ok),
                f"{target} capability {capability} has active reviewer approval",
            )
            target_enforcement_ok = bool(str(enforcement.get(target, "")).strip())
            add_check(
                checks,
                failures,
                f"permission-{target}-{capability}-target-enforcement",
                target_enforcement_ok,
                f"{target} capability {capability} has target enforcement note",
            )
            if common_ok and target_enforcement_ok:
                enforced_count += 1

    return {
        "installer_permission_enforced_count": enforced_count,
        "installer_permission_failure_count": len(failures) - permission_failure_start,
        "permission_target_count": len(targets),
        "permission_capability_count": len(declared_capabilities),
    }


def simulate_install(skill_dir: Path, package_dir: Path, install_root: Path | None, generated_at: str) -> dict[str, Any]:
    skill_dir = skill_dir.resolve()
    package_dir = package_dir.resolve()
    checks: list[dict[str, str]] = []
    failures: list[str] = []
    warnings: list[str] = []
    archive_path = package_dir / f"{skill_dir.name}.zip"
    package_manifest = load_json(package_dir / "manifest.json")
    installed_dir: Path | None = None
    archive_entries: list[str] = []

    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    if install_root is None:
        temp_dir = tempfile.TemporaryDirectory(prefix="yao-skill-install-")
        install_base = Path(temp_dir.name)
        install_root_is_temp = True
    else:
        requested_root = install_root.resolve()
        requested_root.mkdir(parents=True, exist_ok=True)
        install_base = requested_root / f"simulate-{skill_dir.name}"
        if install_base.exists():
            shutil.rmtree(install_base)
        install_base.mkdir(parents=True, exist_ok=True)
        install_root_is_temp = False

    try:
        add_check(checks, failures, "archive-present", archive_path.exists(), f"Package archive exists: {display_path(archive_path)}")
        if archive_path.exists():
            try:
                archive_entries = zip_names(archive_path)
            except zipfile.BadZipFile:
                add_check(checks, failures, "archive-readable", False, f"Archive is not a readable zip: {display_path(archive_path)}")
            else:
                unsafe_entries = unsafe_zip_entries(archive_entries)
                add_check(checks, failures, "archive-safe-paths", not unsafe_entries, "Archive has no absolute or parent-traversal entries")
                roots = top_level_dirs(archive_entries)
                add_check(checks, failures, "single-top-level", roots == [skill_dir.name], f"Archive top-level directory is {skill_dir.name}")
                if not unsafe_entries and roots:
                    with zipfile.ZipFile(archive_path) as archive:
                        archive.extractall(install_base)
                    installed_dir = install_base / roots[0]

        frontmatter = read_frontmatter(installed_dir / "SKILL.md") if installed_dir else {}
        source_manifest = load_json(installed_dir / "manifest.json") if installed_dir else {}
        interface_doc = load_yaml(installed_dir / "agents" / "interface.yaml") if installed_dir else {}
        add_check(checks, failures, "entrypoint-load", bool(frontmatter), "Installed SKILL.md frontmatter is readable")
        add_check(checks, failures, "entrypoint-name", frontmatter.get("name") == skill_dir.name, "Installed SKILL.md name matches package directory")
        add_check(checks, failures, "entrypoint-description", bool(frontmatter.get("description")), "Installed SKILL.md description is present")
        add_check(checks, failures, "manifest-load", bool(source_manifest), "Installed manifest.json is readable")
        add_check(checks, failures, "manifest-name", source_manifest.get("name") == package_manifest.get("name"), "Installed manifest name matches package manifest")
        add_check(checks, failures, "manifest-version", source_manifest.get("version") == package_manifest.get("version"), "Installed manifest version matches package manifest")
        add_check(checks, failures, "interface-load", bool(interface_doc.get("interface")), "Installed agents/interface.yaml is readable")
        add_check(
            checks,
            failures,
            "overview-report",
            installed_dir is not None and (installed_dir / "reports" / "skill-overview.html").exists(),
            "Installed overview report is present",
        )
        add_check(
            checks,
            failures,
            "review-studio-report",
            installed_dir is not None and (installed_dir / "reports" / "review-studio.html").exists(),
            "Installed Review Studio report is present",
        )

        adapter_root = package_dir
        adapters = adapter_targets(adapter_root)
        for target in adapters:
            adapter = load_json(adapter_root / "targets" / target / "adapter.json")
            add_check(checks, failures, f"adapter-{target}", bool(adapter), f"{target} adapter is readable after package install simulation")
            add_check(
                checks,
                failures,
                f"adapter-{target}-name",
                adapter.get("name") == package_manifest.get("name"),
                f"{target} adapter name matches package manifest",
            )

        permission_summary = permission_policy_checks(installed_dir, adapter_root, adapters, generated_at, checks, failures)
        if not adapters:
            warnings.append("No target adapters found in package directory.")

        if install_root_is_temp:
            install_root_display = "[temporary-install-root]"
            installed_dir_display = f"{install_root_display}/{installed_dir.name}" if installed_dir else ""
        else:
            install_root_display = display_path(install_base)
            installed_dir_display = display_path(installed_dir) if installed_dir else ""

        report = {
            "ok": not failures,
            "schema_version": "2.0",
            "generated_at": generated_at,
            "skill_dir": display_path(skill_dir),
            "package_dir": display_path(package_dir),
            "install_root": install_root_display,
            "installed_skill_dir": installed_dir_display,
            "summary": {
                "archive_present": archive_path.exists(),
                "archive_entry_count": len(archive_entries),
                "archive_extracted": bool(installed_dir and installed_dir.exists()),
                "entrypoint_loaded": bool(frontmatter),
                "manifest_loaded": bool(source_manifest),
                "interface_loaded": bool(interface_doc.get("interface")),
                "adapter_count": len(adapters),
                **permission_summary,
                "install_root_is_temp": install_root_is_temp,
                "failure_count": len(failures),
                "warning_count": len(warnings),
            },
            "checks": checks,
            "failures": failures,
            "warnings": warnings,
            "artifacts": {
                "archive": display_path(archive_path) if archive_path.exists() else "",
                "package_manifest": display_path(package_dir / "manifest.json"),
            },
        }
        return report
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Install Simulation",
        "",
        f"- OK: `{report['ok']}`",
        f"- Package directory: `{report['package_dir']}`",
        f"- Archive extracted: `{summary['archive_extracted']}`",
        f"- Entrypoint loaded: `{summary['entrypoint_loaded']}`",
        f"- Manifest loaded: `{summary['manifest_loaded']}`",
        f"- Interface loaded: `{summary['interface_loaded']}`",
        f"- Adapters readable: `{summary['adapter_count']}`",
        f"- Installer permissions enforced: `{summary.get('installer_permission_enforced_count', 0)}`",
        f"- Installer permission failures: `{summary.get('installer_permission_failure_count', 0)}`",
        f"- Failures: `{summary['failure_count']}`",
        f"- Warnings: `{summary['warning_count']}`",
        "",
        "## Checks",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for item in report["checks"]:
        lines.append(f"| `{item['id']}` | `{item['status']}` | {item['detail']} |")
    lines.extend(["", "## Failures", ""])
    lines.extend([f"- {item}" for item in report["failures"]] or ["- None"])
    lines.extend(["", "## Warnings", ""])
    lines.extend([f"- {item}" for item in report["warnings"]] or ["- None"])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate installing a generated skill package into a temporary local skill root.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--package-dir", default="dist")
    parser.add_argument("--install-root")
    parser.add_argument("--output-json", default="reports/install_simulation.json")
    parser.add_argument("--output-md", default="reports/install_simulation.md")
    parser.add_argument("--generated-at", default=str(date.today()))
    args = parser.parse_args()

    package_dir = Path(args.package_dir)
    if not package_dir.is_absolute():
        package_dir = Path.cwd() / package_dir
    install_root = Path(args.install_root) if args.install_root else None
    report = simulate_install(Path(args.skill_dir), package_dir, install_root, args.generated_at)

    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    report["artifacts"]["json"] = display_path(output_json)
    report["artifacts"]["markdown"] = display_path(output_md)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["ok"] else 2)


if __name__ == "__main__":
    main()
