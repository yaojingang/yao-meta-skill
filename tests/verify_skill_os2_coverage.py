#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_skill_os2_coverage.py"
TMP = ROOT / "tests" / "tmp_skill_os2_coverage"


def main() -> None:
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True, exist_ok=True)
    output_json = TMP / "skill_os2_coverage.json"
    output_md = TMP / "skill_os2_coverage.md"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(ROOT),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
            "--generated-at",
            "2026-06-14",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["schema_version"] == "1.0", payload
    assert payload["ok"] is True, payload
    summary = payload["summary"]
    assert summary["decision"] == "local-blueprint-covered-evidence-pending", summary
    assert summary["module_count"] == 8, summary
    assert summary["recommended_pr_count"] == 12, summary
    assert summary["item_count"] == 20, summary
    assert summary["pass_count"] == 20, summary
    assert summary["warn_count"] == 0, summary
    assert summary["missing_count"] == 0, summary
    assert summary["extension_track_count"] == 2, summary
    assert summary["extension_partial_count"] == 1, summary
    assert summary["extension_planned_count"] == 0, summary
    assert summary["extension_covered_count"] == 1, summary
    assert summary["adaptive_extension_ready"] is False, summary
    assert summary["local_blueprint_ready"] is True, summary
    assert summary["public_world_class_ready"] is False, summary
    assert summary["world_class_evidence_pending_count"] == 4, summary
    modules = {item["key"]: item for item in payload["modules"]}
    assert set(modules) == {
        "skill-ir",
        "output-eval-lab",
        "runtime-conformance",
        "trust-security",
        "skill-atlas",
        "registry-distribution",
        "review-studio",
        "telemetry-drift",
    }, modules
    assert modules["skill-ir"]["status"] == "pass", modules["skill-ir"]
    assert modules["review-studio"]["status"] == "pass", modules["review-studio"]
    assert any(entry["path"] == "reports/review-studio.html" and entry["exists"] for entry in modules["review-studio"]["evidence"])
    prs = {item["key"]: item for item in payload["recommended_prs"]}
    assert set(prs) == {
        "benchmark-methodology",
        "output-eval-schema",
        "output-eval-runner",
        "output-quality-scorecard",
        "skill-ir-v0",
        "compiler-refactor",
        "agent-skills-conformance",
        "trust-check",
        "skill-atlas-generator",
        "registry-package-format",
        "review-studio-2",
        "migration-v2-docs",
    }, prs
    assert prs["agent-skills-conformance"]["status"] == "pass", prs["agent-skills-conformance"]
    assert prs["benchmark-methodology"]["status"] == "pass", prs["benchmark-methodology"]
    assert any(entry["path"] == "reports/benchmark_reproducibility.json" and entry["exists"] for entry in prs["benchmark-methodology"]["evidence"])
    assert payload["source_blueprint"]["core_module_count"] == 8, payload
    assert payload["source_blueprint"]["recommended_pr_count"] == 12, payload
    assert payload["source_blueprint"]["reference_extension_count"] == 2, payload
    extension_tracks = {item["key"]: item for item in payload["reference_extension_tracks"]}
    assert extension_tracks["skill-interpretation-report"]["status"] == "covered", extension_tracks
    assert extension_tracks["adaptive-self-iteration"]["status"] == "partial", extension_tracks
    assert any(
        entry["path"] == "reports/skill-overview.html" and entry["exists"]
        for entry in extension_tracks["skill-interpretation-report"]["evidence"]
    ), extension_tracks["skill-interpretation-report"]
    assert any(
        entry["path"] == "scripts/render_skill_interpretation.py" and entry["exists"]
        for entry in extension_tracks["skill-interpretation-report"]["evidence"]
    ), extension_tracks["skill-interpretation-report"]
    assert any(
        entry["path"] == "schemas/skill-interpretation.schema.json" and entry["exists"]
        for entry in extension_tracks["skill-interpretation-report"]["evidence"]
    ), extension_tracks["skill-interpretation-report"]
    assert any(
        entry["path"] == "scripts/summarize_user_signals.py" and entry["exists"]
        for entry in extension_tracks["adaptive-self-iteration"]["evidence"]
    ), extension_tracks["adaptive-self-iteration"]
    assert any(
        entry["path"] == "scripts/apply_adaptation.py" and not entry["exists"]
        for entry in extension_tracks["adaptive-self-iteration"]["evidence"]
    ), extension_tracks["adaptive-self-iteration"]
    assert "Close the four world-class evidence ledger entries" in payload["next_highest_leverage"][0], payload
    assert "skill interpretation report" in " ".join(payload["next_highest_leverage"]), payload
    assert "adaptive self-iteration" in " ".join(payload["next_highest_leverage"]), payload
    markdown = output_md.read_text(encoding="utf-8")
    assert "Skill OS 2.0 Blueprint Coverage" in markdown, markdown
    assert "local blueprint ready: `true`" in markdown, markdown
    assert "public world-class ready: `false`" in markdown, markdown
    assert "extension covered: `1`" in markdown, markdown
    assert "extension partial: `1`" in markdown, markdown
    assert "## Core Modules" in markdown, markdown
    assert "## Recommended PR Coverage" in markdown, markdown
    assert "## Reference Extension Tracks" in markdown, markdown
    assert "Skill Interpretation Report" in markdown, markdown
    assert "Adaptive Self-Iteration" in markdown, markdown
    assert "user-supplied 2.0 reference plan" in markdown, markdown
    assert "`agent-skills-conformance`" not in markdown, markdown
    assert "Agent Skills Conformance" in markdown, markdown
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
