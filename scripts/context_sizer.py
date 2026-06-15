#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


TEXT_EXTS = {".md", ".txt", ".yaml", ".yml", ".json", ".py", ".sh", ".js", ".ts"}
IGNORED_RELATIVE_DIRS = {
    Path("reports") / "release_snapshots",
    Path("tests") / "tmp",
    Path("tests") / "tmp_snapshot",
    Path("tests") / "tmp_cli",
}
PACKAGE_PATHS = (
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
IGNORED_FILE_PATTERNS = {
    "reports/benchmark_reproducibility*.json",
    "reports/benchmark_reproducibility*.md",
    "reports/context_budget*.json",
    "reports/context_budget*.md",
    "reports/evidence_consistency*.json",
    "reports/evidence_consistency*.md",
    "reports/review-studio*.html",
    "reports/review-studio*.json",
    "reports/review-viewer*.html",
    "reports/review-viewer*.json",
    "reports/skill-interpretation*.html",
    "reports/skill-interpretation*.json",
    "reports/skill-overview*.html",
    "reports/skill-overview*.json",
    "reports/world_class_evidence_preflight*.json",
    "reports/world_class_evidence_preflight*.md",
    "reports/world_class_evidence_preflight*.html",
    "reports/*pattern-analysis*.md",
    "reports/*research-plan*.md",
}


def estimate_tokens(text: str) -> int:
    # Fast heuristic suitable for local gating.
    return max(1, len(text) // 4)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def classify(path: Path) -> str:
    parts = set(path.parts)
    if path == Path("SKILL.md"):
        return "skill_body"
    if "agents" in parts:
        return "interface"
    if "references" in parts:
        return "reference"
    if "scripts" in parts:
        return "script"
    if "assets" in parts:
        return "asset"
    if path.suffix in TEXT_EXTS:
        return "other_text"
    return "binary_or_other"


def should_ignore(path: Path, skill_dir: Path) -> bool:
    rel = path.relative_to(skill_dir)
    if any(rel == ignored or ignored in rel.parents for ignored in IGNORED_RELATIVE_DIRS):
        return True
    if any(rel.match(pattern) for pattern in IGNORED_FILE_PATTERNS):
        return True
    return len(rel.parts) >= 2 and rel.parts[0] == "tests" and rel.parts[1].startswith("tmp_")


def summarize(skill_dir: Path) -> dict:
    files = []
    total_tokens = 0
    initial_tokens = 0
    candidate_files = []
    for entry in PACKAGE_PATHS:
        path = skill_dir / entry
        if path.is_file():
            candidate_files.append(path)
        elif path.is_dir():
            candidate_files.extend(sorted(file for file in path.rglob("*") if file.is_file()))

    for path in candidate_files:
        if should_ignore(path, skill_dir):
            continue
        rel = path.relative_to(skill_dir)
        if path.suffix not in TEXT_EXTS and path.name != "SKILL.md":
            size = path.stat().st_size
            files.append({"path": str(rel), "kind": "binary_or_other", "bytes": size})
            continue
        kind = classify(rel)
        if kind in {"binary_or_other", "asset"} and path.suffix not in TEXT_EXTS:
            size = path.stat().st_size
            files.append({"path": str(rel), "kind": kind, "bytes": size})
            continue
        text = read_text(path)
        tokens = estimate_tokens(text)
        record = {
            "path": str(rel),
            "kind": kind,
            "chars": len(text),
            "estimated_tokens": tokens,
        }
        files.append(record)
        total_tokens += tokens
        if rel == Path("SKILL.md") or (rel.parts and rel.parts[0] == "agents"):
            initial_tokens += tokens
    return {
        "skill_dir": str(skill_dir),
        "estimated_initial_load_tokens": initial_tokens,
        "estimated_total_text_tokens": total_tokens,
        "warning": initial_tokens > 2000,
        "files": files,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate context size for a skill package.")
    parser.add_argument("skill_dir", help="Path to the skill directory")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    report = summarize(Path(args.skill_dir).resolve())
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    print(f"Skill: {report['skill_dir']}")
    print(f"Estimated initial-load tokens: {report['estimated_initial_load_tokens']}")
    print(f"Estimated total text tokens: {report['estimated_total_text_tokens']}")
    print(f"Initial-load warning (>2000): {'YES' if report['warning'] else 'NO'}")
    print("")
    for file in report["files"]:
        if "estimated_tokens" in file:
            print(f"{file['kind']:12} {file['estimated_tokens']:6}t  {file['path']}")
        else:
            print(f"{file['kind']:12} {file['bytes']:6}b  {file['path']}")


if __name__ == "__main__":
    main()
