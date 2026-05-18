---
name: omics-router
description: Route omics analysis requests to Codex-Omics plugin-local skills. Use when users ask for omics analysis but have not selected single-cell-rna-qc, scvi-tools, nextflow-development, reporting, or skill authoring; triggers include FASTQ, h5ad, 10x, scVI, nf-core, Nextflow, QC, integration, batch correction, and new omics workflows.
---

# Omics Router

Route to plugin-local skills only.

## Command

```bash
python plugins/omics-analysis/skills/omics-router/scripts/route_omics.py --prompt "run rnaseq" --input data --outdir results/route --json
```

## Routing

- Load `plugins/omics-analysis/skill_registry.yaml`.
- Score candidates using intent, input inventory, constraints, and registered task support.
- Return a structured `router_plan` with candidate scores, selected skill, blockers, warnings, and next actions.

## Standard path

```text
check environment -> inspect input -> dry-run/plan -> user approval -> execute -> manifest/report
```

Use the selected skill's `scripts/check_environment.py` first. Keep long-running commands in dry-run/planned mode unless the user explicitly approves execution.

## References

| Task | Reference |
|---|---|
| Explainable routing workflow | `references/workflow.md` |
