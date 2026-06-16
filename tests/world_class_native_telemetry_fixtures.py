#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

from world_class_evidence_contract import validate_payload


ROOT = Path(__file__).resolve().parent.parent
TMP = ROOT / "tests" / "tmp_world_class_evidence_intake"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def native_telemetry_submission(skill_root: Path) -> dict:
    return {
        "schema_version": "1.0",
        "evidence_key": "native-client-telemetry",
        "template_only": False,
        "category": "external",
        "source_type": "native-client-telemetry",
        "submitted_by": "Yao client integrator",
        "submitted_at": "2026-06-14",
        "summary": "Completed native-client-telemetry evidence for ledger review.",
        "artifact_refs": [
            {
                "path": "reports/adoption_drift_report.json",
                "kind": "adoption-drift-report",
                "contains_raw_content": False,
                "sha256": sha256_file(skill_root / "reports" / "adoption_drift_report.json"),
            },
            {
                "path": "reports/telemetry_hook_recipes.json",
                "kind": "hook-recipes",
                "contains_raw_content": False,
                "sha256": sha256_file(skill_root / "reports" / "telemetry_hook_recipes.json"),
            },
        ],
        "provenance": {
            "client": "Chrome extension production build",
            "native_host_manifest": "/Users/laoyao/.config/chrome/native-hosts/yao-meta-skill.json",
            "event_source": "external",
            "metadata_only": True,
        },
        "privacy": {
            "raw_user_content_included": False,
            "raw_provider_prompt_included": False,
            "credentials_included": False,
            "secrets_included": False,
        },
        "anti_overclaim": {
            "planned_work_counts_as_evidence": False,
            "metadata_fallback_counts_as_native_enforcement": False,
            "pending_review_counts_as_human_decision": False,
            "local_command_runner_counts_as_provider_model": False,
        },
        "attestation": {
            "real_external_or_human_evidence": True,
            "reviewer_or_operator_identity_present": True,
            "artifact_refs_reviewed": True,
            "privacy_contract_satisfied": True,
            "ledger_reviewer_approved": True,
            "ledger_reviewer": "Yao ledger reviewer",
            "ledger_reviewed_at": "2026-06-14",
        },
    }


def write_native_telemetry_artifacts(skill_root: Path, *, complete: bool) -> None:
    recent_events = (
        [
            {
                "command": "chrome-extension",
                "event": "skill_activation",
                "skill": "yao-meta-skill",
                "source": "external",
                "version": "1.1.0",
                "activation_type": "explicit",
                "outcome": "accepted",
                "failure_type": "none",
                "timestamp": "2026-06-14T10:00:00Z",
            }
        ]
        if complete
        else []
    )
    write_json(
        skill_root / "reports" / "adoption_drift_report.json",
        {
            "schema_version": "2.0",
            "ok": True,
            "privacy_contract": {
                "raw_content_allowed": False,
                "raw_event_log_packaged": False,
            },
            "summary": {
                "source_types": {"external": 1 if complete else 0},
                "adoption_sample_count": 1 if complete else 0,
            },
            "adoption_by_skill": [
                {
                    "skill": "yao-meta-skill",
                    "events": 1 if complete else 0,
                    "adoption_events": 1 if complete else 0,
                    "accepted": 1 if complete else 0,
                    "edited": 0,
                    "rejected": 0,
                    "missed": 0,
                    "adoption_rate": 100.0 if complete else 0,
                }
            ],
            "recent_events": recent_events,
        },
    )
    write_json(
        skill_root / "reports" / "telemetry_hook_recipes.json",
        {
            "schema_version": "1.0",
            "ok": True,
            "privacy_contract": {"raw_content_allowed": False},
            "summary": {"recipe_count": 1, "metadata_only_recipe_count": 1},
            "recipes": [
                {
                    "id": "chrome-extension",
                    "source": "external",
                    "metadata_only": True,
                    "native_auto_capture": False,
                    "event": "skill_activation",
                    "outcome": "accepted",
                }
            ],
        },
    )


def assert_native_telemetry_contract_artifact_validation() -> None:
    entry = {"key": "native-client-telemetry", "category": "external"}
    skill_root = TMP / "native_telemetry_contract_root"
    write_native_telemetry_artifacts(skill_root, complete=True)
    valid = validate_payload(
        native_telemetry_submission(skill_root),
        entry,
        path=skill_root / "evidence" / "world_class" / "submissions" / "native-client-telemetry.json",
        root=skill_root,
        template_expected=False,
    )
    assert valid["status"] == "pass", valid

    forged_adoption = json.loads((skill_root / "reports" / "adoption_drift_report.json").read_text(encoding="utf-8"))
    forged_adoption["recent_events"][0]["source"] = "manual"
    write_json(skill_root / "reports" / "adoption_drift_report.json", forged_adoption)
    forged = validate_payload(
        native_telemetry_submission(skill_root),
        entry,
        path=skill_root / "evidence" / "world_class" / "submissions" / "native-client-telemetry.json",
        root=skill_root,
        template_expected=False,
    )
    assert forged["status"] == "fail", forged
    assert any("external event rows must cover summary.source_types.external" in error for error in forged["errors"]), (
        forged["errors"]
    )

    write_native_telemetry_artifacts(skill_root, complete=False)
    invalid = validate_payload(
        native_telemetry_submission(skill_root),
        entry,
        path=skill_root / "evidence" / "world_class" / "submissions" / "native-client-telemetry.json",
        root=skill_root,
        template_expected=False,
    )
    assert invalid["status"] == "fail", invalid
    assert any("summary.source_types.external must be >0" in error for error in invalid["errors"]), invalid["errors"]
    assert any("summary.adoption_sample_count must be >0" in error for error in invalid["errors"]), invalid["errors"]
