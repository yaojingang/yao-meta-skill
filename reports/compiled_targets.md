# Compiled Targets

- OK: `True`
- Targets: `5`
- Pass: `5`
- Warn: `0`
- Block: `0`

## Target Transforms

| Target | Status | Native Surface | Adapter Mode | Permissions | Degradation | Generated Files |
| --- | --- | --- | --- | --- | --- | --- |
| `openai` | `pass` | OpenAI-style interface metadata plus neutral Agent Skills source | `metadata-adapter` | `network, file_write, subprocess` | `metadata-adapter` | targets/openai/adapter.json, targets/openai/agents/openai.yaml |
| `claude` | `pass` | Claude-compatible neutral source folder with adapter notes | `neutral-source-plus-adapter` | `network, file_write, subprocess` | `neutral-source-plus-adapter` | targets/claude/adapter.json, targets/claude/README.md |
| `generic` | `pass` | Agent Skills compatible neutral package | `agent-skills-compatible` | `network, file_write, subprocess` | `neutral-source` | targets/generic/adapter.json |
| `agent-skills-compatible` | `pass` | Agent Skills standard source tree | `neutral-agent-skills-source` | `network, file_write, subprocess` | `neutral-source` | SKILL.md, agents/interface.yaml |
| `vscode` | `pass` | VS Code/Copilot Agent Skills project or user scope | `vscode-agent-skills-adapter` | `network, file_write, subprocess` | `agent-skills-source-with-vscode-notes` | targets/vscode/adapter.json, targets/vscode/README.md |

## Native Behavior Contracts

### openai

- Native surface: OpenAI-style interface metadata plus neutral Agent Skills source
- Activation: Use frontmatter description for catalog routing and targets/openai/agents/openai.yaml for display name, default prompt, and compatibility metadata.
- Resources: Ship the neutral source tree and expose OpenAI-facing interface metadata as a generated companion file.
- Scripts: Keep scripts as local package resources; expose help-smoke and permission metadata for reviewer approval before execution.
- Permission enforcement: `metadata-only`; native enforcement `False`
- Review artifacts: targets/openai/agents/openai.yaml, targets/openai/adapter.json, reports/review-studio.html

### claude

- Native surface: Claude-compatible neutral source folder with adapter notes
- Activation: Use SKILL.md frontmatter description as the primary activation contract and adapter.json for review metadata.
- Resources: Preserve the source tree directly; write target notes in targets/claude/README.md.
- Scripts: Scripts remain local package resources and must be reviewed through trust and permission reports before use.
- Permission enforcement: `metadata-fallback`; native enforcement `False`
- Review artifacts: targets/claude/README.md, targets/claude/adapter.json, reports/review-studio.html

### generic

- Native surface: Agent Skills compatible neutral package
- Activation: Use SKILL.md name and description; consumers decide automatic or manual activation.
- Resources: Preserve references, scripts, assets, evals, reports, and adapter metadata as relative package resources.
- Scripts: Expose script and permission metadata for downstream clients or installers to enforce.
- Permission enforcement: `consumer-enforced-or-metadata-only`; native enforcement `False`
- Review artifacts: targets/generic/adapter.json, reports/review-studio.html

### agent-skills-compatible

- Native surface: Agent Skills standard source tree
- Activation: Use SKILL.md frontmatter name and description for progressive disclosure.
- Resources: Keep optional directories as relative resources next to SKILL.md.
- Scripts: Scripts remain local optional resources and should advertise --help when executable.
- Permission enforcement: `consumer-enforced-or-metadata-only`; native enforcement `False`
- Review artifacts: SKILL.md, agents/interface.yaml, reports/review-studio.html

### vscode

- Native surface: VS Code/Copilot Agent Skills project or user scope
- Activation: Use folder name plus SKILL.md name/description; keep description under platform limits.
- Resources: Install as project or user scoped skill source, preserving relative references and scripts.
- Scripts: Scripts require workspace trust and operator/client approval outside this compiler.
- Permission enforcement: `client-or-workspace-trust`; native enforcement `False`
- Review artifacts: SKILL.md, agents/interface.yaml, reports/review-studio.html


## Failures

- None

## Warnings

- None
