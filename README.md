# Codex Omics

Codex Omics is a Codex plugin for omics analysis. It helps Codex move beyond research assistance and ad hoc scripting into reproducible workflows: diagnose the environment, inspect input data, generate a safe analysis plan, execute approved stages, and produce manifests and reports.

The project has two layers:

- `plugins/omics-analysis/`: the Codex plugin bundle, including plugin metadata, skills, schemas, references, and thin wrapper scripts.
- `omics-codex`: the Python execution backend used by the plugin for environment diagnostics, spec generation, parameter validation, execution, manifests, and reports.

The plugin is the primary entry point. The CLI is the backend capability layer. Users can run the CLI directly for debugging, but this project is designed as an omics analysis plugin for Codex and other agent workflows, not as a standalone analysis platform.

## Capabilities

Codex Omics v0.4.0 focuses on three analysis tracks:

- **nf-core / Nextflow**: inspect nf-core readiness, generate samplesheets, validate parameters, build Nextflow commands, and plan or run workflows such as `rnaseq`, `atacseq`, and `sarek`.
- **single-cell RNA-seq QC**: read `.h5ad`, 10x H5, and 10x MTX inputs; run scRNA-seq QC; and save filtered AnnData, summaries, plots, manifests, and reports.
- **scvi-tools**: discover available scVI family models, validate AnnData, run lightweight training, and summarize downstream outputs such as latent embeddings, neighbors, UMAP, Leiden clusters, and model metadata.

It also provides:

- `doctor` environment diagnostics for UV `.venv`, standard `venv`, conda/mamba, and system Python environments.
- `inspect-data` input inspection for h5ad files, FASTQ directories, reference files, and related omics inputs.
- `route` and `template` commands for generating safe run specs or workflow specs from natural language or common templates.
- `workflow plan|run|resume|status` for multi-stage workflow orchestration.
- `report` for rendering reports from manifests.

## Safe Defaults

Generated workflows default to:

```yaml
approved: false
```

This means Codex should only generate plans, commands, output paths, log paths, and resume strategies by default. Real execution, heavy dependency installation, long training runs, and Nextflow workflows require explicit user approval.

The project does not install these heavy dependencies automatically:

- scvi-tools
- GPU PyTorch
- Java
- Nextflow
- nf-core
- Singularity / Apptainer

`omics-codex doctor` diagnoses and suggests next steps. An agent should only assist with installation after the user explicitly approves it, and the installation method should match the active environment type.

## Quick Start

Clone the repository and install the backend CLI:

```bash
git clone https://github.com/ocean-debug/Codex_Omics.git
cd Codex_Omics
python -m pip install -e ".[dev,nfcore,scverse]"
```

Diagnose the active environment first:

```bash
omics-codex doctor --json
```

Inspect input data:

```bash
omics-codex inspect-data --input /path/to/input
```

Generate a safe workflow from natural language:

```bash
omics-codex route \
  --prompt "Create a bulk RNA-seq workflow" \
  --input /path/to/fastq_dir \
  --outdir results/bulk_rna \
  --out bulk_rna.workflow.json
```

Plan only, without executing analysis stages:

```bash
omics-codex workflow plan --config bulk_rna.workflow.json
```

Inspect status and render a report:

```bash
omics-codex workflow status --config bulk_rna.workflow.json
omics-codex report --manifest results/bulk_rna/workflow_manifest.json
```

## Codex Plugin Usage

The plugin directory in this repository is:

```text
plugins/omics-analysis/
```

It contains:

```text
.codex-plugin/plugin.json
skills/
schemas/
references/
scripts/
```

Load `plugins/omics-analysis/` in a Codex environment that supports local plugin loading. The plugin guides Codex through the standard workflow:

```text
doctor -> inspect-data -> route/template -> workflow plan -> approved run -> report
```

Build the standard plugin package:

```bash
python scripts/release/build_plugin_package.py
python scripts/release/check_release.py --plugin-package dist/codex-omics-plugin-v0.4.0.zip
```

Related documentation:

- [docs/plugin-installation.md](docs/plugin-installation.md)
- [docs/plugin-package.md](docs/plugin-package.md)
- [docs/agent-integration.md](docs/agent-integration.md)

## Common Commands

Environment and data inspection:

```bash
omics-codex doctor --json
omics-codex doctor --kind nfcore --json
omics-codex doctor --kind scvi --json
omics-codex inspect-data --input /path/to/input
```

Templates and routing:

```bash
omics-codex template list
omics-codex template create --name bulk-rna --input /path/to/fastq --out bulk_rna.workflow.json
omics-codex template create --name scrna-qc-scvi --input /path/to/cells.h5ad --out scrna_scvi.workflow.json
omics-codex route --prompt "Analyze these sequencing reads" --input /path/to/input --outdir results/demo --out workflow.json
```

nf-core:

```bash
omics-codex nfcore list
omics-codex nfcore make-samplesheet --pipeline rnaseq --input /path/to/fastq --out samplesheet.csv
omics-codex nfcore build-command --config examples/nfcore_rnaseq/omics_run_spec.yaml
omics-codex nfcore run --config examples/nfcore_rnaseq/omics_run_spec.yaml
```

single-cell RNA-seq QC:

```bash
omics-codex scrna-qc run --config examples/scrna_qc/omics_run_spec.yaml
```

scVI:

```bash
omics-codex scvi list-models
omics-codex scvi validate --config examples/scvi/omics_run_spec.yaml
omics-codex scvi train --config examples/scvi/omics_run_spec.yaml
```

workflow:

```bash
omics-codex workflow plan --config examples/workflows/scrna_qc_scvi.yaml
omics-codex workflow run --config examples/workflows/scrna_qc_scvi.approved.yaml
omics-codex workflow resume --config examples/workflows/scrna_qc_scvi.approved.yaml
omics-codex workflow status --config examples/workflows/scrna_qc_scvi.yaml
```

## Environment Requirements

Base environment:

- Python 3.10+
- `pip install -e ".[dev,nfcore,scverse]"`

scRNA-seq QC requires:

- `scanpy`
- `anndata`

scVI requires:

- `scvi-tools`
- `torch`
- For GPU use: a PyTorch CUDA build that matches the machine GPU, driver, and CUDA stack.

Real nf-core execution requires:

- Java 17+
- Nextflow
- nf-core CLI
- git
- Singularity or Apptainer
- Network access to nf-core pipelines, or pre-cached pipelines

See [docs/environment-setup.md](docs/environment-setup.md) for UV, venv, conda/mamba, and HPC setup notes.

## Validation

Default tests:

```bash
python -m pytest tests/smoke -q
python -m pytest tests/unit -q
python -m pytest tests/integration -q
omics-codex doctor --json
omics-codex workflow plan --config examples/workflows/scrna_qc_scvi.yaml
```

Release checks:

```bash
python scripts/release/build_plugin_package.py
python scripts/release/check_release.py --plugin-package dist/codex-omics-plugin-v0.4.0.zip
```

Heavy tests are opt-in. Real Nextflow runs, GPU scVI family training, and large real-data acceptance checks require explicit user approval.

## Current Scope

Codex Omics is currently suitable for small, reproducible, auditable omics workflows:

- It can help Codex generate run specs, workflow specs, commands, samplesheets, manifests, and reports.
- It can run lightweight scRNA-seq QC and scVI workflows.
- It can plan and, when the environment is ready, execute nf-core workflows.
- It records failure reasons, log paths, commands, and suggested next steps.

It is not a fully automatic platform that guarantees every dataset, every pipeline, or every HPC environment will run successfully without user preparation. Real execution still depends on input data quality, references, HPC permissions, network access, container cache availability, GPU/PyTorch compatibility, and nf-core pipeline availability.

## Documentation

- [docs/user-guide.md](docs/user-guide.md): user commands and expected inputs/outputs
- [docs/environment-setup.md](docs/environment-setup.md): UV, venv, conda/mamba, and HPC setup
- [docs/plugin-installation.md](docs/plugin-installation.md): repo-local plugin loading
- [docs/plugin-package.md](docs/plugin-package.md): standard plugin package build and checks
- [docs/agent-integration.md](docs/agent-integration.md): Codex and agent behavior contract
- [docs/acceptance-matrix.md](docs/acceptance-matrix.md): supported and unsupported capabilities
- [docs/release-checklist.md](docs/release-checklist.md): release checklist

## License

MIT
