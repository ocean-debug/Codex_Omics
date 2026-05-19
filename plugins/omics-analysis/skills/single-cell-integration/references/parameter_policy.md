# Single-cell Integration Parameter Policy

- `--backend` defaults to `scanpy-combat`.
- `--batch-key` defaults to `batch` and must exist in `adata.obs`.
- `--label-key` is optional and reserved for diagnostics or backend handoff.
- `--n-pcs` and `--neighbors` control optional embedding diagnostics.
- `--embedding-key` stores the integrated PCA copy, default `X_pca_integrated`.
- Do not install integration backends automatically.
- Do not mutate the input h5ad in place.
- Use `scvi-tools` directly for approved SCVI/SCANVI training until a dedicated handoff executor is added.
