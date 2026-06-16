#!/usr/bin/env python3
from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by world_class_evidence_contract.py to validate runtime permission evidence from target-level probe rows."


def add_error(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def real_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def object_list(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def sorted_strings(value: Any) -> list[str]:
    return sorted(str(item) for item in value) if isinstance(value, list) else []


def validate_target_rows(probes: dict[str, Any], summary: dict[str, Any], errors: list[str]) -> None:
    targets = object_list(probes.get("targets", []))
    target_count = real_int(summary.get("target_count"))
    native_count = real_int(summary.get("native_enforcement_count"))
    fail_count = real_int(summary.get("fail_count"))
    expected_capabilities = sorted_strings(probes.get("expected_capabilities"))

    add_error(errors, bool(targets), "native-permission-enforcement runtime probe targets must not be empty")
    if target_count is not None:
        add_error(errors, len(targets) == target_count, "native-permission-enforcement runtime probe targets length must equal summary.target_count")
    add_error(errors, fail_count == 0, "native-permission-enforcement runtime probe summary.fail_count must be 0")

    observed_native = 0
    for index, target in enumerate(targets, start=1):
        target_name = str(target.get("target", "")).strip() or str(index)
        add_error(errors, target.get("status") == "pass", f"native-permission-enforcement target {target_name} status must be pass")
        add_error(errors, not target.get("failures"), f"native-permission-enforcement target {target_name} failures must be empty")
        checks = object_list(target.get("checks", []))
        add_error(errors, bool(checks), f"native-permission-enforcement target {target_name} checks must not be empty")
        add_error(
            errors,
            all(item.get("passed") is True for item in checks),
            f"native-permission-enforcement target {target_name} checks must all pass",
        )
        native = target.get("native_enforcement") is True
        if native:
            observed_native += 1
            add_error(
                errors,
                target.get("assurance") == "native-enforced",
                f"native-permission-enforcement target {target_name} assurance must be native-enforced",
            )
        else:
            add_error(
                errors,
                target.get("metadata_fallback_explicit") is True,
                f"native-permission-enforcement fallback target {target_name} must keep metadata_fallback_explicit true",
            )
            add_error(
                errors,
                bool(target.get("residual_risks")),
                f"native-permission-enforcement fallback target {target_name} must retain residual risks",
            )
        if expected_capabilities:
            add_error(
                errors,
                sorted_strings(target.get("declared_capabilities")) == expected_capabilities,
                f"native-permission-enforcement target {target_name} declared_capabilities must match expected_capabilities",
            )
        installer = target.get("installer_enforcement", {}) if isinstance(target.get("installer_enforcement"), dict) else {}
        add_error(
            errors,
            installer.get("enforced") is True,
            f"native-permission-enforcement target {target_name} installer_enforcement.enforced must be true",
        )
        add_error(
            errors,
            not installer.get("missing_capabilities"),
            f"native-permission-enforcement target {target_name} installer_enforcement missing_capabilities must be empty",
        )
        add_error(
            errors,
            not installer.get("failure_details"),
            f"native-permission-enforcement target {target_name} installer_enforcement failure_details must be empty",
        )

    add_error(errors, bool(native_count and observed_native == native_count), "native-permission-enforcement native target rows must match summary.native_enforcement_count")
    add_error(errors, observed_native > 0, "native-permission-enforcement must include at least one native-enforced target row")


def validate_install_simulation_report(install: dict[str, Any], errors: list[str]) -> None:
    summary = install.get("summary", {}) if isinstance(install.get("summary", {}), dict) else {}
    add_error(errors, install.get("ok") is True, "native-permission-enforcement install simulation report ok must be true")
    add_error(
        errors,
        bool(real_int(summary.get("installer_permission_enforced_count")) and summary["installer_permission_enforced_count"] > 0),
        "native-permission-enforcement install simulation summary.installer_permission_enforced_count must be >0",
    )
    add_error(
        errors,
        summary.get("installer_permission_failure_count") == 0,
        "native-permission-enforcement install simulation summary.installer_permission_failure_count must be 0",
    )
    add_error(errors, summary.get("failure_count") == 0, "native-permission-enforcement install simulation summary.failure_count must be 0")
    permission_checks = [
        item
        for item in object_list(install.get("checks", []))
        if str(item.get("id", "")).startswith("permission-") and str(item.get("id", "")).endswith(("-approved", "-target-enforcement"))
    ]
    if permission_checks:
        add_error(
            errors,
            all(item.get("status") == "pass" for item in permission_checks),
            "native-permission-enforcement install simulation permission checks must all pass",
        )


def validate_native_permission_report(probes: dict[str, Any], install: dict[str, Any], errors: list[str]) -> None:
    summary = probes.get("summary", {}) if isinstance(probes.get("summary", {}), dict) else {}
    add_error(errors, probes.get("ok") is True, "native-permission-enforcement runtime probe report ok must be true")
    add_error(
        errors,
        bool(real_int(summary.get("native_enforcement_count")) and summary["native_enforcement_count"] > 0),
        "native-permission-enforcement runtime probe summary.native_enforcement_count must be >0",
    )
    add_error(
        errors,
        summary.get("failure_count") == 0,
        "native-permission-enforcement runtime probe summary.failure_count must be 0",
    )
    add_error(
        errors,
        summary.get("installer_enforcement_ready") is True,
        "native-permission-enforcement runtime probe summary.installer_enforcement_ready must be true",
    )
    validate_target_rows(probes, summary, errors)
    if install:
        validate_install_simulation_report(install, errors)
