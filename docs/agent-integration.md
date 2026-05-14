# Agent Integration

Codex Omics is designed for Codex first, but the same contract works for Claude Code and other coding agents that can run shell commands.

## Role split

- Plugin skills interpret user intent and decide which workflow to plan.
- `omics-codex` performs environment diagnosis, spec generation, execution, manifests, and reports.
- Agent code should not duplicate the analysis logic in temporary scripts unless a user explicitly asks for an experiment outside the plugin boundary.

## Required agent flow

```bash
omics-codex doctor --json
omics-codex inspect-data --input /path/to/input
omics-codex route --prompt "<goal>" --input /path/to/input --outdir results/<analysis> --out workflow.json
omics-codex workflow plan --config workflow.json
```

Run only after the user reviews the plan and sets `approved: true`.

## Environment installation

Agents must ask before installing heavy dependencies. Use `doctor --json` to detect whether the active environment is UV, venv, conda/mamba, or system Python, then present the matching install command.

Default installation targets:

- Python packages: active UV/venv/conda environment.
- Java/Nextflow: project-local `tools/`.
- Caches and results: project-local ignored folders.

System-wide installation is out of scope unless the user explicitly requests it.
