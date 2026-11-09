# Output Risk Profile

Skill: `yao-meta-skill`

## Why This Exists

Generated skills often fail in small output details: generic headings, cluttered citations, fragile screenshots, weak Markdown rendering, or missing execution assumptions. This profile predicts the most likely output mistakes before the skill is used heavily.

## Matched Risk Families

### Markdown readability
- Matched keywords: md, table, report, doc
- Score: `4`

### Tone and specificity
- Matched keywords: copy, content, summary
- Score: `3`

### Citation and footnote clutter
- Matched keywords: source, reference
- Score: `2`

### Code and command safety
- Matched keywords: code, script
- Score: `2`

### Screenshot and visual capture
- Matched keywords: capture
- Score: `1`

## Likely Output Mistakes

- Tables can render as dense grids with weak hierarchy or poor mobile readability.
- Long bullets can make the output look complete while hiding the actual decision logic.
- Headings and summaries can drift into generic, interchangeable language.
- The output can sound polished but lose the user's actual taste, audience, or scenario.
- Footnote markers or dense citation notes can interrupt the reading flow.
- Evidence can be over-attached to obvious statements and under-attached to risky claims.

## Output Constraints To Apply

- Use tables only when comparison is the main job; otherwise prefer compact cards or grouped bullets.
- Keep table cells short and move explanations below the table.
- Anchor titles and summaries in the user's audience, object, and concrete outcome.
- Avoid placeholder phrases such as comprehensive guide, ultimate solution, or key insights unless the source demands them.
- Attach citations only to claims that need evidence, not to every sentence.
- Group source notes at the end of a section when inline markers would hurt readability.

## Self-Repair Checks

- Preview whether each table still reads well when columns are narrow.
- Convert any table with paragraph-length cells into bullets or cards.
- Replace generic title candidates with scenario-specific alternatives.
- Delete any polished sentence that could fit almost any project unchanged.
- Remove decorative citations that do not support a material claim.
- Move repeated source explanations into one compact source note.

## Reviewer Note

Use this report before deepening the package and again before approving example outputs.
