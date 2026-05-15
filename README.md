# Codex-Omics

Codex-Omics is a Codex plugin for omics analysis. It provides self-contained, plugin-local skills for single-cell RNA-seq QC, scvi-tools workflows, and Nextflow/nf-core workflow development.

The plugin is the product. Users load `plugins/omics-analysis/` in Codex, and Codex uses the bundled `SKILL.md` files plus plugin-local scripts. There is no backend CLI requirement.

## What It Provides

- **single-cell-rna-qc**: inspect `.h5ad`, 10x H5, or 10x MTX inputs; check scverse dependencies; plan or run QC; write filtered AnnData, plots, manifest, and report.
- **scvi-tools**: check scvi-tools, torch, CUDA/GPU state, and AnnData readiness; list available models; validate inputs; train only after approval.
- **nextflow-development**: check Java, Nextflow, nf-core, git, and container backends; detect FASTQ inputs; generate samplesheets; build dry-run commands; execute only after approval.
- **omics-router**: guide Codex to the correct skill based on input type and user intent.
- **skill-authoring-kit**: template for adding future bioinformatics skills.

## Safety Model

Default behavior is plan-only. Long-running or environment-changing actions require explicit approval.

Requires approval:

- real Nextflow execution;
- scvi-tools training;
- GPU training;
- heavy dependency installation;
- large downloads;
- destructive overwrite;
- data movement outside user-controlled output directories.

The plugin diagnoses missing tools and suggests environment-specific install commands. It does not silently install scvi-tools, GPU PyTorch, Java, Nextflow, nf-core, Singularity, Apptainer, or Docker.

## Plugin Layout

```text
plugins/omics-analysis/
  .codex-plugin/plugin.json
  skills/
    single-cell-rna-qc/
    scvi-tools/
    nextflow-development/
    omics-router/
    omics-report/
    skill-authoring-kit/
  scripts/common/
  schemas/
```

Each P0 skill has:

```text
SKILL.md
scripts/
references/
schemas/
examples/
```

## Quick Start

Load this plugin directory in Codex:

```text
plugins/omics-analysis/
```

Then use the selected skill's local scripts.

Single-cell RNA-seq QC:

```bash
python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/check_environment.py --json
python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py --input cells.h5ad --output-dir results/qc --dry-run --json
python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py --input cells.h5ad --output-dir results/qc --approved true --write-manifest
```

scvi-tools:

```bash
python plugins/omics-analysis/skills/scvi-tools/scripts/check_environment.py --json
python plugins/omics-analysis/skills/scvi-tools/scripts/list_models.py --json
python plugins/omics-analysis/skills/scvi-tools/scripts/train_model.py --input cells.h5ad --output-dir results/scvi --model SCVI --dry-run --json
```

Nextflow / nf-core:

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/check_environment.py --json
python plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py --pipeline rnaseq --input fastq_dir --out samplesheet.csv
python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py --pipeline rnaseq --input samplesheet.csv --outdir results/rnaseq --profile singularity --dry-run --json
```

## Environment Requirements

Base plugin scripts use Python 3.10+ and the standard library.

Analysis-specific dependencies are checked per skill:

- scRNA QC: `scanpy`, `anndata`, `numpy`, `scipy`, `pandas`, `matplotlib`, `seaborn`
- scVI: `scvi-tools`, `torch`, `scanpy`, `anndata`
- Nextflow: Java 17+, Nextflow, nf-core, git, Singularity/Apptainer or Docker

## Build Plugin Package

```bash
python scripts/release/build_plugin_package.py
python scripts/release/check_release.py --plugin-package dist/codex-omics-plugin-v1.0.0.zip
```

The release check verifies that the plugin package contains the P0 local scripts and does not depend on the removed backend CLI.

## Validation

Plugin-local smoke checks:

```bash
python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/check_environment.py --json
python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py --help
python plugins/omics-analysis/skills/scvi-tools/scripts/check_environment.py --json
python plugins/omics-analysis/skills/scvi-tools/scripts/train_model.py --help
python plugins/omics-analysis/skills/nextflow-development/scripts/check_environment.py --json
python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py --help
```

Run tests when `pytest` is available:

```bash
python -m pytest tests -q
```

## Scope

Codex-Omics is a plugin-local omics skill collection. It helps Codex plan, validate, and run approved omics workflows, but it does not guarantee every dataset, pipeline, HPC environment, network, container cache, or GPU stack will work without preparation.

## License

MIT
