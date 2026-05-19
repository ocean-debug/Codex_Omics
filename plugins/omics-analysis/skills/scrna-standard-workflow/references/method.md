# Method Summary

`scrna-standard-workflow` is a plan-only composition skill. It does not perform analysis directly. It records an ordered plan that delegates work to task skills:

- `single-cell-rna-qc`
- `single-cell-preprocess`
- `single-cell-integration`
- `single-cell-annotation`
- `single-cell-marker-de`
- `pathway-enrichment`
- `omics-report`

Each child skill remains responsible for its own validation, approved execution, manifest, and report.
