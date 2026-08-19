#!/usr/bin/env python3
"""Isolated evidence runs, immutable bundles, and recoverable publishing."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

try:
    import fcntl
except ModuleNotFoundError:  # Windows has no fcntl; fall back to msvcrt region locks.
    fcntl = None
    import msvcrt


def _lock_exclusive_nonblocking(descriptor: int) -> None:
    """Raises BlockingIOError when the lock is held elsewhere, on both platforms."""
    if fcntl is not None:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return
    os.lseek(descriptor, 0, os.SEEK_SET)
    try:
        msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
    except OSError as exc:
        raise BlockingIOError(exc.errno, str(exc)) from exc


def _unlock(descriptor: int) -> None:
    if fcntl is not None:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        return
    os.lseek(descriptor, 0, os.SEEK_SET)
    msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by evidence-build and evidence consumers for transactional local evidence publishing."

RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
POINTER_PATH = Path("reports/.current-run.json")
CANONICAL_INDEX_PATH = Path("reports/artifact-index.json")
TRANSACTION_NAME = "publish-transaction.json"
ARTIFACT_MUTATION_NAME = ".artifact-mutation.json"


class EvidenceError(RuntimeError):
    """Stable evidence failure with a machine-readable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class EvidenceRun:
    run_id: str
    run_dir: Path
    manifest: dict[str, Any]
    artifact_index: dict[str, Any]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def read_json(path: Path, *, code: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError(code, f"Cannot read JSON artifact {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise EvidenceError(code, f"Expected a JSON object at {path}")
    return payload


def ensure_safe_child(root: Path, path: Path, *, code: str = "unsafe-artifact") -> Path:
    """Reject path escapes and symlinks in every existing component."""
    root = root.resolve()
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise EvidenceError(code, f"Path is outside its trusted root: {path}") from exc
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise EvidenceError(code, f"Path contains a symlink: {path}")
    try:
        path.resolve(strict=False).relative_to(root)
    except ValueError as exc:
        raise EvidenceError(code, f"Path escapes its trusted root: {path}") from exc
    return path


class EvidenceStore:
    """Per-skill local evidence workspace and publication store."""

    def __init__(self, skill_dir: Path | str) -> None:
        self.skill_dir = Path(skill_dir).resolve()
        if not (self.skill_dir / "SKILL.md").is_file():
            raise EvidenceError("invalid-skill-dir", f"Missing SKILL.md in {self.skill_dir}")
        self.state_dir = self.skill_dir / ".yao"
        self.runs_dir = self.state_dir / "runs"
        self.releases_dir = self.state_dir / "releases"
        self.transaction_path = self.state_dir / TRANSACTION_NAME

    def _validate_run_id(self, run_id: str) -> str:
        if not RUN_ID_PATTERN.fullmatch(run_id):
            raise EvidenceError("invalid-run-id", "run id must match [A-Za-z0-9][A-Za-z0-9._-]{0,63}")
        return run_id

    def _default_run_id(self) -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"{stamp}-{uuid.uuid4().hex[:10]}"

    def _skill_name(self) -> str:
        manifest_path = self.skill_dir / "manifest.json"
        if manifest_path.exists():
            payload = read_json(manifest_path, code="invalid-manifest")
            if isinstance(payload.get("name"), str) and payload["name"].strip():
                return payload["name"].strip()
        return self.skill_dir.name

    def _git_state(self) -> dict[str, Any]:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.skill_dir,
            capture_output=True,
            text=True,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=self.skill_dir,
            capture_output=True,
            text=True,
        )
        return {
            "commit": commit.stdout.strip() if commit.returncode == 0 else None,
            "dirty": status.returncode != 0 or bool(status.stdout.strip()),
        }

    def assert_clean(self) -> None:
        state = self._git_state()
        if state["commit"] is None:
            raise EvidenceError("git-required", "publishing requires a Git worktree")
        if state["dirty"]:
            raise EvidenceError("dirty-worktree", "publishing requires a clean Git worktree")

    def _git_ignored_reports(self, paths: list[Path]) -> set[Path]:
        if not paths:
            return set()
        repository = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=self.skill_dir,
            capture_output=True,
            text=True,
        )
        if repository.returncode != 0:
            return set()
        relative_paths = [path.relative_to(self.skill_dir) for path in paths]
        encoded = b"\0".join(os.fsencode(path.as_posix()) for path in relative_paths) + b"\0"
        ignored = subprocess.run(
            ["git", "check-ignore", "--stdin", "-z"],
            cwd=self.skill_dir,
            input=encoded,
            capture_output=True,
        )
        if ignored.returncode not in {0, 1}:
            raise EvidenceError("git-ignore-check-failed", "Cannot determine ignored evidence artifacts")
        return {
            self.skill_dir / Path(os.fsdecode(value))
            for value in ignored.stdout.split(b"\0")
            if value
        }

    def _report_sources(self) -> list[Path]:
        reports_dir = self.skill_dir / "reports"
        if not reports_dir.is_dir():
            raise EvidenceError("missing-reports", f"Missing reports directory in {self.skill_dir}")
        sources: list[Path] = []
        excluded = {POINTER_PATH.name, CANONICAL_INDEX_PATH.name}
        for path in sorted(reports_dir.rglob("*")):
            if path.is_symlink():
                raise EvidenceError("unsafe-artifact", f"Symlink evidence artifacts are forbidden: {path}")
            if not path.is_file() or path.parent == reports_dir and path.name in excluded:
                continue
            if path.is_relative_to(reports_dir / "release_snapshots"):
                continue
            try:
                path.resolve().relative_to(self.skill_dir)
            except ValueError as exc:
                raise EvidenceError("unsafe-artifact", f"Evidence artifact escapes the skill root: {path}") from exc
            sources.append(path)
        ignored = self._git_ignored_reports(sources)
        sources = [path for path in sources if path not in ignored]
        if not sources:
            raise EvidenceError("missing-artifacts", "No report artifacts are available to publish")
        return sources

    def build(self, run_id: str | None = None) -> EvidenceRun:
        selected_id = self._validate_run_id(run_id or self._default_run_id())
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        run_dir = self.runs_dir / selected_id
        try:
            run_dir.mkdir()
        except FileExistsError as exc:
            raise EvidenceError("run-exists", f"Run already exists: {selected_id}") from exc
        artifacts_dir = run_dir / "artifacts"
        artifacts_dir.mkdir()
        entries: list[dict[str, Any]] = []
        for source in self._report_sources():
            relative = source.relative_to(self.skill_dir)
            destination = artifacts_dir / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            entries.append(
                {
                    "path": relative.as_posix(),
                    "sha256": sha256_file(destination),
                    "size": destination.stat().st_size,
                }
            )
        git_state = self._git_state()
        artifact_index = {
            "schema_version": "1.0",
            "run_id": selected_id,
            "skill_name": self._skill_name(),
            "artifacts": entries,
        }
        atomic_write_json(run_dir / "artifact-index.json", artifact_index)
        manifest = {
            "schema_version": "1.0",
            "run_id": selected_id,
            "skill_name": self._skill_name(),
            "created_at": utc_now(),
            "source": git_state,
            "artifact_count": len(entries),
            "artifact_index_sha256": sha256_file(run_dir / "artifact-index.json"),
            "status": "built",
        }
        atomic_write_json(run_dir / "run-manifest.json", manifest)
        return EvidenceRun(selected_id, run_dir, manifest, artifact_index)

    def add_json_artifact(self, run: EvidenceRun, relative_path: str | Path, payload: dict[str, Any]) -> EvidenceRun:
        verified = self.verify_run(run.run_dir)
        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0] != "reports":
            raise EvidenceError("unsafe-artifact", f"Run artifacts must stay under reports/: {relative}")
        destination = verified.run_dir / "artifacts" / relative
        ensure_safe_child(verified.run_dir / "artifacts", destination)
        mutation_path = verified.run_dir / ARTIFACT_MUTATION_NAME
        old_exists = destination.is_file()
        mutation = {
            "schema_version": "1.0",
            "relative_path": relative.as_posix(),
            "old_exists": old_exists,
            "old_artifact": read_json(destination, code="invalid-run-artifact") if old_exists else None,
            "old_artifact_index": verified.artifact_index,
            "old_manifest": verified.manifest,
        }
        atomic_write_json(mutation_path, mutation)
        atomic_write_json(destination, payload)
        self._simulate_artifact_crash("after-artifact")
        entries = [item for item in verified.artifact_index["artifacts"] if item.get("path") != relative.as_posix()]
        entries.append(
            {
                "path": relative.as_posix(),
                "sha256": sha256_file(destination),
                "size": destination.stat().st_size,
            }
        )
        entries.sort(key=lambda item: str(item["path"]))
        artifact_index = dict(verified.artifact_index)
        artifact_index["artifacts"] = entries
        index_path = verified.run_dir / "artifact-index.json"
        atomic_write_json(index_path, artifact_index)
        self._simulate_artifact_crash("after-index")
        manifest = dict(verified.manifest)
        manifest["artifact_count"] = len(entries)
        manifest["artifact_index_sha256"] = sha256_file(index_path)
        atomic_write_json(verified.run_dir / "run-manifest.json", manifest)
        mutation_path.unlink()
        return EvidenceRun(verified.run_id, verified.run_dir, manifest, artifact_index)

    def _simulate_artifact_crash(self, point: str) -> None:
        if os.environ.get("YAO_EVIDENCE_ARTIFACT_CRASH_AFTER") == point:
            raise RuntimeError(f"simulated artifact mutation crash at {point}")

    def _recover_artifact_mutation(self, run_dir: Path) -> bool:
        mutation_path = run_dir / ARTIFACT_MUTATION_NAME
        if not mutation_path.exists():
            return False
        mutation = read_json(mutation_path, code="invalid-artifact-mutation")
        relative = Path(str(mutation.get("relative_path", "")))
        if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0] != "reports":
            raise EvidenceError("unsafe-artifact-mutation", f"Unsafe artifact mutation path: {relative}")
        artifacts_root = run_dir / "artifacts"
        destination = artifacts_root / relative
        ensure_safe_child(artifacts_root, destination, code="unsafe-artifact-mutation")
        if mutation.get("old_exists") is True:
            old_artifact = mutation.get("old_artifact")
            if not isinstance(old_artifact, dict):
                raise EvidenceError("invalid-artifact-mutation", "Artifact mutation is missing its rollback payload")
            atomic_write_json(destination, old_artifact)
        else:
            with contextlib.suppress(FileNotFoundError):
                destination.unlink()
        old_index = mutation.get("old_artifact_index")
        old_manifest = mutation.get("old_manifest")
        if not isinstance(old_index, dict) or not isinstance(old_manifest, dict):
            raise EvidenceError("invalid-artifact-mutation", "Artifact mutation is missing rollback metadata")
        atomic_write_json(run_dir / "artifact-index.json", old_index)
        atomic_write_json(run_dir / "run-manifest.json", old_manifest)
        mutation_path.unlink()
        return True

    def add_private_json(self, run: EvidenceRun, relative_path: str | Path, payload: dict[str, Any]) -> Path:
        """Write run-local private material that can never enter a release artifact index."""
        verified = self.verify_run(run.run_dir)
        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise EvidenceError("unsafe-private-artifact", f"Unsafe private run path: {relative}")
        destination = verified.run_dir / "private" / relative
        ensure_safe_child(verified.run_dir / "private", destination, code="unsafe-private-artifact")
        atomic_write_json(destination, payload)
        return destination

    def verify_run(self, run_dir: Path | str) -> EvidenceRun:
        resolved = Path(run_dir).resolve()
        try:
            resolved.relative_to(self.runs_dir.resolve())
        except ValueError as exc:
            raise EvidenceError("unsafe-run-path", f"Run is outside this skill: {resolved}") from exc
        self._recover_artifact_mutation(resolved)
        manifest = read_json(resolved / "run-manifest.json", code="invalid-run-manifest")
        index_path = resolved / "artifact-index.json"
        artifact_index = read_json(index_path, code="invalid-artifact-index")
        if manifest.get("artifact_index_sha256") != sha256_file(index_path):
            raise EvidenceError("artifact-index-hash-mismatch", f"Artifact index was modified: {index_path}")
        run_id = str(manifest.get("run_id", ""))
        self._validate_run_id(run_id)
        if artifact_index.get("run_id") != run_id or manifest.get("skill_name") != self._skill_name():
            raise EvidenceError("run-identity-mismatch", "Run identity does not match the target skill")
        artifacts_root = resolved / "artifacts"
        for entry in artifact_index.get("artifacts", []):
            relative = Path(str(entry.get("path", "")))
            if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0] != "reports":
                raise EvidenceError("unsafe-artifact", f"Unsafe artifact path in index: {relative}")
            path = artifacts_root / relative
            ensure_safe_child(artifacts_root, path)
            if path.is_symlink() or not path.is_file():
                raise EvidenceError("unsafe-artifact", f"Missing or unsafe artifact: {relative}")
            if sha256_file(path) != entry.get("sha256"):
                raise EvidenceError("artifact-hash-mismatch", f"Artifact hash mismatch: {relative}")
        return EvidenceRun(run_id, resolved, manifest, artifact_index)

    @contextlib.contextmanager
    def publish_lock(self) -> Iterator[None]:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        lock_path = self.state_dir / "publish.lock"
        descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            try:
                _lock_exclusive_nonblocking(descriptor)
            except BlockingIOError as exc:
                raise EvidenceError("publish-locked", f"Another evidence publish holds {lock_path}") from exc
            os.ftruncate(descriptor, 0)
            os.write(descriptor, f"pid={os.getpid()}\n".encode())
            yield
        finally:
            with contextlib.suppress(OSError):
                _unlock(descriptor)
            os.close(descriptor)

    def _restore_bundle(self, bundle_dir: Path, *, expected_index_sha256: str | None = None) -> None:
        index_path = bundle_dir / "artifact-index.json"
        if expected_index_sha256 and sha256_file(index_path) != expected_index_sha256:
            raise EvidenceError("release-hash-mismatch", "Immutable release artifact index was modified")
        index = read_json(index_path, code="invalid-artifact-index")
        artifacts_root = (bundle_dir / "artifacts").resolve()
        for entry in index.get("artifacts", []):
            relative = Path(str(entry["path"]))
            if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0] != "reports":
                raise EvidenceError("unsafe-artifact", f"Unsafe release artifact path: {relative}")
            source = bundle_dir / "artifacts" / relative
            ensure_safe_child(artifacts_root, source)
            if source.is_symlink() or not source.is_file() or sha256_file(source) != entry.get("sha256"):
                raise EvidenceError("release-hash-mismatch", f"Immutable release is invalid: {relative}")
            destination = self.skill_dir / relative
            cursor = self.skill_dir
            for part in relative.parts:
                cursor /= part
                if cursor.is_symlink():
                    raise EvidenceError("unsafe-artifact", f"Canonical artifact path contains a symlink: {relative}")
            try:
                destination.resolve(strict=False).relative_to(self.skill_dir)
            except ValueError as exc:
                raise EvidenceError("unsafe-artifact", f"Canonical artifact escapes the skill root: {relative}") from exc
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        atomic_write_json(self.skill_dir / CANONICAL_INDEX_PATH, index)

    def _snapshot_canonical(self, run: EvidenceRun) -> dict[str, Any]:
        snapshot_dir = self.state_dir / "publish-snapshots" / f"{run.run_id}-{uuid.uuid4().hex[:10]}"
        files_dir = snapshot_dir / "files"
        files_dir.mkdir(parents=True)
        records: list[dict[str, Any]] = []
        for entry in run.artifact_index.get("artifacts", []):
            relative = Path(str(entry.get("path", "")))
            source = self.skill_dir / relative
            record = {"path": relative.as_posix(), "existed": source.is_file() and not source.is_symlink()}
            if record["existed"]:
                destination = files_dir / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            records.append(record)
        control: dict[str, Any] = {}
        for label, relative in (("pointer", POINTER_PATH), ("index", CANONICAL_INDEX_PATH)):
            source = self.skill_dir / relative
            exists = source.is_file() and not source.is_symlink()
            control[label] = {"path": relative.as_posix(), "existed": exists}
            if exists:
                destination = files_dir / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
        return {
            "snapshot_dir": snapshot_dir.relative_to(self.skill_dir).as_posix(),
            "files": records,
            "control": control,
        }

    def _restore_snapshot(self, transaction: dict[str, Any]) -> None:
        snapshot_relative = Path(str(transaction.get("snapshot", {}).get("snapshot_dir", "")))
        if snapshot_relative.is_absolute() or ".." in snapshot_relative.parts:
            raise EvidenceError("unsafe-recovery-snapshot", "Publish recovery snapshot path is unsafe")
        snapshot_dir = self.skill_dir / snapshot_relative
        ensure_safe_child(self.state_dir, snapshot_dir, code="unsafe-recovery-snapshot")
        snapshot = transaction.get("snapshot", {}) if isinstance(transaction.get("snapshot"), dict) else {}
        records = [*snapshot.get("files", []), *snapshot.get("control", {}).values()]
        for record in records:
            if not isinstance(record, dict):
                continue
            relative = Path(str(record.get("path", "")))
            if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0] != "reports":
                raise EvidenceError("unsafe-recovery-snapshot", f"Unsafe recovery target: {relative}")
            destination = self.skill_dir / relative
            ensure_safe_child(self.skill_dir, destination, code="unsafe-recovery-snapshot")
            if record.get("existed") is True:
                source = snapshot_dir / "files" / relative
                ensure_safe_child(snapshot_dir, source, code="unsafe-recovery-snapshot")
                if not source.is_file():
                    raise EvidenceError("recovery-snapshot-missing", f"Missing recovery snapshot: {relative}")
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            else:
                with contextlib.suppress(FileNotFoundError):
                    destination.unlink()

    def _recover_locked(self) -> bool:
        if not self.transaction_path.exists():
            return False
        transaction = read_json(self.transaction_path, code="invalid-publish-transaction")
        self._restore_snapshot(transaction)
        previous_pointer = transaction.get("previous_pointer")
        if isinstance(previous_pointer, dict):
            previous = self.skill_dir / str(previous_pointer.get("release_dir", ""))
            ensure_safe_child(self.releases_dir, previous, code="unsafe-release-path")
            self._restore_bundle(
                previous,
                expected_index_sha256=str(previous_pointer.get("artifact_index_sha256", "")) or None,
            )
            atomic_write_json(self.skill_dir / POINTER_PATH, previous_pointer)
        release_relative = Path(str(transaction.get("release_dir", "")))
        if release_relative.parts:
            release_dir = self.skill_dir / release_relative
            ensure_safe_child(self.releases_dir, release_dir, code="unsafe-release-path")
            if release_dir.exists():
                shutil.rmtree(release_dir)
        snapshot_relative = Path(str(transaction.get("snapshot", {}).get("snapshot_dir", "")))
        snapshot_dir = self.skill_dir / snapshot_relative
        if snapshot_dir.exists():
            shutil.rmtree(snapshot_dir)
        self.transaction_path.unlink()
        return True

    def recover(self) -> bool:
        with self.publish_lock():
            return self._recover_locked()

    def _simulate_crash(self, crash_at: str | None, point: str) -> None:
        if crash_at == point:
            raise RuntimeError(f"simulated publish crash at {point}")

    def publish(self, run: EvidenceRun, *, crash_at: str | None = None) -> Path:
        verified = self.verify_run(run.run_dir)
        expected_index_sha256 = verified.manifest.get("artifact_index_sha256")
        expected_manifest_sha256 = sha256_file(verified.run_dir / "run-manifest.json")
        with self.publish_lock():
            self._recover_locked()
            self.assert_clean()
            locked_run = self.verify_run(run.run_dir)
            if (
                locked_run.manifest.get("artifact_index_sha256") != expected_index_sha256
                or sha256_file(locked_run.run_dir / "run-manifest.json") != expected_manifest_sha256
            ):
                raise EvidenceError("run-changed", "Evidence run changed after pre-publish verification")
            release_dir = self.releases_dir / locked_run.run_id
            if release_dir.exists():
                raise EvidenceError("immutable-release-exists", f"Immutable release already exists: {locked_run.run_id}")
            source = locked_run.manifest.get("source", {})
            current = self._git_state()
            if source.get("dirty") is not False or source.get("commit") != current.get("commit"):
                raise EvidenceError("run-source-mismatch", "Evidence run was not built from the current clean source commit")
            verified = locked_run
            self.releases_dir.mkdir(parents=True, exist_ok=True)
            snapshot = self._snapshot_canonical(verified)
            previous_pointer = (
                read_json(self.skill_dir / POINTER_PATH, code="invalid-current-run")
                if (self.skill_dir / POINTER_PATH).exists()
                else None
            )
            transaction = {
                "schema_version": "1.0",
                "run_id": verified.run_id,
                "started_at": utc_now(),
                "previous_pointer": previous_pointer,
                "release_dir": release_dir.relative_to(self.skill_dir).as_posix(),
                "snapshot": snapshot,
            }
            atomic_write_json(self.transaction_path, transaction)
            release_dir.mkdir()
            shutil.copy2(verified.run_dir / "run-manifest.json", release_dir / "run-manifest.json")
            shutil.copy2(verified.run_dir / "artifact-index.json", release_dir / "artifact-index.json")
            shutil.copytree(verified.run_dir / "artifacts", release_dir / "artifacts")
            self._simulate_crash(crash_at, "after-release")
            self._restore_bundle(release_dir)
            self._simulate_crash(crash_at, "after-mirrors")
            self._simulate_crash(crash_at, "before-pointer")
            pointer = {
                "schema_version": "1.0",
                "run_id": verified.run_id,
                "skill_name": verified.manifest["skill_name"],
                "release_dir": release_dir.relative_to(self.skill_dir).as_posix(),
                "artifact_index": CANONICAL_INDEX_PATH.as_posix(),
                "artifact_index_sha256": sha256_file(release_dir / "artifact-index.json"),
                "published_at": utc_now(),
            }
            atomic_write_json(self.skill_dir / POINTER_PATH, pointer)
            self.transaction_path.unlink()
            snapshot_dir = self.skill_dir / Path(snapshot["snapshot_dir"])
            if snapshot_dir.exists():
                shutil.rmtree(snapshot_dir)
            return release_dir
