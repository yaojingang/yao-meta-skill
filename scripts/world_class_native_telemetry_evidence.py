#!/usr/bin/env python3
from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by world_class_evidence_contract.py to validate native client telemetry evidence from metadata event rows."

ADOPTION_EVENTS = {"skill_activation", "skill_output"}


def add_error(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def real_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def object_list(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def source_types(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    value = summary.get("source_types", {})
    return value if isinstance(value, dict) else {}


def validate_adoption_report(adoption: dict[str, Any], errors: list[str]) -> None:
    summary = adoption.get("summary", {}) if isinstance(adoption.get("summary"), dict) else {}
    privacy = adoption.get("privacy_contract", {}) if isinstance(adoption.get("privacy_contract"), dict) else {}
    events = object_list(adoption.get("recent_events", []))
    adoption_rows = object_list(adoption.get("adoption_by_skill", []))
    external_summary_count = real_int(source_types(adoption).get("external"))
    adoption_sample_count = real_int(summary.get("adoption_sample_count"))

    add_error(errors, adoption.get("ok") is True, "native-client-telemetry adoption drift report ok must be true")
    add_error(
        errors,
        bool(external_summary_count and external_summary_count > 0),
        "native-client-telemetry adoption drift summary.source_types.external must be >0",
    )
    add_error(
        errors,
        bool(adoption_sample_count and adoption_sample_count > 0),
        "native-client-telemetry adoption drift summary.adoption_sample_count must be >0",
    )
    add_error(
        errors,
        privacy.get("raw_content_allowed") is False,
        "native-client-telemetry adoption drift privacy_contract.raw_content_allowed must be false",
    )
    add_error(
        errors,
        privacy.get("raw_event_log_packaged") is False,
        "native-client-telemetry adoption drift privacy_contract.raw_event_log_packaged must be false",
    )
    add_error(errors, bool(events), "native-client-telemetry adoption drift recent_events must not be empty")
    external_events = [item for item in events if item.get("source") == "external"]
    external_adoption_events = [item for item in external_events if item.get("event") in ADOPTION_EVENTS]
    add_error(
        errors,
        bool(external_summary_count and len(external_events) >= external_summary_count),
        "native-client-telemetry external event rows must cover summary.source_types.external",
    )
    add_error(
        errors,
        bool(external_adoption_events),
        "native-client-telemetry must include at least one external adoption event row",
    )
    add_error(
        errors,
        bool(
            adoption_sample_count
            and len([item for item in events if item.get("event") in ADOPTION_EVENTS]) >= adoption_sample_count
        ),
        "native-client-telemetry adoption event rows must cover summary.adoption_sample_count",
    )
    add_error(
        errors,
        any((count := real_int(row.get("adoption_events"))) is not None and count > 0 for row in adoption_rows),
        "native-client-telemetry adoption_by_skill must include at least one adoption event",
    )


def validate_recipe_report(recipes: dict[str, Any], errors: list[str]) -> None:
    summary = recipes.get("summary", {}) if isinstance(recipes.get("summary"), dict) else {}
    privacy = recipes.get("privacy_contract", {}) if isinstance(recipes.get("privacy_contract"), dict) else {}
    recipe_rows = object_list(recipes.get("recipes", []))
    recipe_count = real_int(summary.get("recipe_count"))
    metadata_count = real_int(summary.get("metadata_only_recipe_count"))

    add_error(errors, recipes.get("ok") is True, "native-client-telemetry hook recipes report ok must be true")
    add_error(
        errors,
        bool(metadata_count and metadata_count > 0),
        "native-client-telemetry hook recipes summary.metadata_only_recipe_count must be >0",
    )
    add_error(
        errors,
        privacy.get("raw_content_allowed") is False,
        "native-client-telemetry hook recipes privacy_contract.raw_content_allowed must be false",
    )
    add_error(errors, bool(recipe_rows), "native-client-telemetry hook recipes rows must not be empty")
    if recipe_count is not None:
        add_error(errors, len(recipe_rows) == recipe_count, "native-client-telemetry hook recipes length must equal summary.recipe_count")
    if metadata_count is not None:
        add_error(
            errors,
            sum(1 for item in recipe_rows if item.get("metadata_only") is True) == metadata_count,
            "native-client-telemetry metadata_only recipe rows must match summary.metadata_only_recipe_count",
        )
    add_error(
        errors,
        all(item.get("source") == "external" for item in recipe_rows),
        "native-client-telemetry hook recipe rows must use source external",
    )
    add_error(
        errors,
        all(item.get("native_auto_capture") is False for item in recipe_rows),
        "native-client-telemetry hook recipe rows must not claim native_auto_capture",
    )


def validate_native_telemetry_report(adoption: dict[str, Any], recipes: dict[str, Any], errors: list[str]) -> None:
    if adoption:
        validate_adoption_report(adoption, errors)
    if recipes:
        validate_recipe_report(recipes, errors)
