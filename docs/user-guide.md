# User Guide

This guide covers the public v0.2.0 workflow for users who clone the repository and install the `omics-codex` CLI.

## Setup

Install the project in a Python environment:

```bash
python -m pip install -e ".[dev,nfcore,scverse]"
```

The `scvi` extra is intentionally empty. Install `scvi-tools` through the environment manager that matches your GPU stack. For UV environments, activate `.venv` first, then install `scvi-tools` and a PyTorch build matching the GPU node driver/CUDA stack.

Check the CLI:

```bash
omics-codex --help
omics-codex inspect-env --kind all
```

`inspect-env` returns a structured `status`, `blockers`, `warnings`, and `install_hints`. Fix blockers before running real workflows.

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

Real nf-core execution requires Java 17+, Nextflow, nf-core, git access or a pre-cached pipeline, and a container backend such as Singularity or Apptainer. If core runtime components are missing, the runner records a `blocked` manifest instead of failing without provenance. If a pipeline pull fails on a restricted compute node, pre-cache it with `nextflow pull nf-core/<pipeline>` on a node with network access and rerun the saved `command.sh` with `-resume`.

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

Before training, run:

```bash
omics-codex inspect-env --kind scvi
```

If GPU hardware is visible but `torch.cuda.is_available()` is false, install a CUDA-enabled PyTorch build that matches the node driver/CUDA stack. Codex Omics reports the mismatch and blocks only when the run explicitly requests GPU training.

## Real-data acceptance scripts

Reusable templates live in `scripts/acceptance/`:

```bash
export CODEX_OMICS_DATA_DIR=/path/to/data/test
export CODEX_OMICS_RESULT_DIR=/path/to/data/test/result
bash scripts/acceptance/run_scvi.sh
bash scripts/acceptance/run_bulk_rna.sh
bash scripts/acceptance/run_atac.sh
```

Expected input layout is `nf-core/rna`, `nf-core/atac`, `nf-core/genome`, and `scvi` under `CODEX_OMICS_DATA_DIR`. Generated subsets, specs, manifests, logs, and reports are written under separate result subfolders.

## Reports

Render a report from any run manifest:

```bash
omics-codex report --manifest results/workflows/scrna_qc_scvi/workflow_manifest.json
```

Reports summarize inputs, outputs, software versions, commands, errors, and next steps. For workflow runs, review both the aggregate workflow manifest and each stage manifest.
