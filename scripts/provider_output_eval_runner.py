#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1/responses"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_BASE_URL = DEFAULT_OPENAI_BASE_URL
DEFAULT_HOST = urlparse(DEFAULT_OPENAI_BASE_URL).hostname or "api.openai.com"
DEFAULT_PROVIDER_CONFIGS = {
    "openai": {
        "base_url": DEFAULT_OPENAI_BASE_URL,
        "api_format": "responses",
        "api_key_env": "OPENAI_API_KEY",
        "thinking": "",
    },
    "deepseek": {
        "base_url": DEFAULT_DEEPSEEK_BASE_URL,
        "api_format": "chat-completions",
        "api_key_env": "DEEPSEEK_API_KEY",
        "thinking": "disabled",
    },
}
ALLOWED_PATH_PREFIX = "/v1/responses"
CHAT_COMPLETIONS_PATHS = {"/chat/completions", "/v1/chat/completions"}
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(2)


def validate_base_url(
    base_url: str,
    allow_insecure_localhost: bool,
    allow_custom_base_url: bool,
    api_format: str,
) -> None:
    parsed = urlparse(base_url)
    host = parsed.hostname or ""
    if api_format == "responses" and not parsed.path.startswith(ALLOWED_PATH_PREFIX):
        fail(f"provider endpoint path must start with {ALLOWED_PATH_PREFIX}")
    if api_format == "chat-completions" and parsed.path not in CHAT_COMPLETIONS_PATHS:
        fail("chat-completions provider endpoint path must be /chat/completions or /v1/chat/completions")
    if parsed.scheme == "https" and (
        base_url in {DEFAULT_OPENAI_BASE_URL, DEFAULT_DEEPSEEK_BASE_URL}
        or host == DEFAULT_HOST
        or allow_custom_base_url
    ):
        return
    if parsed.scheme == "https":
        fail("custom provider host requires --allow-custom-base-url")
    if parsed.scheme == "http" and allow_insecure_localhost and (parsed.hostname or "") in LOCAL_HOSTS:
        return
    fail("provider runner requires HTTPS; use --allow-insecure-localhost only for local test servers")


def provider_defaults(provider: str) -> dict[str, str]:
    return DEFAULT_PROVIDER_CONFIGS.get(provider, DEFAULT_PROVIDER_CONFIGS["openai"])


def load_request() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        fail("provider runner requires a JSON request on stdin")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON request: {exc}")
    if not isinstance(payload, dict):
        fail("runner request must be a JSON object")
    return payload


def safe_relative(path_value: str) -> Path | None:
    path = Path(path_value)
    if path.is_absolute() or ".." in path.parts:
        return None
    return path


def read_input_files(paths: Any, input_root: Path, max_chars: int) -> list[dict[str, str]]:
    if not isinstance(paths, list):
        return []
    files: list[dict[str, str]] = []
    for item in paths:
        rel = safe_relative(str(item))
        if rel is None:
            files.append({"path": str(item), "status": "skipped-unsafe-path", "content": ""})
            continue
        path = input_root / rel
        if not path.exists() or not path.is_file():
            files.append({"path": str(item), "status": "missing", "content": ""})
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        files.append({"path": str(item), "status": "loaded", "content": text[:max_chars]})
    return files


def read_skill_instructions(path: Path, max_chars: int) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:max_chars]


def build_provider_input(request: dict[str, Any], skill_text: str, input_files: list[dict[str, str]]) -> str:
    variant = str(request.get("variant", ""))
    lines = [
        "You are producing one output for a Yao Meta Skill output-eval case.",
        f"Case id: {request.get('case_id', '')}",
        f"Variant: {variant}",
        "",
        "User task:",
        str(request.get("prompt", "")),
        "",
    ]
    if variant == "with_skill":
        lines.extend(
            [
                "Use the skill instructions below as the operating guidance. Preserve concrete evidence paths and boundaries.",
                "",
                "Skill instructions:",
                skill_text or "(Skill instructions were not available.)",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "Produce a direct baseline answer without using the Yao Meta Skill guidance.",
                "Do not invent files, reports, governance evidence, or hidden review artifacts.",
                "",
            ]
        )
    if input_files:
        lines.append("Input files:")
        for item in input_files:
            lines.append(f"--- {item['path']} ({item['status']}) ---")
            if item["content"]:
                lines.append(item["content"])
        lines.append("")
    lines.extend(
        [
            "Return only the final user-facing answer for this variant.",
            "Do not mention or copy any fixture output from the eval case.",
        ]
    )
    return "\n".join(lines)


def response_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("output_text"), str):
        return str(payload["output_text"])
    parts: list[str] = []
    output = payload.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if isinstance(block.get("text"), str):
                    parts.append(str(block["text"]))
    if parts:
        return "\n".join(part for part in parts if part).strip()
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            message = first.get("message", {})
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                return str(message["content"])
    return ""


def observed_usage(payload: dict[str, Any]) -> dict[str, Any]:
    usage = payload.get("usage", {})
    if not isinstance(usage, dict):
        return {}
    input_tokens = usage.get("input_tokens", usage.get("prompt_tokens"))
    output_tokens = usage.get("output_tokens", usage.get("completion_tokens"))
    total_tokens = usage.get("total_tokens")
    result: dict[str, Any] = {}
    if input_tokens is not None:
        result["input_tokens"] = int(input_tokens)
    if output_tokens is not None:
        result["output_tokens"] = int(output_tokens)
    if total_tokens is not None:
        result["total_tokens"] = int(total_tokens)
    if result:
        result["estimated"] = False
    return result


def request_body(
    model: str,
    provider_input: str,
    api_format: str,
    thinking_type: str,
    temperature: float | None,
) -> dict[str, Any]:
    if api_format == "chat-completions":
        body: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": provider_input}],
        }
        if thinking_type:
            body["thinking"] = {"type": thinking_type}
        if temperature is not None:
            body["temperature"] = temperature
        return body
    body = {"model": model, "input": provider_input}
    if temperature is not None:
        body["temperature"] = temperature
    return body


def call_provider(
    base_url: str,
    api_key: str,
    model: str,
    provider_input: str,
    timeout_seconds: float,
    api_format: str,
    thinking_type: str,
    temperature: float | None,
) -> dict[str, Any]:
    body = json.dumps(
        request_body(model, provider_input, api_format, thinking_type, temperature),
        ensure_ascii=False,
    ).encode("utf-8")
    request = Request(
        base_url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            response_body = response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        fail(f"provider request failed with HTTP {exc.code}: {detail}")
    except URLError as exc:
        fail(f"provider request failed: {exc.reason}")
    try:
        payload = json.loads(response_body)
    except json.JSONDecodeError as exc:
        fail(f"provider returned invalid JSON: {exc}")
    if not isinstance(payload, dict):
        fail("provider response must be a JSON object")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Provider-backed output-eval runner for run_output_execution.py. "
            "Requires real model credentials and reports execution_kind=model only after an HTTP provider call."
        )
    )
    parser.add_argument("--provider", default="openai", help="Provider label to write into execution evidence.")
    parser.add_argument(
        "--base-url",
        help="Override the provider endpoint. Defaults are selected from --provider.",
    )
    parser.add_argument(
        "--api-format",
        choices=["responses", "chat-completions"],
        help="Provider API shape. Defaults are selected from --provider.",
    )
    parser.add_argument("--thinking", choices=["enabled", "disabled"], help="Optional chat-completions thinking mode.")
    parser.add_argument("--temperature", type=float, default=0.0, help="Sampling temperature for provider requests.")
    parser.add_argument("--model", default=os.environ.get("YAO_OUTPUT_EVAL_MODEL", ""))
    parser.add_argument("--api-key-env", help="Environment variable that contains the provider API key.")
    parser.add_argument("--input-root", default=str(ROOT / "evals" / "output"))
    parser.add_argument("--skill-file", default=str(ROOT / "SKILL.md"))
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--max-input-file-chars", type=int, default=6000)
    parser.add_argument("--max-skill-chars", type=int, default=8000)
    parser.add_argument("--allow-insecure-localhost", action="store_true")
    parser.add_argument("--allow-custom-base-url", action="store_true")
    args = parser.parse_args()

    defaults = provider_defaults(args.provider)
    base_url = args.base_url or defaults["base_url"]
    api_format = args.api_format or defaults["api_format"]
    thinking = args.thinking if args.thinking is not None else defaults["thinking"]
    api_key_env = args.api_key_env or defaults["api_key_env"]

    validate_base_url(base_url, args.allow_insecure_localhost, args.allow_custom_base_url, api_format)
    if args.temperature is not None and not 0 <= args.temperature <= 2:
        fail("--temperature must be between 0 and 2")
    if not args.model:
        fail("missing model; pass --model or set YAO_OUTPUT_EVAL_MODEL")
    api_key = os.environ.get(api_key_env, "")
    if not api_key:
        fail(f"missing API key env: {api_key_env}")

    request = load_request()
    input_files = read_input_files(request.get("input_files", []), Path(args.input_root).resolve(), args.max_input_file_chars)
    skill_text = read_skill_instructions(Path(args.skill_file).resolve(), args.max_skill_chars)
    provider_input = build_provider_input(request, skill_text, input_files)
    response = call_provider(
        base_url,
        api_key,
        args.model,
        provider_input,
        args.timeout_seconds,
        api_format,
        thinking,
        args.temperature,
    )
    output = response_text(response)
    if not output:
        fail("provider response did not contain output text")
    result = {
        "output": output,
        "execution_kind": "model",
        "provider": args.provider,
        "model": args.model,
        "usage": observed_usage(response),
        "response_id": str(response.get("id", "")),
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
