# System Model

Skill: `yao-meta-skill`

- Stability score: `100/100`
- Stability band: `system-ready`
- Doctrine: Structure drives behavior: improve the boundary, feedback loops, drift watch, and leverage points before adding weight.

## System Boundary Map

- Owned job: Turn repeated workflows, prompts, transcripts, runbooks, documents, or existing skill packages into routeable, evaluable, packageable, and governable agent skills for personal, team, library, or governed reuse.
- Output boundary: A working skill package with lean SKILL.md, aligned agents/interface.yaml, justified references, scripts only when useful, eval evidence, reports, packaging metadata, and clear next iteration recommendations.
- Maturity assumption: `governed`
- Input boundary:
  - rough workflow notes, SOPs, runbooks, prompts, transcripts, documents, or repeated task descriptions
  - an existing skill directory that needs refactor, evaluation, packaging, or governance hardening
  - target platform requirements such as OpenAI, Claude, generic Agent Skills, or team distribution
  - benchmark references, local constraints, desired maturity tier, and review standards
- Non-goals:
  - one-off writing, translation, explanation, or brainstorming requests that do not need a reusable skill
  - general code review or debugging unless the user is packaging that workflow as a skill
  - raw private material that was not intentionally supplied as skill evidence
  - platform-specific plugin creation when the request is not about an agent skill package
- Constraints:
  - keep SKILL.md lean and route primarily through frontmatter description
  - put durable guidance in references, executable logic in scripts, and evidence in reports
  - default to the lightest reliable mode before adding governance weight
  - preserve portability across OpenAI, Claude, generic, and Agent Skills compatible targets
  - avoid raw prompt, output, transcript, or private content in telemetry
- Standards:
  - trigger boundaries must be tested with should-trigger and should-not-trigger cases
  - production and higher maturity work needs output eval, trust, runtime conformance, and Review Studio evidence
  - governed work needs owner, review cadence, permission approvals, registry metadata, package verification, and install simulation
  - generated reports should be bilingual or reviewer-friendly when they are user-facing
  - each new asset must earn its place by reducing ambiguity, risk, or repeated work
- Human judgment boundary:
  - Infer non-core gaps visibly; ask one focused clarification only for an unresolved core job, primary output, or explicit direction conflict.
  - Escalate visible tradeoffs when benchmark patterns conflict with local privacy, naming, or governance constraints.
  - Do not silently broaden the skill into adjacent jobs just because the examples are nearby.

## Feedback Loops

### Intent boundary loop

- Signal: Intent confidence score is 100/100.
- Response: Ask only the highest-leverage clarification before adding package weight.
- Evidence: reports/intent-confidence.md and reports/intent-dialogue.md

### Reference synthesis loop

- Signal: Benchmark patterns are useful only after they are abstracted into borrow and avoid guidance.
- Response: Borrow one pattern at a time and keep the rest as reviewer-visible evidence.
- Evidence: reports/reference-synthesis.md
- Current patterns:
  - Borrow progressive disclosure: keep the entrypoint lean and move depth into references or scripts.
  - Borrow a small hypothesis-test-learn loop so the first revision is evidence-backed.
  - Borrow the discipline of defining what the skill should not own before growing the package.
  - Borrow the way it turns a messy workflow into a repeatable operating path.
  - Borrow the clear execution entrypoints and command structure.

### Output quality loop

- Signal: Generated output may fail in recurring domain-specific ways.
- Response: Apply predicted output-risk families as self-repair checks before final output.
- Evidence: reports/output-risk-profile.md
- Current risk families:
  - Markdown readability
  - Tone and specificity
  - Citation and footnote clutter
  - Code and command safety
  - Screenshot and visual capture

### Reviewer feedback loop

- Signal: Human review catches drift that static checks miss.
- Response: Capture lightweight feedback and turn repeated findings into gates or references.
- Evidence: reports/review-viewer.html and feedback records

### Lifecycle loop

- Signal: As reuse grows, the skill needs stronger gates, ownership, and regression evidence.
- Response: Promote only when the next gate improves reliability more than context cost.
- Evidence: manifest.json, reports/iteration-directions.md, and governance checks

## Delay And Drift Watch

### Trigger drift

- Watch signal: Users start invoking the skill for adjacent one-off or explanation-only requests.
- Countermeasure: Add near-neighbor exclusions and route evals before expanding workflow steps.
- Cadence: per trigger or description change

### Output drift

- Watch signal: Outputs remain valid but become generic, cluttered, or weakly aligned with the user's domain.
- Countermeasure: Refresh output-risk and artifact-design profiles, then add one self-repair check.
- Cadence: after the first 3-5 real uses
- Risk families:
  - Markdown readability
  - Tone and specificity
  - Citation and footnote clutter
  - Code and command safety
  - Screenshot and visual capture

### Reference drift

- Watch signal: Borrowed benchmark patterns no longer fit the local job or add ceremony without payoff.
- Countermeasure: Re-run reference synthesis and keep only patterns that improve the current boundary.
- Cadence: per material benchmark or product assumption change

### Governance drift

- Watch signal: Skill usage becomes team-critical while ownership, review cadence, or rollback evidence stays informal.
- Countermeasure: Promote maturity tier and add reviewer-visible lifecycle evidence.
- Cadence: monthly

## Failure Pattern Map

### Boundary failure

- Symptom: The skill handles nearby requests that were never part of the recurring job.
- Repair: Narrow the description and add explicit non-goals before adding more execution steps.

### Feedback gap

- Symptom: The skill has rules but no signal telling authors which rule should change after use.
- Repair: Turn repeated reviewer feedback into one eval, one reference note, or one self-repair check.

### Output degradation

- Symptom: The result is structurally correct but generic, cluttered, or weakly matched to the user's domain.
- Repair: Use output-risk families as pre-final checks.
- Current Risk Families:
  - Markdown readability
  - Tone and specificity
  - Citation and footnote clutter
  - Code and command safety
  - Screenshot and visual capture

### Prompt-behavior mismatch

- Symptom: The role, task, and format are copied from a prompt instead of becoming stable skill behavior.
- Repair: Convert reusable role/task/format assumptions into workflow, reports, or references.

## Highest Leverage Moves

### 2. Tune the frontmatter description

- Why: The description is the highest-leverage routing surface.
- Move: Name the recurring job, expected input, output, and strongest non-goal in compact language.

### 3. Install output self-repair checks

- Why: The likely failure families are: Markdown readability, Tone and specificity, Citation and footnote clutter.
- Move: Add only the checks that prevent recurring output mistakes.

### 4. Borrow one pattern, not a whole product

- Why: External references improve quality when reduced to structure, not copied as surface style.
- Move: Start from: Borrow progressive disclosure: keep the entrypoint lean and move depth into references or scripts.

### 5. Close the lifecycle loop

- Why: Team-reused skills need visible ownership, review cadence, and regression evidence.
- Move: Keep manifest, review viewer, and iteration directions aligned after each material change.

## Reviewer Use

- Reviewer should ask whether the skill's structure will keep producing the desired behavior after repeated real use.
- Prefer changing the system boundary, feedback loop, or leverage point before adding more prose.
- If a problem repeats, convert it into a named failure pattern and one regression check.
