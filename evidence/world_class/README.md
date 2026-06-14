# World-Class Evidence Intake

This directory defines the intake contract for external and human evidence required before `yao-meta-skill` can honestly claim public world-class completion.

The templates in `templates/` are review aids only. They do not count as accepted evidence. Real submissions belong in `evidence/world_class/submissions/`, which is intentionally gitignored by default so provider metadata, reviewer identity, or client integration notes can be reviewed before anything is committed.

Run:

```bash
python3 scripts/yao.py world-class-submission-kit . --output-dir /tmp/yao-world-class-submission-kit
python3 scripts/yao.py world-class-intake .
python3 scripts/yao.py world-class-submission-review .
```

The intake validator checks:

- the evidence key matches the current world-class ledger
- the category and source type match the expected human or external evidence path
- artifact references are declared
- real submissions reference concrete files inside the skill directory and include a matching SHA-256 digest for each artifact
- credentials, secrets, raw user content, and raw provider prompts are explicitly excluded
- planned work, local command-only output, and metadata fallback are not claimed as completion evidence

The generated intake report also includes an `operator_checklist` for each pending evidence item. Use it to find the template path, target submission path, preparation command, validation command, required provenance, success checks, and privacy boundary before asking a reviewer or external operator to submit evidence.

The submission kit command creates editable JSON drafts plus a local README for an external operator or human reviewer. Those drafts keep `template_only: true` and do not count as evidence until the real run or review exists, the packet is edited truthfully, every artifact ref points to a local aggregate evidence file with a matching `sha256`, and `world-class-intake` validates it.

The submission review command renders a read-only queue that compares valid packets with the source evidence checks and current ledger state. It is for reviewer triage only; it does not accept evidence or make the world-class claim true.

Accepted intake means "ready for ledger review", not "world-class complete". The ledger remains the source of truth for `ready_to_claim_world_class`.
