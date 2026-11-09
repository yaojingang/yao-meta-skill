---
name: yao-meta-skill
display_name: Yao 技能工厂
display_name_en: Yao Meta Skill
description: Create, improve, or evaluate an existing skill from workflows, prompts, SOPs, scripts. Use for migration/release/package, routing, evals/tests, install/trust checks, 优化已有 skill, 补 trigger 评测. Exclude summary/translation/docs, brainstorming, one-off prompts, copy-only edits, outline-only requests.
description_zh: 将重复流程整理为可复用技能，支持创建、优化、评测、打包和安装检查。
description_en: Create, improve, evaluate, and package reusable agent skills.
version: "2.1.1"
author: Yao Team
metadata:
  author: Yao Team
---

# Yao Meta Skill

## Router Rules

- Route by frontmatter `description` using the lightest mode.
- Keep `SKILL.md` lean: guidance in `references/`, logic in `scripts/`, evidence in `reports/`.

## Modes

- `Scaffold`: exploratory; `Production`: team; `Library`: shared; `Governed`: release-critical.
- Rules: [Method](references/skill-engineering-method.md), [Modes](references/operating-modes.md), [Boundaries](references/resource-boundaries.md).

## Compact Workflow

1. Require `repeated use` + `reusable output contract`; skip one-offs.
2. Lock target path + identity before writes; self-edits require `--self`.
3. Capture job, output, exclusions, constraints, standards, mode.
4. Scan `3-5` useful external/user/local references.
5. Write `description` early; route edits need `trigger_eval.py`; release gates follow risk.
6. Add deeper profiles only when earned.

Playbooks: [Target Safety](references/target-safety.md), [Intent](references/intent-dialogue.md), [Skill IR](references/skill-ir-method.md), [Output Eval](references/output-eval-method.md), [Review Studio](references/review-studio-method.md).

## WorkBuddy

Use [WorkBuddy](references/workbuddy.md) for import, runtime, output metadata and updates.

## Updates

Activation: `scripts/yao.py check-update --notice --self`; show `notice_text` if requested; continue. WorkBuddy updates use ZIP re-import. For supported managed Agent Skills/Codex installs, “更新”: `scripts/yao.py self-update --self --yes`.

## Skill OS 2.0 Gates

For production/library/governed releases, run Skill IR, compiler, trigger/output eval, Atlas, conformance, trust, package/install, upgrade, drift, waiver, Review Studio.

## Governed Package Boundary

Governed/file-backed packages require `owner`, `review cadence`, `input_files` (`file-backed fixture`), `output contract`, `rollback boundary`, `trust report`, and `reports/output_quality_scorecard.md`. Preserve these labels; mark unavailable evidence as `missing evidence`; never fabricate evidence.

## First-Turn Style

- Infer non-core gaps; ask one core-fork question per round, max two, then use recorded preferred inference.
- In Chinese, sound soft and companion-like; use [Intent Dialogue](references/intent-dialogue.md).

## Output Contract

Builds: `SKILL.md`, aligned interface, justified assets, boundary/gate summary. Audits: findings + fixes; edit only when asked. No-skill: no files.
