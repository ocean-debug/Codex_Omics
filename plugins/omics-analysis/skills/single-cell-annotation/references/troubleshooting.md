# Single-cell Annotation Troubleshooting

## Missing group column

Use `--groupby` with an existing `adata.obs` column, or run preprocessing and
clustering first.

## Missing marker reference

For marker-based annotation, provide a local CSV/TSV/GMT file. CSV/TSV should
use at least:

```csv
cell_type,gene,weight
T cell,CD3D,1
```

## Low-confidence annotations

Low confidence usually means weak marker expression, overlapping marker sets,
or marker genes missing from the h5ad var names. Review `annotations.csv` and
`matched_genes`.

## CellTypist, SingleR, or SCANVI blocked

These backends require local dependencies and model/reference paths. This skill
does not install packages or download models automatically.
