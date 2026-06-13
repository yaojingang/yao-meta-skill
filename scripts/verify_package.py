#!/usr/bin/env python3
import argparse
import hashlib
import json
import zipfile
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def generated_zip_entries(names: list[str]) -> list[str]:
    generated = []
    for name in names:
        parts = PurePosixPath(name).parts
        if "dist" in parts or (len(parts) > 2 and parts[1] == "tests" and any(part.startswith("tmp") for part in parts[2:])):
            generated.append(name)
    return generated


def required_targets(expectations: dict[str, Any], package_dir: Path) -> list[str]:
    targets = expectations.get("required_targets") or []
    if targets:
        return [str(item) for item in targets]
    targets_dir = package_dir / "targets"
    if not targets_dir.exists():
        return []
    return sorted(path.name for path in targets_dir.iterdir() if path.is_dir())


def add_check(checks: list[dict[str, str]], failures: list[str], check_id: str, passed: bool, detail: str) -> None:
    checks.append({"id": check_id, "status": "pass" if passed else "fail", "detail": detail})
    if not passed:
        failures.append(detail)


def verify_package(
    skill_dir: Path,
    package_dir: Path,
    expectations: dict[str, Any],
    registry: dict[str, Any],
    require_zip: bool,
    generated_at: str,
) -> dict[str, Any]:
    skill_dir = skill_dir.resolve()
    package_dir = package_dir.resolve()
    checks: list[dict[str, str]] = []
    failures: list[str] = []
    warnings: list[str] = []

    manifest_path = package_dir / "manifest.json"
    manifest = load_json(manifest_path)
    add_check(checks, failures, "package-manifest", bool(manifest), f"Package manifest exists: {display_path(manifest_path)}")

    targets = required_targets(expectations, package_dir)
    adapter_paths = []
    for target in targets:
        adapter_path = package_dir / "targets" / target / "adapter.json"
        adapter_paths.append(adapter_path)
        adapter = load_json(adapter_path)
        add_check(checks, failures, f"{target}-adapter", bool(adapter), f"Adapter exists for target: {target}")
        for field in expectations.get("required_fields", []):
            add_check(
                checks,
                failures,
                f"{target}-field-{field}",
                field in adapter,
                f"{target} adapter includes field: {field}",
            )
    required_files_by_target = {
        key[: -len("_required_files")]: value
        for key, value in expectations.items()
        if key.endswith("_required_files")
    }
    for target, required_files in required_files_by_target.items():
        for rel in required_files:
            add_check(checks, failures, f"{target}-file-{rel}", (package_dir / rel).exists(), f"Package contains {rel}")

    archive_path = package_dir / f"{skill_dir.name}.zip"
    archive_sha = ""
    archive_entries: list[str] = []
    if archive_path.exists():
        archive_sha = sha256_file(archive_path)
        try:
            archive_entries = zip_names(archive_path)
        except zipfile.BadZipFile:
            add_check(checks, failures, "archive-readable", False, f"Archive is not a readable zip: {display_path(archive_path)}")
        else:
            unsafe_entries = unsafe_zip_entries(archive_entries)
            required_entries = [
                f"{skill_dir.name}/SKILL.md",
                f"{skill_dir.name}/manifest.json",
                f"{skill_dir.name}/agents/interface.yaml",
            ]
            add_check(checks, failures, "archive-safe-paths", not unsafe_entries, "Archive has no absolute or parent-traversal entries")
            for entry in required_entries:
                add_check(checks, failures, f"archive-entry-{entry}", entry in archive_entries, f"Archive contains {entry}")
            generated_entries = generated_zip_entries(archive_entries)
            add_check(checks, failures, "archive-excludes-generated", not generated_entries, "Archive excludes generated dist/ and tests/tmp* contents")
    elif require_zip:
        add_check(checks, failures, "archive-present", False, f"Missing required package archive: {display_path(archive_path)}")
    else:
        warnings.append(f"Package archive not found: {display_path(archive_path)}")

    registry_package = registry.get("package", {}) if registry else {}
    if registry_package:
        add_check(checks, failures, "registry-ok", bool(registry.get("ok")), "Registry audit is OK")
        add_check(
            checks,
            failures,
            "registry-name-match",
            registry_package.get("name") == manifest.get("name"),
            "Registry package name matches package manifest",
        )
        add_check(
            checks,
            failures,
            "registry-version-match",
            registry_package.get("version") == manifest.get("version"),
            "Registry package version matches package manifest",
        )
        compatibility = registry_package.get("compatibility", {})
        for target in targets:
            add_check(
                checks,
                failures,
                f"registry-compat-{target}",
                compatibility.get(target) in {"pass", "warn"},
                f"Registry compatibility is reviewable for target: {target}",
            )
    else:
        warnings.append("Registry audit was not supplied; package verification skipped metadata parity checks.")

    report = {
        "ok": not failures,
        "schema_version": "2.0",
        "generated_at": generated_at,
        "skill_dir": display_path(skill_dir),
        "package_dir": display_path(package_dir),
        "summary": {
            "target_count": len(targets),
            "adapter_count": sum(1 for path in adapter_paths if path.exists()),
            "archive_present": archive_path.exists(),
            "archive_sha256": archive_sha,
            "archive_entry_count": len(archive_entries),
            "failure_count": len(failures),
            "warning_count": len(warnings),
        },
        "checks": checks,
        "failures": failures,
        "warnings": warnings,
        "artifacts": {
            "manifest": display_path(manifest_path),
            "archive": display_path(archive_path) if archive_path.exists() else "",
        },
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Package Verification",
        "",
        f"- OK: `{report['ok']}`",
        f"- Package directory: `{report['package_dir']}`",
        f"- Targets: `{summary['adapter_count']} / {summary['target_count']}` adapters present",
        f"- Archive present: `{summary['archive_present']}`",
        f"- Archive SHA256: `{summary['archive_sha256'] or 'n/a'}`",
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
    parser = argparse.ArgumentParser(description="Verify generated skill package artifacts and archive integrity.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--package-dir", default="dist")
    parser.add_argument("--expectations", default="evals/packaging_expectations.json")
    parser.add_argument("--registry-json", default="reports/registry_audit.json")
    parser.add_argument("--output-json", default="reports/package_verification.json")
    parser.add_argument("--output-md", default="reports/package_verification.md")
    parser.add_argument("--require-zip", action="store_true")
    parser.add_argument("--generated-at", default=str(date.today()))
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir)
    package_dir = Path(args.package_dir)
    if not package_dir.is_absolute():
        package_dir = Path.cwd() / package_dir
    expectations = load_json(Path(args.expectations)) if args.expectations else {}
    registry = load_json(Path(args.registry_json)) if args.registry_json else {}
    report = verify_package(skill_dir, package_dir, expectations, registry, args.require_zip, args.generated_at)

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
