#!/usr/bin/env python3
import argparse
import hashlib
import json
import subprocess
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Renders a release-facing benchmark reproducibility manifest and Markdown report."

METHODOLOGY_SECTIONS = [
    "## Benchmark Types",
    "## Sample Sources",
    "## Evaluation Dimensions",
    "## Weighting Rule",
    "## Failure Disclosure",
    "## Reproduction",
]

REQUIRED_ARTIFACTS = [
    ("methodology", "reports/benchmark_methodology.md"),
    ("failure_disclosure", "evals/failure-cases.md"),
    ("output_cases", "evals/output/cases.jsonl"),
    ("output_schema", "evals/output/schema.json"),
    ("output_scorecard", "reports/output_quality_scorecard.json"),
    ("output_execution", "reports/output_execution_runs.json"),
    ("blind_review", "reports/output_blind_review_pack.json"),
    ("review_adjudication", "reports/output_review_adjudication.json"),
    ("trigger_scorecard", "reports/route_scorecard.json"),
    ("runtime_conformance", "reports/conformance_matrix.json"),
    ("trust_report", "reports/security_trust_report.json"),
    ("registry_audit", "reports/registry_audit.json"),
    ("package_verification", "reports/package_verification.json"),
    ("install_simulation", "reports/install_simulation.json"),
    ("skill_os2_audit", "reports/skill_os2_audit.json"),
    ("world_class_evidence_plan", "reports/world_class_evidence_plan.json"),
    ("world_class_evidence_ledger", "reports/world_class_evidence_ledger.json"),
]

REPRODUCTION_COMMANDS = [
    {
        "label": "source commit",
        "command": "git rev-parse HEAD",
        "evidence": "git commit hash",
    },
    {
        "label": "trigger eval",
        "command": "make eval-suite",
        "evidence": "reports/eval_suite.json",
    },
    {
        "label": "output eval",
        "command": "python3 scripts/yao.py output-eval",
        "evidence": "reports/output_quality_scorecard.json",
    },
    {
        "label": "output execution",
        "command": "python3 scripts/yao.py output-exec --runner-command '[\"python3\",\"scripts/local_output_eval_runner.py\"]'",
        "evidence": "reports/output_execution_runs.json",
    },
    {
        "label": "blind review adjudication",
        "command": "python3 scripts/yao.py output-review",
        "evidence": "reports/output_review_adjudication.json",
    },
    {
        "label": "skill ir",
        "command": "python3 scripts/yao.py skill-ir . --output-json skill-ir/examples/yao-meta-skill.json",
        "evidence": "skill-ir/examples/yao-meta-skill.json",
    },
    {
        "label": "runtime conformance",
        "command": "python3 scripts/yao.py conformance .",
        "evidence": "reports/conformance_matrix.json",
    },
    {
        "label": "trust report",
        "command": "python3 scripts/yao.py trust .",
        "evidence": "reports/security_trust_report.json",
    },
    {
        "label": "package",
        "command": "python3 scripts/yao.py package . --platform openai --platform claude --platform generic --platform vscode --expectations evals/packaging_expectations.json --output-dir dist --zip",
        "evidence": "dist/yao-meta-skill.zip",
    },
    {
        "label": "package verify",
        "command": "python3 scripts/yao.py package-verify . --package-dir dist --require-zip",
        "evidence": "reports/package_verification.json",
    },
    {
        "label": "install simulate",
        "command": "python3 scripts/yao.py install-simulate . --package-dir dist",
        "evidence": "reports/install_simulation.json",
    },
    {
        "label": "registry audit",
        "command": "python3 scripts/yao.py registry-audit .",
        "evidence": "reports/registry_audit.json",
    },
    {
        "label": "skill os audit",
        "command": "python3 scripts/yao.py skill-os2-audit .",
        "evidence": "reports/skill_os2_audit.json",
    },
    {
        "label": "world-class evidence plan",
        "command": "python3 scripts/yao.py world-class-evidence .",
        "evidence": "reports/world_class_evidence_plan.json",
    },
    {
        "label": "world-class evidence ledger",
        "command": "python3 scripts/yao.py world-class-ledger .",
        "evidence": "reports/world_class_evidence_ledger.json",
    },
    {
        "label": "full ci",
        "command": "make ci-test",
        "evidence": "CI target output",
    },
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def rel_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit(skill_dir: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=skill_dir,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return proc.stdout.strip() or "unknown"


def git_status(skill_dir: Path) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["git", "status", "--short", "--untracked-files=all"],
            cwd=skill_dir,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return {"available": False, "dirty": None, "changed_file_count": None}
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    return {
        "available": True,
        "dirty": bool(lines),
        "changed_file_count": len(lines),
        "sample": lines[:12],
    }


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def count_failure_cases(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("### "))


def methodology_check(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    sections = [{"heading": heading, "exists": heading in text} for heading in METHODOLOGY_SECTIONS]
    return {
        "path": "reports/benchmark_methodology.md",
        "exists": path.exists(),
        "sections": sections,
        "missing_sections": [item["heading"] for item in sections if not item["exists"]],
    }


def artifact_record(skill_dir: Path, label: str, rel: str) -> dict[str, Any]:
    path = skill_dir / rel
    record: dict[str, Any] = {
        "label": label,
        "path": rel,
        "exists": path.exists(),
    }
    if path.exists() and path.is_file():
        record["bytes"] = path.stat().st_size
        record["sha256"] = sha256_file(path)
    return record


def build_report(skill_dir: Path, generated_at: str) -> dict[str, Any]:
    reports = skill_dir / "reports"
    output_quality = load_json(reports / "output_quality_scorecard.json")
    output_execution = load_json(reports / "output_execution_runs.json")
    output_review = load_json(reports / "output_review_adjudication.json")
    skill_os2 = load_json(reports / "skill_os2_audit.json")
    world_class_plan = load_json(reports / "world_class_evidence_plan.json")
    world_class_ledger = load_json(reports / "world_class_evidence_ledger.json")
    methodology = methodology_check(reports / "benchmark_methodology.md")
    artifacts = [artifact_record(skill_dir, label, rel) for label, rel in REQUIRED_ARTIFACTS]
    missing_artifacts = [item["path"] for item in artifacts if not item["exists"]]
    output_summary = output_quality.get("summary", {})
    execution_summary = output_execution.get("summary", {})
    review_summary = output_review.get("summary", {})
    failure_case_count = count_failure_cases(skill_dir / "evals" / "failure-cases.md")
    output_case_count = count_jsonl(skill_dir / "evals" / "output" / "cases.jsonl")
    status = git_status(skill_dir)
    local_reproducibility_ready = (
        not methodology["missing_sections"]
        and not missing_artifacts
        and output_case_count >= 5
        and failure_case_count > 0
        and output_summary.get("gate_pass") is True
        and execution_summary.get("command_executed_count", 0) > 0
        and execution_summary.get("timing_observed_count", 0) > 0
    )
    human_review_complete = review_summary.get("pair_count", 0) > 0 and review_summary.get("pending_count", 0) == 0
    provider_evidence_complete = execution_summary.get("model_executed_count", 0) > 0 and execution_summary.get("token_observed_count", 0) > 0
    return {
        "schema_version": "1.0",
        "ok": local_reproducibility_ready,
        "generated_at": generated_at,
        "skill_dir": rel_path(skill_dir, ROOT),
        "commit": git_commit(skill_dir),
        "git_status": status,
        "summary": {
            "reproducibility_ready": local_reproducibility_ready,
            "methodology_complete": not methodology["missing_sections"],
            "required_artifact_count": len(artifacts),
            "missing_artifact_count": len(missing_artifacts),
            "output_case_count": output_case_count,
            "failure_disclosure_count": failure_case_count,
            "command_count": len(REPRODUCTION_COMMANDS),
            "command_executed_count": execution_summary.get("command_executed_count", 0),
            "timing_observed_count": execution_summary.get("timing_observed_count", 0),
            "model_executed_count": execution_summary.get("model_executed_count", 0),
            "token_observed_count": execution_summary.get("token_observed_count", 0),
            "human_review_complete": human_review_complete,
            "provider_evidence_complete": provider_evidence_complete,
            "world_class_ready": bool(skill_os2.get("summary", {}).get("world_class_ready", False)),
            "world_class_open_gap_count": skill_os2.get("summary", {}).get("open_gap_count", 0),
            "world_class_task_count": world_class_plan.get("summary", {}).get("task_count", 0),
            "world_class_ledger_pending_count": world_class_ledger.get("summary", {}).get("pending_count", 0),
            "working_tree_dirty": status.get("dirty"),
            "changed_file_count": status.get("changed_file_count"),
        },
        "methodology": methodology,
        "artifacts_checked": artifacts,
        "missing_artifacts": missing_artifacts,
        "reproduction_commands": REPRODUCTION_COMMANDS,
        "failure_disclosure": {
            "path": "evals/failure-cases.md",
            "case_count": failure_case_count,
            "policy": "Keep representative failures visible and tied to regression checks.",
        },
        "limitations": [
            "Local command-runner evidence is reproducible but does not replace provider-backed model holdout evidence.",
            "Pending blind-review decisions are visible but do not count as human adjudication.",
            "World-class readiness remains false until external and human evidence gaps close.",
        ],
        "artifacts": {
            "json": "reports/benchmark_reproducibility.json",
            "markdown": "reports/benchmark_reproducibility.md",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Benchmark Reproducibility",
        "",
        f"Generated at: `{report['generated_at']}`",
        f"Commit: `{report['commit']}`",
        f"Working tree dirty at generation: `{str(summary.get('working_tree_dirty')).lower()}`",
        "",
        "## Summary",
        "",
        f"- reproducibility ready: `{str(summary['reproducibility_ready']).lower()}`",
        f"- methodology complete: `{str(summary['methodology_complete']).lower()}`",
        f"- required artifacts: `{summary['required_artifact_count']}`",
        f"- missing artifacts: `{summary['missing_artifact_count']}`",
        f"- output cases: `{summary['output_case_count']}`",
        f"- disclosed failure cases: `{summary['failure_disclosure_count']}`",
        f"- reproduction commands: `{summary['command_count']}`",
        f"- provider evidence complete: `{str(summary['provider_evidence_complete']).lower()}`",
        f"- human review complete: `{str(summary['human_review_complete']).lower()}`",
        f"- world-class ready: `{str(summary['world_class_ready']).lower()}`",
        f"- changed files at generation: `{summary.get('changed_file_count')}`",
        "",
        "This report proves local benchmark reproducibility only. It keeps external provider and human-review gaps visible instead of counting them as complete.",
        "",
        "## Methodology Sections",
        "",
        "| Section | Status |",
        "| --- | --- |",
    ]
    for section in report["methodology"]["sections"]:
        lines.append(f"| `{section['heading']}` | {'present' if section['exists'] else 'missing'} |")
    lines.extend(["", "## Required Artifacts", "", "| Label | Path | Status | SHA256 |", "| --- | --- | --- | --- |"])
    for artifact in report["artifacts_checked"]:
        digest = artifact.get("sha256", "")
        lines.append(
            f"| {artifact['label']} | `{artifact['path']}` | {'present' if artifact['exists'] else 'missing'} | `{digest[:12]}` |"
        )
    lines.extend(["", "## Reproduction Commands", ""])
    for command in report["reproduction_commands"]:
        lines.append(f"- `{command['command']}`")
        lines.append(f"  - evidence: `{command['evidence']}`")
    lines.extend(["", "## Failure Disclosure", ""])
    disclosure = report["failure_disclosure"]
    lines.append(f"- path: `{disclosure['path']}`")
    lines.append(f"- disclosed cases: `{disclosure['case_count']}`")
    lines.append(f"- policy: {disclosure['policy']}")
    lines.extend(["", "## Limits", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render benchmark reproducibility evidence.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--output-json", default="reports/benchmark_reproducibility.json")
    parser.add_argument("--output-md", default="reports/benchmark_reproducibility.md")
    parser.add_argument("--generated-at", default=date.today().isoformat())
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    report = build_report(skill_dir, args.generated_at)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    if not output_json.is_absolute():
        output_json = skill_dir / output_json
    if not output_md.is_absolute():
        output_md = skill_dir / output_md
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
