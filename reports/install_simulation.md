# Install Simulation

- OK: `True`
- Package directory: `tests/tmp_review_studio/dist`
- Archive extracted: `True`
- Entrypoint loaded: `True`
- Manifest loaded: `True`
- Interface loaded: `True`
- Adapters readable: `4`
- Installer permissions enforced: `12`
- Installer permission failures: `0`
- Failures: `0`
- Warnings: `0`

## Checks

| Check | Status | Detail |
| --- | --- | --- |
| `archive-present` | `pass` | Package archive exists: tests/tmp_review_studio/dist/yao-meta-skill.zip |
| `archive-safe-paths` | `pass` | Archive has no absolute or parent-traversal entries |
| `single-top-level` | `pass` | Archive top-level directory is yao-meta-skill |
| `entrypoint-load` | `pass` | Installed SKILL.md frontmatter is readable |
| `entrypoint-name` | `pass` | Installed SKILL.md name matches package directory |
| `entrypoint-description` | `pass` | Installed SKILL.md description is present |
| `manifest-load` | `pass` | Installed manifest.json is readable |
| `manifest-name` | `pass` | Installed manifest name matches package manifest |
| `manifest-version` | `pass` | Installed manifest version matches package manifest |
| `interface-load` | `pass` | Installed agents/interface.yaml is readable |
| `overview-report` | `pass` | Installed overview report is present |
| `review-studio-report` | `pass` | Installed Review Studio report is present |
| `adapter-claude` | `pass` | claude adapter is readable after package install simulation |
| `adapter-claude-name` | `pass` | claude adapter name matches package manifest |
| `adapter-generic` | `pass` | generic adapter is readable after package install simulation |
| `adapter-generic-name` | `pass` | generic adapter name matches package manifest |
| `adapter-openai` | `pass` | openai adapter is readable after package install simulation |
| `adapter-openai-name` | `pass` | openai adapter name matches package manifest |
| `adapter-vscode` | `pass` | vscode adapter is readable after package install simulation |
| `adapter-vscode-name` | `pass` | vscode adapter name matches package manifest |
| `permission-policy-load` | `pass` | Installed permission policy is readable |
| `permission-claude-contract` | `pass` | claude adapter exposes target permission contract for installer enforcement |
| `permission-claude-file_write-approved` | `pass` | claude capability file_write has active reviewer approval |
| `permission-claude-file_write-target-enforcement` | `pass` | claude capability file_write has target enforcement note |
| `permission-claude-network-approved` | `pass` | claude capability network has active reviewer approval |
| `permission-claude-network-target-enforcement` | `pass` | claude capability network has target enforcement note |
| `permission-claude-subprocess-approved` | `pass` | claude capability subprocess has active reviewer approval |
| `permission-claude-subprocess-target-enforcement` | `pass` | claude capability subprocess has target enforcement note |
| `permission-generic-contract` | `pass` | generic adapter exposes target permission contract for installer enforcement |
| `permission-generic-file_write-approved` | `pass` | generic capability file_write has active reviewer approval |
| `permission-generic-file_write-target-enforcement` | `pass` | generic capability file_write has target enforcement note |
| `permission-generic-network-approved` | `pass` | generic capability network has active reviewer approval |
| `permission-generic-network-target-enforcement` | `pass` | generic capability network has target enforcement note |
| `permission-generic-subprocess-approved` | `pass` | generic capability subprocess has active reviewer approval |
| `permission-generic-subprocess-target-enforcement` | `pass` | generic capability subprocess has target enforcement note |
| `permission-openai-contract` | `pass` | openai adapter exposes target permission contract for installer enforcement |
| `permission-openai-file_write-approved` | `pass` | openai capability file_write has active reviewer approval |
| `permission-openai-file_write-target-enforcement` | `pass` | openai capability file_write has target enforcement note |
| `permission-openai-network-approved` | `pass` | openai capability network has active reviewer approval |
| `permission-openai-network-target-enforcement` | `pass` | openai capability network has target enforcement note |
| `permission-openai-subprocess-approved` | `pass` | openai capability subprocess has active reviewer approval |
| `permission-openai-subprocess-target-enforcement` | `pass` | openai capability subprocess has target enforcement note |
| `permission-vscode-contract` | `pass` | vscode adapter exposes target permission contract for installer enforcement |
| `permission-vscode-file_write-approved` | `pass` | vscode capability file_write has active reviewer approval |
| `permission-vscode-file_write-target-enforcement` | `pass` | vscode capability file_write has target enforcement note |
| `permission-vscode-network-approved` | `pass` | vscode capability network has active reviewer approval |
| `permission-vscode-network-target-enforcement` | `pass` | vscode capability network has target enforcement note |
| `permission-vscode-subprocess-approved` | `pass` | vscode capability subprocess has active reviewer approval |
| `permission-vscode-subprocess-target-enforcement` | `pass` | vscode capability subprocess has target enforcement note |

## Failures

- None

## Warnings

- None
