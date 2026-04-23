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

- Route by frontmatter `description`.
- Keep `SKILL.md` lean.
- Put guidance in `references/`, logic in `scripts/`, and evidence in `reports/`.
- Use the lightest reliable process.

## Modes

- `Scaffold`: exploratory or personal use.
- `Production`: team reuse with focused gates.
- `Library`: shared infrastructure or meta skill.

Mode rules: [Operating Modes](references/operating-modes.md), [QA Ladder](references/qa-ladder.md), [Resource Boundaries](references/resource-boundaries.md), [Method](references/skill-engineering-method.md).

## Compact Workflow

1. Decide whether the request should become a skill and choose the lightest fit.
2. Run a short intent dialogue to capture the job, output, exclusions, constraints, and standards.
3. Run a reference scan: external benchmarks first, user references second, local fit third. Keep synthesis silent unless intent stays unclear or a real design conflict needs a user call.
4. Write the `description` early and test route quality before expanding the package.
5. Add only the folders and gates that earn their keep.
6. After the first package exists, surface the top three next iteration directions.

Core playbooks: [Method](references/skill-engineering-method.md), [Intent Dialogue](references/intent-dialogue.md), [Reference Scan](references/reference-scan.md), [Archetypes](references/skill-archetypes.md), [Gate Selection](references/gate-selection.md), [Iteration Philosophy](references/iteration-philosophy.md), [Non-Skill Decision Tree](references/non-skill-decision-tree.md).

## First-Turn Style

When the skill first activates:

- open warmly, like a thoughtful teacher or design partner
- start from the user's work and desired outcome before asking for structure
- ask only `2-3` key questions unless the user already gave enough detail
- let the user answer naturally first; offer a tiny scaffold only as a shortcut
- avoid cold field lists and turn benchmark work into one recommendation unless uncertainty or conflict needs a visible call

Chinese conversations should sound soft and companion-like rather than procedural.

Opening patterns: [Intent Dialogue](references/intent-dialogue.md).

## Output Contract

Unless the user asks otherwise, produce:

1. a working skill directory
2. a `SKILL.md`
3. aligned `agents/interface.yaml`
4. optional `references/`, `scripts/`, `evals/`, `reports/`, and `manifest.json` only when justified
5. a short summary of boundary, exclusions, gates, and next steps

## Reference Map

Primary references: [Method](references/skill-engineering-method.md), [Reference Scan](references/reference-scan.md), [Intent Dialogue](references/intent-dialogue.md), [Governance](references/governance.md), [Resource Boundaries](references/resource-boundaries.md).
