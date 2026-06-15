# Review Waivers

- OK: `True`
- Waivers: `0`
- Active: `0`
- Expired: `0`
- Invalid: `0`
- Covered gates: `none`
- Waiver candidates: `2`
- Open waiverable candidates: `1`
- Non-waivable boundaries: `1`

## Policy

- Blocker waivers allowed: `False`
- Minimum reason chars: `20`
- Expiry is required for every waiver.
- World-class evidence completion cannot be waived; it can only be proven by accepted ledger evidence.

## Waivers

- None

## Candidate Actions

| Gate | Status | Waiver | Risk | Evidence |
| --- | --- | --- | --- | --- |
| `output-lab` | `needs-reviewer-decision` | `true` | review pending 5; model-executed 0; output failures 0 | `reports/output_review_adjudication.md` |
| `world-class-evidence` | `cannot-waive` | `false` | 4 pending evidence entries; 1 human pending; 3 external pending | `reports/world_class_evidence_ledger.md` |

### Output Lab

- gate: `output-lab`
- status: `needs-reviewer-decision`
- waiver allowed: `true`
- risk: review pending 5; model-executed 0; output failures 0
- evidence: `reports/output_review_adjudication.md`
- verification: `python3 scripts/yao.py review-waivers . --add-waiver --gate-key output-lab --reviewer "<reviewer>" --reason "Output Lab has pending human/provider evidence; accepted only for this bounded review scope." --expires-at 2027-06-15 --evidence reports/output_review_adjudication.md`
- world-class boundary: Does not count as provider, human, or public world-class completion evidence.

#### Required Review

- Reviewer confirms this release does not claim provider-backed or human-adjudicated output superiority.
- Reviewer names the release scope and expiry date.
- Reviewer links output_review_adjudication or output_execution evidence.

### World-Class Evidence

- gate: `world-class-evidence`
- status: `cannot-waive`
- waiver allowed: `false`
- risk: 4 pending evidence entries; 1 human pending; 3 external pending
- evidence: `reports/world_class_evidence_ledger.md`
- verification: `python3 scripts/yao.py world-class-ledger . --submissions-dir evidence/world_class/submissions && python3 scripts/yao.py world-class-claim-guard .`
- world-class boundary: Non-waivable completion boundary.

#### Required Review

- Do not use a waiver to claim public world-class readiness.
- Either submit accepted ledger evidence or state that this release does not claim world-class completion.
- Keep claim guard active until ledger summary.ready_to_claim_world_class is true.

## Failures

- None

## Warnings

- None
