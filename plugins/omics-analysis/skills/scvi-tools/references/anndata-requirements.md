# AnnData Requirements

scvi-tools models generally require non-negative raw count data in `adata.X` or a configured layer.

Check before training:

- observations and variables are non-empty;
- selected count matrix is non-negative and integer-like;
- `batch_key` exists when provided;
- SCANVI labels exist when provided;
- TOTALVI has protein data in `obsm`;
- PEAKVI has accessibility-like count data;
- MULTIVI has RNA/ATAC modality metadata or a MuData input.
