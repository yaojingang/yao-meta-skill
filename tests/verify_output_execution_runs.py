#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "run_output_execution.py"
LOCAL_RUNNER = ROOT / "scripts" / "local_output_eval_runner.py"
PROVIDER_RUNNER = ROOT / "scripts" / "provider_output_eval_runner.py"


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_output_execution"
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    tmp_root.mkdir(parents=True, exist_ok=True)

    recorded_json = tmp_root / "recorded.json"
    recorded_md = tmp_root / "recorded.md"
    recorded_proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--cases",
            str(ROOT / "evals" / "output" / "cases.jsonl"),
            "--output-json",
            str(recorded_json),
            "--output-md",
            str(recorded_md),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    recorded = json.loads(recorded_proc.stdout)
    assert recorded["ok"], recorded
    assert recorded["summary"]["case_count"] == 5, recorded
    assert recorded["summary"]["variant_run_count"] == 10, recorded
    assert recorded["summary"]["recorded_fixture_count"] == 10, recorded
    assert recorded["summary"]["command_executed_count"] == 0, recorded
    assert recorded["summary"]["model_executed_count"] == 0, recorded
    assert recorded["summary"]["token_estimated_count"] == 10, recorded
    assert recorded["summary"]["with_skill_pass_rate"] > recorded["summary"]["baseline_pass_rate"], recorded
    assert "No model-executed runs are recorded yet" in recorded_md.read_text(encoding="utf-8"), recorded_md

    local_proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--cases",
            str(ROOT / "evals" / "output" / "cases.jsonl"),
            "--output-json",
            str(tmp_root / "local.json"),
            "--output-md",
            str(tmp_root / "local.md"),
            "--runner-command",
            json.dumps([sys.executable, str(LOCAL_RUNNER)]),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    local = json.loads(local_proc.stdout)
    assert local["ok"], local
    assert local["summary"]["variant_run_count"] == 10, local
    assert local["summary"]["command_executed_count"] == 10, local
    assert local["summary"]["recorded_fixture_count"] == 0, local
    assert local["summary"]["model_executed_count"] == 0, local
    assert local["summary"]["timing_observed_count"] == 10, local
    assert local["summary"]["token_estimated_count"] == 10, local
    assert all(item["provider"] == "local-output-eval-runner" for item in local["runs"]), local
    local_md = (tmp_root / "local.md").read_text(encoding="utf-8")
    assert "Command runner evidence is present" in local_md, local_md
    assert "not provider-backed model evidence" in local_md, local_md

    runner = tmp_root / "runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, sys, time",
                "request = json.loads(sys.stdin.read())",
                "time.sleep(0.001)",
                "print(json.dumps({",
                "  'output': request['fixture_output'],",
                "  'execution_kind': 'model',",
                "  'provider': 'local-fixture',",
                "  'model': 'fixture-model',",
                "  'usage': {'input_tokens': 11, 'output_tokens': 17, 'total_tokens': 28}",
                "}))",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    command_json = json.dumps([sys.executable, str(runner)])
    command_proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--cases",
            str(ROOT / "evals" / "output" / "cases.jsonl"),
            "--output-json",
            str(tmp_root / "command.json"),
            "--output-md",
            str(tmp_root / "command.md"),
            "--runner-command",
            command_json,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    command = json.loads(command_proc.stdout)
    assert command["ok"], command
    assert command["summary"]["command_executed_count"] == 10, command
    assert command["summary"]["model_executed_count"] == 10, command
    assert command["summary"]["timing_observed_count"] == 10, command
    assert command["summary"]["token_observed_count"] == 10, command
    assert command["summary"]["token_estimated_count"] == 0, command
    assert all(item["duration_ms"] is not None for item in command["runs"]), command
    assert all(item["model"] == "fixture-model" for item in command["runs"]), command

    metadata_only_runner = tmp_root / "metadata_only_runner.py"
    metadata_only_runner.write_text(
        "\n".join(
            [
                "import json, sys",
                "request = json.loads(sys.stdin.read())",
                "print(json.dumps({",
                "  'output': request['fixture_output'],",
                "  'provider': 'metadata-only-provider',",
                "  'model': 'metadata-only-model',",
                "  'usage': {'input_tokens': 11, 'output_tokens': 17, 'total_tokens': 28}",
                "}))",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    metadata_only_proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--cases",
            str(ROOT / "evals" / "output" / "cases.jsonl"),
            "--output-json",
            str(tmp_root / "metadata-only.json"),
            "--output-md",
            str(tmp_root / "metadata-only.md"),
            "--runner-command",
            json.dumps([sys.executable, str(metadata_only_runner)]),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    metadata_only = json.loads(metadata_only_proc.stdout)
    assert metadata_only["ok"], metadata_only
    assert metadata_only["summary"]["command_executed_count"] == 10, metadata_only
    assert metadata_only["summary"]["model_executed_count"] == 0, metadata_only
    assert metadata_only["summary"]["token_observed_count"] == 10, metadata_only
    assert all(item["execution_mode"] == "command" for item in metadata_only["runs"]), metadata_only

    provider_request = {
        "case_id": "provider-contract",
        "variant": "with_skill",
        "prompt": "Create a reusable skill package.",
        "input_files": [],
        "metadata": {},
    }
    missing_env = os.environ.copy()
    missing_env.pop("OPENAI_API_KEY", None)
    missing_env.pop("YAO_OUTPUT_EVAL_MODEL", None)
    missing_provider_proc = subprocess.run(
        [sys.executable, str(PROVIDER_RUNNER), "--model", "fixture-model"],
        cwd=ROOT,
        input=json.dumps(provider_request),
        capture_output=True,
        text=True,
        env=missing_env,
    )
    assert missing_provider_proc.returncode == 2, missing_provider_proc.stdout
    assert "missing API key env" in missing_provider_proc.stderr, missing_provider_proc.stderr
    missing_deepseek_proc = subprocess.run(
        [sys.executable, str(PROVIDER_RUNNER), "--provider", "deepseek", "--model", "fixture-model"],
        cwd=ROOT,
        input=json.dumps(provider_request),
        capture_output=True,
        text=True,
        env=missing_env,
    )
    assert missing_deepseek_proc.returncode == 2, missing_deepseek_proc.stdout
    assert "missing API key env: DEEPSEEK_API_KEY" in missing_deepseek_proc.stderr, missing_deepseek_proc.stderr

    custom_env = os.environ.copy()
    custom_env["OPENAI_API_KEY"] = "test-key"
    custom_env["DEEPSEEK_API_KEY"] = "test-key"
    custom_env["YAO_OUTPUT_EVAL_MODEL"] = "fixture-model"
    custom_host_proc = subprocess.run(
        [
            sys.executable,
            str(PROVIDER_RUNNER),
            "--base-url",
            "https://example.com/v1/responses",
        ],
        cwd=ROOT,
        input=json.dumps(provider_request),
        capture_output=True,
        text=True,
        env=custom_env,
    )
    assert custom_host_proc.returncode == 2, custom_host_proc.stdout
    assert "custom provider host requires --allow-custom-base-url" in custom_host_proc.stderr, custom_host_proc.stderr

    wrong_path_proc = subprocess.run(
        [
            sys.executable,
            str(PROVIDER_RUNNER),
            "--base-url",
            "https://api.openai.com/v1/chat/completions",
        ],
        cwd=ROOT,
        input=json.dumps(provider_request),
        capture_output=True,
        text=True,
        env=custom_env,
    )
    assert wrong_path_proc.returncode == 2, wrong_path_proc.stdout
    assert "provider endpoint path must start with /v1/responses" in wrong_path_proc.stderr, wrong_path_proc.stderr
    empty_path_proc = subprocess.run(
        [
            sys.executable,
            str(PROVIDER_RUNNER),
            "--base-url",
            "https://api.openai.com",
        ],
        cwd=ROOT,
        input=json.dumps(provider_request),
        capture_output=True,
        text=True,
        env=custom_env,
    )
    assert empty_path_proc.returncode == 2, empty_path_proc.stdout
    assert "provider endpoint path must start with /v1/responses" in empty_path_proc.stderr, empty_path_proc.stderr

    class ProviderHandler(BaseHTTPRequestHandler):
        requests: list[dict] = []

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            ProviderHandler.requests.append(
                {
                    "path": self.path,
                    "authorization": self.headers.get("Authorization", ""),
                    "body": json.loads(body),
                }
            )
            if self.path.endswith("/chat/completions"):
                payload = {
                    "id": "chat_fixture",
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "Create SKILL.md and reports/skill-overview.html for this reusable package.",
                            }
                        }
                    ],
                    "usage": {"prompt_tokens": 21, "completion_tokens": 9, "total_tokens": 30},
                }
            else:
                payload = {
                    "id": "resp_fixture",
                    "output": [
                        {
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": "Create SKILL.md and reports/skill-overview.html for this reusable package.",
                                }
                            ]
                        }
                    ],
                    "usage": {"input_tokens": 21, "output_tokens": 9, "total_tokens": 30},
                }
            encoded = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = HTTPServer(("127.0.0.1", 0), ProviderHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    provider_url = f"http://127.0.0.1:{server.server_port}/v1/responses"
    provider_env = os.environ.copy()
    provider_env["OPENAI_API_KEY"] = "test-key"
    provider_env["DEEPSEEK_API_KEY"] = "test-key"
    provider_env["YAO_OUTPUT_EVAL_MODEL"] = "fixture-model"
    try:
        direct_provider_proc = subprocess.run(
            [
                sys.executable,
                str(PROVIDER_RUNNER),
                "--base-url",
                provider_url,
                "--allow-insecure-localhost",
            ],
            cwd=ROOT,
            input=json.dumps(provider_request),
            capture_output=True,
            text=True,
            env=provider_env,
            check=True,
        )
        direct_provider = json.loads(direct_provider_proc.stdout)
        assert direct_provider["execution_kind"] == "model", direct_provider
        assert direct_provider["provider"] == "openai", direct_provider
        assert direct_provider["model"] == "fixture-model", direct_provider
        assert direct_provider["usage"]["estimated"] is False, direct_provider
        assert ProviderHandler.requests[-1]["path"] == "/v1/responses", ProviderHandler.requests[-1]
        assert ProviderHandler.requests[-1]["authorization"] == "Bearer test-key", ProviderHandler.requests[-1]
        assert ProviderHandler.requests[-1]["body"]["model"] == "fixture-model", ProviderHandler.requests[-1]
        assert ProviderHandler.requests[-1]["body"]["temperature"] == 0.0, ProviderHandler.requests[-1]
        assert "Create a reusable skill package." in ProviderHandler.requests[-1]["body"]["input"], ProviderHandler.requests[-1]
        assert "fixture_output" not in ProviderHandler.requests[-1]["body"]["input"], ProviderHandler.requests[-1]

        governed_provider_request = {
            "case_id": "file-backed-governed-package",
            "variant": "with_skill",
            "prompt": "Turn the attached release brief source into a governed skill package.",
            "input_files": ["fixtures/release-brief-source.md"],
            "metadata": {"case_type": "boundary", "tier": "governed"},
        }
        governed_provider_proc = subprocess.run(
            [
                sys.executable,
                str(PROVIDER_RUNNER),
                "--base-url",
                provider_url,
                "--allow-insecure-localhost",
                "--model",
                "fixture-model",
            ],
            cwd=ROOT,
            input=json.dumps(governed_provider_request),
            capture_output=True,
            text=True,
            env=provider_env,
            check=True,
        )
        governed_provider = json.loads(governed_provider_proc.stdout)
        assert governed_provider["execution_kind"] == "model", governed_provider
        governed_input = ProviderHandler.requests[-1]["body"]["input"]
        assert "Release Brief Source Fixture" in governed_input, governed_input
        assert "file-backed fixture" in governed_input, governed_input
        assert "evidence" in governed_input, governed_input
        assert "input_files" in governed_input, governed_input
        assert "output contract" in governed_input, governed_input
        assert "rollback boundary" in governed_input, governed_input
        assert "trust report" in governed_input, governed_input
        assert "reports/output_quality_scorecard.md" in governed_input, governed_input
        assert "missing evidence" in governed_input, governed_input

        chat_provider_url = f"http://127.0.0.1:{server.server_port}/chat/completions"
        direct_chat_provider_proc = subprocess.run(
            [
                sys.executable,
                str(PROVIDER_RUNNER),
                "--provider",
                "deepseek",
                "--api-format",
                "chat-completions",
                "--thinking",
                "disabled",
                "--base-url",
                chat_provider_url,
                "--allow-insecure-localhost",
                "--model",
                "fixture-model",
            ],
            cwd=ROOT,
            input=json.dumps(provider_request),
            capture_output=True,
            text=True,
            env=provider_env,
            check=True,
        )
        direct_chat_provider = json.loads(direct_chat_provider_proc.stdout)
        assert direct_chat_provider["execution_kind"] == "model", direct_chat_provider
        assert direct_chat_provider["provider"] == "deepseek", direct_chat_provider
        assert direct_chat_provider["model"] == "fixture-model", direct_chat_provider
        assert direct_chat_provider["usage"]["estimated"] is False, direct_chat_provider
        assert ProviderHandler.requests[-1]["path"] == "/chat/completions", ProviderHandler.requests[-1]
        assert ProviderHandler.requests[-1]["body"]["model"] == "fixture-model", ProviderHandler.requests[-1]
        assert ProviderHandler.requests[-1]["body"]["thinking"]["type"] == "disabled", ProviderHandler.requests[-1]
        assert ProviderHandler.requests[-1]["body"]["temperature"] == 0.0, ProviderHandler.requests[-1]
        assert "Create a reusable skill package." in ProviderHandler.requests[-1]["body"]["messages"][0]["content"], (
            ProviderHandler.requests[-1]
        )

        provider_cases = tmp_root / "provider_cases.jsonl"
        provider_cases.write_text(
            json.dumps(
                {
                    "id": "provider-contract",
                    "prompt": "Create a reusable skill package.",
                    "baseline_output": "",
                    "with_skill_output": "",
                    "assertions": [
                        {
                            "id": "has-skill-entry",
                            "description": "Provider output includes the skill entrypoint.",
                            "required": ["SKILL.md"],
                        }
                    ],
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        provider_proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--cases",
                str(provider_cases),
                "--output-json",
                str(tmp_root / "provider.json"),
                "--output-md",
                str(tmp_root / "provider.md"),
                "--runner-command",
                json.dumps(
                    [
                        sys.executable,
                        str(PROVIDER_RUNNER),
                        "--base-url",
                        provider_url,
                        "--allow-insecure-localhost",
                        "--model",
                        "fixture-model",
                    ]
                ),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            env=provider_env,
            check=True,
        )
        provider = json.loads(provider_proc.stdout)
        assert provider["ok"], provider
        assert provider["summary"]["variant_run_count"] == 2, provider
        assert provider["summary"]["model_executed_count"] == 2, provider
        assert provider["summary"]["token_observed_count"] == 2, provider
        assert provider["summary"]["token_estimated_count"] == 0, provider
        assert all(item["provider"] == "openai" for item in provider["runs"]), provider
        assert all(item["model"] == "fixture-model" for item in provider["runs"]), provider
    finally:
        server.shutdown()
        thread.join(timeout=2)

    bad_runner = tmp_root / "bad_runner.py"
    bad_runner.write_text("import sys\nsys.exit(3)\n", encoding="utf-8")
    bad_proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--cases",
            str(ROOT / "evals" / "output" / "cases.jsonl"),
            "--output-json",
            str(tmp_root / "bad.json"),
            "--output-md",
            str(tmp_root / "bad.md"),
            "--runner-command",
            json.dumps([sys.executable, str(bad_runner)]),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert bad_proc.returncode == 2, bad_proc.stdout
    bad = json.loads(bad_proc.stdout)
    assert not bad["ok"], bad
    assert bad["summary"]["failure_count"] == 10, bad
    assert bad["failures"], bad

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
