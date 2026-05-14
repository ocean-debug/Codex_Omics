# Plugin Installation

Codex Omics is distributed as a standard-ready Codex plugin package plus an `omics-codex` CLI backend. The plugin is the user-facing entry point; the CLI handles runtime work.

## Plugin Layout

The plugin root is:

```text
plugins/omics-analysis/
```

Important entries:

- `.codex-plugin/plugin.json`: plugin metadata.
- `skills/`: Codex skill instructions.
- `schemas/`: run spec and manifest schemas.
- `scripts/`: thin helper entrypoints that call the Python package runtime.

## Using It Locally

1. Clone the repository.
2. Install the Python package:

   ```bash
   python -m pip install -e ".[dev,nfcore,scverse]"
   ```

3. In Codex environments that support local plugins, register or load the plugin from:

   ```text
   <repo-root>/plugins/omics-analysis
   ```

4. Keep local Codex app state outside the repository. Do not commit `.agents/`, `.env`, remote SSH profiles, result folders, or virtual environments.

## Repo-Local vs Packaged Plugin

A repo-local plugin is still a Codex plugin. The difference is distribution:

- Repo-local: loaded from this checkout, versioned with the project, best for active development.
- Packaged plugin: published through a plugin distribution channel, best after APIs, docs, and environment assumptions are stable.

Codex Omics can be used repo-local during development or built as a plugin zip for standard loading. Omics execution still depends on site-managed tools such as scvi-tools, GPU PyTorch, Java, Nextflow, nf-core, Singularity, and Apptainer.

## Skill-to-CLI Flow

```text
Codex skill
  -> structured omics run spec
  -> omics-codex CLI
  -> src/omics_codex runtime
  -> manifest and report
```

The plugin should guide Codex to create, validate, and explain workflows. The Python package performs execution and provenance recording.

For user-facing analysis requests, plugin skills should drive this CLI path:

```bash
omics-codex doctor --json
omics-codex inspect-data --input /path/to/input
omics-codex route --prompt "..." --input /path/to/input --outdir results/<analysis> --out workflow.json
omics-codex workflow plan --config workflow.json
```

Only after the user reviews the generated spec should `approved: true` be set and `omics-codex workflow run --config workflow.json` be used.

## Toward a Standard Plugin

Before packaging this as a standard plugin, complete these checks:

- Public README and user guide are current.
- Example workflows run or plan without private paths.
- Sensitive information scan is clean.
- Smoke, unit, and integration tests pass in the documented remote environment.
- Heavy-test limitations are documented.
- Plugin metadata points to the public repository.
- `omics-codex doctor --json` correctly identifies UV, venv, conda/mamba, or system Python.
