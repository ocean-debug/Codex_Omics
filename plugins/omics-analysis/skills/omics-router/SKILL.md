---
name: omics-router
description: Route omics analysis requests to the correct Codex Omics skill and create a structured omics_run_spec.yaml. Use when the user asks for omics analysis but has not explicitly chosen nf-core, single-cell RNA QC, scvi-tools, reporting, or new skill authoring; triggers include FASTQ, h5ad, 10x, scVI, nf-core, Nextflow, QC, integration, batch correction, and adding a new omics workflow.
---

# Omics Router

## Required workflow

1. Inspect the user request, environment, input paths, and desired outputs with `omics-codex inspect-env --kind all` and `omics-codex inspect-data --input <path>` when a path is available.
2. Route to exactly one executable skill unless the user asks for a multi-stage workflow:
   - raw FASTQ/BAM/CRAM, SRA/GEO, Nextflow, nf-core -> `nf-core-universal`;
   - h5ad/10x, scRNA-seq QC, mitochondrial filtering -> `single-cell-rna-qc`;
   - scVI/scANVI/totalVI/PeakVI/MultiVI, latent integration, batch correction -> `scvi-universal`;
   - manifest/report summarization -> `omics-report`;
   - adding a new omics workflow skill -> `skill-authoring-kit`.
3. For multi-stage analysis, create a workflow config and use `omics-codex workflow plan|run|resume|status`.
4. Create or update a safe spec using `omics-codex route --outdir <results>` or `omics-codex template create`; generated specs must keep `approved: false`.
5. Validate single-run specs with `omics-codex validate --config omics_run_spec.yaml` or plan workflow specs with `omics-codex workflow plan --config workflow.json`.

## Safety

- Do not run long workflows without an explicit output directory, command preview, resume strategy, and approval.
- Keep protected human data local unless the user explicitly configures another destination.
- Do not invent missing required metadata; ask only for fields that cannot be derived from files or schema.

## Commands

```bash
omics-codex inspect-env --kind all
omics-codex inspect-data --input ./data
omics-codex route --prompt prompt.txt --input ./data --outdir results/demo --out workflow.json
omics-codex template list
omics-codex template create --name bulk-rna --input ./fastq --outdir results/bulk_rna --out bulk_rna.workflow.json
omics-codex validate --config omics_run_spec.yaml
omics-codex workflow plan --config workflow.json
```
