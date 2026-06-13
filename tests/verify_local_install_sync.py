#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SYNC_SCRIPT = ROOT / "scripts" / "sync_local_install.py"
TMP = ROOT / "tests" / "tmp" / "local_install_sync"
PACKAGER = ROOT / "scripts" / "cross_packager.py"
EXPECTATIONS = ROOT / "evals" / "packaging_expectations.json"


def build_package(out_dir: Path) -> dict:
    proc = subprocess.run(
        [
            sys.executable,
            str(PACKAGER),
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
            str(out_dir),
            "--zip",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout) if proc.stdout.strip() else {}
    return {"ok": proc.returncode == 0, "payload": payload, "stderr": proc.stderr}


def rewrite_archive_json(package_dir: Path, relative_path: str, transform) -> None:
    archive_path = package_dir / "yao-meta-skill.zip"
    rewritten_path = package_dir / "yao-meta-skill.rewritten.zip"
    archive_member = f"yao-meta-skill/{relative_path}"
    replaced = False
    with zipfile.ZipFile(archive_path) as archive_in, zipfile.ZipFile(rewritten_path, "w", compression=zipfile.ZIP_DEFLATED) as archive_out:
        for info in archive_in.infolist():
            data = archive_in.read(info.filename)
            if info.filename == archive_member:
                payload = json.loads(data.decode("utf-8"))
                data = (json.dumps(transform(payload), ensure_ascii=False, indent=2) + "\n").encode("utf-8")
                replaced = True
            archive_out.writestr(info, data)
    assert replaced, archive_member
    rewritten_path.replace(archive_path)


def run_sync(install_dir: Path, package_dir: Path) -> dict:
    proc = subprocess.run(
        [
            sys.executable,
            str(SYNC_SCRIPT),
            "--install-dir",
            str(install_dir),
            "--package-dir",
            str(package_dir),
            "--generated-at",
            "2026-06-13",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout) if proc.stdout.strip() else {}
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "payload": payload,
    }


def run_sync_raw(install_dir: Path, package_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SYNC_SCRIPT),
            "--install-dir",
            str(install_dir),
            "--package-dir",
            str(package_dir),
            "--generated-at",
            "2026-06-13",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def main() -> None:
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True, exist_ok=True)
    package_dir = TMP / "dist"
    package = build_package(package_dir)
    assert package["ok"], package

    install_dir = TMP / "installed-skill"
    install_dir.mkdir(parents=True)
    (install_dir / "SKILL.md").write_text(
        "---\nname: yao-meta-skill\ndescription: local install fixture\n---\n",
        encoding="utf-8",
    )
    stale_file = install_dir / "stale.txt"
    stale_file.write_text("old install artifact\n", encoding="utf-8")
    git_config = install_dir / ".git" / "config"
    git_config.parent.mkdir(parents=True)
    git_config.write_text("[core]\n\trepositoryformatversion = 0\n", encoding="utf-8")

    untracked_file = ROOT / "sync-local-untracked.tmp"
    untracked_file.write_text("do not copy me\n", encoding="utf-8")
    try:
        result = run_sync(install_dir, package_dir)
    finally:
        untracked_file.unlink(missing_ok=True)

    policy_gap_dir = TMP / "policy-gap-dist"
    shutil.copytree(package_dir, policy_gap_dir)

    def remove_vscode_network_enforcement(payload: dict) -> dict:
        payload["capabilities"]["network"]["target_enforcement"].pop("vscode", None)
        return payload

    rewrite_archive_json(policy_gap_dir, "security/permission_policy.json", remove_vscode_network_enforcement)
    refused_install_dir = TMP / "preflight-refused-install"
    refused_install_dir.mkdir(parents=True)
    (refused_install_dir / "SKILL.md").write_text(
        "---\nname: yao-meta-skill\ndescription: local install fixture\n---\n",
        encoding="utf-8",
    )
    refused_stale = refused_install_dir / "stale.txt"
    refused_stale.write_text("must not be touched after preflight failure\n", encoding="utf-8")
    preflight_refused = run_sync_raw(refused_install_dir, policy_gap_dir)

    ordinary_dir = TMP / "ordinary-folder"
    ordinary_dir.mkdir(parents=True)
    ordinary_file = ordinary_dir / "keep.txt"
    ordinary_file.write_text("must survive a refused sync\n", encoding="utf-8")
    refused = run_sync_raw(ordinary_dir, package_dir)

    makefile_text = (ROOT / "Makefile").read_text(encoding="utf-8")
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")

    checks = {
        "sync_ok": result["ok"],
        "skill_md_copied": (install_dir / "SKILL.md").exists(),
        "script_copied": (install_dir / "scripts" / "yao.py").exists(),
        "untracked_file_skipped": not (install_dir / "sync-local-untracked.tmp").exists(),
        "untracked_business_skill_skipped": not (install_dir / "geo-ranking-article-generator").exists(),
        "stale_file_removed": not stale_file.exists(),
        "install_git_metadata_preserved": git_config.exists(),
        "install_sentinel_written": (install_dir / ".yao-local-install.json").exists(),
        "install_preflight_enforced": result["payload"]["install_preflight"]["installer_permission_enforced_count"] == 12,
        "install_preflight_permission_failures_zero": result["payload"]["install_preflight"]["installer_permission_failure_count"] == 0,
        "install_preflight_blocks_sync": preflight_refused.returncode != 0,
        "install_preflight_failure_preserves_files": refused_stale.exists(),
        "ordinary_dir_refused": refused.returncode != 0,
        "ordinary_dir_preserved": ordinary_file.exists(),
        "makefile_target_present": "sync-local-install" in makefile_text,
        "makefile_defaults_disabled": "LOCAL_SKILL_INSTALL_DIR ?= $(HOME)/.agents/skills.disabled/yao-meta-skill"
        in makefile_text,
        "makefile_active_opt_in_present": "sync-active-install" in makefile_text,
        "readme_names_development_source": "Development source" in readme_text,
        "readme_names_disabled_mirror": "~/.agents/skills.disabled/yao-meta-skill" in readme_text,
    }
    report = {
        "ok": all(checks.values()),
        "checks": checks,
        "sync_result": result,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
