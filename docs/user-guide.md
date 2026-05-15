# User Guide

Codex-Omics is plugin-only. Load `plugins/omics-analysis/` in Codex, then use the selected skill's local scripts.

## Standard path

```text
select skill -> check environment -> validate input -> dry-run -> approved run -> manifest/report
```

## single-cell-rna-qc

```bash
python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/check_environment.py --json
python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/validate_input.py --input cells.h5ad --json
python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py --input cells.h5ad --output-dir results/qc --dry-run --json
python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py --input cells.h5ad --output-dir results/qc --approved true --write-manifest
```

## scvi-tools

```bash
python plugins/omics-analysis/skills/scvi-tools/scripts/check_environment.py --json
python plugins/omics-analysis/skills/scvi-tools/scripts/list_models.py --json
python plugins/omics-analysis/skills/scvi-tools/scripts/validate_adata.py --input cells.h5ad --model SCVI --json
python plugins/omics-analysis/skills/scvi-tools/scripts/train_model.py --input cells.h5ad --output-dir results/scvi --model SCVI --dry-run --json
```

## nextflow-development

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/check_environment.py --json
python plugins/omics-analysis/skills/nextflow-development/scripts/detect_data_type.py --input fastq_dir --json
python plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py --pipeline rnaseq --input fastq_dir --out samplesheet.csv
python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py --pipeline rnaseq --input samplesheet.csv --outdir results/rnaseq --profile singularity --dry-run --json
```

## Outputs

Each approved or planned run should write:

- `run_manifest.json`
- `report.md`
- logs or command files when applicable
- task-specific outputs

## Safety

Use dry-run first. Require `--approved true` for real Nextflow execution, scvi-tools training, large downloads, and dependency installation.
