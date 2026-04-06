---
name: yao-meta-skill
description: Create, refactor, evaluate, and package agent skills from workflows, prompts, transcripts, docs, or notes. Use when asked to create a skill, turn a repeated process into a reusable skill, improve an existing skill, add evals, or package a skill for team reuse.
metadata:
  author: Yao Team
  philosophy: "structured design, evaluation loop, template ergonomics, operational packaging"
---

# Yao Meta Skill

Build reusable skill packages, not long prompts.

## Router Rules

- Route by frontmatter `description` first.
- Keep `SKILL.md` to routing plus the minimal execution skeleton.
- Push long guidance to `references/`, deterministic logic to `scripts/`, and evidence to `reports/`.
- Use the lightest process that still makes the skill reliable.

## Modes

- `Scaffold`: exploratory or personal.
- `Production`: team reuse with focused gates.
- `Library`: shared infrastructure or meta skill.

Mode rules: [Operating Modes](references/operating-modes.md), [QA Ladder](references/qa-ladder.md), [Resource Boundary Spec](references/resource-boundaries.md), [Skill Engineering Method](references/skill-engineering-method.md).

## Compact Workflow

1. Decide whether the request should become a skill, then choose the lightest archetype.
2. Run a short reference scan to borrow patterns from strong benchmark objects without copying their prose or weight.
3. Capture the recurring job, outputs, trigger phrases, and exclusions.
4. Write the `description` early, then test route quality before expanding the package.
5. Add only the folders and gates that earn their keep: `trigger_eval.py`, `optimize_description.py`, `judge_blind_eval.py`, `resource_boundary_check.py`, `governance_check.py`, `cross_packager.py`.

Playbooks: [Skill Engineering Method](references/skill-engineering-method.md), [Reference Scan Strategy](references/reference-scan.md), [Skill Archetypes](references/skill-archetypes.md), [Gate Selection](references/gate-selection.md), [Non-Skill Decision Tree](references/non-skill-decision-tree.md), [Operating Modes](references/operating-modes.md), [Trigger And Eval Playbook](references/eval-playbook.md).

## Output Contract

Unless the user asks otherwise, produce:

1. a working skill directory
2. a trigger-aware `SKILL.md`
3. aligned `agents/interface.yaml`
4. optional `references/`, `scripts/`, `evals/`, `reports/`, and `manifest.json` only when justified
5. a short summary of boundary, exclusions, benchmark objects, gates, and next steps

## Reference Map

- [Skill Engineering Method](references/skill-engineering-method.md)
- [Reference Scan Strategy](references/reference-scan.md)
- [Skill Archetypes](references/skill-archetypes.md)
- [Gate Selection](references/gate-selection.md)
- [Non-Skill Decision Tree](references/non-skill-decision-tree.md)
- [Operating Modes](references/operating-modes.md)
- [Governance Model](references/governance.md)
- [Resource Boundary Spec](references/resource-boundaries.md)
- [Trigger And Eval Playbook](references/eval-playbook.md)
