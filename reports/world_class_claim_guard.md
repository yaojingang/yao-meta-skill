# World-Class Claim Guard

Generated at: `2026-07-02`

## Summary

- decision: `claim-guard-pass-evidence-pending`
- ledger ready to claim world-class: `false`
- ledger pending evidence: `4`
- claim surfaces scanned: `201`
- JSON claim surfaces scanned: `97`
- metadata claim surfaces scanned: `98`
- package/runtime claim surfaces scanned: `17`
- violations: `0`
- overclaim guard active: `true`

This guard scans public claim surfaces, machine-readable reports, and package/runtime metadata for completion language that would contradict the world-class evidence ledger. It allows evidence planning and pending-state language, but blocks completion claims until the ledger is ready.

## Violations

| Path | Line | Rule | Excerpt |
| --- | ---: | --- | --- |
| `none` | 0 | `none` | none |

## Rules

| Rule | Reason |
| --- | --- |
| `ready-to-claim-true` | ready_to_claim_world_class cannot be true while ledger evidence is pending. |
| `world-class-ready-true` | world-class readiness cannot be claimed before accepted external and human evidence exists. |
| `json-world-class-ready-true` | machine-readable claim fields must remain false until the ledger is ready. |
| `completion-phrase` | completion language is blocked until the world-class ledger is accepted. |
| `zh-completion-phrase` | 中文完成态表述必须等到 ledger ready 后才能出现。 |
