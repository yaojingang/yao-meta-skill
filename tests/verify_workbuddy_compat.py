#!/usr/bin/env python3
"""Exercise the generic archive against WorkBuddy's published Skill contract."""

import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
TMP = ROOT / "tests" / "tmp_workbuddy_compat"
REQUIRED_FIELDS = (
    "name", "display_name", "display_name_en", "description",
    "description_zh", "description_en", "version", "author",
)


def run(*args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, *args], cwd=TMP, capture_output=True, text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result


def main() -> None:
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True)
    package = TMP / "package"
    run(
        str(ROOT / "scripts" / "yao.py"), "package", str(ROOT),
        "--platform", "generic", "--output-dir", str(package), "--zip", "--self",
    )
    with zipfile.ZipFile(package / "yao-meta-skill.zip") as archive:
        names = archive.namelist()
        assert [name for name in names if name.endswith("/SKILL.md")] == [
            "yao-meta-skill/SKILL.md"
        ]
        entry = archive.read("yao-meta-skill/SKILL.md").decode("utf-8")
        metadata = yaml.safe_load(entry.split("---", 2)[1])
        missing = [
            key for key in REQUIRED_FIELDS
            if not isinstance(metadata.get(key), str) or not metadata[key].strip()
        ]
        assert not missing, f"WorkBuddy required frontmatter fields missing: {missing}"
        manifest = json.loads(archive.read("yao-meta-skill/manifest.json"))
        assert metadata["name"] == manifest["name"]
        assert metadata["version"] == manifest["version"] == (ROOT / "VERSION").read_text().strip()
        assert metadata["author"] == manifest["owner"]
        assert "yao-meta-skill/references/workbuddy.md" in names
        for name in names:
            path = Path(name)
            assert not path.is_absolute() and ".." not in path.parts
            assert not {".yao", "__pycache__", ".DS_Store"}.intersection(path.parts), name
            mode = archive.getinfo(name).external_attr >> 16
            assert mode & 0o170000 != 0o120000, name
        installation = TMP / "含空格 workspace"
        archive.extractall(installation)

    installed = installation / "yao-meta-skill"
    entry_hash = hashlib.sha256((installed / "SKILL.md").read_bytes()).hexdigest()
    cli = str(installed / "scripts" / "yao.py")
    assert "usage:" in run(cli, "--help").stdout
    generated = TMP / "输出 skills"
    result = run(
        cli, "init", "workbuddy-demo", "--output-dir", str(generated),
        "--description", "Organize weekly notes into structured reports.",
    )
    assert json.loads(result.stdout)["ok"] is True
    assert (generated / "workbuddy-demo" / "SKILL.md").is_file()
    assert hashlib.sha256((installed / "SKILL.md").read_bytes()).hexdigest() == entry_hash
    print("WorkBuddy generic archive: metadata, resources, isolated CLI, and explicit output target passed.")


if __name__ == "__main__":
    main()
