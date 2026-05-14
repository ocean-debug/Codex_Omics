# Codex Omics Skills

Codex Omics Skills is a standard-ready Codex plugin package with `omics-codex` as its execution backend for reproducible omics analysis workflows. It helps Codex move from research-only assistance to structured analysis planning, validation, execution, and reporting.

Current capabilities:

- nf-core / Nextflow planning, parameter validation, samplesheets, and command generation.
- Single-cell RNA-seq QC with Scanpy/scverse conventions.
- scvi-tools model discovery, validation, lightweight training, and downstream summaries.
- Multi-stage workflow planning with safe defaults, manifests, and reports.
- Skill templates for adding more omics workflows later.

## Install

Clone the repository and install the CLI in an environment that already has the optional scientific stack you need:

```bash
git clone https://github.com/ocean-debug/Codex_Omics.git
cd Codex_Omics
python -m pip install -e ".[dev,nfcore,scverse]"
```

`scvi-tools`, GPU PyTorch, Java, Nextflow, nf-core, Singularity, and Apptainer are environment-managed dependencies. They are not forced into the default install because GPU and HPC stacks are site-specific.

Check the active environment before running real analyses or installing dependencies:

```bash
omics-codex doctor --json
```

Codex Omics detects UV `.venv`, standard `venv`, conda/mamba, and system Python environments. It reports missing components and matching install commands, but it does not install scVI, GPU PyTorch, Java, Nextflow, nf-core, or container tools unless the user explicitly approves.

## Quick Start

The v0.3 user path is:

```text
doctor -> inspect-data -> route/template -> workflow plan -> approved run -> report
```

Start by checking the active environment and input directory:

```bash
omics-codex inspect-env --kind all
omics-codex doctor --json
omics-codex inspect-data --input /path/to/input
```

Generate a safe draft workflow from natural language. Generated specs keep `approved: false`.

```bash
omics-codex route \
  --prompt "Create a bulk RNA workflow" \
  --input /path/to/fastq_dir \
  --outdir results/bulk_rna \
  --out bulk_rna.workflow.json
omics-codex workflow plan --config bulk_rna.workflow.json
```

Or start from a common template:

```bash
omics-codex template list
omics-codex template create --name scrna-qc-scvi --input /path/to/cells.h5ad --outdir results/scrna_scvi --out scrna_scvi.workflow.json
```

The bundled demo also plans safely. It writes a workflow manifest and report, but does not run analysis stages because the example is not approved by default.

```bash
omics-codex workflow plan --config examples/workflows/scrna_qc_scvi.yaml
```

Inspect the generated plan:

```bash
omics-codex workflow status --config examples/workflows/scrna_qc_scvi.yaml
omics-codex report --manifest results/workflows/scrna_qc_scvi/workflow_manifest.json
```

Only run the approved demo when you intentionally want to execute the synthetic QC-to-SCVI workflow:

```bash
omics-codex workflow run --config examples/workflows/scrna_qc_scvi.approved.yaml
```

## Codex Plugin

The Codex plugin lives inside this repository and can be packaged as a standard plugin zip:

```text
plugins/omics-analysis/
```

It contains the plugin descriptor, skills, schemas, and helper scripts. See [docs/plugin-package.md](docs/plugin-package.md) for building `codex-omics-plugin-v0.4.0.zip`, and [docs/plugin-installation.md](docs/plugin-installation.md) for repo-local loading.

## Common Commands

```bash
omics-codex --help
omics-codex doctor --json
omics-codex validate --config examples/scrna_qc/omics_run_spec.yaml
omics-codex inspect-data --input /path/to/input
omics-codex route --prompt "Analyze these sequencing reads" --input /path/to/input --outdir results/demo --out omics_run_spec.json
omics-codex template list
omics-codex template create --name bulk-rna --input /path/to/fastq_dir --out bulk_rna.workflow.json
omics-codex nfcore build-command --config examples/nfcore_rnaseq/omics_run_spec.yaml
omics-codex scrna-qc run --config examples/scrna_qc/omics_run_spec.yaml
omics-codex scvi list-models
omics-codex scvi validate --config examples/scvi/omics_run_spec.yaml
omics-codex workflow plan --config examples/workflows/scrna_qc_scvi.yaml
```

For command details and expected outputs, see [docs/user-guide.md](docs/user-guide.md).

## Validation

This project is developed on Windows but validated on a remote Linux/HPC environment. The generic validation contract is documented in [docs/remote-validation.md](docs/remote-validation.md).

Default validation:

```bash
source .venv/bin/activate
source envs/activate-nextflow.sh
python -m pytest tests/smoke -q
python -m pytest tests/unit -q
python -m pytest tests/integration -q
omics-codex inspect-env --kind nfcore
omics-codex inspect-env --kind scvi
omics-codex workflow plan --config examples/workflows/scrna_qc_scvi.yaml
```

Heavy checks are opt-in:

```bash
source .venv/bin/activate
source envs/activate-nextflow.sh
RUN_HEAVY_OMICS=1 python -m pytest tests/heavy -q
```

`envs/activate-nextflow.sh` sets project-local Java/Nextflow and a project-local Singularity cache. nf-core Singularity examples use `envs/nextflow-singularity.config` for resumed validation and longer image pull timeouts.

Real-data acceptance script templates are available under `scripts/acceptance/`. They use `CODEX_OMICS_DATA_DIR` and `CODEX_OMICS_RESULT_DIR` instead of hard-coded site paths, and keep generated data/results out of Git.

```bash
export CODEX_OMICS_DATA_DIR=/path/to/data/test
export CODEX_OMICS_RESULT_DIR=/path/to/data/test/result
export CODEX_OMICS_NFCORE_PROFILE=singularity
export CODEX_OMICS_MAX_CPUS=12
export CODEX_OMICS_MAX_MEMORY=48.GB
bash scripts/acceptance/run_all.sh
```

`run_all.sh` continues through scVI, bulk RNA, and ATAC checks, then writes `summary.json`. scVI and bulk RNA must complete; ATAC is allowed to remain failed or blocked only when the manifest contains a classified pipeline pull, config parse, or container pull failure with saved commands and logs.

See [docs/acceptance-matrix.md](docs/acceptance-matrix.md) and [docs/release-checklist.md](docs/release-checklist.md) for the current support boundary and release process.
