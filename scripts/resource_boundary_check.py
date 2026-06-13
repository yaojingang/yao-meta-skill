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
    for path in files:
        if path.suffix and path.suffix not in TEXT_EXTS and path.name != "SKILL.md":
            continue
        text = read_text(path)
        tokens = estimate_tokens(text)
        total_text_tokens += tokens
        rel = path.relative_to(root)
        if rel == Path("SKILL.md"):
            skill_body_tokens += tokens
            initial_load_tokens += tokens
        else:
            other_tokens += tokens
            if rel.parts[0] in {"agents"}:
                initial_load_tokens += tokens

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
