---
name: single-cell-rna-qc
description: Run reproducible single-cell RNA-seq QC and preprocessing for h5ad, 10x H5, or 10x MTX inputs using Scanpy/scverse conventions, raw-count preservation, mitochondrial/ribosomal/hemoglobin metrics, MAD or fixed-threshold filtering, QC plots, filtered AnnData outputs, reports, and run manifests. Use when users request scRNA-seq QC, low-quality cell filtering, mitochondrial filtering, or quality assessment.
---

# Single-cell RNA-seq QC

## Required workflow

1. Read and validate `omics_run_spec.yaml`.
2. Confirm input format: `.h5ad`, 10x `.h5`, or 10x MTX directory.
3. Preserve raw counts in `adata.raw` and a counts layer when available.
4. Compute QC metrics for total counts, detected genes, mitochondrial, ribosomal, and hemoglobin genes.
5. Apply MAD-based or fixed-threshold filtering.
6. Write `filtered.h5ad`, `with_qc.h5ad`, QC plots, `qc_summary.json`, `report.md`, and `run_manifest.json`.

## Commands

```bash
omics-codex scrna-qc run --config omics_run_spec.yaml
```

## Notes

- Do not modify the source h5ad in place.
- Prefer permissive defaults; users should inspect plots before aggressive filtering.
- Species-specific gene prefixes belong in `scrna_qc.gene_patterns`.

## When to read references

- Read `references/qc-metrics.md` when explaining metrics, plots, or gene patterns.
- Read `references/filtering-policy.md` when tuning thresholds or reviewing output contracts.
