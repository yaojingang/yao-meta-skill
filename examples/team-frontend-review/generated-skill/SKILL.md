---
name: frontend-review
description: Review frontend code for accessibility, risky UI security issues, missing states, and common UX regressions. Use when asked to review React, UI, frontend components, forms, a11y, or pre-merge frontend quality.
---

# Frontend Review

Review UI code with a pre-merge mindset. Findings come first. Focus on behavior regressions, accessibility gaps, risky form handling, unsafe rendering, and missing user states.

## Workflow

1. Identify the UI surface and user flows affected.
2. Check accessibility, security-sensitive inputs, loading states, and error states.
3. Report findings by severity with concrete code references.
4. Prefer actionable fixes over generic advice.

## Output Contract

- Start with findings, ordered by severity.
- Include file references for each finding.
- Call out open questions separately from confirmed issues.
- If there are no findings, say that explicitly and note residual risks or test gaps.

## Reference Map

- Read `references/checklist.md` for the review standard.
