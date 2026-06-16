#!/usr/bin/env python3
from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by output-review import and world-class human evidence validators to reject raw content, credential, secret, token, and answer-key fields recursively."

RAW_CONTENT_FIELDS = {
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

ANSWER_KEY_FIELDS = {
    "answer_key",
    "baseline_label",
    "expected",
    "expected_winner",
    "expected_winner_role",
    "expected_winner_variant",
    "label",
    "variant_label",
    "with_skill_label",
}

BLOCKED_DECISION_FIELDS = RAW_CONTENT_FIELDS | ANSWER_KEY_FIELDS


def forbidden_decision_field_paths(value: Any, prefix: str) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).strip()
            child_path = f"{prefix}.{key_text}"
            if key_text.casefold() in BLOCKED_DECISION_FIELDS:
                found.append(child_path)
            found.extend(forbidden_decision_field_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(forbidden_decision_field_paths(child, f"{prefix}[{index}]"))
    return found


def forbidden_raw_content_field_paths(value: Any, prefix: str) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).strip()
            child_path = f"{prefix}.{key_text}"
            if key_text.casefold() in RAW_CONTENT_FIELDS:
                found.append(child_path)
            found.extend(forbidden_raw_content_field_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(forbidden_raw_content_field_paths(child, f"{prefix}[{index}]"))
    return found
