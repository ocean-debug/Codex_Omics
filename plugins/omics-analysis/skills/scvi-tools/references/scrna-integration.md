# scRNA-seq Integration

Use this reference for SCVI or SCANVI integration, batch correction, latent
embeddings, UMAP, Leiden clustering, and label-aware reference workflows.

## Use Cases

- Use `SCVI` for unsupervised integration when cell labels are unavailable or
  incomplete.
- Use `SCANVI` when a reliable label column exists and the goal includes label
  transfer or better cell type preservation.
- Use `batch_key` for batches, donors, technologies, studies, or lanes that
  should be modeled as technical covariates.

## Input Checks

- AnnData must contain non-empty observations and variables.
- Counts should be non-negative and integer-like in `X` or a selected layer.
- `batch_key` must exist in `adata.obs` when provided.
- `labels_key` must exist in `adata.obs` for SCANVI.
- Label columns should avoid empty strings; use an explicit unknown category
  when labels are partial.

## Plugin Workflow

```bash
python plugins/omics-analysis/skills/scvi-tools/scripts/check_environment.py --json
python plugins/omics-analysis/skills/scvi-tools/scripts/validate_adata.py --input cells.h5ad --model SCVI --batch-key batch --json
python plugins/omics-analysis/skills/scvi-tools/scripts/train_model.py --input cells.h5ad --output-dir results/scvi --model SCVI --batch-key batch --dry-run --json
```

Switch to `--model SCANVI --labels-key cell_type` only when labels are present.
Training requires `--approved true`.

## Expected Outputs

- A planned or completed `run_manifest.json`.
- `report.md` with input checks, model selection, and execution status.
- Model outputs and latent embeddings when approved training completes.

## Review Points

- Confirm that integration does not remove the biological grouping of interest.
- Check that cells mix by technical batch but remain interpretable by cell type,
  condition, or sample metadata.
- Treat differential expression results as downstream analysis outputs that need
  biological review, not as automatic interpretation.
