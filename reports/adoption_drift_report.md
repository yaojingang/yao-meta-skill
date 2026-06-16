# Adoption And Drift Report

Local-first, metadata-only telemetry for skill operations. Raw prompts, outputs, transcripts, and notes are not allowed in the event stream.

## Summary

- Events: `1`
- Adoption samples: `1`
- Activation events: `1`
- Adoption rate: `100.0`
- Missed trigger signals: `0`
- Bad output signals: `0`
- Script error signals: `0`
- Review overdue signals: `0`
- Risk band: `low`

## Privacy Contract

- Storage is local-first.
- Events are metadata-only.
- Raw user prompts, model outputs, transcripts, notes, and messages are blocked.
- Distributed packages should include this aggregate report, not raw `reports/telemetry_events.jsonl`.

## Adoption By Skill

| Skill | Events | Adoption Samples | Accepted | Edited | Rejected | Missed | Adoption Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `yao-meta-skill` | 1 | 1 | 1 | 0 | 0 | 0 | 100.0 |

## Next Iteration Candidates

- No telemetry-driven iteration candidate yet.

## Recent Metadata Events

- `2026-06-13T10:00:00Z` `yao-meta-skill` event=`skill_activation` source=`manual` command=`unknown` activation=`explicit` outcome=`accepted` failure=`none`
