"""Patch target and baseline hash checks for approval-gated adaptation."""

import hashlib
from pathlib import Path
from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Shared adaptation patch target parsing and target-file baseline verification helpers."

BLOCKED_PATH_PARTS = {".git", "__pycache__", ".pytest_cache", "dist"}
ABSENT_FILE_SHA256 = "__absent__"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def target_file_sha256(skill_dir: Path, target_files: list[str]) -> dict[str, str]:
    observed: dict[str, str] = {}
    for target in target_files:
        path = skill_dir / target
        observed[target] = sha256_file(path) if path.exists() else ABSENT_FILE_SHA256
    return observed


def normalize_patch_path(raw: str) -> str | None:
    token = raw.strip().split("\t", 1)[0].split(" ", 1)[0]
    if token == "/dev/null":
        return None
    if token.startswith("a/") or token.startswith("b/"):
        token = token[2:]
    path = Path(token)
    if path.is_absolute() or ".." in path.parts or any(part in BLOCKED_PATH_PARTS for part in path.parts):
        raise ValueError(f"Unsafe patch path: {raw}")
    if not token or token == ".":
        raise ValueError(f"Empty patch path: {raw}")
    return token


def patch_target_files(patch_text: str) -> list[str]:
    targets: set[str] = set()
    for line in patch_text.splitlines():
        if line.startswith("--- ") or line.startswith("+++ "):
            raw = line[4:].strip()
            path = normalize_patch_path(raw)
            if path:
                targets.add(path)
    return sorted(targets)


def validate_target_file_sha256(
    skill_dir: Path,
    target_files: list[str],
    expected_sha256: dict[str, Any],
) -> tuple[list[str], dict[str, str]]:
    failures: list[str] = []
    observed: dict[str, str] = {}
    for target in target_files:
        path = skill_dir / target
        expected = str(expected_sha256.get(target, ""))
        if not expected:
            failures.append(f"Approval target_file_sha256 missing target: {target}")
            continue
        if path.exists() and not path.is_file():
            failures.append(f"Patch target is not a file: {target}")
            continue
        current = sha256_file(path) if path.exists() else ABSENT_FILE_SHA256
        observed[target] = current
        if current != expected:
            failures.append(f"Target file baseline sha256 does not match approval ledger: {target}")
    return failures, observed
