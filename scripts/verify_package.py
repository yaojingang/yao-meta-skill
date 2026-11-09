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
        if (
            any(part in {".DS_Store", ".mypy_cache", ".previews", ".pytest_cache", ".ruff_cache", ".yao", "__pycache__", "dist"} for part in parts)
            or PurePosixPath(name).suffix in {".pyc", ".pyo"}
            or (len(parts) > 3 and parts[1:4] == ("evidence", "world_class", "submissions"))
            or (len(parts) > 2 and parts[1] == "tests" and any(part.startswith("tmp") for part in parts[2:]))
        ):
            generated.append(name)
    return generated


def non_root_skill_entries(names: list[str], package_root: str) -> list[str]:
    root_entry = f"{package_root}/SKILL.md"
    return sorted(name for name in names if PurePosixPath(name).name == "SKILL.md" and name != root_entry)


def stale_source_entries(skill_dir: Path, archive: zipfile.ZipFile, package_root: str) -> list[str]:
    portable_entries = {"reports/.current-run.json", "reports/artifact-index.json"}
    stale = []
    for name in archive.namelist():
        if unsafe_zip_entries([name]):
            continue
        member = PurePosixPath(name)
        if not member.parts or member.parts[0] != package_root:
            continue
        relative = PurePosixPath(*member.parts[1:])
        if relative.as_posix() in portable_entries:
            continue
        source = skill_dir.joinpath(*relative.parts)
        if source.is_symlink() or not source.resolve().is_relative_to(skill_dir):
            stale.append(relative.as_posix())
        elif not source.is_file():
            stale.append(relative.as_posix())
        else:
            try:
                if source.read_bytes() != archive.read(name):
                    stale.append(relative.as_posix())
            except OSError:
                stale.append(relative.as_posix())
    return sorted(stale)


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


def package_name(manifest: dict[str, Any], skill_dir: Path) -> str:
    return str(manifest.get("name") or skill_dir.name)


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
    package_root = package_name(manifest, skill_dir)
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

    archive_path = package_dir / f"{package_root}.zip"
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
            nested_skill_entries = non_root_skill_entries(archive_entries, package_root)
            required_entries = [
                f"{package_root}/SKILL.md",
                f"{package_root}/manifest.json",
                f"{package_root}/agents/interface.yaml",
            ]
            add_check(checks, failures, "archive-safe-paths", not unsafe_entries, "Archive has no absolute or parent-traversal entries")
            for entry in required_entries:
                add_check(checks, failures, f"archive-entry-{entry}", entry in archive_entries, f"Archive contains {entry}")
            add_check(
                checks,
                failures,
                "archive-single-skill-entrypoint",
                not nested_skill_entries,
                "Archive exposes only the root SKILL.md entrypoint",
            )
            generated_entries = generated_zip_entries(archive_entries)
            add_check(checks, failures, "archive-excludes-generated", not generated_entries, "Archive excludes local caches, platform noise, .yao state, external submission drafts, local evidence pointers, generated dist/, .previews/, and tests/tmp* contents")
            with zipfile.ZipFile(archive_path) as archive:
                stale_entries = stale_source_entries(skill_dir, archive, package_root)
                add_check(
                    checks, failures, "archive-source-snapshot", not stale_entries,
                    "Archive payload matches current source files, except its generated portable pointer and index"
                    + (f": stale files: {', '.join(stale_entries)}" if stale_entries else ""),
                )
                pointer_name = f"{package_root}/reports/.current-run.json"
                index_name = f"{package_root}/reports/artifact-index.json"
                try:
                    pointer = json.loads(archive.read(pointer_name))
                    portable_index_bytes = archive.read(index_name)
                    portable_index = json.loads(portable_index_bytes)
                except (KeyError, json.JSONDecodeError):
                    pointer = {}
                    portable_index = {}
                    portable_index_bytes = b""
                portable_failures = []
                if pointer.get("mode") != "portable":
                    portable_failures.append("portable pointer mode is missing")
                if pointer.get("artifact_index_sha256") != hashlib.sha256(portable_index_bytes).hexdigest():
                    portable_failures.append("portable artifact index hash does not match")
                for entry in portable_index.get("artifacts", []) if isinstance(portable_index, dict) else []:
                    member = f"{package_root}/{entry.get('path', '')}"
                    try:
                        content = archive.read(member)
                    except KeyError:
                        portable_failures.append(f"portable evidence artifact is missing: {member}")
                        continue
                    if hashlib.sha256(content).hexdigest() != entry.get("sha256"):
                        portable_failures.append(f"portable evidence artifact hash mismatch: {member}")
            add_check(
                checks,
                failures,
                "archive-portable-evidence-index",
                not portable_failures,
                "Archive includes a self-contained portable evidence pointer and verified report index"
                + (f": {'; '.join(portable_failures)}" if portable_failures else ""),
            )
    elif require_zip:
        add_check(checks, failures, "archive-present", False, f"Missing required package archive: {display_path(archive_path)}")
    else:
        warnings.append(f"Package archive not found: {display_path(archive_path)}")

    registry_package = registry.get("package", {}) if registry else {}
    if registry_package:
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
            "nested_skill_entry_count": len(non_root_skill_entries(archive_entries, package_root)),
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
        f"- Nested SKILL.md entries: `{summary.get('nested_skill_entry_count', 0)}`",
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
    parser.add_argument("skill_dir")
    parser.add_argument("--package-dir", default="dist")
    parser.add_argument("--expectations", default="evals/packaging_expectations.json")
    parser.add_argument("--registry-json", default="reports/registry_audit.json")
    parser.add_argument("--output-json", default="reports/package_verification.json")
    parser.add_argument("--output-md", default="reports/package_verification.md")
    parser.add_argument("--require-zip", action="store_true")
    parser.add_argument("--generated-at", default=str(date.today()))
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()

    def target_path(raw_path: str) -> Path:
        path = Path(raw_path).expanduser()
        return path.resolve() if path.is_absolute() else (skill_dir / path).resolve()

    package_dir = target_path(args.package_dir)
    expectations = load_json(target_path(args.expectations)) if args.expectations else {}
    registry = load_json(target_path(args.registry_json)) if args.registry_json else {}
    report = verify_package(skill_dir, package_dir, expectations, registry, args.require_zip, args.generated_at)

    output_json = target_path(args.output_json)
    output_md = target_path(args.output_md)
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
