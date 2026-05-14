---
name: nf-core-universal
description: Plan, configure, validate, run, monitor, and summarize any nf-core pipeline through Nextflow using dynamic pipeline discovery, nextflow_schema.json parameter validation, safe command generation, samplesheet support, run manifests, and optional pipeline adapters. Use for FASTQ/BAM/CRAM workflows, RNA-seq, WGS/WES, ATAC-seq, ChIP-seq, methylation, metagenomics, SRA/GEO reanalysis, nf-core, Nextflow, and samplesheet creation.
---

# Universal nf-core Skill

## Required workflow

1. Create or read `omics_run_spec.yaml`. For common starts, prefer `omics-codex template create --name bulk-rna|atac` or `omics-codex route --prompt ... --input ... --outdir ...`.
2. Inspect environment with `omics-codex doctor --kind nfcore --json`.
3. Discover or inspect the pipeline with `omics-codex nfcore list` or `omics-codex nfcore inspect <pipeline>`.
4. Fetch the pipeline schema and validate params.
5. Generate or validate samplesheets; use enhanced adapters for `rnaseq`, `sarek`, and `atacseq` when possible.
6. Build the Nextflow command with `omics-codex nfcore build-command --config omics_run_spec.yaml`.
7. Run only when `execution.approved: true`; otherwise return command-only output.
8. Write `run_manifest.json`, `command.sh`, logs, and report paths.

## Never skip

- Record the pipeline version or explicit `latest` choice.
- Preserve input data and never overwrite result directories destructively.
- Prefer test profile or command-only mode before full execution.
- Use `-resume` unless the user asks for a clean run.

## When to read references

- Read `references/schema-driven-params.md` when configuring or validating pipeline params.
- Read `references/samplesheets.md` when creating or checking CSV/TSV inputs.
- Read `references/execution-policy.md` before running or approving a Nextflow job.

## Commands

```bash
omics-codex nfcore list
omics-codex doctor --kind nfcore --json
omics-codex template create --name bulk-rna --input fastq/ --outdir results/bulk_rna --out bulk_rna.workflow.json
omics-codex workflow plan --config bulk_rna.workflow.json
omics-codex nfcore inspect rnaseq
omics-codex nfcore create-params rnaseq --version latest --out params.json
omics-codex nfcore validate-params --pipeline rnaseq --params params.yaml
omics-codex nfcore make-samplesheet --pipeline rnaseq --input fastq/ --out samplesheet.csv
omics-codex nfcore build-command --config omics_run_spec.yaml
omics-codex nfcore verify-output --pipeline rnaseq --outdir results/nfcore_rnaseq
omics-codex nfcore run --config omics_run_spec.yaml
```
