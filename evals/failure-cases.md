# Failure Cases

These cases document where the current trigger strategy is still weak.

## Current Weak Spots

### 1. One-off prompt requests

Example:

`Create a one-off prompt for this task.`

Why it is hard:

- it overlaps strongly with skill-creation vocabulary
- but the user explicitly does not want a reusable package

### 2. Documentation improvement requests

Example:

`Improve this README but do not turn it into a skill.`

Why it is hard:

- it contains transformation language
- but the packaging intent is explicitly absent

### 3. Early-stage brainstorming

Example:

`Help me brainstorm process ideas without building a skill.`

Why it is hard:

- it is adjacent to skill-design work
- but it is still pre-packaging exploration

## How To Use These Failures

- keep them in `near_neighbor`
- use them when adjusting thresholds
- treat them as persistent regression checks
