# User Guide

This guide covers the public v0.1.0 workflow for users who clone the repository and install the `omics-codex` CLI.

## Setup

Install the project in a Python environment:

```bash
python -m pip install -e ".[dev,nfcore,scverse]"
```

The `scvi` extra is intentionally empty. Install `scvi-tools` through the environment manager that matches your GPU stack.

Check the CLI:

```bash
omics-codex --help
omics-codex inspect-env --kind all
```

## Workflow

Start with a safe plan:

```bash
omics-codex workflow plan --config examples/workflows/scrna_qc_scvi.yaml
```

The default workflow has `approved: false`, so it writes a plan without running analysis stages. Expected outputs:

- `results/workflows/scrna_qc_scvi/workflow_manifest.json`
- `results/workflows/scrna_qc_scvi/workflow_report.md`

Run only an approved workflow:

```bash
omics-codex workflow run --config examples/workflows/scrna_qc_scvi.approved.yaml
omics-codex workflow status --config examples/workflows/scrna_qc_scvi.approved.yaml
```

Resume skips only stages with an existing stage manifest whose status is `completed`:

```bash
omics-codex workflow resume --config examples/workflows/scrna_qc_scvi.approved.yaml
```

## nf-core

Build a Nextflow command without running the workflow:

```bash
omics-codex nfcore build-command --config examples/nfcore_rnaseq/omics_run_spec.yaml
```

Create a samplesheet from FASTQ files:

```bash
omics-codex nfcore make-samplesheet --pipeline rnaseq --input /path/to/fastq_dir --out samplesheet.csv
```

Inspect output inventory after a run:

```bash
omics-codex nfcore verify-output --pipeline rnaseq --outdir results/nfcore_rnaseq
```

Real nf-core execution requires a working Java 17+, Nextflow, nf-core, and container backend. If those are missing, the runner records a `blocked` manifest instead of failing without provenance.

## scRNA QC

Run the synthetic demo:

```bash
omics-codex scrna-qc run --config examples/scrna_qc/omics_run_spec.yaml
```

Supported input forms include `.h5ad`, 10x `.h5`, and 10x MTX directories. The QC runner checks raw-count suitability, computes standard QC metrics, supports MAD/fixed filters, and writes:

- filtered `.h5ad`
- QC summary JSON
- QC plots
- `run_manifest.json`
- `report.md`

## scVI

List and inspect available models:

```bash
omics-codex scvi list-models
omics-codex scvi inspect SCVI
```

Validate and train the synthetic SCVI demo:

```bash
omics-codex scvi validate --config examples/scvi/omics_run_spec.yaml
omics-codex scvi train --config examples/scvi/omics_run_spec.yaml
```

The curated adapters cover `SCVI`, `SCANVI`, `TOTALVI`, `PEAKVI`, and `MULTIVI`. Outputs include model files, trained AnnData or MuData, summary JSON, and a report.

## Reports

Render a report from any run manifest:

```bash
omics-codex report --manifest results/workflows/scrna_qc_scvi/workflow_manifest.json
```

Reports summarize inputs, outputs, software versions, commands, errors, and next steps. For workflow runs, review both the aggregate workflow manifest and each stage manifest.
