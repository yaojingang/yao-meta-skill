#!/usr/bin/env python3
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by world-class evidence reports to share intake validation and artifact integrity checks."

REQUIRED_TOP_LEVEL = [
    "schema_version",
    "evidence_key",
    "template_only",
    "category",
    "source_type",
    "submitted_by",
    "submitted_at",
    "summary",
    "artifact_refs",
    "provenance",
    "privacy",
    "anti_overclaim",
    "attestation",
]
REQUIRED_PRIVACY_FALSE = [
    "raw_user_content_included",
    "raw_provider_prompt_included",
    "credentials_included",
    "secrets_included",
]
REQUIRED_ANTI_OVERCLAIM_FALSE = [
    "planned_work_counts_as_evidence",
    "metadata_fallback_counts_as_native_enforcement",
    "pending_review_counts_as_human_decision",
    "local_command_runner_counts_as_provider_model",
]
REQUIRED_ATTESTATION_TRUE = [
    "real_external_or_human_evidence",
    "reviewer_or_operator_identity_present",
    "artifact_refs_reviewed",
    "privacy_contract_satisfied",
]
EXPECTED_SOURCE_TYPES = {
    "provider-holdout": "provider-output-eval",
    "human-adjudication": "blind-ab-review",
    "native-permission-enforcement": "runtime-permission-guard",
    "native-client-telemetry": "native-client-telemetry",
}
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
DISALLOWED_REAL_ARTIFACTS = {"reports/telemetry_events.jsonl"}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_json_with_status(path: Path) -> tuple[dict[str, Any], str]:
    if not path.exists():
        return {}, "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}, "invalid-json"
    if not isinstance(payload, dict):
        return {}, "invalid-json"
    return payload, "present"


def rel_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def add_error(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_artifact_path(raw_path: str, root: Path) -> tuple[Path | None, str | None]:
    text = raw_path.strip()
    if any(token in text for token in ("<", ">", "*", "?")):
        return None, "artifact_refs path must be concrete, not a placeholder or glob"
    candidate = Path(text)
    if candidate.is_absolute():
        return None, "artifact_refs path must be relative to the skill directory"
    if ".." in candidate.parts:
        return None, "artifact_refs path must not escape the skill directory"
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, "artifact_refs path must stay inside the skill directory"
    return resolved, None


def validate_artifact_refs(
    payload: dict[str, Any],
    errors: list[str],
    *,
    root: Path,
    template_expected: bool,
) -> dict[str, int]:
    refs = payload.get("artifact_refs")
    add_error(errors, isinstance(refs, list) and len(refs) > 0, "artifact_refs must contain at least one reference")
    stats = {
        "artifact_ref_count": len(refs) if isinstance(refs, list) else 0,
        "artifact_existing_count": 0,
        "artifact_sha256_verified_count": 0,
    }
    if not isinstance(refs, list):
        return stats
    for index, ref in enumerate(refs):
        if not isinstance(ref, dict):
            errors.append(f"artifact_refs[{index}] must be an object")
            continue
        path_text = str(ref.get("path", "")).strip()
        add_error(errors, bool(path_text), f"artifact_refs[{index}].path is required")
        add_error(errors, bool(str(ref.get("kind", "")).strip()), f"artifact_refs[{index}].kind is required")
        add_error(errors, ref.get("contains_raw_content") is False, f"artifact_refs[{index}] must not contain raw content")
        if template_expected or not path_text:
            continue
        resolved, path_error = resolve_artifact_path(path_text, root)
        if path_error:
            errors.append(f"artifact_refs[{index}].path {path_error}")
            continue
        rel = rel_path(resolved, root)
        if rel in DISALLOWED_REAL_ARTIFACTS:
            errors.append(f"artifact_refs[{index}].path must not reference raw local telemetry logs")
        if not resolved.exists() or not resolved.is_file():
            errors.append(f"artifact_refs[{index}].path does not exist as a local file")
            continue
        stats["artifact_existing_count"] += 1
        declared = str(ref.get("sha256", "")).strip()
        if not declared:
            errors.append(f"artifact_refs[{index}].sha256 is required for a real submission")
            continue
        if not SHA256_RE.match(declared):
            errors.append(f"artifact_refs[{index}].sha256 must be a 64-character hex digest")
            continue
        actual = sha256_file(resolved)
        if actual.lower() != declared.lower():
            errors.append(f"artifact_refs[{index}].sha256 does not match local artifact")
            continue
        stats["artifact_sha256_verified_count"] += 1
    return stats


def validate_evidence_specific(payload: dict[str, Any], errors: list[str]) -> None:
    key = str(payload.get("evidence_key", ""))
    provenance = payload.get("provenance", {}) if isinstance(payload.get("provenance", {}), dict) else {}
    if key == "provider-holdout":
        add_error(errors, bool(str(provenance.get("provider", "")).strip()), "provider-holdout provenance.provider is required")
        add_error(errors, bool(str(provenance.get("model", "")).strip()), "provider-holdout provenance.model is required")
        add_error(
            errors,
            provenance.get("credential_material_committed") is False,
            "provider-holdout must attest credential_material_committed is false",
        )
    elif key == "human-adjudication":
        add_error(errors, bool(str(provenance.get("reviewer", "")).strip()), "human-adjudication provenance.reviewer is required")
        add_error(
            errors,
            provenance.get("answer_key_opened_after_decisions") is True,
            "human-adjudication must attest answer_key_opened_after_decisions is true",
        )
    elif key == "native-permission-enforcement":
        add_error(errors, bool(str(provenance.get("target", "")).strip()), "native-permission-enforcement provenance.target is required")
        add_error(
            errors,
            bool(str(provenance.get("guard_location", "")).strip()),
            "native-permission-enforcement provenance.guard_location is required",
        )
        add_error(
            errors,
            str(provenance.get("guard_scope", "")).strip()
            in {"target-client-native", "external-installer-runtime-guard"},
            "native-permission-enforcement provenance.guard_scope must be target-client-native or external-installer-runtime-guard",
        )
        add_error(
            errors,
            provenance.get("guard_blocks_undeclared_capability") is True,
            "native-permission-enforcement must attest guard_blocks_undeclared_capability is true",
        )
        add_error(
            errors,
            provenance.get("metadata_fallback_retained_for_other_targets") is True,
            "native-permission-enforcement must retain metadata fallback for non-native targets",
        )
    elif key == "native-client-telemetry":
        add_error(errors, bool(str(provenance.get("client", "")).strip()), "native-client-telemetry provenance.client is required")
        add_error(errors, provenance.get("event_source") == "external", "native-client-telemetry event_source must be external")
        add_error(errors, provenance.get("metadata_only") is True, "native-client-telemetry must be metadata_only")


def validate_payload(
    payload: dict[str, Any],
    entry: dict[str, Any],
    *,
    path: Path,
    root: Path,
    template_expected: bool,
) -> dict[str, Any]:
    errors: list[str] = []
    for key in REQUIRED_TOP_LEVEL:
        add_error(errors, key in payload, f"missing {key}")
    evidence_key = str(entry.get("key", ""))
    add_error(errors, payload.get("schema_version") == "1.0", "schema_version must be 1.0")
    add_error(errors, payload.get("evidence_key") == evidence_key, f"evidence_key must be {evidence_key}")
    add_error(errors, payload.get("template_only") is template_expected, f"template_only must be {str(template_expected).lower()}")
    add_error(errors, payload.get("category") == entry.get("category"), f"category must be {entry.get('category')}")
    add_error(
        errors,
        payload.get("source_type") == EXPECTED_SOURCE_TYPES.get(evidence_key),
        f"source_type must be {EXPECTED_SOURCE_TYPES.get(evidence_key)}",
    )
    add_error(errors, bool(str(payload.get("submitted_by", "")).strip()), "submitted_by is required")
    add_error(errors, bool(str(payload.get("submitted_at", "")).strip()), "submitted_at is required")
    add_error(errors, bool(str(payload.get("summary", "")).strip()), "summary is required")
    artifact_integrity = validate_artifact_refs(payload, errors, root=root, template_expected=template_expected)
    privacy = payload.get("privacy", {}) if isinstance(payload.get("privacy", {}), dict) else {}
    for key in REQUIRED_PRIVACY_FALSE:
        add_error(errors, privacy.get(key) is False, f"privacy.{key} must be false")
    anti_overclaim = payload.get("anti_overclaim", {}) if isinstance(payload.get("anti_overclaim", {}), dict) else {}
    for key in REQUIRED_ANTI_OVERCLAIM_FALSE:
        add_error(errors, anti_overclaim.get(key) is False, f"anti_overclaim.{key} must be false")
    validate_evidence_specific(payload, errors)
    attestation = payload.get("attestation", {}) if isinstance(payload.get("attestation", {}), dict) else {}
    if not template_expected:
        for key in REQUIRED_ATTESTATION_TRUE:
            add_error(errors, attestation.get(key) is True, f"attestation.{key} must be true for a real submission")
    return {
        "path": rel_path(path, root),
        "evidence_key": evidence_key,
        "status": "pass" if not errors else "fail",
        "template_only": template_expected,
        "artifact_integrity": artifact_integrity,
        "errors": errors,
    }
