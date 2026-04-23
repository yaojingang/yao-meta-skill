#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "scripts" / "yao.py"
BENCHMARK_FIXTURE_DIR = ROOT / "tests" / "fixtures" / "github_benchmark_scan"


def run(*args: str, input_text: str | None = None) -> dict:
    proc = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        input=input_text,
    )
    payload = json.loads(proc.stdout)
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "payload": payload,
        "stderr": proc.stderr,
    }


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_cli"
    if tmp_root.exists():
        subprocess.run(["rm", "-rf", str(tmp_root)], check=True)
    tmp_root.mkdir(parents=True, exist_ok=True)

    init_result = run("init", "cli-demo-skill", "--description", "CLI demo skill.", "--output-dir", str(tmp_root))
    assert init_result["ok"], init_result
    created = Path(init_result["payload"]["root"])
    assert (created / "SKILL.md").exists(), created
    assert (created / "README.md").exists(), created
    assert (created / "reports" / "intent-dialogue.md").exists(), created
    assert (created / "reports" / "intent-confidence.md").exists(), created
    assert (created / "reports" / "skill-overview.html").exists(), created
    assert (created / "reports" / "review-viewer.html").exists(), created
    assert (created / "reports" / "reference-scan.md").exists(), created
    assert (created / "reports" / "reference-synthesis.md").exists(), created
    assert (created / "reports" / "iteration-directions.md").exists(), created

    quickstart_result = run(
        "quickstart",
        "--output-dir",
        str(tmp_root),
        "--github-fixture-dir",
        str(BENCHMARK_FIXTURE_DIR),
        input_text=(
            "quickstart-skill\n"
            "Turn messy release notes into a reusable release brief skill.\n"
            "release notes, changelog snippets\n"
            "A reusable markdown release brief.\n"
            "looks right\n"
            "It should not publish blog posts or send email.\n"
            "consistency, portability\n"
            "production\n"
            "production\n"
            "\n"
            "privacy and naming\n"
        ),
    )
    assert quickstart_result["ok"], quickstart_result
    quickstart_root = Path(quickstart_result["payload"]["root"])
    assert (quickstart_root / "reports" / "review-viewer.html").exists(), quickstart_root
    assert (quickstart_root / "reports" / "github-benchmark-scan.md").exists(), quickstart_root
    assert (quickstart_root / "reports" / "intent-confidence.md").exists(), quickstart_root
    assert (quickstart_root / "reports" / "reference-synthesis.md").exists(), quickstart_root
    assert quickstart_result["payload"]["archetype"] == "production", quickstart_result
    assert quickstart_result["payload"]["guidance"]["experience_note"], quickstart_result
    assert quickstart_result["payload"]["intent_confidence"]["score"] >= 70, quickstart_result
    assert quickstart_result["payload"]["recommendation"]["summary"], quickstart_result
    assert quickstart_result["payload"]["reference_mode"]["mode"] == "silent", quickstart_result
    assert quickstart_result["payload"]["reviewer_evidence"]["artifacts"]["reference_synthesis"].endswith(
        "reports/reference-synthesis.md"
    ), quickstart_result
    assert "uncertainty_or_conflict" not in quickstart_result["payload"], quickstart_result

    quickstart_conflict_result = run(
        "quickstart",
        "--output-dir",
        str(tmp_root),
        "--github-fixture-dir",
        str(BENCHMARK_FIXTURE_DIR),
        input_text=(
            "quickstart-conflict-skill\n"
            "Turn repeated release notes into a governed release command skill.\n"
            "release notes, changelog snippets\n"
            "A governed release packet.\n"
            "looks right\n"
            "It should not publish blog posts or send email.\n"
            "auditability, portability\n"
            "governed\n"
            "governed\n"
            "Minimal vibe helper::taste::Keep the first pass fast, minimal, and lightweight.::Do not add review, governance, or approval steps.\n"
            "privacy and naming\n"
        ),
    )
    assert quickstart_conflict_result["ok"], quickstart_conflict_result
    assert quickstart_conflict_result["payload"]["reference_mode"]["mode"] == "explicit", quickstart_conflict_result
    assert quickstart_conflict_result["payload"]["uncertainty_or_conflict"]["conflicts"], quickstart_conflict_result

    validate_result = run("validate", str(created))
    assert validate_result["ok"], validate_result
    assert len(validate_result["payload"]["steps"]) == 4, validate_result

    skill_report_result = run("skill-report", str(created))
    assert skill_report_result["ok"], skill_report_result
    assert skill_report_result["payload"]["artifacts"]["html"].endswith("reports/skill-overview.html"), skill_report_result

    review_viewer_result = run("review-viewer", str(created))
    assert review_viewer_result["ok"], review_viewer_result
    assert review_viewer_result["payload"]["artifacts"]["html"].endswith("reports/review-viewer.html"), review_viewer_result

    reference_scan_result = run(
        "reference-scan",
        str(created),
        "--external-reference",
        "World Class Method::method::Borrow the smallest repeatable evaluation loop.::Do not copy heavy ceremony.",
        "--user-reference",
        "Product I Admire::taste::Learn the calm structure and clarity of output.::Do not copy wording.",
        "--local-constraint",
        "Local Naming::structure::Keep folder naming aligned with the local library.::Do not inherit private references.",
    )
    assert reference_scan_result["ok"], reference_scan_result
    assert reference_scan_result["payload"]["artifacts"]["markdown"].endswith("reports/reference-scan.md"), reference_scan_result
    assert len(reference_scan_result["payload"]["summary"]["user_references"]) == 1, reference_scan_result

    github_benchmark_result = run(
        "github-benchmark-scan",
        str(created),
        "--query",
        "workflow evaluation portability",
        "--fixture-dir",
        str(BENCHMARK_FIXTURE_DIR),
    )
    assert github_benchmark_result["ok"], github_benchmark_result
    assert len(github_benchmark_result["payload"]["repositories"]) == 3, github_benchmark_result

    intent_confidence_result = run("intent-confidence", str(created))
    assert intent_confidence_result["ok"], intent_confidence_result
    assert intent_confidence_result["payload"]["summary"]["score"] >= 0, intent_confidence_result

    intent_result = run("intent-dialogue", str(created))
    assert intent_result["ok"], intent_result
    assert intent_result["payload"]["artifacts"]["markdown"].endswith("reports/intent-dialogue.md"), intent_result

    reference_synthesis_result = run("reference-synthesis", str(created))
    assert reference_synthesis_result["ok"], reference_synthesis_result
    assert reference_synthesis_result["payload"]["artifacts"]["markdown"].endswith("reports/reference-synthesis.md"), reference_synthesis_result

    directions_result = run("iteration-directions", str(created))
    assert directions_result["ok"], directions_result
    assert directions_result["payload"]["artifacts"]["markdown"].endswith("reports/iteration-directions.md"), directions_result

    feedback_result = run(
        "feedback",
        str(created),
        "--note",
        "Keep the first version light and tighten exclusions before adding scripts.",
        "--rating",
        "4",
        "--category",
        "boundary",
        "--recommended-action",
        "tighten-trigger",
    )
    assert feedback_result["ok"], feedback_result
    assert feedback_result["payload"]["feedback"]["summary"]["count"] == 1, feedback_result

    optimize_result = run("optimize-description", "--target", "root")
    assert optimize_result["ok"], optimize_result
    assert optimize_result["payload"]["winner"]["label"] == "Current", optimize_result

    baseline_compare_result = run("baseline-compare")
    assert baseline_compare_result["ok"], baseline_compare_result
    assert baseline_compare_result["payload"]["summary"]["target_count"] == 3, baseline_compare_result

    promote_result = run("promote-check")
    assert promote_result["ok"], promote_result
    assert promote_result["payload"]["summary"]["blocked"] == 0, promote_result

    review_result = run("review", "--target", "root")
    assert review_result["ok"], review_result
    assert review_result["payload"]["artifacts"]["review_md"].endswith("reports/iteration_bundles/yao-meta-skill/review.md")

    snapshot_result = run("release-snapshot", "--target", "root", "--label", "cli-smoke")
    assert snapshot_result["ok"], snapshot_result
    assert snapshot_result["payload"]["artifacts"]["snapshot_json"].endswith("cli-smoke.json"), snapshot_result

    flow_result = run("workspace-flow", "--target", "root", "--label", "cli-flow")
    assert flow_result["ok"], flow_result
    assert flow_result["payload"]["artifacts"][0]["snapshot"]["artifacts"]["snapshot_md"].endswith("cli-flow.md"), flow_result

    report_result = run("report")
    assert report_result["ok"], report_result
    assert "iteration_ledger" in report_result["payload"]["artifacts"], report_result
    assert "portability_score" in report_result["payload"]["artifacts"], report_result

    package_dir = tmp_root / "dist"
    package_result = run("package", ".", "--platform", "generic", "--output-dir", str(package_dir))
    assert package_result["ok"], package_result
    assert (package_dir / "targets" / "generic" / "adapter.json").exists(), package_dir

    test_result = run("test", "--target", "promotion-check")
    assert test_result["ok"], test_result

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
