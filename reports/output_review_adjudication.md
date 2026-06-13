# Output Review Adjudication

This report adjudicates reviewer choices from the blind A/B output review pack against the separate answer key.

- Pairs: `5`
- Judgments: `0`
- Pending: `5`
- Agreement rate: `n/a`
- Invalid decisions: `0`
- Answer keys revealed: `0`
- Pending/invalid answers hidden: `5`
- Reviewer checklist: `0` ready / `5` total

No reviewer decisions recorded yet.

Generate a template with `--write-template`, fill `winner_variant` with `A` or `B`, then rerun adjudication.
Expected winners stay hidden until a valid reviewer decision is recorded.

## Case Adjudication

| Case | Reviewer | Expected | Status | Confidence | Reason |
| --- | --- | --- | --- | ---: | --- |
| skill-package-contract | pending | hidden | pending |  |  |
| output-eval-expectation | pending | hidden | pending |  |  |
| ir-before-packaging | pending | hidden | pending |  |  |
| near-neighbor-boundary | pending | hidden | pending |  |  |
| file-backed-governed-package | pending | hidden | pending |  |  |

## Reviewer Checklist

| Case | Readiness | Answer key | Decision file |
| --- | --- | --- | --- |
| `skill-package-contract` | `awaiting-decision` | `hidden` | `reports/output_review_decisions.json` |
| `output-eval-expectation` | `awaiting-decision` | `hidden` | `reports/output_review_decisions.json` |
| `ir-before-packaging` | `awaiting-decision` | `hidden` | `reports/output_review_decisions.json` |
| `near-neighbor-boundary` | `awaiting-decision` | `hidden` | `reports/output_review_decisions.json` |
| `file-backed-governed-package` | `awaiting-decision` | `hidden` | `reports/output_review_decisions.json` |

### skill-package-contract

- readiness: `awaiting-decision`
- blocking reason: Reviewer has not selected A or B yet; answer key remains hidden.
- answer key visible: `false`
- blind pack: `reports/output_blind_review_pack.json`
- decisions: `reports/output_review_decisions.json`

#### Commands

- prepare_review_kit: `python3 scripts/yao.py output-review-kit`
- write_template: `python3 scripts/adjudicate_output_review.py --write-template`
- adjudicate: `python3 scripts/yao.py output-review`
- refresh_review_studio: `python3 scripts/yao.py review-studio .`

#### Required Fields

- winner_variant: A or B after reading only the blind review pack.
- confidence: Optional number from 0 to 1.
- reason: Short rationale; do not reveal baseline or with-skill labels before adjudication.

#### Privacy Contract

- Do not paste raw private user data into the decision reason.
- Do not open the answer key before reviewer choices are recorded.
- Leave winner_variant blank when the reviewer is not ready to decide.

### output-eval-expectation

- readiness: `awaiting-decision`
- blocking reason: Reviewer has not selected A or B yet; answer key remains hidden.
- answer key visible: `false`
- blind pack: `reports/output_blind_review_pack.json`
- decisions: `reports/output_review_decisions.json`

#### Commands

- prepare_review_kit: `python3 scripts/yao.py output-review-kit`
- write_template: `python3 scripts/adjudicate_output_review.py --write-template`
- adjudicate: `python3 scripts/yao.py output-review`
- refresh_review_studio: `python3 scripts/yao.py review-studio .`

#### Required Fields

- winner_variant: A or B after reading only the blind review pack.
- confidence: Optional number from 0 to 1.
- reason: Short rationale; do not reveal baseline or with-skill labels before adjudication.

#### Privacy Contract

- Do not paste raw private user data into the decision reason.
- Do not open the answer key before reviewer choices are recorded.
- Leave winner_variant blank when the reviewer is not ready to decide.

### ir-before-packaging

- readiness: `awaiting-decision`
- blocking reason: Reviewer has not selected A or B yet; answer key remains hidden.
- answer key visible: `false`
- blind pack: `reports/output_blind_review_pack.json`
- decisions: `reports/output_review_decisions.json`

#### Commands

- prepare_review_kit: `python3 scripts/yao.py output-review-kit`
- write_template: `python3 scripts/adjudicate_output_review.py --write-template`
- adjudicate: `python3 scripts/yao.py output-review`
- refresh_review_studio: `python3 scripts/yao.py review-studio .`

#### Required Fields

- winner_variant: A or B after reading only the blind review pack.
- confidence: Optional number from 0 to 1.
- reason: Short rationale; do not reveal baseline or with-skill labels before adjudication.

#### Privacy Contract

- Do not paste raw private user data into the decision reason.
- Do not open the answer key before reviewer choices are recorded.
- Leave winner_variant blank when the reviewer is not ready to decide.

### near-neighbor-boundary

- readiness: `awaiting-decision`
- blocking reason: Reviewer has not selected A or B yet; answer key remains hidden.
- answer key visible: `false`
- blind pack: `reports/output_blind_review_pack.json`
- decisions: `reports/output_review_decisions.json`

#### Commands

- prepare_review_kit: `python3 scripts/yao.py output-review-kit`
- write_template: `python3 scripts/adjudicate_output_review.py --write-template`
- adjudicate: `python3 scripts/yao.py output-review`
- refresh_review_studio: `python3 scripts/yao.py review-studio .`

#### Required Fields

- winner_variant: A or B after reading only the blind review pack.
- confidence: Optional number from 0 to 1.
- reason: Short rationale; do not reveal baseline or with-skill labels before adjudication.

#### Privacy Contract

- Do not paste raw private user data into the decision reason.
- Do not open the answer key before reviewer choices are recorded.
- Leave winner_variant blank when the reviewer is not ready to decide.

### file-backed-governed-package

- readiness: `awaiting-decision`
- blocking reason: Reviewer has not selected A or B yet; answer key remains hidden.
- answer key visible: `false`
- blind pack: `reports/output_blind_review_pack.json`
- decisions: `reports/output_review_decisions.json`

#### Commands

- prepare_review_kit: `python3 scripts/yao.py output-review-kit`
- write_template: `python3 scripts/adjudicate_output_review.py --write-template`
- adjudicate: `python3 scripts/yao.py output-review`
- refresh_review_studio: `python3 scripts/yao.py review-studio .`

#### Required Fields

- winner_variant: A or B after reading only the blind review pack.
- confidence: Optional number from 0 to 1.
- reason: Short rationale; do not reveal baseline or with-skill labels before adjudication.

#### Privacy Contract

- Do not paste raw private user data into the decision reason.
- Do not open the answer key before reviewer choices are recorded.
- Leave winner_variant blank when the reviewer is not ready to decide.

## Next Fixes

- Keep the blind review pack separate from the answer key until decisions are recorded.
- Treat disagreement cases as prompts for rubric tuning or output improvement.
- Add model-executed holdout runs after this human adjudication harness is stable.
