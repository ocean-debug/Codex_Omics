# Multiome with MULTIVI

Use this reference for paired or partially paired single-cell RNA plus ATAC data
and `MULTIVI`-style joint latent representation workflows.

## Input Requirements

- RNA counts should be raw, non-negative, and integer-like.
- ATAC counts should represent accessibility over peaks or genomic intervals.
- Modality metadata must make it clear which features or matrices belong to RNA
  and ATAC.
- Batch metadata should be provided when runs, donors, chemistries, or studies
  differ.

## Plugin Workflow

```bash
python plugins/omics-analysis/skills/scvi-tools/scripts/check_environment.py --json
python plugins/omics-analysis/skills/scvi-tools/scripts/validate_adata.py --input multiome.h5ad --model MULTIVI --json
python plugins/omics-analysis/skills/scvi-tools/scripts/train_model.py --input multiome.h5ad --output-dir results/multivi --model MULTIVI --dry-run --json
```

Use dry-run validation to confirm that the available input shape is compatible
with the selected model before approved training.

## Fit Boundaries

- Use TOTALVI for RNA plus protein CITE-seq data.
- Use PEAKVI for ATAC-only data.
- Use SCVI or SCANVI for RNA-only integration.
- If the input is split across multiple files or uses MuData-specific layout,
  validate the exact layout before running.

## Review Points

- Confirm that RNA and ATAC modalities refer to the same cells or that missing
  modality handling is intentional.
- Record genome build and peak set provenance in the run report when available.
- Inspect modality balance; a weak or sparse modality can dominate failure
  modes even when the file passes basic validation.
