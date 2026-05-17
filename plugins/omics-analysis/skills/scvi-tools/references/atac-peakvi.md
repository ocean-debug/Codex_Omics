# scATAC-seq with PEAKVI

Use this reference for single-cell ATAC-seq accessibility data, `PEAKVI`, latent
embeddings, batch correction, and accessibility-focused clustering.

## Input Requirements

- Matrix values should represent peak accessibility counts or binary-like
  accessibility observations.
- Features should represent peaks or genomic intervals, not gene expression.
- Observations and variables must be non-empty.
- Provide `batch_key` when samples, chemistries, or sequencing runs differ.

## Plugin Workflow

```bash
python plugins/omics-analysis/skills/scvi-tools/scripts/check_environment.py --json
python plugins/omics-analysis/skills/scvi-tools/scripts/validate_adata.py --input peaks.h5ad --model PEAKVI --json
python plugins/omics-analysis/skills/scvi-tools/scripts/train_model.py --input peaks.h5ad --output-dir results/peakvi --model PEAKVI --dry-run --json
```

Training requires explicit approval with `--approved true`.

## Fit Boundaries

- Use PEAKVI for ATAC-only data.
- Use MULTIVI when RNA and ATAC modalities are both part of the same analysis.
- Do not use this workflow for bulk ATAC-seq peak calling; use an nf-core or
  Nextflow workflow instead.

## Review Points

- Verify the peak set and genome build before interpreting clusters.
- Inspect sparsity and all-zero cells before training.
- Confirm output embeddings are used for downstream visualization or clustering,
  not treated as direct peak calls.
