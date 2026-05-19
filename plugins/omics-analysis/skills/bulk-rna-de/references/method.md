# Bulk RNA DE Method

This skill provides a dependency-light first pass for local bulk RNA count tables.

The approved execution path:

1. Loads a gene-by-sample count matrix.
2. Loads sample metadata and an explicit `variable:reference:target` contrast.
3. Filters low-count genes.
4. Converts counts to log2 CPM.
5. Computes an exploratory Welch-style two-group score with normal approximation.
6. Applies Benjamini-Hochberg adjustment.
7. Writes `de_results.csv`, `de_summary.json`, `run_manifest.json`, and `report.md`.

This is intended for smoke testing, triage, and report wiring. For publication-grade differential expression, use a reviewed DESeq2, edgeR, or limma-voom workflow.
