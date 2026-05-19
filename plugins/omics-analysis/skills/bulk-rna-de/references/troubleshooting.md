# Bulk RNA DE Troubleshooting

## Missing counts or metadata

Check that `--counts` and `--metadata` point to local CSV/TSV files.

## Invalid contrast

Use `variable:reference:target`, for example:

```bash
--contrast condition:control:treatment
```

## Sample mismatch

Sample ids in metadata must match count matrix column names.

## Too few replicates

The default `--min-samples 2` requires at least two samples in each group. Lower this only for smoke tests, not biological inference.

## No genes tested

Check the count matrix, `--gene-column`, and low-count thresholds.
