#!/usr/bin/env python3
import argparse
import json
from datetime import date
from pathlib import Path

from render_reference_scan import render_reference_scan
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
2. Follow the workflow steps in `SKILL.md`.
3. Check `reports/skill-overview.html` if you want a fast visual explanation of the package.

## Package Map

- `SKILL.md`: trigger and workflow entrypoint
- `agents/interface.yaml`: portable interface metadata
- `manifest.json`: lifecycle and packaging metadata
- `reports/skill-overview.html`: visual overview report
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


def build_manifest(name: str) -> dict:
    return {
        "name": name,
        "version": "0.1.0",
        "owner": "Yao Team",
        "updated_at": str(date.today()),
        "status": "active",
        "maturity_tier": "scaffold",
        "lifecycle_stage": "scaffold",
        "context_budget_tier": "scaffold",
        "review_cadence": "per-release",
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize a minimal skill package.")
    parser.add_argument("name", help="skill folder and frontmatter name")
    parser.add_argument("--description", default="Describe what the skill does and when to use it.")
    parser.add_argument("--title", default=None)
    parser.add_argument("--output-dir", default=".")
    args = parser.parse_args()

    title = args.title or args.name.replace("-", " ").title()
    root = Path(args.output_dir).resolve() / args.name
    (root / "agents").mkdir(parents=True, exist_ok=True)
    (root / "references").mkdir(exist_ok=True)
    (root / "scripts").mkdir(exist_ok=True)
    (root / "reports").mkdir(exist_ok=True)
    (root / "SKILL.md").write_text(SKILL_TEMPLATE.format(name=args.name, description=args.description, title=title), encoding="utf-8")
    (root / "README.md").write_text(
        README_TEMPLATE.format(name=args.name, description=args.description, title=title),
        encoding="utf-8",
    )
    (root / "agents" / "interface.yaml").write_text(
        INTERFACE_TEMPLATE.format(
            name=args.name,
            title=title,
            short_description=args.description[:80],
            default_prompt=args.description.rstrip("."),
        ),
        encoding="utf-8",
    )
    (root / "manifest.json").write_text(
        json.dumps(build_manifest(args.name), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    overview = render_skill_overview(root)
    reference_scan = render_reference_scan(root, [])
    print(
        json.dumps(
            {
                "ok": True,
                "root": str(root),
                "artifacts": {
                    "readme": str(root / "README.md"),
                    "manifest": str(root / "manifest.json"),
                    **overview["artifacts"],
                    **reference_scan["artifacts"],
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
