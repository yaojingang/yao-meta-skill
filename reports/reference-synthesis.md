# Reference Synthesis

Skill: `yao-meta-skill`
- Description: Create, refactor, evaluate, and package agent skills from workflows, prompts, transcripts, docs, or notes. Use for skill creation, reusable workflow packaging, skill improvement, evals, and team-ready distribution.
- Intent confidence: `100/100` (`high`)

## Live GitHub Benchmarks

### obra/superpowers
- URL: https://github.com/obra/superpowers
- Stars: `226125`
- Borrow: Borrow the way it turns a messy workflow into a repeatable operating path.
- Borrow: Borrow the clear execution entrypoints and command structure.

### affaan-m/ECC
- URL: https://github.com/affaan-m/ECC
- Stars: `214381`
- Borrow: Borrow the way it turns a messy workflow into a repeatable operating path.
- Borrow: Borrow the clear execution entrypoints and command structure.

### multica-ai/andrej-karpathy-skills
- URL: https://github.com/multica-ai/andrej-karpathy-skills
- Stars: `174264`
- Borrow: Borrow explicit validation and quality gates that make iteration safer.
- Borrow: Borrow the way it separates explanation, examples, and reusable structure.

## Curated World-Class Pattern Tracks

### Official skill anatomy and context discipline
- Type: `official`
- Evidence mode: `curated-pattern-track`
- Why relevant: This track matches: metadata, references.
- Borrow: Borrow progressive disclosure: keep the entrypoint lean and move depth into references or scripts.
- Avoid: Do not let packaging or platform concerns swallow the core job boundary.

### Human-in-the-loop verification
- Type: `research`
- Evidence mode: `curated-pattern-track`
- Why relevant: This track matches: review, govern.
- Borrow: Borrow a review checkpoint wherever trust matters more than raw speed.
- Avoid: Do not force every skill through heavyweight review when the risk is low.

### Boundary-first design
- Type: `principles`
- Evidence mode: `curated-pattern-track`
- Why relevant: This track matches: route.
- Borrow: Borrow the discipline of defining what the skill should not own before growing the package.
- Avoid: Do not expand execution assets until route boundaries stay clean.

## Borrow Now

- Borrow progressive disclosure: keep the entrypoint lean and move depth into references or scripts.
- Borrow a review checkpoint wherever trust matters more than raw speed.
- Borrow the discipline of defining what the skill should not own before growing the package.
- Borrow the way it turns a messy workflow into a repeatable operating path.
- Borrow the clear execution entrypoints and command structure.

## Avoid Now

- Do not let packaging or platform concerns swallow the core job boundary.
- Do not force every skill through heavyweight review when the risk is low.
- Do not expand execution assets until route boundaries stay clean.
- Do not import process overhead that only exists for that project's scale.
- Do not copy repo-specific commands or environment assumptions verbatim.

## Pattern Gate

- Summary: 5 accepted, 1 deferred using threshold 4/4.
- Acceptance threshold: `4/4`
- Accepted patterns:
  - **Official skill anatomy and context discipline**: 4/4 (recurrence, generativity, distinctiveness, boundary)
  - **Human-in-the-loop verification**: 4/4 (recurrence, generativity, distinctiveness, boundary)
  - **Boundary-first design**: 4/4 (recurrence, generativity, distinctiveness, boundary)
  - **obra/superpowers**: 4/4 (recurrence, generativity, distinctiveness, boundary)
  - **affaan-m/ECC**: 4/4 (recurrence, generativity, distinctiveness, boundary)
- Deferred patterns:
  - **multica-ai/andrej-karpathy-skills**: missing generativity

## Default Recommendation

- Summary: Start by borrowing this pattern: Borrow progressive disclosure: keep the entrypoint lean and move depth into references or scripts. Avoid this for the first pass: Do not let packaging or platform concerns swallow the core job boundary.
- Why: There is a real design conflict to resolve: The stated preference leans lightweight or speed-first, while the benchmark mix leans toward governance, review, or heavier evaluation structure.
- User decision required: `True`

## Visibility Mode

- Mode: `explicit`
- Reasons: design_conflict
- User note: Surface the recommendation because intent is still settling or there is a real design conflict that needs a user call.
- Reviewer note: Keep the full benchmark and synthesis evidence visible for authors and reviewers.

## Conflict Check

- **lightweight_vs_governance**: The stated preference leans lightweight or speed-first, while the benchmark mix leans toward governance, review, or heavier evaluation structure.

## Quality Lift Thesis

- Use GitHub repositories for concrete package and workflow patterns.
- Use curated official or commercial tracks for entrypoint and operator ergonomics.
- Use research tracks to justify the smallest evaluation loop that still catches regressions.
- Use principle tracks to keep the package small, boundary-aware, and outcome-driven.

## Decision Prompt

Use the recommendation by default. Only surface the underlying benchmark tradeoffs when intent is uncertain or a real design conflict needs a deliberate call.
