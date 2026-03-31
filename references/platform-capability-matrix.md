# Platform Capability Matrix

This matrix describes the current packaging targets and their support level.

| Target | Metadata Adapter | Output Contract | Snapshot Test | Notes |
| --- | --- | --- | --- | --- |
| `openai` | Yes | Yes | Yes | Generates `targets/openai/agents/openai.yaml` |
| `claude` | Yes | Yes | Yes | Generates `targets/claude/README.md` plus adapter metadata |
| `generic` | Yes | Yes | Yes | Uses neutral adapter metadata only |

## Current Support Model

- `openai`: strongest metadata adapter support
- `claude`: lightweight compatibility adapter, behavior still relies mainly on neutral source files
- `generic`: lowest-friction export for neutral Agent Skills consumers

## Explicit Non-Goals

This project does not yet implement:

- runtime-specific behavior transforms
- client SDK integration
- provider-specific execution logic

## Degradation Rule

If a target cannot support a source feature directly:

1. preserve the neutral source package
2. emit a minimal adapter
3. document the fallback in the target output
