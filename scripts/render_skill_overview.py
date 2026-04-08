#!/usr/bin/env python3
import argparse
import html
import json
import re
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


KNOWN_ENTRIES = [
    ("SKILL.md", "Skill entrypoint"),
    ("README.md", "Human-readable usage guide"),
    ("agents/interface.yaml", "Neutral interface metadata"),
    ("manifest.json", "Lifecycle and portability metadata"),
    ("references", "Extended guidance and reusable notes"),
    ("scripts", "Deterministic helpers or local tooling"),
    ("evals", "Trigger and quality checks"),
    ("reports", "Generated evidence and overview artifacts"),
]


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
        data = yaml.safe_load(frontmatter_text) or {}
        return data if isinstance(data, dict) else {}, body

    data = {}
    for line in frontmatter_text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data, body


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        payload = yaml.safe_load(text) or {}
        return payload if isinstance(payload, dict) else {}
    return {}


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def extract_title(body: str, fallback: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def parse_sections(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = "_preamble"
    sections[current] = []
    for line in body.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
            continue
        sections[current].append(line)
    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def extract_list_items(text: str) -> list[str]:
    items = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        ordered = re.match(r"^\d+\.\s+(.*)$", stripped)
        bullet = re.match(r"^[-*]\s+(.*)$", stripped)
        match = ordered or bullet
        if match:
            items.append(match.group(1).strip())
    return items


def summarize_logic(sections: dict[str, str]) -> list[str]:
    for key in ("Compact Workflow", "Workflow", "How It Works", "Logic", "Quick Start"):
        if key in sections:
            items = extract_list_items(sections[key])
            if items:
                return items[:5]
    preamble_items = extract_list_items(sections.get("_preamble", ""))
    return preamble_items[:5]


def summarize_usage(sections: dict[str, str], default_prompt: str, description: str) -> list[str]:
    usage = []
    for key in ("How To Use", "Quick Start", "Usage", "Runbook"):
        if key in sections:
            usage = extract_list_items(sections[key])
            if usage:
                return usage[:5]
    if default_prompt:
        usage.append(default_prompt)
    usage.append(f"Use this skill when the request matches: {description}")
    return usage[:4]


def package_entries(skill_dir: Path) -> list[dict]:
    items = []
    for rel_path, label in KNOWN_ENTRIES:
        target = skill_dir / rel_path
        if target.exists():
            kind = "folder" if target.is_dir() else "file"
            items.append({"path": rel_path, "label": label, "kind": kind})
    return items


def derive_strengths(skill_dir: Path, metadata: dict) -> list[str]:
    strengths = ["Lean trigger surface anchored in frontmatter description."]
    if (skill_dir / "agents" / "interface.yaml").exists():
        strengths.append("Portable interface metadata is already packaged for adapter-based export.")
    if (skill_dir / "references").exists() and any((skill_dir / "references").iterdir()):
        strengths.append("Long guidance is separated into references so the entrypoint can stay compact.")
    if (skill_dir / "scripts").exists() and any((skill_dir / "scripts").iterdir()):
        strengths.append("Deterministic helpers are packaged with the skill instead of hidden in prompt text.")
    if (skill_dir / "evals").exists() and any((skill_dir / "evals").iterdir()):
        strengths.append("The package includes quality gates or trigger checks that can travel with the skill.")
    if metadata.get("maturity_tier"):
        strengths.append(f"Lifecycle metadata is explicit, with maturity tier set to `{metadata['maturity_tier']}`.")
    return strengths[:5]


def card_items(interface_data: dict, logic_steps: list[str], package_map: list[dict], usage_steps: list[str], description: str) -> list[dict]:
    compatibility = interface_data.get("compatibility", {})
    execution = compatibility.get("execution", {})
    activation = compatibility.get("activation", {})
    return [
        {
            "title": "Trigger",
            "body": description,
            "meta": [
                f"Activation: {activation.get('mode', 'manual')}",
                f"Context: {execution.get('context', 'inline')}",
            ],
        },
        {
            "title": "Logic",
            "body": logic_steps or ["Understand the request", "Execute the task", "Validate the result"],
            "meta": [],
        },
        {
            "title": "Usage",
            "body": usage_steps,
            "meta": [],
        },
        {
            "title": "Package",
            "body": [entry["path"] for entry in package_map[:6]],
            "meta": [f"{len(package_map)} structured entries detected"],
        },
    ]


def build_summary(skill_dir: Path) -> dict:
    skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(skill_text)
    interface_data = load_yaml(skill_dir / "agents" / "interface.yaml")
    manifest = load_json(skill_dir / "manifest.json")
    sections = parse_sections(body)

    name = frontmatter.get("name", skill_dir.name)
    description = frontmatter.get("description", "No description found.")
    title = extract_title(body, name.replace("-", " ").title())
    display_name = interface_data.get("interface", {}).get("display_name", title)
    default_prompt = interface_data.get("interface", {}).get("default_prompt", "")
    logic_steps = summarize_logic(sections)
    usage_steps = summarize_usage(sections, default_prompt, description)
    package_map = package_entries(skill_dir)
    strengths = derive_strengths(skill_dir, manifest)

    return {
        "name": name,
        "title": title,
        "display_name": display_name,
        "description": description,
        "logic_steps": logic_steps,
        "usage_steps": usage_steps,
        "package_map": package_map,
        "strengths": strengths,
        "cards": card_items(interface_data, logic_steps, package_map, usage_steps, description),
        "metadata": {
            "canonical_format": interface_data.get("compatibility", {}).get("canonical_format", "agent-skills"),
            "targets": interface_data.get("compatibility", {}).get("adapter_targets", []),
            "maturity_tier": manifest.get("maturity_tier", "scaffold"),
            "skill_archetype": manifest.get("skill_archetype", manifest.get("maturity_tier", "scaffold")),
            "updated_at": manifest.get("updated_at", str(date.today())),
        },
    }


def render_card_body(card: dict) -> str:
    body = card["body"]
    if isinstance(body, list):
        items = "".join(f"<li>{html.escape(str(item))}</li>" for item in body)
        body_html = f"<ol>{items}</ol>"
    else:
        body_html = f"<p>{html.escape(str(body))}</p>"
    meta = "".join(f"<span>{html.escape(str(item))}</span>" for item in card.get("meta", []))
    meta_html = f"<div class='meta'>{meta}</div>" if meta else ""
    return f"<div class='card'><h3>{html.escape(card['title'])}</h3>{body_html}{meta_html}</div>"


def render_html(summary: dict) -> str:
    target_badges = "".join(f"<span>{html.escape(str(target))}</span>" for target in summary["metadata"]["targets"])
    cards_html = "".join(render_card_body(card) for card in summary["cards"])
    strengths_html = "".join(f"<li>{html.escape(item)}</li>" for item in summary["strengths"])
    package_rows = "".join(
        f"<tr><td>{html.escape(item['path'])}</td><td>{html.escape(item['label'])}</td><td>{html.escape(item['kind'])}</td></tr>"
        for item in summary["package_map"]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(summary['display_name'])} Overview</title>
  <style>
    :root {{
      --text: #101010;
      --muted: #666666;
      --line: #e8e6e1;
      --soft: #f7f6f3;
      --white: #ffffff;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--white);
      color: var(--text);
      font-family: "Inter", "Helvetica Neue", Arial, sans-serif;
      line-height: 1.6;
    }}
    .wrap {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 40px 24px 80px;
    }}
    .eyebrow {{
      margin: 0 0 12px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }}
    h1, h2, h3 {{
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", Georgia, serif;
      font-weight: 600;
      letter-spacing: -0.02em;
    }}
    h1 {{
      font-size: clamp(2.4rem, 5vw, 4.4rem);
      line-height: 1.02;
      max-width: 10ch;
    }}
    .lead {{
      max-width: 760px;
      margin: 18px 0 0;
      font-size: 1.05rem;
      color: #222;
    }}
    .hero-meta, .badges {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 22px;
    }}
    .hero-meta span, .badges span {{
      display: inline-flex;
      align-items: center;
      padding: 8px 12px;
      border: 1px solid var(--line);
      border-radius: 999px;
      color: var(--muted);
      background: var(--white);
      font-size: 13px;
    }}
    section {{
      padding-top: 28px;
      margin-top: 28px;
      border-top: 1px solid var(--line);
    }}
    .section-head {{
      display: grid;
      grid-template-columns: minmax(0, 240px) minmax(0, 1fr);
      gap: 24px;
      align-items: start;
    }}
    .section-head p {{
      margin: 8px 0 0;
      color: var(--muted);
      max-width: 40ch;
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }}
    .card {{
      min-height: 220px;
      padding: 22px;
      border: 1px solid var(--line);
      border-radius: 20px;
      background: var(--white);
    }}
    .card h3 {{
      font-size: 1.2rem;
      margin-bottom: 14px;
    }}
    .card p, .card li {{
      color: #222;
      margin: 0;
    }}
    .card ol, .card ul {{
      margin: 0;
      padding-left: 20px;
      display: grid;
      gap: 10px;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 16px;
    }}
    .meta span {{
      padding: 6px 10px;
      border-radius: 999px;
      background: var(--soft);
      color: var(--muted);
      font-size: 12px;
    }}
    .strengths {{
      margin: 0;
      padding-left: 20px;
      display: grid;
      gap: 12px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      padding: 14px 10px;
      text-align: left;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-weight: 600;
    }}
    @media (max-width: 900px) {{
      .section-head {{ grid-template-columns: 1fr; }}
      .cards {{ grid-template-columns: 1fr; }}
      .card {{ min-height: auto; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <p class="eyebrow">Skill Overview</p>
    <h1>{html.escape(summary["display_name"])}</h1>
    <p class="lead">{html.escape(summary["description"])}</p>
    <div class="hero-meta">
      <span>Skill name: {html.escape(summary["name"])}</span>
      <span>Maturity: {html.escape(summary["metadata"]["maturity_tier"])}</span>
      <span>Format: {html.escape(summary["metadata"]["canonical_format"])}</span>
      <span>Updated: {html.escape(summary["metadata"]["updated_at"])}</span>
    </div>
    <div class="badges">{target_badges}</div>

    <section>
      <div class="section-head">
        <div>
          <h2>Architecture</h2>
          <p>One clear flow: define the boundary, choose the right structure, run the checks, then ship a reusable package.</p>
        </div>
        <div class="cards">{cards_html}</div>
      </div>
    </section>

    <section>
      <div class="section-head">
        <div>
          <h2>Why It Works</h2>
          <p>These are the strengths the package already makes explicit instead of leaving hidden in prompt text.</p>
        </div>
        <ul class="strengths">{strengths_html}</ul>
      </div>
    </section>

    <section>
      <div class="section-head">
        <div>
          <h2>Package Map</h2>
          <p>Use this map to understand what lives where before you read the whole package.</p>
        </div>
        <div>
          <table>
            <thead>
              <tr><th>Path</th><th>Role</th><th>Type</th></tr>
            </thead>
            <tbody>{package_rows}</tbody>
          </table>
        </div>
      </div>
    </section>
  </div>
</body>
</html>
"""


def render_skill_overview(skill_dir: Path, output_html: Path | None = None, output_json: Path | None = None) -> dict:
    skill_dir = skill_dir.resolve()
    reports_dir = skill_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    output_html = output_html or reports_dir / "skill-overview.html"
    output_json = output_json or reports_dir / "skill-overview.json"

    summary = build_summary(skill_dir)
    output_html.write_text(render_html(summary), encoding="utf-8")
    output_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "skill_dir": str(skill_dir),
        "artifacts": {
            "html": str(output_html),
            "json": str(output_json),
        },
        "summary": summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a visual overview report for a skill package.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--output-html")
    parser.add_argument("--output-json")
    args = parser.parse_args()

    result = render_skill_overview(
        Path(args.skill_dir),
        Path(args.output_html).resolve() if args.output_html else None,
        Path(args.output_json).resolve() if args.output_json else None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
