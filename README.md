# Codex Omics Skills

Codex Omics Skills is a repo-local Codex plugin plus Python CLI for reproducible omics analysis workflows. It helps Codex move from research-only assistance to structured analysis planning, validation, execution, and reporting.

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

`scvi-tools`, Java, Nextflow, nf-core, Singularity, and Apptainer are environment-managed dependencies. They are not forced into the default install because GPU and HPC stacks are site-specific.

## Quick Start

Use the safe workflow plan first. This writes a workflow manifest and report, but does not run analysis stages because the example is not approved by default.

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

The Codex plugin lives inside this repository:

```text
plugins/omics-analysis/
```

It contains the plugin descriptor, skills, schemas, and helper scripts. See [docs/plugin-installation.md](docs/plugin-installation.md) for how to use it as a repo-local plugin and how this differs from a packaged Codex plugin.

## Common Commands

```bash
omics-codex --help
omics-codex validate --config examples/scrna_qc/omics_run_spec.yaml
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
omics-codex workflow plan --config examples/workflows/scrna_qc_scvi.yaml
```

Heavy checks are opt-in:

```bash
source .venv/bin/activate
source envs/activate-nextflow.sh
RUN_HEAVY_OMICS=1 python -m pytest tests/heavy -q
```

`envs/activate-nextflow.sh` sets project-local Java/Nextflow and a project-local Singularity cache. nf-core Singularity examples use `envs/nextflow-singularity.config` for resumed validation and longer image pull timeouts.

See [docs/acceptance-matrix.md](docs/acceptance-matrix.md) and [docs/release-checklist.md](docs/release-checklist.md) for the current support boundary and release process.
