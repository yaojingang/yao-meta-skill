#!/usr/bin/env python3
import argparse
import json
from datetime import date
from pathlib import Path

from render_intent_dialogue import render_intent_dialogue
from render_iteration_directions import render_iteration_directions
from render_reference_scan import render_reference_scan
from render_review_viewer import render_review_viewer
from render_skill_overview import render_skill_overview


SKILL_TEMPLATE = """---
name: {name}
description: {description}
---

# {title}

## Workflow

1. Understand the request.
2. Execute the main task.
3. Validate the result.
"""


README_TEMPLATE = """# {title}

## What It Does

`{name}` is a reusable skill package for this job:

> {description}

## How To Use

1. Load the skill through `SKILL.md`.
2. Start with `reports/intent-dialogue.md` to tighten the real job, outputs, and exclusions.
3. Follow the workflow steps in `SKILL.md`.
4. Check `reports/skill-overview.html` if you want a fast visual explanation of the package.
5. Open `reports/review-viewer.html` for a compact visual review of the package.
6. Review `reports/iteration-directions.md` for the three most valuable next moves.

## Package Map

- `SKILL.md`: trigger and workflow entrypoint
- `agents/interface.yaml`: portable interface metadata
- `manifest.json`: lifecycle and packaging metadata
- `reports/intent-dialogue.md`: front-loaded discovery questions for better boundary design
- `reports/skill-overview.html`: visual overview report
- `reports/review-viewer.html`: compact review page for architecture, usage, feedback, and next steps
- `reports/iteration-directions.md`: the top three next iteration directions
"""


INTERFACE_TEMPLATE = """interface:
  display_name: "{title}"
  short_description: "{short_description}"
  default_prompt: "Use ${name} when you need to {default_prompt}."
compatibility:
  canonical_format: "agent-skills"
  adapter_targets:
    - "openai"
    - "claude"
    - "generic"
  activation:
    mode: "manual"
    paths: []
  execution:
    context: "inline"
    shell: "bash"
  trust:
    source_tier: "local"
    remote_inline_execution: "forbid"
    remote_metadata_policy: "allow-metadata-only"
  degradation:
    openai: "metadata-adapter"
    claude: "neutral-source-plus-adapter"
    generic: "neutral-source"
"""


MODE_CONFIG = {
    "scaffold": {
        "maturity_tier": "scaffold",
        "lifecycle_stage": "scaffold",
        "context_budget_tier": "scaffold",
        "review_cadence": "per-release",
    },
    "production": {
        "maturity_tier": "production",
        "lifecycle_stage": "active",
        "context_budget_tier": "production",
        "review_cadence": "monthly",
    },
    "library": {
        "maturity_tier": "library",
        "lifecycle_stage": "active",
        "context_budget_tier": "library",
        "review_cadence": "quarterly",
    },
    "governed": {
        "maturity_tier": "governed",
        "lifecycle_stage": "governed",
        "context_budget_tier": "governed",
        "review_cadence": "monthly",
    },
}


def build_manifest(name: str, mode: str, archetype: str) -> dict:
    mode_payload = MODE_CONFIG.get(mode, MODE_CONFIG["scaffold"])
    return {
        "name": name,
        "version": "0.1.0",
        "owner": "Yao Team",
        "updated_at": str(date.today()),
        "status": "active",
        "maturity_tier": mode_payload["maturity_tier"],
        "lifecycle_stage": mode_payload["lifecycle_stage"],
        "context_budget_tier": mode_payload["context_budget_tier"],
        "review_cadence": mode_payload["review_cadence"],
        "skill_archetype": archetype,
        "target_platforms": [
            "openai",
            "claude",
            "generic",
            "agent-skills-compatible",
        ],
        "factory_components": [
            "references",
            "scripts",
            "reports",
        ],
    }


def initialize_skill(
    name: str,
    description: str,
    title: str | None = None,
    output_dir: str = ".",
    mode: str = "scaffold",
    archetype: str = "scaffold",
) -> dict:
    title = title or name.replace("-", " ").title()
    root = Path(output_dir).resolve() / name
    (root / "agents").mkdir(parents=True, exist_ok=True)
    (root / "references").mkdir(exist_ok=True)
    (root / "scripts").mkdir(exist_ok=True)
    (root / "reports").mkdir(exist_ok=True)
    (root / "SKILL.md").write_text(
        SKILL_TEMPLATE.format(name=name, description=json.dumps(description, ensure_ascii=False), title=title),
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        README_TEMPLATE.format(name=name, description=description, title=title),
        encoding="utf-8",
    )
    (root / "agents" / "interface.yaml").write_text(
        INTERFACE_TEMPLATE.format(
            name=name,
            title=title,
            short_description=description[:80],
            default_prompt=description.rstrip("."),
        ),
        encoding="utf-8",
    )
    (root / "manifest.json").write_text(
        json.dumps(build_manifest(name, mode, archetype), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    overview = render_skill_overview(root)
    intent_dialogue = render_intent_dialogue(root)
    reference_scan = render_reference_scan(root, [])
    iteration_directions = render_iteration_directions(root)
    review_viewer = render_review_viewer(root)
    return {
        "ok": True,
        "root": str(root),
        "mode": mode,
        "archetype": archetype,
        "artifacts": {
            "readme": str(root / "README.md"),
            "manifest": str(root / "manifest.json"),
            "skill_overview_html": overview["artifacts"]["html"],
            "skill_overview_json": overview["artifacts"]["json"],
            "intent_dialogue_md": intent_dialogue["artifacts"]["markdown"],
            "intent_dialogue_json": intent_dialogue["artifacts"]["json"],
            "reference_scan_md": reference_scan["artifacts"]["markdown"],
            "reference_scan_json": reference_scan["artifacts"]["json"],
            "iteration_directions_md": iteration_directions["artifacts"]["markdown"],
            "iteration_directions_json": iteration_directions["artifacts"]["json"],
            "review_viewer_html": review_viewer["artifacts"]["html"],
            "review_viewer_json": review_viewer["artifacts"]["json"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize a minimal skill package.")
    parser.add_argument("name", help="skill folder and frontmatter name")
    parser.add_argument("--description", default="Describe what the skill does and when to use it.")
    parser.add_argument("--title", default=None)
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--mode", choices=sorted(MODE_CONFIG.keys()), default="scaffold")
    parser.add_argument("--archetype", choices=sorted(MODE_CONFIG.keys()), default="scaffold")
    args = parser.parse_args()
    result = initialize_skill(args.name, args.description, args.title, args.output_dir, args.mode, args.archetype)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
