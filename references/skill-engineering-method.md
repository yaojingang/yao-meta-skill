# Skill Engineering Method

This doctrine defines the default method for turning messy workflow material into a reusable skill without bloating the entrypoint.

## Core Loop

1. Decide whether the request should become a skill at all.
2. Choose the smallest viable archetype.
3. Set one clear capability boundary.
4. Write and test the trigger description before expanding the body.
5. Add only the gates that match the risk.
6. Package and govern the skill only as far as real reuse demands.

## Phase 1: Qualification

Promote a request into a skill only when at least one of these is true:

- the workflow will be reused
- the workflow is easy to route incorrectly
- deterministic scripts reduce repeated effort
- governance or portability matters

Reject skill creation when the request is only:

- explanation
- summary
- translation
- brainstorming
- documentation without agent execution
- a one-off answer with no reuse value

See [Non-Skill Decision Tree](non-skill-decision-tree.md).

## Phase 2: Archetype Selection

Choose the lightest archetype that fits the job.

- `Scaffold`: exploratory, personal, or short-lived
- `Production`: team-reused, quality-sensitive, but still compact
- `Library`: broad reuse, visible evidence, portability, and maintenance expectations
- `Governed`: organizationally sensitive or operationally critical; lifecycle and review are explicit

See [Skill Archetypes](skill-archetypes.md).

## Phase 3: Boundary Design

Every skill should answer four questions clearly:

- what recurring job does it own
- what outputs does it produce
- what near-neighbor requests should not route here
- what detail belongs outside `SKILL.md`

Boundary work comes before polishing prose.

## Phase 4: Reference Scan

Run a short benchmark pass before deep authoring.

- scan `3-5` reference objects at most
- prioritize external GitHub and official benchmark sources first
- use local files second, only for fit, privacy, and compatibility calibration
- choose from method, structure, execution, portability, and domain patterns
- extract only what improves reliability or clarity
- record what not to borrow so the new skill stays light

See [Reference Scan Strategy](reference-scan.md).

## Phase 5: Trigger-First Authoring

Author the frontmatter `description` before expanding the body.

- start with the recurring job
- include the trigger actions that should route here
- include exclusions when confusion is plausible
- test the route before growing the file tree

Trigger quality is improved through:

- `trigger_eval.py`
- `optimize_description.py`
- blind holdout
- judge-backed blind holdout
- adversarial holdout
- route confusion

## Phase 6: Gate Selection

Add gates by risk, not by habit.

- low-risk scaffolds: validate structure and context size
- production skills: trigger eval plus resource-boundary checks
- library skills: description optimization, route confusion, packaging checks
- governed skills: governance scoring, lifecycle metadata, regression history

See [Gate Selection](gate-selection.md).

## Phase 7: Promotion

A candidate route or package is promotable only when:

- visible holdout does not regress
- blind holdout does not regress
- judge-backed blind holdout does not regress
- adversarial holdout does not regress
- route confusion stays clean
- context and governance gates still pass

See [Promotion Policy](../evals/promotion_policy.md).

## Design Principle

The method is only correct if rigor grows faster than context cost. If a new check or document makes the skill heavier without making it more reliable, remove or relocate it.
