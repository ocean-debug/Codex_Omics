---
name: skill-authoring-kit
description: Create new Codex-Omics plugin-local analysis skills with SKILL.md, scripts, references, schemas, examples, smoke tests, manifests, and reports. Use when adding bulk RNA differential expression, enrichment, spatial transcriptomics, cell-cell communication, GRN analysis, perturbation analysis, multi-omics integration, or other bioinformatics skills.
---

# Skill Authoring Kit

Create plugin-local skills. Do not add a backend CLI command.

If the work is only adding another nf-core pipeline to the existing
`nextflow-development` skill, use
`plugins/omics-analysis/skills/nextflow-development/references/nfcore-workflow-adapter-template.md`
instead of creating a new skill.

## Required structure

```text
plugins/omics-analysis/skills/<new-skill>/
  SKILL.md
  scripts/
  references/
  schemas/
  examples/
```

## Rules

- Scripts must run from the plugin package without installing this repository as a Python package.
- Scripts may import `plugins/omics-analysis/scripts/common/`.
- Scripts must not import the removed backend package.
- Default to dry-run/planned behavior.
- Require `--approved true` for long-running execution, installation, downloads, or destructive actions.
- Write `run_manifest.json` and `report.md` when possible.

## Minimum scripts

```text
scripts/check_environment.py
scripts/validate_input.py
scripts/run.py
scripts/summarize.py
```

Read `references/new-skill-template.md` for the detailed template.

## References

| Task | Reference |
|---|---|
| Authoring workflow diagram | `references/workflow.md` |
| New skill template | `references/new-skill-template.md` |
