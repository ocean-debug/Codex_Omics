# Parameter Policy

Defaults are intentionally conservative and Scanpy-compatible:

| Parameter | Default | Notes |
|---|---:|---|
| `target_sum` | `10000` | Total-count normalization target. |
| `hvg_flavor` | `seurat` | Avoids extra optional dependencies required by `seurat_v3`. |
| `n_top_genes` | `2000` | Marks HVGs but does not subset genes. |
| `scale_max_value` | `10` | Caps scaled values. |
| `n_pcs` | `50` | Reduced automatically for small datasets. |
| `n_neighbors` | `15` | Capped for small cell counts. |
| `resolution` | `1.0` | Leiden clustering resolution. |
| `random_state` | `0` | Recorded for reproducibility. |

Use `single-cell-integration` or `scvi-tools` for batch-aware integration. This skill only creates a standard single-cell representation.
