---
name: yao-meta-skill
description: Create/improve/evaluate agent skills from workflows, prompts, SOPs, scripts. Use for migration/release/package, routing, evals/tests, install checks, 优化已有 skill, 补 trigger 评测. Exclude no-skill summary/translation/docs.
metadata:
  author: Yao Team
---

# Yao Meta Skill

## Router Rules

- Route by frontmatter `description`.
- Keep `SKILL.md` lean; put guidance in `references/`, logic in `scripts/`, and evidence in `reports/`.
- Use the lightest reliable process.

## Modes

- `Scaffold`: exploratory/personal. `Production`: team reuse. `Library`: shared infra. `Governed`: high-trust/release-critical.
- Rules: [Method](references/skill-engineering-method.md), [Operating Modes](references/operating-modes.md), [Resource Boundaries](references/resource-boundaries.md).

## Compact Workflow

1. One-off/no reusable process: `Do not create a skill`; `near-neighbor`; require `repeated use` + `reusable output contract`.
2. Capture job, output, exclusions, constraints, standards, lightest fit.
3. Scan up to `3-5` references: external, user, local; skip tiny edits; surface only uncertainty/conflict.
4. Write `description` early; route/boundary edits need `trigger_eval.py`; releases need risk-matched gates before folders.
5. Add output-risk, artifact-design, prompt-quality, system-model, next directions only when earned.

Playbooks: [Method](references/skill-engineering-method.md), [Intent](references/intent-dialogue.md), [Skill IR](references/skill-ir-method.md), [Output Eval](references/output-eval-method.md), [Review Studio](references/review-studio-method.md).

## Skill OS 2.0 Gates

For production/library/governed/team releases, run Skill IR, compiler, trigger/output eval, Skill Atlas, conformance, trust, registry/package/install, upgrade, drift, waiver, Review Studio.

## Governed Package Boundary

For file-backed/release-critical/governed packages, name `input_files` as `file-backed fixture`; include `owner`, `review cadence`, `input_files`, `output contract`, `rollback boundary`; require `trust report` and `reports/output_quality_scorecard.md`; mark unavailable telemetry/approvals/metrics/benchmarks as `missing evidence`; do not fabricate evidence.

Preserve labels literally when they apply: `file-backed fixture`, `input_files`, `output contract`, `rollback boundary`, `trust report`, `reports/output_quality_scorecard.md`, `missing evidence`.

## First-Turn Style

- Start from the user's work/outcome before structure.
- Ask only `2-3` key questions unless enough detail exists.
- In Chinese, sound soft and companion-like; use [Intent Dialogue](references/intent-dialogue.md).

## Output Contract

Create/refactor/package: produce `SKILL.md`, aligned `agents/interface.yaml`, justified assets, boundary/exclusion/gate summary. Audit/evaluate-only: findings + proposed fixes; edit files only if asked. No-skill: no files.

## Reference Map

Primary: [Method](references/skill-engineering-method.md), [Artifact Design](references/artifact-design-doctrine.md), [Systems](references/systems-thinking-doctrine.md), [Governance](references/governance.md), [SkillOps](references/skillops-decision-policy.md).
