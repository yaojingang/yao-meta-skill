#!/usr/bin/env python3
import re
from typing import Any

from output_review_privacy import forbidden_decision_field_paths


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by world_class_evidence_contract.py to validate provider-backed holdout execution evidence from run rows."

SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def add_error(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def real_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def summary(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("summary", {})
    return value if isinstance(value, dict) else {}


def normalized(value: Any) -> str:
    return str(value or "").strip().casefold()


def run_rows(execution: dict[str, Any]) -> list[dict[str, Any]]:
    runs = execution.get("runs", [])
    return [item for item in runs if isinstance(item, dict)] if isinstance(runs, list) else []


def validate_no_raw_fields(execution: dict[str, Any], errors: list[str]) -> None:
    blocked = forbidden_decision_field_paths(execution, "output_execution_runs")
    add_error(
        errors,
        not blocked,
        "provider-holdout output execution report must not include raw content, credential, secret, token, prompt, output, transcript, message, or answer-key fields: "
        + ", ".join(blocked[:8]),
    )


def positive_duration(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def observed_usage(run: dict[str, Any]) -> bool:
    usage = run.get("usage", {})
    if not isinstance(usage, dict) or usage.get("estimated") is not False:
        return False
    token_values = [
        real_int(usage.get("input_tokens")),
        real_int(usage.get("output_tokens")),
        real_int(usage.get("total_tokens")),
    ]
    return all(value is not None and value > 0 for value in token_values)


def provider_model_runs(execution: dict[str, Any], provenance: dict[str, Any]) -> list[dict[str, Any]]:
    expected_provider = normalized(provenance.get("provider"))
    expected_model = normalized(provenance.get("model"))
    matches: list[dict[str, Any]] = []
    for run in run_rows(execution):
        if run.get("status") != "pass":
            continue
        if run.get("model_executed") is not True or run.get("execution_mode") != "model":
            continue
        if normalized(run.get("provider")) != expected_provider:
            continue
        if normalized(run.get("model")) != expected_model:
            continue
        if not observed_usage(run):
            continue
        if not positive_duration(run.get("duration_ms")):
            continue
        if not SHA256_RE.match(str(run.get("output_sha256", "")).strip()):
            continue
        matches.append(run)
    return matches


def validate_provider_execution_report(
    execution: dict[str, Any],
    provenance: dict[str, Any],
    errors: list[str],
) -> None:
    execution_summary = summary(execution)
    runs = run_rows(execution)
    validate_no_raw_fields(execution, errors)
    add_error(errors, execution.get("ok") is True, "provider-holdout output execution report ok must be true")
    add_error(errors, bool(runs), "provider-holdout output execution report must include run rows")

    computed_model_runs = sum(1 for run in runs if run.get("model_executed") is True)
    computed_timing = sum(1 for run in runs if run.get("duration_ms") is not None)
    computed_token_observed = sum(1 for run in runs if isinstance(run.get("usage"), dict) and run["usage"].get("estimated") is False)
    computed_failures = sum(1 for run in runs if run.get("status") != "pass")
    add_error(
        errors,
        real_int(execution_summary.get("model_executed_count")) == computed_model_runs,
        "provider-holdout output execution summary.model_executed_count must match model-executed run rows",
    )
    add_error(
        errors,
        real_int(execution_summary.get("timing_observed_count")) == computed_timing,
        "provider-holdout output execution summary.timing_observed_count must match timed run rows",
    )
    add_error(
        errors,
        real_int(execution_summary.get("token_observed_count")) == computed_token_observed,
        "provider-holdout output execution summary.token_observed_count must match non-estimated usage rows",
    )
    add_error(
        errors,
        real_int(execution_summary.get("failure_count")) == computed_failures,
        "provider-holdout output execution summary.failure_count must match failed run rows",
    )
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
    add_error(
        errors,
        bool(provider_model_runs(execution, provenance)),
        "provider-holdout output execution runs must include a passing model run with matching provider, model, timing, non-estimated usage, and output hash",
    )
