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

- h5ad/10x, QC, mitochondrial filtering -> `single-cell-rna-qc`
- scVI, scANVI, totalVI, latent embeddings, batch correction -> `scvi-tools`
- FASTQ, nf-core, Nextflow, rnaseq, scrnaseq, riboseq, spatialvi, Visium, atacseq, sarek -> `nextflow-development`
- manifest/report summarization -> `omics-report`
- adding a new reusable omics workflow -> `skill-authoring-kit`

## Standard path

```text
check environment -> inspect input -> dry-run/plan -> user approval -> execute -> manifest/report
```

Use the selected skill's `scripts/check_environment.py` first. Keep long-running commands in dry-run/planned mode unless the user explicitly approves execution.
