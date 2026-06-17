# World-Class Evidence Intake

This directory defines the intake contract for external and human evidence required before `yao-meta-skill` can honestly claim public world-class completion.

The templates in `templates/` are review aids only. They do not count as accepted evidence. Real submissions belong in `evidence/world_class/submissions/`, which is intentionally gitignored by default so provider metadata, reviewer identity, or client integration notes can be reviewed before anything is committed.

Run:

```bash
SUBMISSIONS_DIR="${SUBMISSIONS_DIR:-evidence/world_class/submissions}"
python3 scripts/yao.py world-class-preflight . --submissions-dir "$SUBMISSIONS_DIR"
python3 scripts/yao.py world-class-submission-kit . --output-dir "$SUBMISSIONS_DIR"
# Alternative: prefill artifact SHA-256 digests while keeping drafts template-only.
python3 scripts/yao.py world-class-submission-kit . --output-dir "$SUBMISSIONS_DIR" --prefill-artifacts
python3 scripts/yao.py world-class-intake . --submissions-dir "$SUBMISSIONS_DIR"
python3 scripts/yao.py world-class-submission-review . --submissions-dir "$SUBMISSIONS_DIR"
python3 scripts/yao.py world-class-ledger . --submissions-dir "$SUBMISSIONS_DIR"
python3 scripts/yao.py world-class-runbook . --submissions-dir "$SUBMISSIONS_DIR"
```

The intake validator checks:

- the evidence key matches the current world-class ledger
- the category and source type match the expected human or external evidence path
- artifact references are declared
- real submissions reference concrete files inside the skill directory and include a matching SHA-256 digest for each artifact
- real submissions use the canonical `<evidence-key>.json` filename expected by the ledger
- credentials, secrets, raw user content, and raw provider prompts are explicitly excluded
- raw prompt, output, transcript, message, credential, secret, token, and API-key fields are rejected even when nested
- human adjudication packets must preserve reviewer identity, review date, A/B winner, confidence, and a required rationale before answer-key reveal can count
- planned work, local command-only output, and metadata fallback are not claimed as completion evidence

Run `world-class-preflight` before assigning external or human work. It checks local files, redacted environment readiness, human/external prerequisites, and source-evidence blockers without accepting evidence or printing secrets.

The generated intake report also includes an `operator_checklist` for each pending evidence item. Use it to find the template path, target submission path, preparation command, validation command, required provenance, success checks, and privacy boundary before asking a reviewer or external operator to submit evidence.

The submission kit command creates editable JSON drafts plus a local README for an external operator or human reviewer. Use `--prefill-artifacts` when you want the kit to insert SHA-256 digests for currently available local aggregate artifacts. Prefill is operator convenience only: those drafts still keep `template_only: true` and do not count as evidence until the real run or review exists, the packet is edited truthfully, every artifact ref points to a local aggregate evidence file with a matching `sha256`, and `world-class-intake` validates it.

The submission kit separates artifact rows into `submission-ref` and `supporting-evidence`. `submission-ref` rows are the concrete paths expected in a real packet's `artifact_refs`; `supporting-evidence` rows help reviewers audit the packet and do not all need to be copied into the submission.

The submission review command renders a read-only queue that compares valid packets with the source evidence checks and current ledger state. It is for reviewer triage only; it does not accept evidence or make the world-class claim true.

The operator runbook is the step-by-step coordination cockpit for finishing the remaining real-world work. It includes a Coordination Plan that separates user-required provider, reviewer, native-client, and telemetry actions from assistant-run commands, plus a Release Gate that mirrors the ledger, claim guard, benchmark, Review Studio, evidence consistency, and final CI checks. The runbook is operational guidance only: planning rows, submission drafts, and release-gate rows keep `counts_as_completion: false`.

Accepted intake means "ready for ledger review", not evidence that the final public claim is ready. The ledger remains the source of truth for `ready_to_claim_world_class`.
