#!/usr/bin/env python3
import json
from pathlib import Path
from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Builds world-class operator coordination steps and release gates for render_world_class_operator_runbook.py."


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


COORDINATION_GUIDANCE: dict[str, dict[str, str]] = {
    "provider-holdout": {
        "phase": "provider-holdout",
        "owner": "assistant + operator with provider credentials",
        "user_action": "Provide the selected provider API key through an environment variable and confirm the provider, model, endpoint, and API format to use.",
        "assistant_action": "Run provider-backed output execution, verify aggregate timing and token metadata, then prepare the evidence packet.",
        "external_dependency": "Valid provider credentials and a live provider endpoint.",
        "command": "python3 scripts/yao.py output-exec . --provider-runner <openai|deepseek> --provider-model <model> --timeout-seconds 60",
        "pass_condition": "reports/output_execution_runs.json has model_executed_count > 0 and token_observed_count > 0.",
        "artifact": "reports/output_execution_runs.json",
        "privacy_boundary": "Commit aggregate metadata only; do not commit API keys, raw prompts, raw outputs, or provider request payloads.",
    },
    "human-adjudication": {
        "phase": "human-review",
        "owner": "human reviewer + assistant",
        "user_action": "Open the blind review kit, choose winners for all pairs, add reviewer metadata and reasons, and keep the answer key hidden until decisions are saved.",
        "assistant_action": "Generate the review kit, import decisions, validate integrity, and prepare the human evidence packet.",
        "external_dependency": "A real human reviewer who can make blind A/B judgments.",
        "command": "python3 scripts/yao.py output-review-kit . && python3 scripts/yao.py output-review .",
        "pass_condition": "reports/output_review_adjudication.json has pending_count == 0 and ready_for_human_evidence == true.",
        "artifact": "reports/output_review_adjudication.json",
        "privacy_boundary": "Store reviewer choices, reasons, hashes, and attestations; do not store raw prompts or answer-key exposure before decisions.",
    },
    "native-permission-enforcement": {
        "phase": "native-permission",
        "owner": "target client or installer integrator + assistant",
        "user_action": "Select a real target client or external installer guard that can enforce declared capabilities instead of metadata-only fallback.",
        "assistant_action": "Run runtime permission probes, package verification, install simulation, and prepare the native enforcement evidence packet.",
        "external_dependency": "A real target runtime, extension, client, or installer guard that can block undeclared capabilities.",
        "command": "python3 scripts/yao.py runtime-permissions . --package-dir dist",
        "pass_condition": "reports/runtime_permission_probes.json has native_enforcement_count > 0 and failure_count == 0.",
        "artifact": "reports/runtime_permission_probes.json",
        "privacy_boundary": "Do not mark metadata fallback as native enforcement; keep residual risks visible for fallback targets.",
    },
    "native-client-telemetry": {
        "phase": "native-telemetry",
        "owner": "real client integrator + assistant",
        "user_action": "Install the native host manifest in a real Browser, Chrome, IDE, or provider client and trigger a metadata-only event.",
        "assistant_action": "Generate native host assets, import the external event JSONL, refresh adoption drift, and prepare the telemetry evidence packet.",
        "external_dependency": "A real client process that emits metadata-only telemetry through the native host.",
        "command": "python3 scripts/yao.py telemetry-import . --input-jsonl .yao/telemetry_spool/external_events.jsonl --source external",
        "pass_condition": "reports/adoption_drift_report.json has source_types.external > 0 and adoption_sample_count > 0.",
        "artifact": "reports/adoption_drift_report.json",
        "privacy_boundary": "Telemetry must remain metadata-only; do not store raw prompts, outputs, transcripts, notes, or messages.",
    },
}


def build_coordination_plan(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pending_keys = [str(item.get("evidence_key", "")) for item in items if item.get("ledger_status") != "accepted"]
    plan: list[dict[str, Any]] = [
        {
            "step_id": "prepare-evidence-session",
            "phase": "prepare",
            "evidence_key": "",
            "owner": "assistant + user",
            "requires_user_input": True,
            "user_action": "Confirm provider access, reviewer availability, target client path, and telemetry client path before collection starts.",
            "assistant_action": "Run preflight and prepare submission drafts without accepting them as evidence.",
            "external_dependency": "User-selected provider, reviewer, and real client surfaces.",
            "command": "python3 scripts/yao.py world-class-preflight . --submissions-dir evidence/world_class/submissions && python3 scripts/yao.py world-class-submission-kit . --output-dir evidence/world_class/submissions --prefill-artifacts",
            "pass_condition": "Preflight lists the same pending evidence keys and no credential values are printed.",
            "artifact": "reports/world_class_evidence_preflight.json",
            "privacy_boundary": "Drafts and preflight are planning artifacts only; they do not count as evidence.",
            "counts_as_completion": False,
        }
    ]
    for item in items:
        key = str(item.get("evidence_key", ""))
        if key not in pending_keys:
            continue
        guidance = COORDINATION_GUIDANCE.get(key, {})
        must_collect = item.get("must_collect", {}) if isinstance(item.get("must_collect", {}), dict) else {}
        commands = item.get("commands", {}) if isinstance(item.get("commands", {}), dict) else {}
        plan.append(
            {
                "step_id": f"collect-{key}",
                "phase": guidance.get("phase", "collect-source"),
                "evidence_key": key,
                "owner": guidance.get("owner", item.get("owner", "release reviewer")),
                "requires_user_input": True,
                "user_action": guidance.get("user_action", item.get("blocking_reason", "")),
                "assistant_action": guidance.get("assistant_action", "Validate source evidence and prepare the submission packet."),
                "external_dependency": guidance.get("external_dependency", "Real external or human evidence source."),
                "command": guidance.get("command", commands.get("prepare_submission", "")),
                "pass_condition": guidance.get("pass_condition", "; ".join(must_collect.get("success_checks", []))),
                "artifact": guidance.get("artifact", item.get("submission_path", "")),
                "privacy_boundary": guidance.get("privacy_boundary", "; ".join(must_collect.get("privacy_contract", []))),
                "counts_as_completion": False,
            }
        )
    plan.append(
        {
            "step_id": "review-and-release-gate",
            "phase": "release-gate",
            "evidence_key": "",
            "owner": "assistant + ledger reviewer",
            "requires_user_input": True,
            "user_action": "Approve only validated evidence packets and confirm the release wording after the claim guard passes.",
            "assistant_action": "Run intake, submission review, ledger, claim guard, benchmark, evidence consistency, Review Studio, and CI before final publish.",
            "external_dependency": "Accepted evidence packets for every pending world-class key.",
            "command": "python3 scripts/yao.py world-class-intake . --submissions-dir evidence/world_class/submissions && python3 scripts/yao.py world-class-submission-review . --submissions-dir evidence/world_class/submissions && python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions && python3 scripts/yao.py world-class-claim-guard . && make ci-test",
            "pass_condition": "Ledger ready_to_claim_world_class, benchmark public_claim_ready, claim guard violation_count == 0, Review Studio has no blockers, and CI passes.",
            "artifact": "reports/world_class_evidence_ledger.json",
            "privacy_boundary": "Release evidence may include aggregate reports and hashes only; raw content and credentials remain out of git.",
            "counts_as_completion": False,
        }
    )
    return plan


def build_release_gate(skill_dir: Path, ledger: dict[str, Any]) -> dict[str, Any]:
    reports_dir = skill_dir / "reports"
    ledger_summary = ledger.get("summary", {}) if isinstance(ledger.get("summary", {}), dict) else {}
    claim_guard = load_json(reports_dir / "world_class_claim_guard.json")
    benchmark = load_json(reports_dir / "benchmark_reproducibility.json")
    review_studio = load_json(reports_dir / "review-studio.json")
    evidence_consistency = load_json(reports_dir / "evidence_consistency.json")
    claim_summary = claim_guard.get("summary", {}) if isinstance(claim_guard.get("summary", {}), dict) else {}
    benchmark_summary = benchmark.get("summary", {}) if isinstance(benchmark.get("summary", {}), dict) else {}
    studio_summary = review_studio.get("summary", {}) if isinstance(review_studio.get("summary", {}), dict) else {}
    consistency_summary = (
        evidence_consistency.get("summary", {})
        if isinstance(evidence_consistency.get("summary", {}), dict)
        else {}
    )
    checks = [
        {
            "key": "world_class_ledger_ready",
            "label": "World-class ledger ready",
            "passed": ledger_summary.get("ready_to_claim_world_class") is True,
            "current": ledger_summary.get("decision", "missing"),
            "expected": "ready_to_claim_world_class == true",
            "artifact": "reports/world_class_evidence_ledger.json",
        },
        {
            "key": "claim_guard_clean",
            "label": "Claim guard clean",
            "passed": claim_summary.get("violation_count") == 0
            and claim_summary.get("ledger_ready_to_claim_world_class") is True,
            "current": (
                f"violations {claim_summary.get('violation_count', 'n/a')}; "
                f"ledger ready {claim_summary.get('ledger_ready_to_claim_world_class', 'n/a')}"
            ),
            "expected": "violation_count == 0 and ledger_ready_to_claim_world_class == true",
            "artifact": "reports/world_class_claim_guard.json",
        },
        {
            "key": "benchmark_public_claim_ready",
            "label": "Benchmark public claim ready",
            "passed": benchmark_summary.get("public_claim_ready") is True,
            "current": f"public_claim_ready {benchmark_summary.get('public_claim_ready', 'n/a')}",
            "expected": "public_claim_ready == true",
            "artifact": "reports/benchmark_reproducibility.json",
        },
        {
            "key": "review_studio_clean",
            "label": "Review Studio clean",
            "passed": int(studio_summary.get("blocker_count", 1) or 0) == 0
            and int(studio_summary.get("warning_count", 1) or 0) == 0,
            "current": (
                f"blockers {studio_summary.get('blocker_count', 'n/a')}; "
                f"warnings {studio_summary.get('warning_count', 'n/a')}"
            ),
            "expected": "blocker_count == 0 and warning_count == 0",
            "artifact": "reports/review-studio.json",
        },
        {
            "key": "evidence_consistency_clean",
            "label": "Evidence consistency clean",
            "passed": consistency_summary.get("decision") == "consistent"
            and int(consistency_summary.get("fail_count", 1) or 0) == 0,
            "current": consistency_summary.get("decision", "missing"),
            "expected": "decision == consistent and fail_count == 0",
            "artifact": "reports/evidence_consistency.json",
        },
    ]
    blocked = [item for item in checks if not item["passed"]]
    return {
        "ready": not blocked,
        "decision": "ready-for-public-claim" if not blocked else "blocked-until-evidence-accepted",
        "check_count": len(checks),
        "blocked_count": len(blocked),
        "checks": checks,
        "blocked_checks": blocked,
        "final_manual_check": "Run make ci-test in a clean worktree and verify GitHub Actions before converting the PR out of Draft.",
        "counts_as_completion": False,
    }
