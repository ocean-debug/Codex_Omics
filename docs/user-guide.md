# User Guide

Codex-Omics is plugin-only. Load `plugins/omics-analysis/` in Codex, then use the selected skill's local scripts.

## Standard path

```text
route or select skill -> check environment -> validate input -> dry-run -> approved run -> manifest/report
```

The router reads `plugins/omics-analysis/skill_registry.yaml` and writes a
structured `router_plan` with detected intent, input inventory, candidate
scores, selected skill, blockers, warnings, and next actions.

```bash
python plugins/omics-analysis/skills/omics-router/scripts/route_omics.py --prompt "run scVI integration" --input data --outdir results/route --json
```

## single-cell-rna-qc

```bash
python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/check_environment.py --json
python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/validate_input.py --input cells.h5ad --json
python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py --input cells.h5ad --output-dir results/qc --dry-run --json
python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py --input cells.h5ad --output-dir results/qc --approved true --write-manifest
```

Reports include raw-count source checks, filtering summaries, and batch-aware counts when a `batch` column is present.

## single-cell-preprocess

```bash
python plugins/omics-analysis/skills/single-cell-preprocess/scripts/check_environment.py --json
python plugins/omics-analysis/skills/single-cell-preprocess/scripts/validate_input.py --input filtered.h5ad --json
python plugins/omics-analysis/skills/single-cell-preprocess/scripts/plan.py --input filtered.h5ad --output-dir results/preprocess --dry-run --json
python plugins/omics-analysis/skills/single-cell-preprocess/scripts/run.py --input filtered.h5ad --output-dir results/preprocess --approved true --write-manifest
```

This skill keeps QC separate from preprocessing. It writes `preprocessed.h5ad`, `preprocess_summary.json`, `run_manifest.json`, and `report.md`.

## single-cell-integration

```bash
python plugins/omics-analysis/skills/single-cell-integration/scripts/check_environment.py --json
python plugins/omics-analysis/skills/single-cell-integration/scripts/validate_input.py --input preprocessed.h5ad --batch-key batch --json
python plugins/omics-analysis/skills/single-cell-integration/scripts/plan.py --input preprocessed.h5ad --output-dir results/integration --backend scanpy-combat --batch-key batch --dry-run --json
python plugins/omics-analysis/skills/single-cell-integration/scripts/run.py --input preprocessed.h5ad --output-dir results/integration --backend scanpy-combat --batch-key batch --approved true --write-manifest
```

This skill writes `integrated.h5ad`, `integration_summary.json`, `batch_diagnostics.csv`, `run_manifest.json`, and `report.md`. `scanpy-combat` is the approved lightweight backend in the first release; `scvi`, `harmony`, and `scanorama` return planned or blocked manifests unless their execution path is added later.

## single-cell-annotation

```bash
python plugins/omics-analysis/skills/single-cell-annotation/scripts/check_environment.py --json
python plugins/omics-analysis/skills/single-cell-annotation/scripts/validate_input.py --input preprocessed.h5ad --backend marker-based --marker-reference marker_reference.csv --groupby leiden --json
python plugins/omics-analysis/skills/single-cell-annotation/scripts/plan.py --input preprocessed.h5ad --output-dir results/annotation --backend marker-based --marker-reference marker_reference.csv --groupby leiden --dry-run --json
python plugins/omics-analysis/skills/single-cell-annotation/scripts/run.py --input preprocessed.h5ad --output-dir results/annotation --backend marker-based --marker-reference marker_reference.csv --groupby leiden --approved true --write-manifest
```

This skill writes `annotated.h5ad`, `annotations.csv`, `annotation_confidence.csv`, `annotation_summary.json`, `run_manifest.json`, and `report.md`. `marker-based` is executable in the first release; `celltypist`, `singler`, and `scanvi` are planned/blocked unless local dependencies and model/reference paths are available.

## single-cell-marker-de

```bash
python plugins/omics-analysis/skills/single-cell-marker-de/scripts/check_environment.py --json
python plugins/omics-analysis/skills/single-cell-marker-de/scripts/validate_input.py --input preprocessed.h5ad --groupby leiden --json
python plugins/omics-analysis/skills/single-cell-marker-de/scripts/plan.py --input preprocessed.h5ad --output-dir results/markers --groupby leiden --dry-run --json
python plugins/omics-analysis/skills/single-cell-marker-de/scripts/run.py --input preprocessed.h5ad --output-dir results/markers --groupby leiden --approved true --write-manifest
```

This skill uses Scanpy `rank_genes_groups` for first-pass cluster or cell type markers. It writes `markers.csv`, `de_summary.json`, `run_manifest.json`, and `report.md`.

## pathway-enrichment

```bash
python plugins/omics-analysis/skills/pathway-enrichment/scripts/check_environment.py --json
python plugins/omics-analysis/skills/pathway-enrichment/scripts/validate_input.py --input markers.csv --gene-sets gene_sets.gmt --json
python plugins/omics-analysis/skills/pathway-enrichment/scripts/plan.py --input markers.csv --gene-sets gene_sets.gmt --output-dir results/enrichment --dry-run --json
python plugins/omics-analysis/skills/pathway-enrichment/scripts/run.py --input markers.csv --gene-sets gene_sets.gmt --output-dir results/enrichment --approved true --write-manifest
```

This skill performs lightweight ORA with local GMT/CSV gene sets. It writes `enrichment.csv`, `enrichment_summary.json`, `run_manifest.json`, and `report.md`.

## scrna-standard-workflow

```bash
python plugins/omics-analysis/skills/scrna-standard-workflow/scripts/check_environment.py --json
python plugins/omics-analysis/skills/scrna-standard-workflow/scripts/validate_input.py --input cells.h5ad --json
python plugins/omics-analysis/skills/scrna-standard-workflow/scripts/plan.py --input cells.h5ad --output-dir results/scrna_workflow --dry-run --json
```

This workflow skill is plan-only. It writes `workflow_plan.json`, `workflow_plan.md`, `run_manifest.json`, and `report.md`, with child dry-run and approved commands for QC, preprocessing, integration, annotation, marker detection, enrichment, and report rendering.

## bulk-rna-de

```bash
python plugins/omics-analysis/skills/bulk-rna-de/scripts/check_environment.py --json
python plugins/omics-analysis/skills/bulk-rna-de/scripts/validate_input.py --counts counts.csv --metadata metadata.csv --contrast condition:control:treatment --json
python plugins/omics-analysis/skills/bulk-rna-de/scripts/plan.py --counts counts.csv --metadata metadata.csv --contrast condition:control:treatment --output-dir results/bulk_de --dry-run --json
python plugins/omics-analysis/skills/bulk-rna-de/scripts/run.py --counts counts.csv --metadata metadata.csv --contrast condition:control:treatment --output-dir results/bulk_de --approved true --write-manifest
```

This skill performs dependency-light exploratory log2-CPM DE from local count tables. It writes `de_results.csv`, `de_summary.json`, `run_manifest.json`, and `report.md`; use DESeq2/edgeR/limma for publication-grade modeling.

## scvi-tools

```bash
python plugins/omics-analysis/skills/scvi-tools/scripts/check_environment.py --json
python plugins/omics-analysis/skills/scvi-tools/scripts/list_models.py --json
python plugins/omics-analysis/skills/scvi-tools/scripts/recommend_model.py --input cells.h5ad --task "batch correction" --json
python plugins/omics-analysis/skills/scvi-tools/scripts/validate_adata.py --input cells.h5ad --model SCVI --json
python plugins/omics-analysis/skills/scvi-tools/scripts/train_model.py --input cells.h5ad --output-dir results/scvi --model SCVI --seed 0 --dry-run --json
```

Model-specific validation covers `SCVI`, `SCANVI`, `TOTALVI`, `PEAKVI`, and `MULTIVI`. Training requires `--approved true` and records seed, timing, GPU memory, training history, and lightweight latent QC diagnostics when available.

## nextflow-development

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/check_environment.py --json
python plugins/omics-analysis/skills/nextflow-development/scripts/detect_data_type.py --input fastq_dir --json
python plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py --pipeline rnaseq --input fastq_dir --out samplesheet.csv
python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py --pipeline rnaseq --input samplesheet.csv --outdir results/rnaseq --profile singularity --dry-run --json
python plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py --pipeline scrnaseq --input fastq_dir --out scrnaseq_samplesheet.csv --metadata metadata.csv
python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py --pipeline scrnaseq --input scrnaseq_samplesheet.csv --outdir results/scrnaseq --profile singularity --aligner cellranger --protocol 10x --dry-run --json
python plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py --pipeline riboseq --input fastq_dir --out riboseq_samplesheet.csv --sample-type riboseq
python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py --pipeline riboseq --revision 1.2.0 --input riboseq_samplesheet.csv --outdir results/riboseq --profile singularity --fasta genome.fa --gtf genes.gtf --dry-run --json
python plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py --pipeline spatialvi --input spatial_dir --out spatialvi_samplesheet.csv --metadata metadata.csv --spatial-mode auto
python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py --pipeline spatialvi --input spatialvi_samplesheet.csv --outdir results/spatialvi --profile singularity --spaceranger-reference /refs/spaceranger --dry-run --json
```

Failed execution records stdout/stderr, `.nextflow.log` when available, output inventory, and a classified failure reason.
Planning also writes `params.yaml`; completed runs parse MultiQC data when present and add interpretation plus suggested fixes to the report.

## Reports and install planning

```bash
python plugins/omics-analysis/skills/omics-report/scripts/render_report.py --manifest results/run_manifest.json --out results/report.md
python plugins/omics-analysis/scripts/common/install_planner.py --task scvi --output-dir results/install_scvi --json
```

Installation is plan-only by default. Use `--execute --approved true` only after reviewing the plan. System Python environments remain blocked unless the user chooses a scoped environment.

## Outputs

Each approved or planned run should write:

- `run_manifest.json`
- `report.md`
- logs or command files when applicable
- task-specific outputs

## Safety

Use dry-run first. Require `--approved true` for real Nextflow execution, scvi-tools training, large downloads, and dependency installation.
