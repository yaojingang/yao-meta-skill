# Permission Policy

Permission metadata is generated from `reports/security_trust_report.json` and embedded into target adapters at package time. Governed releases also require explicit reviewer approvals in `security/permission_policy.json`.

Current v0 capabilities:

- `network`: scripts that perform outbound requests, bounded by `security/network_policy.json`.
- `file_write`: scripts that create, modify, delete, copy, move, or archive local files.
- `subprocess`: scripts that spawn local commands.
- `interactive`: scripts that prompt for user input.

Each packaged target must carry:

- `permission_contract`: platform-neutral capability summary and evidence path.
- `target_permission_contract`: target-specific representation, reviewer note, and native-enforcement status.

Each high-permission approval must include:

- `decision: approved`
- `reviewer`
- `scope`
- `reason`
- `expires_at`
- `evidence`
- `target_enforcement` for OpenAI, Claude, generic, and VS Code / Copilot packages

Review Studio exposes this as the `permission-gates` gate. Missing, invalid, or expired approvals block governed mode and stay reviewer-visible in lighter modes.

Install simulation also enforces this policy after archive extraction. `python3 scripts/simulate_install.py . --package-dir dist` reads the installed `security/permission_policy.json`, reads each installed target adapter's `target_permission_contract.declared_capabilities`, and fails when any target/capability pair lacks an active reviewer approval or target-specific enforcement note. This keeps package distribution from relying only on metadata presence in the source tree.

After packaging, run `python3 scripts/probe_runtime_permissions.py . --package-dir dist` to generate `reports/runtime_permission_probes.md` and `reports/runtime_permission_probes.json`. Review Studio exposes that evidence as the `permission-runtime` gate, separate from approval governance. A passing probe means target adapters make permission handling explicit and auditable; it does not claim client-native enforcement when the target only supports metadata fallback.

Current targets preserve permission semantics as metadata. They do not enforce permissions at runtime. Any future native installer or client integration must map these capabilities into that client's permission model rather than dropping them.
