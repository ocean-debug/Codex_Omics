# User Guide

Codex-Omics is plugin-only. Load `plugins/omics-analysis/` in Codex, then use the selected skill's local scripts.

## Standard path

```text
route or select skill -> check environment -> validate input -> dry-run -> approved run -> manifest/report
```

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

## scvi-tools

```bash
python plugins/omics-analysis/skills/scvi-tools/scripts/check_environment.py --json
python plugins/omics-analysis/skills/scvi-tools/scripts/list_models.py --json
python plugins/omics-analysis/skills/scvi-tools/scripts/validate_adata.py --input cells.h5ad --model SCVI --json
python plugins/omics-analysis/skills/scvi-tools/scripts/train_model.py --input cells.h5ad --output-dir results/scvi --model SCVI --dry-run --json
```

Model-specific validation covers `SCVI`, `SCANVI`, `TOTALVI`, `PEAKVI`, and `MULTIVI`. Training requires `--approved true`.

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
