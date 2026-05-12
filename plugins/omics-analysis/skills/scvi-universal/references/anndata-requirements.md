# AnnData requirements for scvi-tools

Use this reference when validating input h5ad files or preparing a run spec for scvi-tools.

## Required structure

- Observations are cells in `adata.obs`.
- Variables are genes, peaks, proteins, or features in `adata.var`.
- Raw count matrix is in `adata.X` or a configured layer.
- Batch and label columns live in `adata.obs`.
- Multimodal matrices live in `adata.obsm` or modality-specific structures expected by the model.

## Raw counts

scvi-tools models generally expect non-negative integer count data. The selected matrix should pass:

- no negative values;
- values are close to integers;
- shape is cells by features;
- sparse matrices are accepted.

Run spec example:

```yaml
scvi:
  model: SCVI
  setup_anndata:
    layer: counts
    batch_key: batch
```

## Common keys

- `layer`: counts layer, often `counts`.
- `batch_key`: technical batch, sample, donor, or study.
- `labels_key`: cell type labels for semi-supervised models.
- `protein_expression_obsm_key`: CITE-seq protein matrix for totalVI.

## Validation failures

- `MissingCountsLayer`: configured layer is absent.
- `AnnDataValidationFailed`: selected matrix does not look like raw counts.
- `MissingBatchKey`: configured batch column is absent.
- `MissingLabelKey`: configured label column is absent.
- `MissingProteinObsm`: configured protein matrix is absent.

## Outputs

Successful training should produce:

- saved model directory;
- trained h5ad;
- latent representation in `adata.obsm`, usually `X_scvi`;
- `scvi_model_summary.json`;
- `report.md`;
- `run_manifest.json`.
