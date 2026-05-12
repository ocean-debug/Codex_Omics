# New omics skill template

Use this reference when adding a new executable omics analysis capability.

## Minimum directory shape

```text
plugins/omics-analysis/skills/<new-skill>/
  SKILL.md
  agents/openai.yaml
  references/

plugins/omics-analysis/scripts/<new_domain>/
  run_<new_domain>.py

src/omics_codex/<new_domain>/
  __init__.py
  workflow.py

examples/<new_domain>/
  omics_run_spec.yaml

tests/unit/test_<new_domain>.py
tests/integration/test_<new_domain>_synthetic.py
```

## SKILL.md frontmatter

Use only `name` and `description` in frontmatter. Put trigger conditions in `description`, because Codex reads frontmatter before loading the skill body.

Example:

```yaml
---
name: spatial-transcriptomics-qc
description: Run spatial transcriptomics QC and preprocessing for Visium or AnnData inputs, including image/spatial coordinate validation, filtering, plots, reports, and run manifests. Use when users request spatial transcriptomics QC, Squidpy workflows, Visium preprocessing, or spatial AnnData validation.
---
```

## Runtime contract

Every executable workflow should:

- read `omics_run_spec.yaml`;
- validate input paths and required metadata;
- avoid overwriting raw inputs;
- write outputs under `outputs.outdir`;
- write `run_manifest.json`;
- write a concise `report.md`;
- emit structured errors using known error types where possible.

## CLI contract

Add a command under `omics-codex` when the workflow is user-facing:

```bash
omics-codex <domain> run --config omics_run_spec.yaml
omics-codex <domain> validate --config omics_run_spec.yaml
```

Thin wrappers under `plugins/omics-analysis/scripts/<domain>/` should call the Python package implementation.

## Testing contract

- Unit tests cover config validation, path logic, command generation, and output summaries.
- Integration tests use synthetic or tiny public data and must run on the remote validation environment.
- Heavy tests are opt-in and must not run by default.

## Documentation contract

Keep `SKILL.md` concise. Put longer scientific and implementation details in `references/` and link them from the skill body.
