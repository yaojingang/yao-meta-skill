from pathlib import Path
from typing import Any, Callable


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by build_skill_atlas.py to keep no-route opportunity detection out of the atlas CLI."


SkipPredicate = Callable[[Path, Path], bool]
RelFormatter = Callable[[Path, Path], str]


def failure_case_no_route_opportunities(
    workspace_root: Path,
    *,
    should_skip: SkipPredicate,
    safe_rel: RelFormatter,
) -> list[dict[str, Any]]:
    opportunities = []
    for path in sorted(workspace_root.rglob("failure-cases.md")):
        if should_skip(path, workspace_root):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.startswith("-"):
                continue
            lowered = stripped.casefold()
            if "no_route" in lowered or "no route" in lowered or "missed" in lowered or "under-trigger" in lowered:
                opportunities.append(
                    {
                        "source_type": "failure-case",
                        "source": safe_rel(workspace_root, path),
                        "note": stripped.lstrip("- ").strip(),
                        "actionable": True,
                        "privacy_contract": "source note only; raw prompts are not required",
                    }
                )
    return opportunities[:50]


def telemetry_no_route_opportunities(drift_signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    opportunities = []
    for signal in drift_signals:
        signal_types = {str(item) for item in signal.get("signal_types", [])}
        if not {"missed trigger", "under trigger"} & signal_types:
            continue
        summary = signal.get("summary", {}) if isinstance(signal.get("summary"), dict) else {}
        opportunities.append(
            {
                "source_type": "telemetry",
                "source": str(signal.get("source", "")),
                "skill": str(signal.get("name", "")),
                "path": str(signal.get("path", "")),
                "signal": "missed trigger",
                "missed_trigger_count": int(summary.get("missed_trigger_count") or 0),
                "recommendation": str(
                    signal.get("recommendation")
                    or "Add missed prompts to trigger eval and evaluate whether a new skill route is needed."
                ),
                "actionable": bool(signal.get("actionable")),
                "scope": str(signal.get("scope", "")),
                "privacy_contract": "metadata-only telemetry; no raw prompt, output, transcript, or note is stored",
            }
        )
    return opportunities


def no_route_opportunities(
    workspace_root: Path,
    drift_signals: list[dict[str, Any]],
    *,
    should_skip: SkipPredicate,
    safe_rel: RelFormatter,
) -> list[dict[str, Any]]:
    opportunities = failure_case_no_route_opportunities(
        workspace_root,
        should_skip=should_skip,
        safe_rel=safe_rel,
    )
    opportunities.extend(telemetry_no_route_opportunities(drift_signals))
    return opportunities[:80]
