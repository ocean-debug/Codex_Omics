# Parameter Policy

Defaults are intended for first-pass cluster marker discovery:

| Parameter | Default | Notes |
|---|---:|---|
| `groupby` | `leiden` | Use an existing `.obs` column. |
| `method` | `wilcoxon` | Scanpy-supported rank method. |
| `reference` | `rest` | Group-vs-rest marker detection. |
| `n_genes` | `100` | Top genes exported per group. |
| `min_cells_per_group` | `3` | Avoids groups too small for meaningful ranking. |
| `use_raw` | `auto` | Uses `.raw` when present; otherwise uses X or selected layer. |

Use explicit contrast-aware tools for study-level disease/control DE. This skill is optimized for cluster or cell type marker discovery.
