# Troubleshooting

## Missing Scanpy or AnnData

The environment check reports blockers and installation hints. Do not install dependencies unless the user explicitly approves.

## Input Is Not h5ad

Run `single-cell-rna-qc` first for 10x H5 or MTX inputs, then pass the filtered `.h5ad` to this skill.

## `seurat_v3` HVG Fails

`seurat_v3` can require optional packages such as `scikit-misc`. Use the default `seurat` flavor unless that dependency is already available.

## Too Few Cells or Genes

For very small test files, PCA, neighbors, UMAP, and Leiden may be skipped. The manifest records this as a warning.
