# Yao Meta Skill

[![English](https://img.shields.io/badge/Docs-English-black)](README.md)
[![中文](https://img.shields.io/badge/Docs-%E4%B8%AD%E6%96%87-red)](docs/README.zh-CN.md)
[![日本語](https://img.shields.io/badge/Docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-blue)](docs/README.ja-JP.md)
[![Français](https://img.shields.io/badge/Docs-Fran%C3%A7ais-green)](docs/README.fr-FR.md)
[![Русский](https://img.shields.io/badge/Docs-%D0%A0%D1%83%D1%81%D1%81%D0%BA%D0%B8%D0%B9-purple)](docs/README.ru-RU.md)

`yao-meta-skill` is a meta-skill for building other agent skills.

It turns rough workflows, transcripts, prompts, notes, and runbooks into reusable skill packages with:

- a clear trigger surface
- a lean `SKILL.md`
- optional references, scripts, and evals
- neutral source metadata plus client-specific adapters

## Quick Start

1. Describe the workflow, prompt set, or repeated task you want to turn into a skill.
2. Use `yao-meta-skill` to generate or improve the package in scaffold, production, or library mode.
3. Run `context_sizer.py`, `trigger_eval.py`, and `cross_packager.py` as needed to validate and export the result.

## What It Does

This project helps you create, refactor, evaluate, and package skills as durable capability bundles rather than one-off prompts.

The design logic is simple:

1. Capture the real recurring job behind the user's request.
2. Set a clean skill boundary so one package does one coherent job.
3. Optimize the trigger description before over-writing the body.
4. Keep the main skill file small and move details into references or scripts.
5. Add quality gates only when they pay for themselves.
6. Export compatibility artifacts only for the clients you actually need.

## Why It Exists

Most teams keep valuable operating knowledge scattered across chats, personal prompts, oral habits, and undocumented workflows. This project converts that hidden process knowledge into:

- discoverable skill packages
- repeatable execution flows
- lower-context instructions
- reusable team assets
- compatibility-ready distributions

## Repository Structure

```text
yao-meta-skill/
├── SKILL.md
├── README.md
├── LICENSE
├── .gitignore
├── agents/
│   └── interface.yaml
├── references/
├── scripts/
└── templates/
```

## Core Components

### `SKILL.md`

The main skill entrypoint. It defines the trigger surface, operating modes, compact workflow, and output contract.

### `agents/interface.yaml`

The neutral metadata source of truth. It stores display and compatibility metadata without locking the source tree to one vendor-specific path.

### `references/`

Long-form material that should not bloat the main skill file. This includes design rules, evaluation guidance, compatibility strategy, and quality rubrics.

### `scripts/`

Utility scripts that make the meta-skill operational:

- `trigger_eval.py`: checks whether a trigger description is too broad or too weak
- `context_sizer.py`: estimates context weight and warns when the initial load gets too large
- `cross_packager.py`: builds client-specific export artifacts from the neutral source package

### `templates/`

Starter templates for simple and more advanced skill packages.

## How To Use

### 1. Use the skill directly

Invoke `yao-meta-skill` when you want to:

- create a new skill
- improve an existing skill
- add evals to a skill
- convert a workflow into a reusable package
- prepare a skill for wider team adoption

### 2. Generate a new skill package

The typical flow is:

1. describe the workflow or capability
2. identify trigger phrases and outputs
3. choose scaffold, production, or library mode
4. generate the package
5. run the sizing and trigger checks if needed
6. export target-specific compatibility artifacts

### 3. Export compatibility artifacts

Examples:

```bash
python3 scripts/cross_packager.py ./yao-meta-skill --platform openai --platform claude --zip
python3 scripts/context_sizer.py ./yao-meta-skill
python3 scripts/trigger_eval.py --description "Create and improve agent skills..." --cases ./cases.json
```

## Advantages

- **Neutral by default**: source files stay vendor-neutral, while adapters are generated only when needed.
- **Context efficient**: the project explicitly pushes detail out of the main skill file.
- **Evaluation-aware**: trigger and sizing checks are built into the workflow.
- **Reusable**: the output is a package, not just a paragraph of prompt text.
- **Portable**: compatibility is handled through packaging rather than duplicating source files for every client.

## Best Fit

This project is best for:

- agent builders
- internal tooling teams
- prompt engineers moving toward structured skills
- organizations building reusable skill libraries

## Documentation

| Language | Entry |
| --- | --- |
| English | [README.md](README.md) |
| 中文 | [docs/README.zh-CN.md](docs/README.zh-CN.md) |
| 日本語 | [docs/README.ja-JP.md](docs/README.ja-JP.md) |
| Français | [docs/README.fr-FR.md](docs/README.fr-FR.md) |
| Русский | [docs/README.ru-RU.md](docs/README.ru-RU.md) |

## License

MIT. See [LICENSE](LICENSE).
