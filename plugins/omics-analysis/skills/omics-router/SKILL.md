---
name: omics-router
description: Route omics analysis requests to the correct Codex Omics skill and create a structured omics_run_spec.yaml. Use when the user asks for omics analysis but has not explicitly chosen nf-core, single-cell RNA QC, scvi-tools, reporting, or new skill authoring; triggers include FASTQ, h5ad, 10x, scVI, nf-core, Nextflow, QC, integration, batch correction, and adding a new omics workflow.
---

# Omics Router

## Required workflow

1. Inspect the user request, input paths, and desired outputs with `omics-codex inspect-data --input <path>` when a path is available.
2. Route to exactly one executable skill unless the user asks for a multi-stage workflow:
   - raw FASTQ/BAM/CRAM, SRA/GEO, Nextflow, nf-core -> `nf-core-universal`;
   - h5ad/10x, scRNA-seq QC, mitochondrial filtering -> `single-cell-rna-qc`;
   - scVI/scANVI/totalVI/PeakVI/MultiVI, latent integration, batch correction -> `scvi-universal`;
   - manifest/report summarization -> `omics-report`;
   - adding a new omics workflow skill -> `skill-authoring-kit`.
3. For multi-stage analysis, create a workflow config and use `omics-codex workflow plan|run|resume|status`.
4. Create or update `omics_run_spec.yaml` using `omics-codex route` or by following `plugins/omics-analysis/schemas/omics_run_spec.schema.json`.
5. Validate the run spec with `omics-codex validate --config omics_run_spec.yaml`.

## Safety

- Do not run long workflows without an explicit output directory, command preview, resume strategy, and approval.
- Keep protected human data local unless the user explicitly configures another destination.
- Do not invent missing required metadata; ask only for fields that cannot be derived from files or schema.

## Commands

```bash
omics-codex route --prompt prompt.txt --input ./data --out omics_run_spec.yaml
omics-codex inspect-data --input ./data
omics-codex validate --config omics_run_spec.yaml
omics-codex workflow plan --config examples/workflows/scrna_qc_scvi.yaml
```
