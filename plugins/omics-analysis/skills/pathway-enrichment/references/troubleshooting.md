# Troubleshooting

## Missing Gene Sets

Approved runs require `--gene-sets`. Use a local GMT file or CSV/TSV with `term,gene` columns.

## Gene Column Not Detected

Pass `--gene-column` explicitly if your input does not use common column names such as `names`, `gene`, or `symbol`.

## No Enriched Terms

Check the gene ID namespace, gene set species, `--top-n`, `--min-overlap`, and gene set size filters.

## GSEA Requested

`--mode gsea` is reserved for future backend integration. Use `--mode ora` in this lightweight implementation.
