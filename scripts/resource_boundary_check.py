#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from context_sizer import estimate_tokens, read_text, TEXT_EXTS
from governance_check import compute_score, read_frontmatter


OPTIONAL_DIRS = ("references", "scripts", "assets", "evals", "templates", "reports", "input", "outputs")
IGNORED_RELATIVE_DIRS = {
    Path("reports") / "release_snapshots",
    Path("tests") / "tmp",
    Path("tests") / "tmp_snapshot",
    Path("tests") / "tmp_cli",
}
IGNORED_FILE_PATTERNS = {
    "reports/context_budget*.json",
    "reports/context_budget*.md",
    "reports/*pattern-analysis*.md",
    "reports/*research-plan*.md",
}
CANONICAL_PATHS = (
    "SKILL.md",
    "manifest.json",
    "agents",
    "references",
    "scripts",
    "assets",
    "evals",
    "templates",
    "reports",
    "failures",
    "tests",
    "input",
    "outputs",
)
CONTEXT_BUDGETS = {
    "scaffold": 700,
    "production": 1000,
    "library": 1300,
    "governed": 1300,
}
SKILL_BODY_BUFFER = 100
SKILL_BODY_WARN_RATIO = 0.85
DEFERRED_RESOURCE_DIRS = {"references", "scripts", "evals", "templates", "assets", "input", "outputs"}
DEFERRED_RESOURCE_WARN_TOKENS = 120_000
DEFERRED_RESOURCE_WARN_DIR_TOKENS = 80_000
SCRIPT_GOVERNANCE_REPORTS = (
    "reports/security_trust_report.json",
    "reports/architecture_maintainability.json",
    "reports/python_compatibility.json",
)


def has_files(path: Path) -> bool:
    return path.exists() and any(child.is_file() for child in path.rglob("*"))


def should_ignore(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    if any(rel == ignored or ignored in rel.parents for ignored in IGNORED_RELATIVE_DIRS):
        return True
    if any(rel.match(pattern) for pattern in IGNORED_FILE_PATTERNS):
        return True
    return len(rel.parts) >= 2 and rel.parts[0] == "tests" and rel.parts[1].startswith("tmp_")


def load_manifest(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def iter_relevant_files(root: Path) -> list[Path]:
    files = []
    for entry in CANONICAL_PATHS:
        path = root / entry
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(file for file in path.rglob("*") if file.is_file() and not should_ignore(file, root)))
    return files


def budget_tier_for(manifest: dict) -> str:
    for field in ("context_budget_tier", "lifecycle_stage", "maturity_tier"):
        value = manifest.get(field)
        if value in CONTEXT_BUDGETS:
            return value
    return "production"


def explicit_dir_reference(dirname: str, path: Path, skill_text: str, manifest: dict) -> bool:
    lowered = skill_text.lower()
    if dirname.lower() in lowered or f"{dirname}/" in lowered:
        return True
    for file in path.rglob("*"):
        if file.is_file() and file.name.lower() in lowered:
            return True
    declared = manifest.get("factory_components") or []
    return dirname in declared


def quality_signal_points(root: Path, manifest: dict, governance_score: int) -> int:
    points = governance_score
    if has_files(root / "evals"):
        points += 10
    if has_files(root / "reports"):
        points += 10
    if has_files(root / "scripts"):
        points += 5
    if has_files(root / "references"):
        points += 5
    if (root / "agents" / "interface.yaml").exists() and manifest:
        points += 5
    if has_files(root / "failures") or has_files(root / "tests"):
        points += 5
    return points


def script_resource_governance(root: Path, expected_file_count: int) -> dict:
    trust = load_json(root / "reports" / "security_trust_report.json")
    architecture = load_json(root / "reports" / "architecture_maintainability.json")
    python_compat = load_json(root / "reports" / "python_compatibility.json")
    trust_summary = trust.get("summary", {}) if isinstance(trust.get("summary", {}), dict) else {}
    architecture_summary = architecture.get("summary", {}) if isinstance(architecture.get("summary", {}), dict) else {}
    python_summary = python_compat.get("summary", {}) if isinstance(python_compat.get("summary", {}), dict) else {}

    reasons = []
    missing = []
    checks = [
        (
            "trust report covers scripts",
            trust.get("ok") is True
            and int(trust_summary.get("script_count", 0) or 0) >= expected_file_count
            and int(trust_summary.get("secret_findings", 0) or 0) == 0
            and int(trust_summary.get("help_smoke_failed_count", 0) or 0) == 0,
        ),
        (
            "architecture report has no script hotspots or blockers",
            architecture.get("ok") is True
            and int(architecture_summary.get("hotspot_count", 0) or 0) == 0
            and int(architecture_summary.get("blocker_count", 0) or 0) == 0,
        ),
        (
            "Python compatibility report has no issues",
            python_compat.get("ok") is True
            and int(python_summary.get("issue_count", 0) or 0) == 0,
        ),
    ]
    for label, ok in checks:
        if ok:
            reasons.append(label)
        else:
            missing.append(label)
    return {
        "status": "governed" if not missing else "needs-review",
        "evidence": list(SCRIPT_GOVERNANCE_REPORTS),
        "reasons": reasons,
        "missing": missing,
    }


def deferred_dir_governance(
    root: Path,
    dirname: str,
    payload: dict,
    manifest: dict,
    skill_text: str,
) -> dict:
    file_count = int(payload.get("file_count", 0) or 0)
    if dirname == "scripts":
        governance = script_resource_governance(root, file_count)
        governance.update(
            {
                "path": dirname,
                "estimated_tokens": int(payload.get("estimated_tokens", 0) or 0),
                "file_count": file_count,
                "rationale": "Script resources are deterministic deferred tools, not initial-load prompt context.",
            }
        )
        return governance

    referenced = explicit_dir_reference(dirname, root / dirname, skill_text, manifest)
    declared = dirname in (manifest.get("factory_components") or [])
    governed = referenced or declared
    return {
        "path": dirname,
        "status": "governed" if governed else "needs-review",
        "estimated_tokens": int(payload.get("estimated_tokens", 0) or 0),
        "file_count": file_count,
        "evidence": ["SKILL.md", "manifest.json"],
        "reasons": ["directory is explicitly referenced or declared as a factory component"] if governed else [],
        "missing": [] if governed else ["directory is not referenced in SKILL.md or manifest factory_components"],
        "rationale": "Deferred resources are acceptable when they are discoverable and intentionally part of the package contract.",
    }


def deferred_resource_governance(
    root: Path,
    manifest: dict,
    skill_text: str,
    deferred_resource_dirs: dict[str, dict[str, int | str]],
    large_deferred_resource_dirs: list[dict],
) -> dict:
    governed_dirs = [
        deferred_dir_governance(root, str(item["path"]), item, manifest, skill_text)
        for item in large_deferred_resource_dirs
    ]
    missing = [item for item in governed_dirs if item["status"] != "governed"]
    return {
        "status": "governed" if governed_dirs and not missing else ("not-required" if not governed_dirs else "needs-review"),
        "large_dir_count": len(governed_dirs),
        "governed_large_dir_count": len(governed_dirs) - len(missing),
        "directories": governed_dirs,
        "summary": (
            "Large deferred resources are indexed and backed by evidence."
            if governed_dirs and not missing
            else "No large deferred resource directory exceeds the per-dir threshold."
            if not governed_dirs
            else "One or more large deferred resource directories still need explicit governance evidence."
        ),
    }


def analyze_skill(
    root: Path,
    max_initial_tokens: int | None = None,
    warn_skill_body_tokens: int | None = None,
) -> dict:
    skill_md = root / "SKILL.md"
    failures = []
    warnings = []
    manifest = load_manifest(root / "manifest.json")

    if not skill_md.exists():
        failures.append("Missing SKILL.md")
        return {"ok": False, "failures": failures, "warnings": warnings}

    files = iter_relevant_files(root)
    skill_body_tokens = 0
    other_tokens = 0
    initial_load_tokens = 0
    total_text_tokens = 0
    deferred_resource_tokens = 0
    deferred_resource_dirs: dict[str, dict[str, int | str]] = {}
    for path in files:
        if path.suffix and path.suffix not in TEXT_EXTS and path.name != "SKILL.md":
            continue
        text = read_text(path)
        tokens = estimate_tokens(text)
        total_text_tokens += tokens
        rel = path.relative_to(root)
        top_dir = rel.parts[0] if rel.parts else str(rel)
        if rel == Path("SKILL.md"):
            skill_body_tokens += tokens
            initial_load_tokens += tokens
        else:
            other_tokens += tokens
            if rel.parts[0] in {"agents"}:
                initial_load_tokens += tokens
            if top_dir in DEFERRED_RESOURCE_DIRS:
                deferred_resource_tokens += tokens
                current = deferred_resource_dirs.setdefault(
                    top_dir,
                    {"path": top_dir, "estimated_tokens": 0, "file_count": 0},
                )
                current["estimated_tokens"] = int(current["estimated_tokens"]) + tokens
                current["file_count"] = int(current["file_count"]) + 1

    budget_tier = budget_tier_for(manifest)
    budget_limit = max_initial_tokens if max_initial_tokens is not None else CONTEXT_BUDGETS[budget_tier]
    skill_body_limit = (
        warn_skill_body_tokens
        if warn_skill_body_tokens is not None
        else max(int(budget_limit * SKILL_BODY_WARN_RATIO), budget_limit - SKILL_BODY_BUFFER)
    )

    if initial_load_tokens > budget_limit:
        failures.append(
            f"Estimated initial-load tokens exceed budget: {initial_load_tokens} > {budget_limit}"
        )
    if skill_body_tokens > skill_body_limit:
        warnings.append(f"SKILL.md is getting heavy: {skill_body_tokens} estimated tokens.")

    skill_text = skill_md.read_text(encoding="utf-8")
    unused_resource_dirs = []
    for dirname in OPTIONAL_DIRS:
        path = root / dirname
        if path.exists() and not has_files(path):
            warnings.append(f"{dirname}/ exists but is empty.")
            continue
        if has_files(path) and not explicit_dir_reference(dirname, path, skill_text, manifest):
            warnings.append(
                f"{dirname}/ contains files but is not referenced in SKILL.md or declared in manifest factory_components."
            )
            unused_resource_dirs.append(dirname)

    if other_tokens and skill_body_tokens / (skill_body_tokens + other_tokens) > 0.75:
        warnings.append("Most text still lives in SKILL.md; consider moving detail into references/ or scripts/.")

    large_deferred_resource_dirs = [
        item
        for item in sorted(
            deferred_resource_dirs.values(),
            key=lambda payload: int(payload["estimated_tokens"]),
            reverse=True,
        )
        if int(item["estimated_tokens"]) > DEFERRED_RESOURCE_WARN_DIR_TOKENS
    ]
    deferred_governance = deferred_resource_governance(
        root,
        manifest,
        skill_text,
        deferred_resource_dirs,
        large_deferred_resource_dirs,
    )

    if deferred_resource_tokens > DEFERRED_RESOURCE_WARN_TOKENS and deferred_governance["status"] != "governed":
        warnings.append(
            "Deferred resource footprint is high: "
            f"{deferred_resource_tokens} estimated tokens across references/scripts/evals. "
            "Keep Review Studio warnings visible until the largest resource dirs are split, archived, or justified."
        )

    frontmatter = read_frontmatter(skill_md)
    governance_score, _ = compute_score(root, manifest, frontmatter, skill_text, bool(manifest))
    signal_points = quality_signal_points(root, manifest, governance_score)
    quality_density = round(signal_points / max(initial_load_tokens, 1) * 1000, 1)

    report = {
        "ok": not failures,
        "failures": failures,
        "warnings": warnings,
        "stats": {
            "context_budget_tier": budget_tier,
            "context_budget_limit": budget_limit,
            "skill_body_tokens": skill_body_tokens,
            "other_text_tokens": other_tokens,
            "estimated_initial_load_tokens": initial_load_tokens,
            "estimated_total_text_tokens": total_text_tokens,
            "deferred_resource_tokens": deferred_resource_tokens,
            "deferred_resource_warn_threshold": DEFERRED_RESOURCE_WARN_TOKENS,
            "deferred_resource_dirs": sorted(
                deferred_resource_dirs.values(),
                key=lambda payload: int(payload["estimated_tokens"]),
                reverse=True,
            ),
            "large_deferred_resource_dirs": large_deferred_resource_dirs,
            "deferred_resource_governance": deferred_governance,
            "relevant_file_count": len(files),
            "unused_resource_dirs": unused_resource_dirs,
            "quality_signal_points": signal_points,
            "quality_density": quality_density,
        },
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Check whether a skill package keeps resource boundaries under control.")
    parser.add_argument("skill_dir")
    parser.add_argument("--max-initial-tokens", type=int, default=None)
    parser.add_argument("--warn-skill-body-tokens", type=int, default=None)
    args = parser.parse_args()

    root = Path(args.skill_dir).resolve()
    report = analyze_skill(
        root,
        max_initial_tokens=args.max_initial_tokens,
        warn_skill_body_tokens=args.warn_skill_body_tokens,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["failures"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
