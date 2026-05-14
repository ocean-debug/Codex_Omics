# Codex Omics Agent Contract

Use this repository as a standard plugin package with `omics-codex` as the execution backend.

## Default workflow

1. Run `omics-codex doctor --json` before planning installation or analysis.
2. Run `omics-codex inspect-data --input <path>` before generating specs from user data.
3. Generate safe specs with `omics-codex route` or `omics-codex template create`.
4. Keep `approved: false` until the user explicitly approves execution.
5. Use `omics-codex workflow plan` before long or expensive runs.
6. Render reports from manifests with `omics-codex report`.

## Environment policy

- Do not assume UV. Detect UV `.venv`, normal `venv`, conda/mamba, or system Python.
- Do not install scVI, GPU PyTorch, Java, Nextflow, nf-core, or container tools without explicit user approval.
- If the user approves installation, only modify the active Python environment or project-local `tools/` by default.
- For unknown or system Python, generate an installation plan instead of mutating the environment.

## Execution policy

- Prefer the plugin skills and `omics-codex` CLI over ad hoc analysis scripts.
- Keep protected data in the user-controlled workspace.
- Do not commit `.env`, private paths, caches, virtual environments, `tools/`, or analysis results.
- ATAC true execution is not a default validation blocker unless the user explicitly asks for it.
