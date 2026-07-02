---
name: yao-meta-skill
description: Create, refactor, evaluate, package, migrate, govern, and release agent skills from workflows, prompts, transcripts, docs, notes, SOPs, scripts, or repeated team practices. Use when asked to create/build a skill, turn a repeated process into a reusable agent capability, improve or migrate an existing skill, optimize trigger routing, add evals/tests, add references/scripts/interface/manifest, prepare packaging/installation/release, or make a skill team-ready. Also trigger on Chinese asks such as 做/改/重构/迁移/发布 skill, 把流程/SOP/提示词/对话记录沉淀成可复用能力, 封装成团队可复用的 skill, 优化已有 skill, 补 trigger 评测, 收紧触发边界, or 做打包发布检查. Do not use for summary-only, translation-only, brainstorming-only, or documentation-only requests that explicitly say no skill or agent execution.
metadata:
  author: Yao Team
---

# Yao Meta Skill

## Router Rules

- Route by frontmatter `description`.
- Keep `SKILL.md` lean; put guidance in `references/`, logic in `scripts/`, and evidence in `reports/`.
- Use the lightest reliable process.

## Modes

- `Scaffold`: exploratory/personal. `Production`: team reuse. `Library`: shared infrastructure. `Governed`: high-trust, policy-sensitive, or release-critical.
- Rules: [Method](references/skill-engineering-method.md), [Operating Modes](references/operating-modes.md), [Resource Boundaries](references/resource-boundaries.md).

## Compact Workflow

1. For one-off/no reusable process: `Do not create a skill`; `near-neighbor`; require `repeated use` + `reusable output contract`.
2. Capture job, output, exclusions, constraints, standards, and the lightest fit.
3. Scan references in order: external benchmark, user source, local fit; surface only uncertainty or conflict.
4. Write `description` early, test route quality, then add only earned folders and gates.
5. Add output-risk, artifact-design, prompt-quality, system-model, and next directions only when useful.

Playbooks: [Method](references/skill-engineering-method.md), [Intent](references/intent-dialogue.md), [Skill IR](references/skill-ir-method.md), [Output Eval](references/output-eval-method.md), [Review Studio](references/review-studio-method.md).

## Skill OS 2.0 Gates

For production, library, governed, or team-distributed work, run Skill IR, target compiler, trigger + output eval, Skill Atlas, conformance, trust, registry/package/install, upgrade, drift, waiver, and Review Studio gates before release.

## Governed Package Boundary

For file-backed, release-critical, or governed packages, name `input_files` as `file-backed fixture` evidence; include `owner`, `review cadence`, `input_files`, `output contract`, `rollback boundary`; require `trust report` and `reports/output_quality_scorecard.md`; mark unavailable telemetry, approvals, metrics, or benchmarks as `missing evidence`; do not fabricate evidence.

Preserve audit labels literally when they apply: `file-backed fixture`, `input_files`, `output contract`, `rollback boundary`, `trust report`, `reports/output_quality_scorecard.md`, `missing evidence`.

## First-Turn Style

- Start from the user's work/outcome before structure.
- Ask only `2-3` key questions unless enough detail exists.
- In Chinese, sound soft and companion-like; use [Intent Dialogue](references/intent-dialogue.md).

## Output Contract

Unless asked otherwise, produce `SKILL.md`, aligned `agents/interface.yaml`, justified assets, and a short summary of boundary, exclusions, gates, and next steps.

## Reference Map

Primary: [Method](references/skill-engineering-method.md), [Artifact Design](references/artifact-design-doctrine.md), [Systems Thinking](references/systems-thinking-doctrine.md), [Governance](references/governance.md), [SkillOps Decision](references/skillops-decision-policy.md).
