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
    "ledger_reviewer_approved",
]
EXPECTED_SOURCE_TYPES = {
    "provider-holdout": "provider-output-eval",
    "human-adjudication": "blind-ab-review",
    "native-permission-enforcement": "runtime-permission-guard",
    "native-client-telemetry": "native-client-telemetry",
}
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
SUBMITTED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}Z)?$")
DISALLOWED_REAL_ARTIFACTS = {"reports/telemetry_events.jsonl"}
REQUIRED_REAL_ARTIFACT_PATHS = {
    "provider-holdout": {"reports/output_execution_runs.json"},
    "human-adjudication": {
        "reports/output_review_adjudication.json",
        "reports/output_review_decisions.json",
    },
    "native-permission-enforcement": {
        "reports/runtime_permission_probes.json",
        "reports/install_simulation.json",
    },
    "native-client-telemetry": {
        "reports/adoption_drift_report.json",
        "reports/telemetry_hook_recipes.json",
    },
}
PLACEHOLDER_FRAGMENTS = (
    "YYYY-MM-DD",
    "name or team handle",
    "operator with provider credentials",
    "human reviewer",
    "target client or installer integrator",
    "Browser/Chrome/IDE/provider client integrator",
    "Browser/Chrome/IDE/provider client",
    "openai|claude|generic|vscode|other",
    "client or installer component",
    "/local/path/not/committed",
)
FORBIDDEN_REAL_SUBMISSION_FIELDS = {
    "api_key",
    "assistant_message",
    "assistant_messages",
    "baseline_output",
    "credential",
    "credentials",
    "input",
    "inputs",
    "message",
    "messages",
    "model_output",
    "output",
    "outputs",
    "prompt",
    "prompts",
    "raw_content",
    "raw_output",
    "raw_prompt",
    "raw_provider_prompt",
    "raw_user_content",
    "secret",
    "secrets",
    "token",
    "transcript",
    "transcripts",
    "user_message",
    "user_messages",
    "with_skill_output",
}


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


def has_placeholder_text(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    lowered = text.lower()
    return any(fragment.lower() in lowered for fragment in PLACEHOLDER_FRAGMENTS)


def require_real_text(errors: list[str], value: Any, field: str) -> None:
    text = str(value or "").strip()
    add_error(errors, bool(text), f"{field} is required")
    add_error(errors, not has_placeholder_text(text), f"{field} must not use template placeholder text")


def forbidden_submission_field_paths(value: Any, prefix: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{prefix}.{key_text}"
            if key_text.strip().lower() in FORBIDDEN_REAL_SUBMISSION_FIELDS:
                found.append(child_path)
            found.extend(forbidden_submission_field_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(forbidden_submission_field_paths(child, f"{prefix}[{index}]"))
    return found


def validate_real_submission_file_identity(
    payload: dict[str, Any],
    errors: list[str],
    *,
    path: Path,
    template_expected: bool,
) -> None:
    if template_expected:
        return
    evidence_key = str(payload.get("evidence_key", "")).strip()
    expected_name = f"{evidence_key}.json"
    add_error(
        errors,
        path.name == expected_name,
        f"real submission filename must be {expected_name}",
    )


def validate_real_submission_privacy_fields(
    payload: dict[str, Any],
    errors: list[str],
    *,
    template_expected: bool,
) -> None:
    if template_expected:
        return
    blocked_paths = forbidden_submission_field_paths(payload)
    add_error(
        errors,
        not blocked_paths,
        "real submission must not include raw content, credential, secret, token, prompt, output, transcript, or message fields: "
        + ", ".join(blocked_paths[:8]),
    )


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
    required_paths = REQUIRED_REAL_ARTIFACT_PATHS.get(str(payload.get("evidence_key", "")), set())
    observed_paths: set[str] = set()
    stats = {
        "artifact_ref_count": len(refs) if isinstance(refs, list) else 0,
        "artifact_existing_count": 0,
        "artifact_sha256_verified_count": 0,
        "required_artifact_count": len(required_paths) if not template_expected else 0,
        "required_artifact_verified_count": 0,
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
        candidate = Path(path_text)
        if not candidate.is_absolute() and ".." not in candidate.parts and not any(
            token in path_text for token in ("<", ">", "*", "?")
        ):
            observed_paths.add(candidate.as_posix())
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
        if rel in required_paths:
            stats["required_artifact_verified_count"] += 1
    if not template_expected and required_paths:
        missing_required = sorted(required_paths - observed_paths)
        for path in missing_required:
            errors.append(f"artifact_refs must include required evidence artifact {path}")
        if not missing_required and stats["required_artifact_verified_count"] < len(required_paths):
            errors.append("all required evidence artifacts must have verified sha256 digests")
    return stats


def artifact_ref_path_map(payload: dict[str, Any], root: Path) -> dict[str, Path]:
    refs = payload.get("artifact_refs", [])
    if not isinstance(refs, list):
        return {}
    paths: dict[str, Path] = {}
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        path_text = str(ref.get("path", "")).strip()
        if not path_text:
            continue
        resolved, path_error = resolve_artifact_path(path_text, root)
        if path_error or resolved is None:
            continue
        paths[rel_path(resolved, root)] = resolved
    return paths


def real_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def summary(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("summary", {})
    return value if isinstance(value, dict) else {}


def source_types(payload: dict[str, Any]) -> dict[str, Any]:
    value = summary(payload).get("source_types", {})
    return value if isinstance(value, dict) else {}


def privacy_contract(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("privacy_contract", {})
    return value if isinstance(value, dict) else {}


def validate_provider_holdout_artifacts(payload: dict[str, Any], errors: list[str], root: Path) -> None:
    paths = artifact_ref_path_map(payload, root)
    execution = load_json(paths.get("reports/output_execution_runs.json", root / "__missing__"))
    if not execution:
        return
    execution_summary = summary(execution)
    add_error(errors, execution.get("ok") is True, "provider-holdout output execution report ok must be true")
    add_error(
        errors,
        bool(real_int(execution_summary.get("model_executed_count")) and execution_summary["model_executed_count"] > 0),
        "provider-holdout output execution summary.model_executed_count must be >0",
    )
    add_error(
        errors,
        bool(real_int(execution_summary.get("timing_observed_count")) and execution_summary["timing_observed_count"] > 0),
        "provider-holdout output execution summary.timing_observed_count must be >0",
    )
    add_error(
        errors,
        bool(real_int(execution_summary.get("token_observed_count")) and execution_summary["token_observed_count"] > 0),
        "provider-holdout output execution summary.token_observed_count must be >0",
    )
    add_error(
        errors,
        execution_summary.get("failure_count") == 0,
        "provider-holdout output execution summary.failure_count must be 0",
    )


def validate_human_adjudication_artifacts(payload: dict[str, Any], errors: list[str], root: Path) -> None:
    paths = artifact_ref_path_map(payload, root)
    adjudication = load_json(paths.get("reports/output_review_adjudication.json", root / "__missing__"))
    decisions = load_json(paths.get("reports/output_review_decisions.json", root / "__missing__"))
    if not adjudication or not decisions:
        return

    summary = adjudication.get("summary", {}) if isinstance(adjudication.get("summary", {}), dict) else {}
    pair_count = real_int(summary.get("pair_count"))
    judgment_count = real_int(summary.get("judgment_count"))
    pending_count = real_int(summary.get("pending_count"))
    invalid_decision_count = real_int(summary.get("invalid_decision_count"))
    answer_revealed_count = real_int(summary.get("answer_revealed_count"))
    pending_answer_hidden_count = real_int(summary.get("pending_answer_hidden_count"))
    add_error(errors, bool(pair_count and pair_count > 0), "human-adjudication adjudication summary.pair_count must be >0")
    add_error(
        errors,
        bool(pair_count and judgment_count == pair_count),
        "human-adjudication adjudication summary.judgment_count must equal summary.pair_count",
    )
    add_error(errors, pending_count == 0, "human-adjudication adjudication summary.pending_count must be 0")
    add_error(
        errors,
        invalid_decision_count == 0,
        "human-adjudication adjudication summary.invalid_decision_count must be 0",
    )
    add_error(
        errors,
        bool(pair_count and answer_revealed_count == pair_count),
        "human-adjudication adjudication summary.answer_revealed_count must equal summary.pair_count",
    )
    add_error(
        errors,
        pending_answer_hidden_count == 0,
        "human-adjudication adjudication summary.pending_answer_hidden_count must be 0",
    )
    add_error(errors, summary.get("needs_review") is False, "human-adjudication adjudication summary.needs_review must be false")

    decision_rows = decisions.get("decisions", [])
    add_error(errors, decisions.get("schema_version") == "1.0", "human-adjudication decisions.schema_version must be 1.0")
    reviewer = str(decisions.get("reviewer", "")).strip()
    reviewed_at = str(decisions.get("reviewed_at", "")).strip()
    require_real_text(errors, reviewer, "human-adjudication decisions.reviewer")
    add_error(
        errors,
        bool(SUBMITTED_AT_RE.match(reviewed_at)),
        "human-adjudication decisions.reviewed_at must use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ",
    )
    add_error(
        errors,
        isinstance(decision_rows, list) and bool(pair_count and len(decision_rows) == pair_count),
        "human-adjudication decisions count must equal adjudication summary.pair_count",
    )
    if isinstance(decision_rows, list):
        invalid_winners = [
            str(item.get("case_id", index + 1))
            for index, item in enumerate(decision_rows)
            if not isinstance(item, dict) or str(item.get("winner_variant", "")).strip().upper() not in {"A", "B"}
        ]
        missing_reasons = [
            str(item.get("case_id", index + 1))
            for index, item in enumerate(decision_rows)
            if not isinstance(item, dict) or not str(item.get("reason", "")).strip()
        ]
        add_error(
            errors,
            not invalid_winners,
            "human-adjudication decisions must include A/B winner_variant for every case",
        )
        add_error(errors, not missing_reasons, "human-adjudication decisions must include reviewer reason for every case")

    provenance = payload.get("provenance", {}) if isinstance(payload.get("provenance", {}), dict) else {}
    provenance_reviewer = str(provenance.get("reviewer", "")).strip()
    add_error(
        errors,
        bool(reviewer and provenance_reviewer and reviewer == provenance_reviewer),
        "human-adjudication provenance.reviewer must match decisions.reviewer",
    )
    add_error(
        errors,
        adjudication.get("reviewer") == reviewer,
        "human-adjudication adjudication reviewer must match decisions.reviewer",
    )
    add_error(
        errors,
        adjudication.get("reviewed_at") == reviewed_at,
        "human-adjudication adjudication reviewed_at must match decisions.reviewed_at",
    )


def validate_native_permission_artifacts(payload: dict[str, Any], errors: list[str], root: Path) -> None:
    paths = artifact_ref_path_map(payload, root)
    probes = load_json(paths.get("reports/runtime_permission_probes.json", root / "__missing__"))
    install = load_json(paths.get("reports/install_simulation.json", root / "__missing__"))
    if probes:
        probe_summary = summary(probes)
        add_error(errors, probes.get("ok") is True, "native-permission-enforcement runtime probe report ok must be true")
        add_error(
            errors,
            bool(real_int(probe_summary.get("native_enforcement_count")) and probe_summary["native_enforcement_count"] > 0),
            "native-permission-enforcement runtime probe summary.native_enforcement_count must be >0",
        )
        add_error(
            errors,
            probe_summary.get("failure_count") == 0,
            "native-permission-enforcement runtime probe summary.failure_count must be 0",
        )
        add_error(
            errors,
            probe_summary.get("installer_enforcement_ready") is True,
            "native-permission-enforcement runtime probe summary.installer_enforcement_ready must be true",
        )
    if install:
        install_summary = summary(install)
        add_error(errors, install.get("ok") is True, "native-permission-enforcement install simulation report ok must be true")
        add_error(
            errors,
            bool(
                real_int(install_summary.get("installer_permission_enforced_count"))
                and install_summary["installer_permission_enforced_count"] > 0
            ),
            "native-permission-enforcement install simulation summary.installer_permission_enforced_count must be >0",
        )
        add_error(
            errors,
            install_summary.get("installer_permission_failure_count") == 0,
            "native-permission-enforcement install simulation summary.installer_permission_failure_count must be 0",
        )
        add_error(
            errors,
            install_summary.get("failure_count") == 0,
            "native-permission-enforcement install simulation summary.failure_count must be 0",
        )


def validate_native_client_telemetry_artifacts(payload: dict[str, Any], errors: list[str], root: Path) -> None:
    paths = artifact_ref_path_map(payload, root)
    adoption = load_json(paths.get("reports/adoption_drift_report.json", root / "__missing__"))
    recipes = load_json(paths.get("reports/telemetry_hook_recipes.json", root / "__missing__"))
    if adoption:
        adoption_summary = summary(adoption)
        adoption_privacy = privacy_contract(adoption)
        add_error(errors, adoption.get("ok") is True, "native-client-telemetry adoption drift report ok must be true")
        add_error(
            errors,
            bool(real_int(source_types(adoption).get("external")) and source_types(adoption)["external"] > 0),
            "native-client-telemetry adoption drift summary.source_types.external must be >0",
        )
        add_error(
            errors,
            bool(real_int(adoption_summary.get("adoption_sample_count")) and adoption_summary["adoption_sample_count"] > 0),
            "native-client-telemetry adoption drift summary.adoption_sample_count must be >0",
        )
        add_error(
            errors,
            adoption_privacy.get("raw_content_allowed") is False,
            "native-client-telemetry adoption drift privacy_contract.raw_content_allowed must be false",
        )
        add_error(
            errors,
            adoption_privacy.get("raw_event_log_packaged") is False,
            "native-client-telemetry adoption drift privacy_contract.raw_event_log_packaged must be false",
        )
    if recipes:
        recipes_summary = summary(recipes)
        recipes_privacy = privacy_contract(recipes)
        add_error(errors, recipes.get("ok") is True, "native-client-telemetry hook recipes report ok must be true")
        add_error(
            errors,
            bool(
                real_int(recipes_summary.get("metadata_only_recipe_count"))
                and recipes_summary["metadata_only_recipe_count"] > 0
            ),
            "native-client-telemetry hook recipes summary.metadata_only_recipe_count must be >0",
        )
        add_error(
            errors,
            recipes_privacy.get("raw_content_allowed") is False,
            "native-client-telemetry hook recipes privacy_contract.raw_content_allowed must be false",
        )


def validate_real_artifact_payloads(payload: dict[str, Any], errors: list[str], root: Path, template_expected: bool) -> None:
    if template_expected:
        return
    evidence_key = str(payload.get("evidence_key", ""))
    if evidence_key == "provider-holdout":
        validate_provider_holdout_artifacts(payload, errors, root)
    elif evidence_key == "human-adjudication":
        validate_human_adjudication_artifacts(payload, errors, root)
    elif evidence_key == "native-permission-enforcement":
        validate_native_permission_artifacts(payload, errors, root)
    elif evidence_key == "native-client-telemetry":
        validate_native_client_telemetry_artifacts(payload, errors, root)


def validate_evidence_specific(payload: dict[str, Any], errors: list[str]) -> None:
    key = str(payload.get("evidence_key", ""))
    template_expected = payload.get("template_only") is True
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
        if not template_expected:
            require_real_text(errors, provenance.get("reviewer", ""), "human-adjudication provenance.reviewer")
        add_error(
            errors,
            provenance.get("answer_key_opened_after_decisions") is True,
            "human-adjudication must attest answer_key_opened_after_decisions is true",
        )
    elif key == "native-permission-enforcement":
        add_error(errors, bool(str(provenance.get("target", "")).strip()), "native-permission-enforcement provenance.target is required")
        if not template_expected:
            require_real_text(errors, provenance.get("target", ""), "native-permission-enforcement provenance.target")
        add_error(
            errors,
            bool(str(provenance.get("guard_location", "")).strip()),
            "native-permission-enforcement provenance.guard_location is required",
        )
        if not template_expected:
            require_real_text(
                errors,
                provenance.get("guard_location", ""),
                "native-permission-enforcement provenance.guard_location",
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
        if not template_expected:
            require_real_text(errors, provenance.get("client", ""), "native-client-telemetry provenance.client")
            if str(provenance.get("native_host_manifest", "")).strip():
                require_real_text(
                    errors,
                    provenance.get("native_host_manifest", ""),
                    "native-client-telemetry provenance.native_host_manifest",
                )
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
    if not template_expected:
        validate_real_submission_file_identity(payload, errors, path=path, template_expected=template_expected)
        validate_real_submission_privacy_fields(payload, errors, template_expected=template_expected)
        require_real_text(errors, payload.get("submitted_by", ""), "submitted_by")
        add_error(
            errors,
            bool(SUBMITTED_AT_RE.match(str(payload.get("submitted_at", "")).strip())),
            "submitted_at must use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ",
        )
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
        ledger_reviewer = str(attestation.get("ledger_reviewer", "")).strip()
        submitted_by = str(payload.get("submitted_by", "")).strip()
        require_real_text(errors, ledger_reviewer, "attestation.ledger_reviewer")
        add_error(
            errors,
            bool(SUBMITTED_AT_RE.match(str(attestation.get("ledger_reviewed_at", "")).strip())),
            "attestation.ledger_reviewed_at must use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ",
        )
        add_error(
            errors,
            bool(ledger_reviewer and submitted_by and ledger_reviewer.casefold() != submitted_by.casefold()),
            "attestation.ledger_reviewer must be different from submitted_by",
        )
    validate_real_artifact_payloads(payload, errors, root, template_expected)
    return {
        "path": rel_path(path, root),
        "evidence_key": evidence_key,
        "status": "pass" if not errors else "fail",
        "template_only": template_expected,
        "artifact_integrity": artifact_integrity,
        "errors": errors,
    }
