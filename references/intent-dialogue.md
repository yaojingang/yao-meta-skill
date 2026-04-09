# Intent Dialogue

Use a short, human conversation before deep authoring so the first version of the skill is anchored in the real job rather than in a guessed prompt shape.

## Why This Step Exists

- raw workflow material is often incomplete, mixed, or ambiguous
- the wrong boundary chosen early is expensive to repair later
- good trigger design depends on knowing what should not route here
- execution assets should follow confirmed outputs, not assumptions

## What To Capture

Ask only the questions that change the package design.

1. If this worked beautifully, what recurring job would it quietly take off the user's plate?
2. What real inputs would people actually hand to it?
3. What finished output should it hand back so the user can keep moving?
4. What near-neighbor requests should it politely refuse?
5. What matters most here: speed, consistency, auditability, portability, governance, or tone/style fit?
6. Are there any public or private references the user wants this skill to learn from? Only borrow patterns, never copy wording or private material.
7. What assets already exist: docs, scripts, templates, examples, or prior prompts?
8. What constraints matter: privacy, naming, local library fit, or target environments?

## Interview Rule

- prefer `5-7` sharp questions over a long discovery questionnaire
- start with a calm, human framing before switching into precise design questions
- guide like a patient teacher or thoughtful coach, not like a rigid intake clerk
- mirror the user's language and emotional temperature
- first invite a natural explanation, then offer a lightweight template only as an option
- ask boundary questions early
- ask output questions before architecture questions
- stop once the skill can be described clearly in one sentence

## First Message Pattern

The first message should feel like guided co-creation, not form filling.

Recommended flow:

1. briefly acknowledge the user's seed idea
2. explain that you want to first understand the real recurring work and what a good outcome looks like
3. invite the user to describe it naturally in their own words
4. offer a tiny scaffold only if they want a shortcut

Good example shape:

- `Let's make this easy. Tell me what kind of repeated work you want this skill to quietly take over, what people will hand to it, and what a useful finished result should look like. If you want, I can also give you a tiny template to fill in.`

Bad example shape:

- `Name:`
- `One-line capability:`
- `Real input:`
- `Target output:`

The second pattern is allowed only when the user explicitly asks for a structured template.

## Output

The dialogue should produce:

- one clear capability sentence
- a list of real inputs
- a list of required outputs
- a short exclusion list
- a note on user-supplied references or benchmark preferences
- one recommended archetype
- one recommended first evaluation target

## Failure Pattern

Do not continue into full authoring when the dialogue still leaves these unresolved:

- whether the request is really reusable
- which near-neighbor requests should not trigger
- what concrete deliverable the skill must return

Also treat these as dialogue failures:

- the first reply feels like a cold worksheet instead of a guided conversation
- the user is forced into a full template before the real job is understood
- the assistant asks for package structure before clarifying the desired outcome
