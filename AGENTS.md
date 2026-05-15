# Codex-Omics Agent Contract

Use this repository as a plugin-only Codex omics skill collection.

## Default workflow

1. Select the relevant skill from `plugins/omics-analysis/skills/`.
2. Read that skill's `SKILL.md`.
3. Run its plugin-local `scripts/check_environment.py --json`.
4. Validate inputs with the skill-local validation script when available.
5. Start with `--dry-run` or planned mode.
6. Use `--approved true` only after the user explicitly approves execution.
7. Write and inspect `run_manifest.json` and `report.md`.

## Environment policy

- Detect UV, standard venv, conda/mamba, or system Python before suggesting installs.
- Do not install scvi-tools, GPU PyTorch, Java, Nextflow, nf-core, or container tools without explicit user approval.
- Prefer the active Python environment or project-local `tools/` when installation is approved.
- For unknown or system Python, generate an installation plan instead of mutating the environment.

## Execution policy

- Prefer plugin-local scripts over ad hoc analysis scripts.
- Keep protected data in the user-controlled workspace.
- Do not commit `.env`, private paths, caches, virtual environments, `tools/`, or analysis results.
