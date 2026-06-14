#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parent.parent


def run(name: str, cmd: list[str], expect_ok: bool = True, expected_substrings: list[str] | None = None) -> dict:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    payload = {}
    if proc.stdout.strip():
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload = {"raw_stdout": proc.stdout}

    joined = proc.stdout + "\n" + proc.stderr
    passed = proc.returncode == 0 if expect_ok else proc.returncode == 2
    if expected_substrings:
        passed = passed and all(fragment in joined for fragment in expected_substrings)

    return {
        "name": name,
        "passed": passed,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "payload": payload,
    }


def require_min_score(case: dict, minimum: int) -> None:
    score = case.get("payload", {}).get("details", {}).get("governance_score")
    case["minimum_score"] = minimum
    case["observed_score"] = score
    case["passed"] = case["passed"] and score is not None and score >= minimum


def require_context_targets(case: dict, max_initial: int, min_density: float) -> None:
    stats = case.get("payload", {}).get("stats", {})
    initial = stats.get("estimated_initial_load_tokens")
    density = stats.get("quality_density")
    deferred = stats.get("deferred_resource_tokens")
    deferred_threshold = stats.get("deferred_resource_warn_threshold")
    deferred_dirs = stats.get("deferred_resource_dirs", [])
    deferred_governance = stats.get("deferred_resource_governance", {})
    unused = stats.get("unused_resource_dirs", [])
    case["max_initial_load"] = max_initial
    case["observed_initial_load"] = initial
    case["minimum_quality_density"] = min_density
    case["observed_quality_density"] = density
    case["observed_deferred_resource_tokens"] = deferred
    case["deferred_resource_warn_threshold"] = deferred_threshold
    case["deferred_resource_dir_count"] = len(deferred_dirs) if isinstance(deferred_dirs, list) else None
    case["deferred_resource_governance_status"] = deferred_governance.get("status") if isinstance(deferred_governance, dict) else None
    case["unused_resource_dirs"] = unused
    case["passed"] = (
        case["passed"]
        and initial is not None
        and density is not None
        and deferred is not None
        and deferred_threshold is not None
        and isinstance(deferred_dirs, list)
        and isinstance(deferred_governance, dict)
        and deferred_governance.get("status") in {"governed", "not-required", "needs-review"}
        and initial <= max_initial
        and density >= min_density
        and not unused
    )


def verify_private_report_ignored() -> dict:
    with TemporaryDirectory(prefix="yao-private-report-ignore-") as temp_dir:
        skill_dir = Path(temp_dir) / "skill"
        (skill_dir / "reports").mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: report-ignore-fixture\n"
            "description: Test fixture for ignored private reports.\n"
            "---\n"
            "Use this fixture to validate context sizing.\n",
            encoding="utf-8",
        )
        (skill_dir / "reports" / "kept.md").write_text("stable evidence\n", encoding="utf-8")
        baseline = run(
            "private_report_ignore_baseline",
            [sys.executable, "scripts/context_sizer.py", str(skill_dir), "--json"],
        )
        (skill_dir / "reports" / "client-research-plan.md").write_text(
            "private notes\n" * 500,
            encoding="utf-8",
        )
        context_case = run(
            "private_report_ignore_context_sizer",
            [sys.executable, "scripts/context_sizer.py", str(skill_dir), "--json"],
        )
        boundary_case = run(
            "private_report_ignore_resource_boundary",
            [sys.executable, "scripts/resource_boundary_check.py", str(skill_dir), "--max-initial-tokens", "5000"],
        )

    baseline_total = baseline.get("payload", {}).get("estimated_total_text_tokens")
    context_total = context_case.get("payload", {}).get("estimated_total_text_tokens")
    boundary_files = boundary_case.get("payload", {}).get("stats", {}).get("relevant_file_count")
    passed = (
        baseline["passed"]
        and context_case["passed"]
        and boundary_case["passed"]
        and baseline_total == context_total
        and boundary_files == 2
    )
    return {
        "name": "private_report_ignore",
        "passed": passed,
        "baseline_total_tokens": baseline_total,
        "observed_total_tokens": context_total,
        "resource_relevant_file_count": boundary_files,
        "context_stdout": context_case["stdout"],
        "boundary_stdout": boundary_case["stdout"],
    }


def main() -> None:
    python = sys.executable
    cases = []

    root_governance = run(
            "root_governance",
            [python, "scripts/governance_check.py", str(ROOT), "--require-manifest"],
        )
    require_min_score(root_governance, 90)
    cases.append(root_governance)

    root_resource = run(
        "root_resource_boundaries",
        [python, "scripts/resource_boundary_check.py", str(ROOT)],
    )
    require_context_targets(root_resource, 1000, 100.0)
    root_payload = root_resource.get("payload", {})
    root_governance_status = root_resource.get("deferred_resource_governance_status")
    root_resource["passed"] = (
        root_resource["passed"]
        and root_governance_status == "governed"
        and not any("Deferred resource footprint is high" in item for item in root_payload.get("warnings", []))
    )
    cases.append(root_resource)

    complex_resource = run(
        "complex_example_resource_boundaries",
        [python, "scripts/resource_boundary_check.py", str(ROOT / "examples" / "complex-release-orchestrator" / "generated-skill")],
    )
    require_context_targets(complex_resource, 1000, 120.0)

    governed_resource = run(
        "governed_example_resource_boundaries",
        [python, "scripts/resource_boundary_check.py", str(ROOT / "examples" / "governed-incident-command" / "generated-skill")],
    )
    require_context_targets(governed_resource, 1000, 120.0)

    cases.extend([
        run(
            "complex_example_governance",
            [python, "scripts/governance_check.py", str(ROOT / "examples" / "complex-release-orchestrator" / "generated-skill"), "--require-manifest"],
        ),
        complex_resource,
        run(
            "invalid_governance_manifest",
            [python, "scripts/governance_check.py", str(ROOT / "tests" / "fixtures" / "governance_invalid_manifest"), "--require-manifest"],
            expect_ok=False,
            expected_substrings=[
                "Missing manifest fields",
                "Invalid status",
                "updated_at must use YYYY-MM-DD",
                "manifest name does not match",
            ],
        ),
    ])

    governed_example = run(
        "governed_example_governance",
        [python, "scripts/governance_check.py", str(ROOT / "examples" / "governed-incident-command" / "generated-skill"), "--require-manifest"],
    )
    require_min_score(governed_example, 90)
    cases.insert(4, governed_example)
    cases.insert(5, governed_resource)
    cases.append(verify_private_report_ignored())

    report = {"ok": all(case["passed"] for case in cases), "cases": cases}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
