# Single-cell Preprocess Method

This skill prepares a filtered AnnData object for downstream single-cell analysis.

Default method:

1. Load a filtered `.h5ad`.
2. Preserve the original `X` matrix in `layers['counts']` when no counts layer exists.
3. Normalize total counts per cell.
4. Apply `log1p`.
5. Mark highly variable genes.
6. Scale expression.
7. Compute PCA.
8. Build a neighbor graph.
9. Compute UMAP.
10. Run Leiden clustering.

The skill writes a new `preprocessed.h5ad`; it does not mutate the source file.
