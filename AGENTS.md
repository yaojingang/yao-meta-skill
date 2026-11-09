# Agent Instructions

## Project Map

`yao-meta-skill` is the source repository for the Yao Meta Skill / Skill OS. Keep the root `SKILL.md` lean and route depth through the existing project layers:

- `SKILL.md`: public trigger surface, compact workflow, and Skill OS gates.
- `references/`: stable method doctrine and operating guidance.
- `scripts/`: executable logic, report generators, compilers, gates, and CLI entrypoints.
- `evals/`: trigger, output, packaging, semantic, and regression fixtures.
- `skill-ir/`: platform-neutral skill contract and examples.
- `agents/interface.yaml`: portable runtime and trust metadata.
- `security/`: script, dependency, network, permission, and trust policies.
- `registry/`: package metadata, installability evidence, and compatibility metadata.
- `skill_atlas/`: portfolio catalog, route overlap, ownership, stale-skill, and dependency evidence.
- `reports/`: generated review, trust, conformance, registry, overview, and release evidence.
- `docs/`: durable public docs such as migration notes and localized READMEs.

Profile identity and keyword classification must use the canonical `SKILL.md` frontmatter `name`. Use the directory name only when the frontmatter name is absent; moving a checkout must preserve profile results.

Skill Atlas discovery must skip `.yao/` at every project depth, keeping private backups, validation copies, evidence runs, and releases outside the portfolio catalog.

## Verification

Use `make ci-test` as the default full verification command before calling a change done. For focused work, run the smallest relevant target first, then finish with `make ci-test` when generated artifacts, packaging, registry, trust, or report UI changed.

Common focused checks:

- CLI changes: `python3 tests/verify_yao_cli.py`
- Operator UX changes: `python3 tests/verify_operator_ux.py`
- Skill overview report changes: `python3 tests/verify_skill_overview.py`
- Review Studio changes: `python3 tests/verify_review_studio.py`
- Trust or script inventory changes: `python3 tests/verify_trust_check.py`
- Packaging or registry changes: `python3 tests/verify_package_verification.py && python3 tests/verify_registry_audit.py`
- Phase-one trigger/context changes: `python3 tests/verify_phase1_trigger_holdout.py`
- Provider output changes: `python3 tests/verify_output_provider_matrix.py`

## Trusted evidence runs

Use `python3 scripts/yao.py evidence-build <skill_dir>` for an isolated dry run. Add `--publish` only after source and generated evidence have been committed and the target worktree is clean. Publishing creates an immutable bundle under the target Skill's `.yao/releases`, refreshes canonical report mirrors, and updates `reports/.current-run.json` last.

Official report consumers must use `scripts/evidence_resolver.py`. Keep `.yao/runs` and `.yao/releases` local. Commit the canonical pointer and artifact index when they form release evidence. If `.yao/publish-transaction.json` exists, dry runs must stay read-only and return `recovery-required`; use `evidence-build <skill_dir> --recover` for explicit recovery. Preserve the transaction marker, snapshot, and previous release bundle when recovery reports an integrity error. Packaged installs use a portable pointer and report index. See `references/evidence-publication.md` for the full protocol.

`--publish` checks clean source before provider execution. Provider answer text must remain under `.yao/runs/<run-id>/raw-outputs`; role-neutral reviewer copies stay under the run's `review-materials`, and the answer key stays under `private`. Releases carry commitments, hashes, redacted summaries, and role-neutral locators. Use `evidence-finalize-review` with three controlled reviewer packets and their registry; add `--resume` only for the same named run after an interrupted finalization. Never write `DEEPSEEK_API_KEY` to reports, fixtures, manifests, commands, or logs. Resolve Skill IR through `scripts/skill_ir_paths.py`; wildcard example scanning is forbidden.

Promote completed Provider evidence into tracked reports only with `python3 scripts/publish_provider_evidence.py . --source-run <ADJUDICATED_RUN_ID> --generated-at YYYY-MM-DD`. The exporter allowlists aggregate run data, adjudication results, commitments, and lineage. It excludes raw-output locators, Provider response identifiers, system fingerprints, reviewer packets, decision reasons, controlled submission identifiers, and the reviewer registry.

After source changes that affect scripts, package contents, trust evidence, Review Studio, registry metadata, or generated reports, refresh the release evidence before final sign-off:

```bash
GENERATED_AT="${GENERATED_AT:-$(date +%F)}"
python3 scripts/trust_check.py . --output-json reports/security_trust_report.json --output-md reports/security_trust_report.md
python3 scripts/compile_skill.py . --generated-at "$GENERATED_AT"
python3 scripts/cross_packager.py . --platform openai --platform claude --platform generic --platform vscode --expectations evals/packaging_expectations.json --output-dir dist --zip
python3 scripts/simulate_install.py . --package-dir dist --install-root dist/install-simulation --output-json reports/install_simulation.json --output-md reports/install_simulation.md --generated-at "$GENERATED_AT"
python3 scripts/registry_audit.py . --generated-at "$GENERATED_AT"
python3 scripts/verify_package.py . --package-dir dist --expectations evals/packaging_expectations.json --registry-json reports/registry_audit.json --output-json reports/package_verification.json --output-md reports/package_verification.md --require-zip --generated-at "$GENERATED_AT"
python3 scripts/registry_audit.py . --generated-at "$GENERATED_AT"
python3 scripts/upgrade_check.py . --previous-package-json registry/examples/yao-meta-skill-1.0.0.json --current-package-json reports/registry_audit.json --output-json reports/upgrade_check.json --output-md reports/upgrade_check.md --generated-at "$GENERATED_AT"
python3 scripts/render_adoption_drift_report.py . --generated-at "$GENERATED_AT"
python3 scripts/render_architecture_maintainability.py . --generated-at "$GENERATED_AT"
python3 scripts/python_compat_check.py . --generated-at "$GENERATED_AT"
python3 scripts/probe_runtime_permissions.py . --package-dir dist
python3 scripts/render_review_waivers.py . --generated-at "$GENERATED_AT"
python3 scripts/render_review_annotations.py .
python3 scripts/build_skill_atlas.py --workspace-root . --output-dir skill_atlas --report-html reports/skill_atlas.html --report-json reports/skill_atlas.json --today "$GENERATED_AT"
python3 scripts/render_world_class_evidence_plan.py . --generated-at "$GENERATED_AT"
python3 scripts/render_world_class_evidence_ledger.py . --generated-at "$GENERATED_AT"
python3 scripts/render_world_class_evidence_intake.py . --generated-at "$GENERATED_AT"
python3 scripts/render_world_class_submission_review.py . --generated-at "$GENERATED_AT"
python3 scripts/render_world_class_operator_runbook.py . --generated-at "$GENERATED_AT"
python3 scripts/render_world_class_claim_guard.py . --generated-at "$GENERATED_AT"
python3 scripts/render_daily_skillops_report.py . --generated-at "$GENERATED_AT"
python3 scripts/render_weekly_curator_report.py . --generated-at "$GENERATED_AT"
python3 scripts/render_skill_os2_audit.py . --generated-at "$GENERATED_AT"
python3 scripts/render_skill_os2_coverage.py . --generated-at "$GENERATED_AT"
python3 scripts/render_context_reports.py --generated-at "$GENERATED_AT"
python3 scripts/render_benchmark_reproducibility.py . --generated-at "$GENERATED_AT"
python3 scripts/render_skill_overview.py .
python3 scripts/render_skill_interpretation.py .
python3 scripts/render_review_viewer.py .
python3 scripts/render_world_class_preflight.py . --generated-at "$GENERATED_AT"
python3 scripts/render_review_studio.py . --output-html reports/review-studio.html --output-json reports/review-studio.json
python3 scripts/render_evidence_consistency.py . --generated-at "$GENERATED_AT"
```

`reports/output_execution_runs.json` is the immutable legacy provider baseline. Do not replace it with the local runner during routine report refresh. Phase 1 Provider evidence is generated inside `evidence-build` runs and promoted through the evidence publication protocol.

For final release evidence, commit source and generated package evidence first, then run the clean-lock reports from a clean worktree:

```bash
python3 scripts/render_context_reports.py --generated-at "$GENERATED_AT"
python3 scripts/render_benchmark_reproducibility.py . --generated-at "$GENERATED_AT"
python3 scripts/render_daily_skillops_report.py . --generated-at "$GENERATED_AT"
python3 scripts/render_weekly_curator_report.py . --generated-at "$GENERATED_AT"
python3 scripts/render_skill_overview.py .
python3 scripts/render_skill_interpretation.py .
python3 scripts/render_review_viewer.py .
python3 scripts/render_world_class_preflight.py . --generated-at "$GENERATED_AT"
python3 scripts/render_review_studio.py . --output-html reports/review-studio.html --output-json reports/review-studio.json
python3 scripts/render_evidence_consistency.py . --generated-at "$GENERATED_AT"
```

If `reports/benchmark_reproducibility.json` reports `release_lock_ready: false`, do not commit that benchmark as release evidence. Restore the transient dirty-lock reports, commit the source/generated evidence that caused the dirty state, and regenerate the clean-lock reports on the resulting clean tree.

Before delivering an archive, rebuild it after the final generated report refresh. Refresh the package, registry, and checksum-consuming evidence for those final bytes, then run `verify_package.py` again after all generation has finished. Its `archive-source-snapshot` gate must pass: included source and report files match the archive, with only the generated portable evidence pointer and index exempted. Keep archive-attestation consumers excluded from the archive to avoid checksum cycles.

Local sync into `~/.agents/skills.disabled/yao-meta-skill` or `~/.agents/skills/yao-meta-skill` must keep the install preflight enabled unless the user explicitly requests a diagnostic bypass. Build and verify the archive before invoking `make sync-local-install` or `make sync-active-install`. The sync targets preserve the attested archive. `scripts/sync_local_install.py` checks the archive bytes against `reports/package_verification.json`, installs those exact bytes, and refuses the copy when the hash, install simulation, or installer permission enforcement fails.

Clean test-only scratch directories after verification with `find tests -maxdepth 1 \( -name 'tmp' -o -name 'tmp_*' \) -type d -exec rm -rf {} +`. Do not clean unrelated untracked files.

## Boundaries

- Agent-facing authoring must use `scripts/yao.py` with an explicit target path. Resolve the canonical target before writing, require `--self` for Yao Meta Skill source or identity, and keep runtime cache/telemetry outside source and installed Skill directories. Standalone writer scripts must require an explicit `skill_dir`.
- Packaging may recursively replace only a recognized generated output directory. Refuse non-empty unmanaged destinations, and preserve Git-governed source selection for Skills located at repository roots or nested inside larger repositories.
- Do not expand root `SKILL.md` with long method text. Add durable guidance to `references/` or executable behavior to `scripts/`.
- Do not commit private customer work, one-off business skills, or local research reports unless the user explicitly promotes them into examples, fixtures, or public evidence.
- Treat untracked files outside `tests/tmp_*` as user work. Do not delete, move, or overwrite them without explicit approval.
- Do not hand-edit generated evidence when a generator exists. Regenerate the source report instead.
- Do not introduce external chart or UI dependencies for static reports unless the user explicitly approves them. The current report pattern is static HTML, local CSS, and inline SVG.
- Keep package artifacts, registry checksums, install simulation, trust reports, overview reports, and Review Studio evidence in sync after source changes.

## Hotspot Ownership

- `scripts/yao.py`: unified CLI orchestration. Keep command behavior stable; move pure config and side-effect-free helpers into small internal modules.
- `scripts/render_skill_overview.py`: v2 bilingual skill overview report. Preserve `reports/skill-overview.html` / `.json`, `body data-report-lang="zh-CN"`, default Simplified Chinese, English switch, and inline-chart/no-external-dependency behavior.
- `scripts/skill_report_layout.py` plus `assets/skill-overview.css` / `assets/skill-overview.js`: overview report layout contract and inline assets. Keep the generated report single-file at render time, but keep long CSS/JS source in `assets/` instead of embedding it inside Python.
- `scripts/render_review_studio.py`: Review Studio gate orchestration. Keep gate scoring, evidence links, and action generation separate from layout helpers.
- `scripts/review_studio_layout.py` plus `assets/review-studio.css`: Review Studio static layout and CSS contract. Keep the generated report single-file at render time, but keep long CSS source in `assets/` instead of embedding it inside Python.
- `scripts/review_studio_formatting.py`: Review Studio dictionary-to-panel formatting and Chinese metric labels.
- `scripts/review_studio_gates.py`: Review Studio gate evaluation, release decision scoring, and gate status labels.
- `scripts/render_skill_os2_audit.py`: requirement-by-requirement Skill OS 2.0 completion audit. Keep local evidence, human-required gaps, and external-required gaps separate so reports do not overclaim world-class readiness.
- `scripts/render_world_class_evidence_plan.py`: executable evidence task plan for the remaining world-class readiness gaps. Keep provider, human, native-permission, and real-client telemetry evidence requirements concrete without marking planned work as complete.
- `scripts/render_world_class_evidence_ledger.py`: machine-checkable acceptance ledger for the remaining world-class evidence gaps. Keep anti-overclaim guards explicit so planned work, metadata fallbacks, pending review, and local command runners never count as final evidence.
- `scripts/render_world_class_evidence_intake.py`: intake validator for external and human world-class evidence packets. Real submissions must reference concrete local aggregate artifacts with matching SHA-256 digests; templates may stay hash-free and must not count as evidence.
- `scripts/world_class_evidence_contract.py`: shared intake contract and artifact-integrity validator. Keep ledger, intake, and submission review aligned so source evidence cannot be accepted without a valid real submission and matching artifact SHA-256 checks.
- `scripts/render_world_class_submission_review.py`: read-only queue for external and human evidence packets after intake validation. Keep it from accepting evidence; it may only compare packet validity, source evidence checks, and ledger state.
- `scripts/render_world_class_operator_runbook.py`: operator-facing world-class evidence runbook. Keep it as coordination guidance only; it must not accept evidence or flip world-class readiness.
- `scripts/render_world_class_preflight.py` plus `scripts/world_class_preflight_layout.py`: operator-facing collection preflight for world-class evidence. Keep data assembly and CLI emission in the renderer, keep HTML layout in the layout helper, keep environment and external prerequisite checks redacted, and never let preflight count as accepted evidence.
- `scripts/render_benchmark_reproducibility.py`: release-facing benchmark reproducibility manifest. Keep methodology sections, required artifacts, failure disclosure, reproduction commands, and world-class limitations machine-checkable.
- `scripts/skill_report_model.py`, `scripts/skill_report_metrics.py`, `scripts/skill_report_charts.py`: skill overview data model, scoring, and inline SVG chart generation.
- `scripts/yao_cli_config.py`: CLI target maps, archetype heuristics, diagnosis copy, and side-effect-free shaping helpers.
- `scripts/yao_cli_parser.py`: CLI argparse command surface, flags, choices, and command handler binding.
- `scripts/yao_cli_operator_commands.py`: read-only operator diagnostics for active install status, localized homepage sync, and PR review reports. Keep install checks non-mutating, docs sync explicit, and PR review free of merge/write actions.
- `scripts/yao_cli_parser_operator.py`: argparse surface for operator UX commands. Keep command names stable and route all behavior into `yao_cli_operator_commands.py`.
- `scripts/yao_cli_telemetry.py`: opt-in metadata-only CLI run telemetry. Keep it free of prompt, argument, output, transcript, note, or message capture.
- `scripts/import_telemetry_events.py`: external telemetry importer. Validate the whole input before appending events, and keep raw prompt/output/transcript/message/note fields blocked.
- `scripts/emit_telemetry_event.py`: external client telemetry emitter. It may append one normalized metadata event to a local spool, but must never accept or write raw prompt, output, transcript, message, note, argument, or private content.
- `scripts/render_telemetry_hook_recipes.py`: client hook recipe report. Keep recipes metadata-only, mark native auto-capture as unclaimed unless a real client integration exists, and preserve dry-run commands for Browser/Chrome/IDE/wrapper adapters.
- `scripts/telemetry_native_host.py`: Browser/Chrome Native Messaging telemetry bridge. Preserve length-prefixed stdio behavior, raw-content blocking, and launcher/manifest generation tests.

New helper modules that are imported by CLI/report scripts but are not standalone commands must declare:

```python
SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by <caller> for <purpose>."
```

Then update `tests/verify_trust_check.py` so help-smoke coverage and trust reporting stay explicit.

## Long-Running Work

Stop and surface state instead of retrying when any of these happens:

- Two consecutive checkpoints show no new files, no new passing test, and no new diagnosis.
- The same command fails with the same error three times.
- A required credential, network, package registry, or external service is unavailable.
- A generated package hash, registry checksum, install simulation, or trust summary cannot be reconciled after regeneration.

When stopping, report the exact command, current `git status --short --branch -uall`, and the smallest next diagnostic.
