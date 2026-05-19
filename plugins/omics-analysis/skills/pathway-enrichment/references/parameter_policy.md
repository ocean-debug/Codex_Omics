# Parameter Policy

Defaults are intended for first-pass marker interpretation:

| Parameter | Default | Notes |
|---|---:|---|
| `mode` | `ora` | Only ORA executes in the lightweight v1. |
| `gene_column` | `auto` | Checks `names`, `gene`, `symbol`, and related columns. |
| `group_column` | `group` | Uses `all` when no group column exists. |
| `top_n` | `100` | Top genes per group. |
| `min_overlap` | `2` | Minimum query/pathway overlap. |
| `min_set_size` | `3` | Filters very small gene sets. |
| `max_set_size` | `500` | Filters broad gene sets. |
| `padj_threshold` | `0.05` | Summary significance cutoff. |

For GO/KEGG/Reactome/MSigDB production analysis, provide a reviewed local gene set file. Do not silently download databases.
