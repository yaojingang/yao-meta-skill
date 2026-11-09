#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from cross_packager_sources import archive_source_paths  # noqa: E402
from verify_package import stale_source_entries  # noqa: E402


TMP = ROOT / "tests" / "tmp_package_verification"
PACKAGER = ROOT / "scripts" / "cross_packager.py"
VERIFIER = ROOT / "scripts" / "verify_package.py"
EXPECTATIONS = ROOT / "evals" / "packaging_expectations.json"


def run(cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    payload = {}
    if proc.stdout.strip():
        payload = json.loads(proc.stdout)
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "payload": payload,
    }


def build_package(out_dir: Path, skill_root: Path = ROOT) -> dict:
    return run(
        [
            sys.executable,
            str(PACKAGER),
            str(skill_root),
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
            str(out_dir),
            "--zip",
        ]
    )


def verify_package(out_dir: Path, output_json: Path, output_md: Path, skill_root: Path = ROOT) -> dict:
    return run(
        [
            sys.executable,
            str(VERIFIER),
            str(skill_root),
            "--package-dir",
            str(out_dir),
            "--expectations",
            str(EXPECTATIONS),
            "--registry-json",
            str(ROOT / "reports" / "registry_audit.json"),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
            "--require-zip",
            "--generated-at",
            "2026-06-13",
        ]
    )


def verify_source_entrypoint_scan() -> None:
    with tempfile.TemporaryDirectory(prefix="source-entrypoint-scan-") as temp_root:
        root = Path(temp_root)
        (root / "SKILL.md").write_text("root\n", encoding="utf-8")
        (root / "examples" / "demo").mkdir(parents=True)
        (root / "examples" / "demo" / "SKILL.md").write_text("nested\n", encoding="utf-8")
        (root / ".agents" / "skills" / "local-helper").mkdir(parents=True)
        (root / ".agents" / "skills" / "local-helper" / "SKILL.md").write_text("local\n", encoding="utf-8")

        assert source_skill_entries(root) == [
            Path("SKILL.md"),
            Path("examples/demo/SKILL.md"),
        ]


def verify_git_archive_source_boundary() -> None:
    with tempfile.TemporaryDirectory(prefix="archive-source-boundary-") as temp_root:
        root = Path(temp_root)
        (root / "scripts").mkdir()
        (root / "reports").mkdir()
        (root / "evidence" / "world_class" / "submissions").mkdir(parents=True)
        (root / "docs").mkdir()
        (root / "SKILL.md").write_text("tracked\n", encoding="utf-8")
        (root / "scripts" / "tracked.py").write_text("tracked = True\n", encoding="utf-8")
        (root / ".gitignore").write_text("ignored-secret.txt\n", encoding="utf-8")
        subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
        subprocess.run(["git", "add", "SKILL.md", "scripts/tracked.py", ".gitignore"], cwd=root, check=True)
        (root / "scripts" / "new_helper.py").write_text("new = True\n", encoding="utf-8")
        (root / "docs" / "new-guide.md").write_text("guide\n", encoding="utf-8")
        (root / "reports" / "private-research.md").write_text("private\n", encoding="utf-8")
        (root / "evidence" / "world_class" / "submissions" / "reviewer.json").write_text("{}\n", encoding="utf-8")
        (root / "ignored-secret.txt").write_text("secret\n", encoding="utf-8")

        candidates = {path.relative_to(root) for path in archive_source_paths(root)}
        assert Path("SKILL.md") in candidates, candidates
        assert Path("scripts/tracked.py") in candidates, candidates
        assert Path("scripts/new_helper.py") in candidates, candidates
        assert Path("docs/new-guide.md") in candidates, candidates
        assert Path("reports/private-research.md") not in candidates, candidates
        assert Path("evidence/world_class/submissions/reviewer.json") not in candidates, candidates
        assert Path("ignored-secret.txt") not in candidates, candidates

        nested_skill = root / "skills" / "nested-demo"
        (nested_skill / "scripts").mkdir(parents=True)
        (nested_skill / "reports").mkdir()
        (nested_skill / "SKILL.md").write_text("nested tracked\n", encoding="utf-8")
        (nested_skill / "scripts" / "tracked.py").write_text("tracked = True\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "skills/nested-demo/SKILL.md", "skills/nested-demo/scripts/tracked.py"],
            cwd=root,
            check=True,
        )
        (nested_skill / "scripts" / "new_helper.py").write_text("new = True\n", encoding="utf-8")
        (nested_skill / "reports" / "private-research.md").write_text("private\n", encoding="utf-8")

        nested_candidates = {path.relative_to(nested_skill) for path in archive_source_paths(nested_skill)}
        assert Path("SKILL.md") in nested_candidates, nested_candidates
        assert Path("scripts/tracked.py") in nested_candidates, nested_candidates
        assert Path("scripts/new_helper.py") in nested_candidates, nested_candidates
        assert Path("reports/private-research.md") not in nested_candidates, nested_candidates

        with patch("cross_packager_sources.subprocess.run", side_effect=FileNotFoundError("git")):
            try:
                archive_source_paths(nested_skill)
            except ValueError as exc:
                assert "git is unavailable" in str(exc), exc
            else:
                raise AssertionError("Git-backed packaging must fail closed when git is unavailable.")


def source_skill_entries(root: Path) -> list[Path]:
    entries = []
    for path in root.rglob("SKILL.md"):
        relative = path.relative_to(root)
        if relative.parts[0] in {".agents", ".git", ".yao", "dist"}:
            continue
        if len(relative.parts) >= 2 and relative.parts[0] == "tests" and relative.parts[1].startswith("tmp"):
            continue
        if (root / ".git").exists():
            ignored = subprocess.run(
                ["git", "check-ignore", "--quiet", "--", str(relative)],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            if ignored.returncode == 0:
                continue
        entries.append(relative)
    return sorted(entries)


def verify_deleted_source_snapshot() -> None:
    with tempfile.TemporaryDirectory(prefix="archive-deleted-source-") as temp_root:
        root = Path(temp_root).resolve()
        source = root / "resource.txt"
        source.write_text("current resource\n", encoding="utf-8")
        archive_path = root / "demo.zip"
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.write(source, "demo/resource.txt")
        with zipfile.ZipFile(archive_path) as archive:
            assert stale_source_entries(root, archive, "demo") == []
        source.unlink()
        with zipfile.ZipFile(archive_path) as archive:
            assert stale_source_entries(root, archive, "demo") == ["resource.txt"]


def main() -> None:
    verify_source_entrypoint_scan()
    verify_git_archive_source_boundary()
    verify_deleted_source_snapshot()
    source_entries = source_skill_entries(ROOT)
    assert source_entries == [Path("SKILL.md")], source_entries

    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True, exist_ok=True)

    valid_dir = TMP / "dist"
    build = build_package(valid_dir)
    assert build["ok"], build
    valid = verify_package(valid_dir, TMP / "package_verification.json", TMP / "package_verification.md")
    payload = valid["payload"]
    assert valid["ok"], valid
    assert payload["ok"], payload
    with zipfile.ZipFile(valid_dir / "yao-meta-skill.zip") as archive:
        assert not any("/reports/release_snapshots/" in name for name in archive.namelist()), archive.namelist()
        assert not any("/registry/packages/" in name for name in archive.namelist()), archive.namelist()
        assert "yao-meta-skill/registry/index.json" not in archive.namelist(), archive.namelist()
    assert payload["summary"]["target_count"] == 4, payload
    assert payload["summary"]["adapter_count"] == 4, payload
    assert payload["summary"]["archive_present"], payload
    assert payload["summary"]["archive_sha256"], payload
    assert payload["summary"]["nested_skill_entry_count"] == 0, payload
    assert not payload["failures"], payload
    assert (TMP / "package_verification.md").exists(), TMP
    with zipfile.ZipFile(valid_dir / "yao-meta-skill.zip") as archive:
        archive_names = archive.namelist()
        skill_entries = sorted(name for name in archive_names if name.endswith("/SKILL.md"))
    assert skill_entries == ["yao-meta-skill/SKILL.md"], skill_entries
    assert not [name for name in archive_names if "/geo-ranking-article-generator/" in name], archive_names
    assert not [name for name in archive_names if "/.yao/" in name], "local .yao state leaked into package"
    assert not [name for name in archive_names if "/evidence/world_class/submissions/" in name], "external submission draft leaked into package"
    assert not [
        name
        for name in archive_names
        if any(part in {".DS_Store", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__"} for part in Path(name).parts)
        or Path(name).suffix in {".pyc", ".pyo"}
    ], "cache or platform noise leaked into package"
    assert "yao-meta-skill/reports/.current-run.json" in archive_names, archive_names
    assert "yao-meta-skill/reports/artifact-index.json" in archive_names, archive_names
    with zipfile.ZipFile(valid_dir / "yao-meta-skill.zip") as archive:
        portable_pointer = json.loads(archive.read("yao-meta-skill/reports/.current-run.json"))
    assert portable_pointer["mode"] == "portable", portable_pointer

    first_hash = payload["summary"]["archive_sha256"]
    verification_report = ROOT / "reports" / "package_verification.json"
    original_verification = verification_report.read_bytes()
    try:
        verification_report.write_text('{"archive_sha256":"excluded-consumer-change"}\n', encoding="utf-8")
        rebuilt = build_package(valid_dir)
        assert rebuilt["ok"], rebuilt
        second_hash = __import__("hashlib").sha256((valid_dir / "yao-meta-skill.zip").read_bytes()).hexdigest()
    finally:
        verification_report.write_bytes(original_verification)
    assert second_hash == first_hash, (first_hash, second_hash)

    with tempfile.TemporaryDirectory(prefix="renamed-package-root-") as temp_root:
        renamed_root = Path(temp_root) / "checkout-alias"
        shutil.copytree(
            ROOT,
            renamed_root,
            ignore=shutil.ignore_patterns(".git", ".previews", ".yao", "dist", "__pycache__", ".pytest_cache", "tmp*"),
        )
        renamed_dir = TMP / "renamed-dist"
        renamed_build = build_package(renamed_dir, renamed_root)
        assert renamed_build["ok"], renamed_build
        assert (renamed_dir / "yao-meta-skill.zip").exists(), renamed_build
        with zipfile.ZipFile(renamed_dir / "yao-meta-skill.zip") as archive:
            names = set(archive.namelist())
        assert "yao-meta-skill/SKILL.md" in names, sorted(list(names))[:10]
        assert not [name for name in names if name.endswith("/SKILL.md") and name != "yao-meta-skill/SKILL.md"], names
        renamed_valid = verify_package(renamed_dir, TMP / "renamed_package_verification.json", TMP / "renamed_package_verification.md", renamed_root)
        assert renamed_valid["ok"], renamed_valid

        renamed_entry = renamed_root / "SKILL.md"
        renamed_entry.write_text(renamed_entry.read_text(encoding="utf-8") + "\nUpdated after packaging.\n", encoding="utf-8")
        stale = verify_package(renamed_dir, TMP / "stale_snapshot.json", TMP / "stale_snapshot.md", renamed_root)
        assert stale["returncode"] == 2, stale
        assert any(
            check["id"] == "archive-source-snapshot" and check["status"] == "fail"
            for check in stale["payload"]["checks"]
        ), stale
        refreshed_build = build_package(renamed_dir, renamed_root)
        assert refreshed_build["ok"], refreshed_build
        refreshed = verify_package(renamed_dir, TMP / "refreshed_snapshot.json", TMP / "refreshed_snapshot.md", renamed_root)
        assert refreshed["ok"], refreshed

    nested_skill_dir = TMP / "nested-skill-dist"
    shutil.copytree(valid_dir, nested_skill_dir)
    with zipfile.ZipFile(nested_skill_dir / "yao-meta-skill.zip", "a", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("yao-meta-skill/examples/demo/SKILL.md", "---\nname: demo\n---\n")
    nested = verify_package(nested_skill_dir, TMP / "nested_skill.json", TMP / "nested_skill.md")
    assert nested["returncode"] == 2, nested
    nested_payload = nested["payload"]
    assert nested_payload["summary"]["nested_skill_entry_count"] == 1, nested_payload
    assert any("Archive exposes only the root SKILL.md entrypoint" in item for item in nested_payload["failures"]), nested_payload

    unsafe_dir = TMP / "unsafe-dist"
    shutil.copytree(valid_dir, unsafe_dir)
    with zipfile.ZipFile(unsafe_dir / "yao-meta-skill.zip", "a", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("../evil.txt", "bad")
    unsafe = verify_package(unsafe_dir, TMP / "unsafe.json", TMP / "unsafe.md")
    assert unsafe["returncode"] == 2, unsafe
    unsafe_payload = unsafe["payload"]
    assert not unsafe_payload["ok"], unsafe_payload
    assert any("Archive has no absolute or parent-traversal entries" in item for item in unsafe_payload["failures"]), unsafe_payload

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
