# Single-cell Integration Method

This skill provides a user-facing integration entrypoint for batch-aware
single-cell analysis.

Supported backend interfaces:

- `scanpy-combat`: approved execution supported in this release.
- `scvi`: interface and blocked/handoff manifest; use `scvi-tools` for real training.
- `harmony`: interface and dependency checks only in this release.
- `scanorama`: interface and dependency checks only in this release.

The `scanpy-combat` backend runs `scanpy.pp.combat` using `obs[batch_key]` and
writes a new `integrated.h5ad`. It optionally computes PCA, neighbors, and UMAP
diagnostics when the dataset is large enough.

Integration is a technical correction. Review batch mixing and cell type
conservation before using integrated data for biological claims.
