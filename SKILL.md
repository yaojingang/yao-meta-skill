---
name: yao-meta-skill
description: Create, refactor, evaluate, and package agent skills from workflows, prompts, transcripts, docs, or notes. Use when asked to create a skill, turn a repeated process into a reusable skill, improve an existing skill, add evals, or package a skill for team reuse.
metadata:
  author: Yao Team
  philosophy: "structured design, evaluation loop, template ergonomics, operational packaging"
---

# Yao Meta Skill

## Router Rules

- Route by frontmatter `description`.
- Keep `SKILL.md` lean; put guidance in `references/`, logic in `scripts/`, and evidence in `reports/`.
- Use the lightest reliable process.

## Modes

- `Scaffold`: exploratory or personal.
- `Production`: team reuse.
- `Library`: shared infrastructure.

Mode rules: [Method](references/skill-engineering-method.md), [Operating Modes](references/operating-modes.md), [Resource Boundaries](references/resource-boundaries.md).

## Compact Workflow

1. Decide whether the request should become a skill and choose the lightest fit.
2. Capture job, output, exclusions, constraints, and standards.
3. Run reference scan: external benchmarks first, user references second, local fit third; surface only uncertainty or conflict.
4. Write the `description` early and test route quality before expanding the package.
5. Add output-risk, artifact-design, prompt-quality, and system-model reports only when they matter.
6. Add only folders and gates that earn their keep.
7. Surface the top three next iteration directions.

Core playbooks: [Method](references/skill-engineering-method.md), [Intent](references/intent-dialogue.md), [Skill IR](references/skill-ir-method.md), [Output Eval](references/output-eval-method.md), [Registry](references/distribution-registry-method.md), [Review Studio](references/review-studio-method.md).

## Skill OS 2.0 Gates

For production, library, governed, or team-distributed work, run Skill IR, target compiler, trigger + output eval, Skill Atlas, conformance, trust, registry/package/install, upgrade, drift, waiver, and Review Studio gates before release.

## First-Turn Style

When the skill first activates:

- start from the user's work and desired outcome before structure
- ask only `2-3` key questions unless the user already gave enough detail
- avoid cold field lists; surface benchmark choices only when uncertainty or conflict needs a call

Chinese conversations should sound soft and companion-like rather than procedural.

Opening patterns: [Intent Dialogue](references/intent-dialogue.md).

## Output Contract

Unless the user asks otherwise, produce a working skill directory with `SKILL.md`, aligned `agents/interface.yaml`, justified assets, and a short summary of boundary, exclusions, gates, and next steps.

## Reference Map

Primary references: [Method](references/skill-engineering-method.md), [Artifact Design](references/artifact-design-doctrine.md), [Systems Thinking](references/systems-thinking-doctrine.md), [Governance](references/governance.md).
