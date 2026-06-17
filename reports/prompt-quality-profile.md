# Prompt Quality Profile

Skill: `yao-meta-skill`
Relevance: `prompt-aware`
Overall quality score: `89.0/100`

## Primary Task Family

**Execution operation**
- Matched keywords: workflow, runbook

## Complexity

- Band: `expert`
- Score: `27`
- Reason: multiple task families plus governance, evaluation, or expert-level constraints

## Need Model

- Explicit Need: Turn repeated workflows, prompts, transcripts, runbooks, documents, or existing skill packages into routeable, evaluable, packageable, and governable agent skills for personal, team, library, or governed reuse.
- Implicit Need: The reusable skill needs a stable role, task, and output contract rather than a one-off prompt.
- Scenario: rough workflow notes, SOPs, runbooks, prompts, transcripts, documents, or repeated task descriptions, an existing skill directory that needs refactor, evaluation, packaging, or governance hardening, target platform requirements such as OpenAI, Claude, generic Agent Skills, or team distribution, benchmark references, local constraints, desired maturity tier, and review standards
- User Level: infer from examples and standards; ask only if it changes output depth
- Success Standard: trigger boundaries must be tested with should-trigger and should-not-trigger cases, production and higher maturity work needs output eval, trust, runtime conformance, and Review Studio evidence, governed work needs owner, review cadence, permission approvals, registry metadata, package verification, and install simulation, generated reports should be bilingual or reviewer-friendly when they are user-facing, each new asset must earn its place by reducing ambiguity, risk, or repeated work

## RTF To Skill Mapping

- Role: Use an operator role with explicit boundaries, inputs, outputs, and failure handling.
- Task: Convert the job into ordered steps with validation checks and stop conditions.
- Format: Return a runbook-like handoff with commands, checks, owners, and next actions when relevant.

## Quality Matrix

### Completeness — 100/100
- Matched signals: input, output, constraint, standard
- Repair: Name missing inputs, outputs, constraints, or success standards before deepening the package.

### Clarity — 85/100
- Matched signals: clear
- Repair: Replace broad verbs with observable actions and define what done means.

### Consistency — 90/100
- Matched signals: aligned, boundary
- Repair: Check that role, task, format, exclusions, and examples do not contradict each other.

### Practicality — 90/100
- Matched signals: use, workflow
- Repair: Add runnable steps, examples, or verification cues instead of abstract advice.

### Specificity — 80/100
- Matched signals: none
- Repair: Anchor wording in the user's audience, domain nouns, and target outcome.

## Matched Task Families

### Execution operation
- Score: `2`
- Keywords: workflow, runbook
- Role: Use an operator role with explicit boundaries, inputs, outputs, and failure handling.
- Task: Convert the job into ordered steps with validation checks and stop conditions.
- Format: Return a runbook-like handoff with commands, checks, owners, and next actions when relevant.

### Creative generation
- Score: `1`
- Keywords: content
- Role: Use a taste-aware creator role with clear audience, tone, and originality boundaries.
- Task: Generate variants, explain selection logic, and preserve the user's distinctive constraints.
- Format: Return options with rationale, selection criteria, and refinement paths.

### Analytical reasoning
- Score: `1`
- Keywords: decision
- Role: Use an analyst role that separates evidence, inference, uncertainty, and recommendation.
- Task: State assumptions, compare alternatives, and make the decision path inspectable.
- Format: Return findings, evidence, tradeoffs, recommendation, and residual risks.

### Dialogue interaction
- Score: `1`
- Keywords: dialogue
- Role: Use a conversational role that asks only high-leverage questions and remembers the user's goal.
- Task: Clarify intent, resolve uncertainty, and converge toward a recommendation instead of a long option list.
- Format: Return concise prompts, decision points, and reviewer-visible assumptions.

## Self-Repair Checks

- Check explicit need, implicit need, scenario, user level, and success standard before deepening.
- Map Role, Task, and Format into skill behavior, not decorative prompt labels.
- Ask one focused clarification only when missing information changes the package boundary.
- Add tests or examples for prompt-heavy behavior before treating it as reusable.
- Keep prompt methodology in references and reports instead of bloating SKILL.md.

## Reviewer Note

Use this profile when the package depends on prompt behavior, role design, output contracts, or conversation quality.
