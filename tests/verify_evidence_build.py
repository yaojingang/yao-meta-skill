#!/usr/bin/env python3
"""Behavior tests for isolated evidence runs and immutable publishing."""

from __future__ import annotations

import json
import contextlib
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from evidence_resolver import resolve_evidence_path  # noqa: E402
from evidence_store import EvidenceError, EvidenceStore  # noqa: E402


def try_symlink(link: Path, target: Path, *, target_is_directory: bool = False) -> bool:
    """False when the platform refuses symlinks (Windows without Developer Mode or admin)."""
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except OSError:
        return False
    return True


def write_skill(root: Path, name: str, marker: str) -> None:
    (root / "reports").mkdir(parents=True)
    (root / "agents").mkdir()
    (root / "SKILL.md").write_text(
        f'---\nname: {name}\ndescription: "Generate {name} evidence."\n---\n\n# {name}\n',
        encoding="utf-8",
    )
    (root / "agents" / "interface.yaml").write_text("interface:\n  display_name: Demo\n", encoding="utf-8")
    (root / "manifest.json").write_text(
        json.dumps({"name": name, "version": "1.0.0", "updated_at": "2026-08-12"}),
        encoding="utf-8",
    )
    (root / "reports" / "quality.json").write_text(json.dumps({"marker": marker}), encoding="utf-8")
    (root / "reports" / "local-private.json").write_text(
        json.dumps({"private": True}),
        encoding="utf-8",
    )
    (root / "reports" / "release_snapshots" / name).mkdir(parents=True)
    (root / "reports" / "release_snapshots" / name / "local.json").write_text(
        json.dumps({"local_only": True}),
        encoding="utf-8",
    )
    (root / ".gitignore").write_text(".yao/\nreports/local-private.json\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Evidence Test"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "evidence@example.test"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="yao-evidence-") as temp:
        temp_root = Path(temp)
        alpha = temp_root / "alpha-skill"
        beta = temp_root / "beta-skill"
        alpha.mkdir()
        beta.mkdir()
        write_skill(alpha, "alpha-skill", "alpha-v1")
        write_skill(beta, "beta-skill", "beta-v1")

        alpha_store = EvidenceStore(alpha)
        beta_store = EvidenceStore(beta)
        alpha_run = alpha_store.build("alpha-run")
        beta_run = beta_store.build("beta-run")
        assert alpha_run.run_dir.parent == (alpha / ".yao" / "runs").resolve(), alpha_run
        assert beta_run.run_dir.parent == (beta / ".yao" / "runs").resolve(), beta_run
        assert alpha_run.manifest["skill_name"] == "alpha-skill", alpha_run.manifest
        assert beta_run.manifest["skill_name"] == "beta-skill", beta_run.manifest
        assert not any("release_snapshots" in item["path"] for item in alpha_run.artifact_index["artifacts"])
        assert not any(
            item["path"] == "reports/local-private.json" for item in alpha_run.artifact_index["artifacts"]
        ), alpha_run.artifact_index

        for crash_point in ("after-artifact", "after-index"):
            before_manifest = json.loads((beta_run.run_dir / "run-manifest.json").read_text(encoding="utf-8"))
            before_index = json.loads((beta_run.run_dir / "artifact-index.json").read_text(encoding="utf-8"))
            try:
                os.environ["YAO_EVIDENCE_ARTIFACT_CRASH_AFTER"] = crash_point
                beta_store.add_json_artifact(beta_run, "reports/crash-test.json", {"point": crash_point})
            except RuntimeError as exc:
                assert "simulated artifact mutation crash" in str(exc), exc
            else:
                raise AssertionError(f"{crash_point} mutation crash point did not fire")
            finally:
                os.environ.pop("YAO_EVIDENCE_ARTIFACT_CRASH_AFTER", None)
            beta_run = beta_store.verify_run(beta_run.run_dir)
            assert beta_run.manifest == before_manifest, beta_run.manifest
            assert beta_run.artifact_index == before_index, beta_run.artifact_index
            assert not (beta_run.run_dir / "artifacts" / "reports" / "crash-test.json").exists()
            assert not (beta_run.run_dir / ".artifact-mutation.json").exists()

        try:
            alpha_store.build("../escape")
        except EvidenceError as exc:
            assert exc.code == "invalid-run-id", exc
        else:
            raise AssertionError("path traversal run id was accepted")

        outside = temp_root / "outside.json"
        outside.write_text("{}", encoding="utf-8")
        if try_symlink(alpha / "reports" / "escape.json", outside):
            try:
                alpha_store.build("symlink-run")
            except EvidenceError as exc:
                assert exc.code == "unsafe-artifact", exc
            else:
                raise AssertionError("symlink artifact was accepted")
            (alpha / "reports" / "escape.json").unlink()
        else:
            print("skipped symlink artifact case: platform does not permit symlinks")

        (alpha_run.run_dir / "raw-outputs").mkdir()
        (alpha_run.run_dir / "raw-outputs" / "private.txt").write_text("raw provider output", encoding="utf-8")
        first_release = alpha_store.publish(alpha_run)
        pointer = json.loads((alpha / "reports" / ".current-run.json").read_text(encoding="utf-8"))
        assert pointer["run_id"] == "alpha-run", pointer
        assert first_release == (alpha / ".yao" / "releases" / "alpha-run").resolve(), first_release
        assert not (first_release / "raw-outputs").exists(), first_release
        assert json.loads((alpha / "reports" / "quality.json").read_text(encoding="utf-8"))["marker"] == "alpha-v1"
        subprocess.run(["git", "add", "reports/.current-run.json", "reports/artifact-index.json"], cwd=alpha, check=True)
        subprocess.run(["git", "commit", "-qm", "publish pointer"], cwd=alpha, check=True)
        try:
            alpha_store.publish(alpha_run)
        except EvidenceError as exc:
            assert exc.code == "immutable-release-exists", exc
        else:
            raise AssertionError("immutable release was overwritten")

        tampered = alpha_run.run_dir / "artifacts" / "reports" / "quality.json"
        tampered.write_text(json.dumps({"marker": "tampered"}), encoding="utf-8")
        try:
            alpha_store.verify_run(alpha_run.run_dir)
        except EvidenceError as exc:
            assert exc.code == "artifact-hash-mismatch", exc
        else:
            raise AssertionError("tampered run passed verification")

        (alpha / "reports" / "quality.json").write_text(json.dumps({"marker": "alpha-v2"}), encoding="utf-8")
        subprocess.run(["git", "add", "reports/quality.json"], cwd=alpha, check=True)
        subprocess.run(["git", "commit", "-qm", "new evidence"], cwd=alpha, check=True)
        second_run = alpha_store.build("alpha-run-2")
        try:
            alpha_store.publish(second_run, crash_at="after-mirrors")
        except RuntimeError as exc:
            assert "simulated publish crash" in str(exc), exc
        else:
            raise AssertionError("publish crash point did not fire")
        assert (alpha / ".yao" / "publish-transaction.json").exists()
        alpha_store.recover()
        restored = json.loads((alpha / "reports" / "quality.json").read_text(encoding="utf-8"))
        assert restored["marker"] == "alpha-v1", restored
        assert not (alpha / ".yao" / "publish-transaction.json").exists()

        for crash_point in ("after-release", "before-pointer"):
            crash_skill = temp_root / f"crash-{crash_point}"
            crash_skill.mkdir()
            write_skill(crash_skill, crash_skill.name, "stable")
            crash_store = EvidenceStore(crash_skill)
            stable_run = crash_store.build("stable-run")
            crash_store.publish(stable_run)
            subprocess.run(
                ["git", "add", "reports/.current-run.json", "reports/artifact-index.json"],
                cwd=crash_skill,
                check=True,
            )
            subprocess.run(["git", "commit", "-qm", "publish pointer"], cwd=crash_skill, check=True)
            (crash_skill / "reports" / "quality.json").write_text(json.dumps({"marker": "candidate"}), encoding="utf-8")
            subprocess.run(["git", "add", "reports/quality.json"], cwd=crash_skill, check=True)
            subprocess.run(["git", "commit", "-qm", "candidate evidence"], cwd=crash_skill, check=True)
            candidate_run = crash_store.build("candidate-run")
            try:
                crash_store.publish(candidate_run, crash_at=crash_point)
            except RuntimeError:
                pass
            else:
                raise AssertionError(f"{crash_point} crash point did not fire")
            assert crash_store.recover() is True
            restored_payload = json.loads((crash_skill / "reports" / "quality.json").read_text(encoding="utf-8"))
            assert restored_payload["marker"] == "stable", (crash_point, restored_payload)

        first_publish_skill = temp_root / "first-publish-crash"
        first_publish_skill.mkdir()
        write_skill(first_publish_skill, "first-publish-crash", "original")
        first_publish_store = EvidenceStore(first_publish_skill)
        first_publish_run = first_publish_store.build("first-run")
        try:
            first_publish_store.publish(first_publish_run, crash_at="after-mirrors")
        except RuntimeError:
            pass
        else:
            raise AssertionError("first publish crash point did not fire")
        pending_dry = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "yao.py"), "evidence-build", str(first_publish_skill)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert pending_dry.returncode == 2, pending_dry.stdout
        assert json.loads(pending_dry.stdout)["error"]["code"] == "recovery-required", pending_dry.stdout
        assert (first_publish_skill / ".yao" / "publish-transaction.json").exists()
        recovered_cli = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "yao.py"), "evidence-build", str(first_publish_skill), "--recover"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert recovered_cli.returncode == 0, recovered_cli.stderr or recovered_cli.stdout
        assert not (first_publish_skill / ".yao" / "publish-transaction.json").exists()
        assert not (first_publish_skill / ".yao" / "releases" / "first-run").exists()
        assert not (first_publish_skill / "reports" / ".current-run.json").exists()
        assert not (first_publish_skill / "reports" / "artifact-index.json").exists()
        first_publish_store.publish(first_publish_run)

        with beta_store.publish_lock():
            try:
                with beta_store.publish_lock():
                    raise AssertionError("second publisher acquired an active lock")
            except EvidenceError as exc:
                assert exc.code == "publish-locked", exc

        stale_lock = beta / ".yao" / "publish.lock"
        stale_lock.write_text("pid=99999999\n", encoding="utf-8")
        with beta_store.publish_lock():
            pass

        race_skill = temp_root / "race-skill"
        race_skill.mkdir()
        write_skill(race_skill, "race-skill", "race")

        class RacingEvidenceStore(EvidenceStore):
            @contextlib.contextmanager
            def publish_lock(self):
                (self.skill_dir / "SKILL.md").write_text(
                    (self.skill_dir / "SKILL.md").read_text(encoding="utf-8") + "\nConcurrent mutation.\n",
                    encoding="utf-8",
                )
                yield

        race_store = RacingEvidenceStore(race_skill)
        race_run = race_store.build("race-run")
        try:
            race_store.publish(race_run)
        except EvidenceError as exc:
            assert exc.code == "dirty-worktree", exc
        else:
            raise AssertionError("publish accepted a worktree mutation after lock acquisition")
        assert not (race_skill / ".yao" / "releases" / "race-run").exists()

        run_race_skill = temp_root / "run-race-skill"
        run_race_skill.mkdir()
        write_skill(run_race_skill, "run-race-skill", "stable")

        class RunRacingEvidenceStore(EvidenceStore):
            @contextlib.contextmanager
            def publish_lock(self):
                run_dir = self.runs_dir / "run-race"
                artifact = run_dir / "artifacts" / "reports" / "quality.json"
                artifact.write_text(json.dumps({"marker": "mutated-after-verify"}), encoding="utf-8")
                index_path = run_dir / "artifact-index.json"
                index = json.loads(index_path.read_text(encoding="utf-8"))
                index["artifacts"][0]["sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
                index["artifacts"][0]["size"] = artifact.stat().st_size
                index_path.write_text(json.dumps(index), encoding="utf-8")
                manifest_path = run_dir / "run-manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["artifact_index_sha256"] = hashlib.sha256(index_path.read_bytes()).hexdigest()
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                yield

        run_race_store = RunRacingEvidenceStore(run_race_skill)
        run_race = run_race_store.build("run-race")
        try:
            run_race_store.publish(run_race)
        except EvidenceError as exc:
            assert exc.code == "run-changed", exc
        else:
            raise AssertionError("publish accepted a rehashed run mutation after initial verification")

        source_drift_skill = temp_root / "source-drift-skill"
        source_drift_skill.mkdir()
        write_skill(source_drift_skill, "source-drift-skill", "stable")
        source_drift_store = EvidenceStore(source_drift_skill)
        stale_source_run = source_drift_store.build("stale-source-run")
        (source_drift_skill / "SOURCE.txt").write_text("new source commit\n", encoding="utf-8")
        subprocess.run(["git", "add", "SOURCE.txt"], cwd=source_drift_skill, check=True)
        subprocess.run(["git", "commit", "-qm", "source drift"], cwd=source_drift_skill, check=True)
        try:
            source_drift_store.publish(stale_source_run)
        except EvidenceError as exc:
            assert exc.code == "run-source-mismatch", exc
        else:
            raise AssertionError("publish accepted evidence built from an older source commit")

        recovery_skill = temp_root / "recovery-skill"
        recovery_skill.mkdir()
        write_skill(recovery_skill, "recovery-skill", "stable")
        recovery_store = EvidenceStore(recovery_skill)
        recovery_run = recovery_store.build("stable-run")
        recovery_release = recovery_store.publish(recovery_run)
        release_index_path = recovery_release / "artifact-index.json"
        release_index = json.loads(release_index_path.read_text(encoding="utf-8"))
        release_index["artifacts"].append(
            {"path": "../../escaped.json", "sha256": "0" * 64, "size": 0}
        )
        release_index_path.write_text(json.dumps(release_index), encoding="utf-8")
        try:
            recovery_store._restore_bundle(recovery_release)
        except EvidenceError as exc:
            assert exc.code == "unsafe-artifact", exc
        else:
            raise AssertionError("recovery accepted a release artifact path escape")

        dry = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "yao.py"), "evidence-build", str(beta), "--run-id", "cli-dry"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert dry.returncode == 0, dry.stderr or dry.stdout
        dry_payload = json.loads(dry.stdout)
        assert dry_payload["mode"] == "dry-run", dry_payload
        assert not (beta / "reports" / ".current-run.json").exists()

        completed_provider_skill = temp_root / "completed-provider-skill"
        completed_provider_skill.mkdir()
        write_skill(completed_provider_skill, "completed-provider-skill", "completed-provider")
        (completed_provider_skill / "evals" / "output").mkdir(parents=True)
        shutil.copy2(
            ROOT / "evals" / "output" / "provider_matrix.json",
            completed_provider_skill / "evals" / "output" / "provider_matrix.json",
        )
        shutil.copy2(
            ROOT / "evals" / "output" / "holdout_cases.zh-CN.jsonl",
            completed_provider_skill / "evals" / "output" / "holdout_cases.zh-CN.jsonl",
        )
        shutil.copy2(
            ROOT / "reports" / "provider_output_evaluation.json",
            completed_provider_skill / "reports" / "provider_output_evaluation.json",
        )
        subprocess.run(["git", "add", "."], cwd=completed_provider_skill, check=True)
        subprocess.run(["git", "commit", "-qm", "add completed public provider evidence"], cwd=completed_provider_skill, check=True)
        preserve_completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "yao.py"),
                "evidence-build",
                str(completed_provider_skill),
                "--run-id",
                "preserve-completed-provider",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert preserve_completed.returncode == 0, preserve_completed.stderr or preserve_completed.stdout
        preserved_provider = json.loads(
            (
                completed_provider_skill
                / ".yao"
                / "runs"
                / "preserve-completed-provider"
                / "artifacts"
                / "reports"
                / "provider_output_evaluation.json"
            ).read_text(encoding="utf-8")
        )
        assert preserved_provider["schema_version"] == "1.1-public", preserved_provider
        assert preserved_provider["status"] == "completed", preserved_provider
        assert preserved_provider["summary"]["call_count"] == 40, preserved_provider
        assert preserved_provider["summary"]["model_executed_count"] == 40, preserved_provider
        assert preserved_provider["summary"]["failure_count"] == 0, preserved_provider

        publish = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "yao.py"),
                "evidence-build",
                str(beta),
                "--run-id",
                "cli-publish",
                "--publish",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert publish.returncode == 0, publish.stderr or publish.stdout
        assert json.loads(publish.stdout)["mode"] == "published", publish.stdout
        subprocess.run(["git", "add", "reports/.current-run.json", "reports/artifact-index.json"], cwd=beta, check=True)
        subprocess.run(["git", "commit", "-qm", "publish cli pointer"], cwd=beta, check=True)
        resolved_quality = resolve_evidence_path(beta, "reports/quality.json")
        assert ".yao/releases/cli-publish/" in resolved_quality.as_posix(), resolved_quality
        assert json.loads(resolved_quality.read_text(encoding="utf-8"))["marker"] == "beta-v1"
        published_reports = beta / ".yao" / "releases" / "cli-publish" / "artifacts" / "reports"
        external_published_reports = temp_root / "external-published-reports"
        shutil.move(str(published_reports), external_published_reports)
        if try_symlink(published_reports, external_published_reports, target_is_directory=True):
            try:
                resolve_evidence_path(beta, "reports/quality.json")
            except EvidenceError as exc:
                assert exc.code == "unsafe-evidence-path", exc
            else:
                raise AssertionError("evidence resolver followed a symlink outside the immutable release")
            published_reports.unlink()
        else:
            print("skipped symlink evidence-path case: platform does not permit symlinks")
        shutil.move(str(external_published_reports), published_reports)
        (beta / "SKILL.md").write_text((beta / "SKILL.md").read_text(encoding="utf-8") + "\nDirty.\n", encoding="utf-8")
        rejected = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "yao.py"),
                "evidence-build",
                str(beta),
                "--run-id",
                "dirty-publish",
                "--publish",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert rejected.returncode == 2, rejected.stdout
        assert json.loads(rejected.stdout)["error"]["code"] == "dirty-worktree", rejected.stdout
        assert not (beta / ".yao" / "runs" / "dirty-publish").exists()

    print(json.dumps({"ok": True}, indent=2))


if __name__ == "__main__":
    main()
