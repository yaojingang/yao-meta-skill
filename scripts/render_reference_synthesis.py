#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


CURATED_TRACKS = [
    {
        "source_type": "official",
        "name": "Official skill anatomy and context discipline",
        "keywords": ["adapter", "portable", "metadata", "description", "references", "context", "entrypoint"],
        "borrow": "Borrow progressive disclosure: keep the entrypoint lean and move depth into references or scripts.",
        "avoid": "Do not let packaging or platform concerns swallow the core job boundary.",
    },
    {
        "source_type": "official",
        "name": "Official workflow product ergonomics",
        "keywords": ["quickstart", "review", "viewer", "feedback", "operator", "workflow", "guide"],
        "borrow": "Borrow a first-time operator flow that explains itself before it asks for more structure.",
        "avoid": "Do not mimic product polish that adds UI bulk without improving clarity.",
    },
    {
        "source_type": "research",
        "name": "Hypothesis-test-learn loop",
        "keywords": ["test", "benchmark", "baseline", "compare", "holdout", "optimize", "iteration"],
        "borrow": "Borrow a small hypothesis-test-learn loop so the first revision is evidence-backed.",
        "avoid": "Do not create experimental overhead that exceeds the skill's real risk tier.",
    },
    {
        "source_type": "research",
        "name": "Human-in-the-loop verification",
        "keywords": ["review", "audit", "govern", "incident", "compliance", "approval"],
        "borrow": "Borrow a review checkpoint wherever trust matters more than raw speed.",
        "avoid": "Do not force every skill through heavyweight review when the risk is low.",
    },
    {
        "source_type": "principles",
        "name": "Boundary-first design",
        "keywords": ["route", "trigger", "boundary", "exclude", "scope", "near-neighbor"],
        "borrow": "Borrow the discipline of defining what the skill should not own before growing the package.",
        "avoid": "Do not expand execution assets until route boundaries stay clean.",
    },
    {
        "source_type": "principles",
        "name": "Minimum sufficient structure",
        "keywords": ["lightweight", "lean", "minimal", "small", "context", "scaffold", "focus"],
        "borrow": "Borrow the smallest structure that makes the skill reliable and explainable.",
        "avoid": "Do not add files or gates that raise context cost faster than they raise trust.",
    },
    {
        "source_type": "principles",
        "name": "Outcome-backwards design",
        "keywords": ["output", "deliverable", "result", "handoff", "keep moving", "packet", "summary"],
        "borrow": "Borrow the habit of designing from the required hand-back output backwards.",
        "avoid": "Do not start with architecture terms before the deliverable is concrete.",
    },
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    try:
        end_index = lines[1:].index("---") + 1
    except ValueError:
        return {}, text
    frontmatter_text = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :]).lstrip()
    if yaml is not None:
        payload = yaml.safe_load(frontmatter_text) or {}
        return payload if isinstance(payload, dict) else {}, body
    data = {}
    for line in frontmatter_text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data, body


def anchor_text(skill_dir: Path, benchmark: dict[str, Any], intent: dict[str, Any]) -> str:
    skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    frontmatter, _ = parse_frontmatter(skill_text)
    pieces = [
        frontmatter.get("name", skill_dir.name),
        frontmatter.get("description", ""),
        benchmark.get("query", ""),
        intent.get("anchor_sentence", ""),
    ]
    return " ".join(piece for piece in pieces if piece).lower()


def match_keywords(text: str, keywords: list[str]) -> list[str]:
    hits = []
    for keyword in keywords:
        if keyword in text:
            hits.append(keyword)
    return hits


def select_source_tracks(text: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for track in CURATED_TRACKS:
        matched = match_keywords(text, track["keywords"])
        score = len(matched)
        payload = {**track, "matched_keywords": matched, "score": score}
        grouped.setdefault(track["source_type"], []).append(payload)

    selected = []
    for source_type in ("official", "research", "principles"):
        candidates = sorted(grouped.get(source_type, []), key=lambda item: item["score"], reverse=True)
        chosen = candidates[0] if candidates else None
        if chosen is None:
            continue
        if chosen["score"] == 0:
            chosen = {**chosen, "matched_keywords": ["general fit"]}
        selected.append(
            {
                "source_type": source_type,
                "name": chosen["name"],
                "evidence_mode": "curated-pattern-track",
                "matched_keywords": chosen["matched_keywords"],
                "borrow": chosen["borrow"],
                "avoid": chosen["avoid"],
                "why_relevant": (
                    f"This track matches: {', '.join(chosen['matched_keywords'])}."
                    if chosen["matched_keywords"]
                    else "This track is the best general fit for the current skill shape."
                ),
            }
        )
    return selected


def unique_items(items: list[str], limit: int) -> list[str]:
    seen = set()
    output = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
        if len(output) == limit:
            break
    return output


def build_visibility(intent_payload: dict[str, Any], user_refs: list[dict[str, Any]]) -> dict[str, Any]:
    reasons = []
    if not intent_payload.get("gate_passed", False):
        reasons.append("intent_uncertain")
    if user_refs:
        reasons.append("user_reference_alignment")
    mode = "explicit" if reasons else "silent"
    return {
        "mode": mode,
        "user_decision_required": mode == "explicit",
        "reasons": reasons,
        "user_note": (
            "Surface the recommendation because intent is still settling or a user reference needs to be reconciled."
            if mode == "explicit"
            else "Apply the synthesis quietly unless uncertainty or a real design conflict appears."
        ),
        "reviewer_note": "Keep the full benchmark and synthesis evidence visible for authors and reviewers.",
    }


def build_recommendation(
    borrow_now: list[str],
    avoid_now: list[str],
    intent_payload: dict[str, Any],
    visibility: dict[str, Any],
) -> dict[str, Any]:
    primary_borrow = borrow_now[0] if borrow_now else "Keep the entrypoint lean and boundary-first."
    primary_avoid = avoid_now[0] if avoid_now else "Do not add weight that the first pass does not yet need."
    why = (
        "Intent is clear enough, so the system should make the first pattern call quietly."
        if intent_payload.get("gate_passed", False)
        else "Intent still has gaps, so the system should surface the recommendation and ask for correction before deepening the package."
    )
    return {
        "summary": f"Start by borrowing this pattern: {primary_borrow} Avoid this for the first pass: {primary_avoid}",
        "borrow_now": borrow_now[:2],
        "avoid_for_now": avoid_now[:2],
        "why": why,
        "user_decision_required": visibility["user_decision_required"],
    }


def build_summary(skill_dir: Path) -> dict[str, Any]:
    skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    frontmatter, _ = parse_frontmatter(skill_text)
    benchmark = load_json(skill_dir / "reports" / "github-benchmark-scan.json")
    intent_payload = load_json(skill_dir / "reports" / "intent-confidence.json")
    reference_scan = load_json(skill_dir / "reports" / "reference-scan.json")

    source_tracks = select_source_tracks(anchor_text(skill_dir, benchmark, intent_payload))
    github_repos = benchmark.get("repositories", [])[:3]
    github_borrow = benchmark.get("cross_repo", {}).get("borrow", [])
    github_avoid = benchmark.get("cross_repo", {}).get("avoid", [])
    track_borrow = [track["borrow"] for track in source_tracks]
    track_avoid = [track["avoid"] for track in source_tracks]
    user_refs = reference_scan.get("user_references", [])

    borrow_now = unique_items(
        [
            *track_borrow,
            *github_borrow,
            *[ref.get("borrow", "") for ref in user_refs],
        ],
        5,
    )
    avoid_now = unique_items(
        [
            *track_avoid,
            *github_avoid,
            *[ref.get("avoid", "") for ref in user_refs],
        ],
        5,
    )
    quality_risers = unique_items(
        [
            "Use GitHub repositories for concrete package and workflow patterns.",
            "Use curated official or commercial tracks for entrypoint and operator ergonomics.",
            "Use research tracks to justify the smallest evaluation loop that still catches regressions.",
            "Use principle tracks to keep the package small, boundary-aware, and outcome-driven.",
        ],
        4,
    )
    visibility = build_visibility(intent_payload, user_refs)
    recommendation = build_recommendation(borrow_now, avoid_now, intent_payload, visibility)

    return {
        "skill_name": frontmatter.get("name", skill_dir.name),
        "description": frontmatter.get("description", "No description found."),
        "intent_confidence": {
            "score": intent_payload.get("score", 0),
            "band": intent_payload.get("band", "low"),
            "gate_passed": intent_payload.get("gate_passed", False),
        },
        "github_benchmarks": [
            {
                "name": repo.get("full_name"),
                "url": repo.get("html_url"),
                "stars": repo.get("stars"),
                "borrow": repo.get("borrow", [])[:2],
            }
            for repo in github_repos
        ],
        "source_tracks": source_tracks,
        "synthesis": {
            "borrow_now": borrow_now,
            "avoid_now": avoid_now,
            "quality_risers": quality_risers,
            "recommendation": recommendation,
            "visibility": visibility,
            "decision_prompt": (
                "Use the recommendation by default. Only surface the underlying benchmark tradeoffs when intent is uncertain or a user reference needs a deliberate call."
            ),
            "source_mix": {
                "github_benchmarks": len(github_repos),
                "curated_tracks": len(source_tracks),
                "user_references": len(user_refs),
            },
        },
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Reference Synthesis",
        "",
        f"Skill: `{summary['skill_name']}`",
        f"- Description: {summary['description']}",
        f"- Intent confidence: `{summary['intent_confidence']['score']}/100` (`{summary['intent_confidence']['band']}`)",
        "",
        "## Live GitHub Benchmarks",
        "",
    ]
    if summary["github_benchmarks"]:
        for repo in summary["github_benchmarks"]:
            lines.extend(
                [
                    f"### {repo['name']}",
                    f"- URL: {repo['url']}",
                    f"- Stars: `{repo['stars']}`",
                ]
            )
            for item in repo.get("borrow", []):
                lines.append(f"- Borrow: {item}")
            lines.append("")
    else:
        lines.append("- No live GitHub benchmarks are attached yet.")
        lines.append("")

    lines.extend(["## Curated World-Class Pattern Tracks", ""])
    for track in summary["source_tracks"]:
        lines.extend(
            [
                f"### {track['name']}",
                f"- Type: `{track['source_type']}`",
                f"- Evidence mode: `{track['evidence_mode']}`",
                f"- Why relevant: {track['why_relevant']}",
                f"- Borrow: {track['borrow']}",
                f"- Avoid: {track['avoid']}",
                "",
            ]
        )

    lines.extend(["## Borrow Now", ""])
    for item in summary["synthesis"]["borrow_now"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Avoid Now", ""])
    for item in summary["synthesis"]["avoid_now"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Default Recommendation", ""])
    lines.append(f"- Summary: {summary['synthesis']['recommendation']['summary']}")
    lines.append(f"- Why: {summary['synthesis']['recommendation']['why']}")
    lines.append(f"- User decision required: `{summary['synthesis']['recommendation']['user_decision_required']}`")

    lines.extend(["", "## Visibility Mode", ""])
    lines.append(f"- Mode: `{summary['synthesis']['visibility']['mode']}`")
    if summary["synthesis"]["visibility"]["reasons"]:
        lines.append(f"- Reasons: {', '.join(summary['synthesis']['visibility']['reasons'])}")
    lines.append(f"- User note: {summary['synthesis']['visibility']['user_note']}")
    lines.append(f"- Reviewer note: {summary['synthesis']['visibility']['reviewer_note']}")

    lines.extend(["", "## Quality Lift Thesis", ""])
    for item in summary["synthesis"]["quality_risers"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Decision Prompt", "", summary["synthesis"]["decision_prompt"], ""])
    return "\n".join(lines).strip() + "\n"


def render_reference_synthesis(
    skill_dir: Path,
    output_md: Path | None = None,
    output_json: Path | None = None,
) -> dict[str, Any]:
    skill_dir = skill_dir.resolve()
    reports_dir = skill_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    output_md = output_md or reports_dir / "reference-synthesis.md"
    output_json = output_json or reports_dir / "reference-synthesis.json"
    summary = build_summary(skill_dir)
    output_md.write_text(render_markdown(summary), encoding="utf-8")
    output_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "skill_dir": str(skill_dir),
        "artifacts": {
            "markdown": str(output_md),
            "json": str(output_json),
        },
        "summary": summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a multi-source reference synthesis report for a skill package.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--output-md")
    parser.add_argument("--output-json")
    args = parser.parse_args()

    result = render_reference_synthesis(
        Path(args.skill_dir),
        output_md=Path(args.output_md).resolve() if args.output_md else None,
        output_json=Path(args.output_json).resolve() if args.output_json else None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
