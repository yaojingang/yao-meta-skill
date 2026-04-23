# Reference Synthesis

Skill: `yao-meta-skill`
- Description: Create, refactor, evaluate, and package agent skills from workflows, prompts, transcripts, docs, or notes. Use when asked to create a skill, turn a repeated process into a reusable skill, improve an existing skill, add evals, or package a skill for team reuse.
- Intent confidence: `30/100` (`low`)

## Live GitHub Benchmarks

- No live GitHub benchmarks are attached yet.

## Curated World-Class Pattern Tracks

### Official workflow product ergonomics
- Type: `official`
- Evidence mode: `curated-pattern-track`
- Why relevant: This track matches: workflow.
- Borrow: Borrow a first-time operator flow that explains itself before it asks for more structure.
- Avoid: Do not mimic product polish that adds UI bulk without improving clarity.

### Hypothesis-test-learn loop
- Type: `research`
- Evidence mode: `curated-pattern-track`
- Why relevant: This track matches: general fit.
- Borrow: Borrow a small hypothesis-test-learn loop so the first revision is evidence-backed.
- Avoid: Do not create experimental overhead that exceeds the skill's real risk tier.

### Boundary-first design
- Type: `principles`
- Evidence mode: `curated-pattern-track`
- Why relevant: This track matches: general fit.
- Borrow: Borrow the discipline of defining what the skill should not own before growing the package.
- Avoid: Do not expand execution assets until route boundaries stay clean.

## Borrow Now

- Borrow a first-time operator flow that explains itself before it asks for more structure.
- Borrow a small hypothesis-test-learn loop so the first revision is evidence-backed.
- Borrow the discipline of defining what the skill should not own before growing the package.

## Avoid Now

- Do not mimic product polish that adds UI bulk without improving clarity.
- Do not create experimental overhead that exceeds the skill's real risk tier.
- Do not expand execution assets until route boundaries stay clean.

## Default Recommendation

- Summary: Start by borrowing this pattern: Borrow a first-time operator flow that explains itself before it asks for more structure. Avoid this for the first pass: Do not mimic product polish that adds UI bulk without improving clarity.
- Why: Intent still has gaps, so the system should surface the recommendation and ask for correction before deepening the package.
- User decision required: `True`

## Visibility Mode

- Mode: `explicit`
- Reasons: intent_uncertain
- User note: Surface the recommendation because intent is still settling or a user reference needs to be reconciled.
- Reviewer note: Keep the full benchmark and synthesis evidence visible for authors and reviewers.

## Quality Lift Thesis

- Use GitHub repositories for concrete package and workflow patterns.
- Use curated official or commercial tracks for entrypoint and operator ergonomics.
- Use research tracks to justify the smallest evaluation loop that still catches regressions.
- Use principle tracks to keep the package small, boundary-aware, and outcome-driven.

## Decision Prompt

Use the recommendation by default. Only surface the underlying benchmark tradeoffs when intent is uncertain or a user reference needs a deliberate call.
