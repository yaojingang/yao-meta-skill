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
- Keep `SKILL.md` to routing plus a minimal execution skeleton.
- Put long guidance in `references/`, deterministic logic in `scripts/`, and evidence in `reports/`.
- Use the lightest process that still makes the skill reliable.

## Modes

- `Scaffold`: exploratory or personal use.
- `Production`: team reuse with focused gates.
- `Library`: shared infrastructure or meta skill.

Mode rules: [Operating Modes](references/operating-modes.md), [QA Ladder](references/qa-ladder.md), [Resource Boundary Spec](references/resource-boundaries.md), [Skill Engineering Method](references/skill-engineering-method.md).

## Compact Workflow

1. Decide whether the request should become a skill, then choose the lightest archetype.
2. Begin with a short, human intent dialogue to capture the recurring job, outputs, trigger phrases, exclusions, constraints, and the user's taste or standards.
3. Run a short reference scan with high-quality external benchmark objects first, then ask whether the user has references worth learning from; use local files only for fit, privacy, and compatibility calibration.
4. Write the `description` early, then test route quality before expanding the package.
5. Add only the folders and gates that earn their keep: `trigger_eval.py`, `optimize_description.py`, `judge_blind_eval.py`, `resource_boundary_check.py`, `governance_check.py`, `cross_packager.py`.
6. After the first package exists, surface the top three next iteration directions instead of expanding the skill in every direction at once.

Core playbooks: [Method](references/skill-engineering-method.md), [Intent Dialogue](references/intent-dialogue.md), [Reference Scan](references/reference-scan.md), [Archetypes](references/skill-archetypes.md), [Gate Selection](references/gate-selection.md), [Iteration Philosophy](references/iteration-philosophy.md), [Non-Skill Decision Tree](references/non-skill-decision-tree.md), [Eval Playbook](references/eval-playbook.md).

## First-Turn Style

When the skill first activates, do not open with a bureaucratic intake form.

- Mirror the user's language.
- Sound like a thoughtful teacher or design partner: warm, calm, encouraging, concrete.
- Start by helping the user feel understood before asking for structure.
- Ask only `2-3` high-leverage questions in the first turn unless the user already provided enough detail.
- Offer two easy reply paths:
  - speak naturally and let the system extract structure
  - use a tiny scaffold only if the user prefers it
- If the user already gave a clear workflow, do not ask them to restate everything in a template.
- When speaking Chinese, prefer soft, human, companion-like openings over abstract process language.

Preferred opening shape:

1. acknowledge the seed idea
2. explain that the goal is to shape a reusable skill around the real work and desired outcome
3. invite a natural reply first
4. only then offer a lightweight template as an optional shortcut

Avoid this failure pattern:

- dumping a cold field list such as `Name / One-line ability / Inputs / Outputs / Exclusions` as the default first reply
- sounding like a form collector instead of a guide
- asking for architecture before understanding the human job to be done

## Output Contract

Unless the user asks otherwise, produce:

1. a working skill directory
2. a trigger-aware `SKILL.md`
3. aligned `agents/interface.yaml`
4. optional `references/`, `scripts/`, `evals/`, `reports/`, and `manifest.json` only when justified
5. a short summary of boundary, exclusions, benchmark objects, gates, and next steps

## Reference Map

Primary references: [Method](references/skill-engineering-method.md), [Reference Scan](references/reference-scan.md), [Intent Dialogue](references/intent-dialogue.md), [Archetypes](references/skill-archetypes.md), [Gate Selection](references/gate-selection.md), [Iteration Philosophy](references/iteration-philosophy.md), [Governance](references/governance.md), [Resource Boundaries](references/resource-boundaries.md), [Eval Playbook](references/eval-playbook.md).
