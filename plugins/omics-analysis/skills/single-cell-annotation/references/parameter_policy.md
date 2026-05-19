# Single-cell Annotation Parameter Policy

- `--backend` defaults to `marker-based`.
- `--groupby` defaults to `leiden`.
- `--marker-reference` is required for `marker-based`.
- Marker CSV/TSV must include `cell_type,gene`; `weight` is optional and defaults to 1.
- GMT marker reference uses term as cell type and genes as markers.
- `--model` is required for `celltypist` and `scanvi`.
- `--reference` is required for `singler`.
- Do not download models, references, or ontology resources automatically.
- Do not mutate the input h5ad in place.
