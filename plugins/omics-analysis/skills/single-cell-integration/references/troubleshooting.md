# Single-cell Integration Troubleshooting

## Missing batch key

Use `--batch-key` with an existing `adata.obs` column. If the dataset has only
one batch, integration may not be meaningful.

## ComBat failed

Check for invalid matrix values, empty batches, or non-numeric expression data.
Use a larger preprocessed h5ad for embedding diagnostics.

## Optional backend blocked

`scvi`, `harmony`, and `scanorama` are interface-first in this release. Missing
dependencies or execution handoff are recorded in `run_manifest.json`; no
package is installed automatically.

## Over-correction risk

Inspect integrated embeddings and downstream markers. Integration should reduce
technical batch effects without erasing biological differences.
