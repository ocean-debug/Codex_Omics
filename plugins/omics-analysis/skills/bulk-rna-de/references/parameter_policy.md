# Bulk RNA DE Parameter Policy

- `--contrast` is required and must use `variable:reference:target`.
- `--counts` must be a CSV/TSV table with one gene id column and sample count columns.
- `--metadata` must include a `sample` column by default; change with `--sample-column`.
- `--min-count` and `--min-samples` control low-count filtering.
- `--padj-threshold` and `--lfc-threshold` are summary thresholds only; all tested genes are written to `de_results.csv`.
- Do not infer contrasts from filenames or metadata levels.
- Do not install external DE packages automatically.
