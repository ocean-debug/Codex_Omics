---
name: single-cell-rna-qc
description: Run plugin-local single-cell RNA-seq quality control for h5ad, 10x H5, or 10x MTX inputs. Use for scRNA-seq QC, raw count checks, mitochondrial/ribosomal/hemoglobin metrics, MAD or fixed threshold filtering, QC plots, filtered AnnData outputs, manifests, reports, and scanpy/anndata dependency diagnostics.
---

# Single-cell RNA-seq QC

Use plugin-local scripts only.

## Workflow

1. Check dependencies:
   `python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/check_environment.py --json`
2. Validate input:
   `python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/validate_input.py --input cells.h5ad --json`
3. Plan QC first:
   `python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py --input cells.h5ad --output-dir results/qc --dry-run --json`
4. Run QC only after explicit approval:
   `python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py --input cells.h5ad --output-dir results/qc --approved true --write-manifest`
5. Review `run_manifest.json`, `report.md`, QC plots, and filtered h5ad before downstream analysis.

## Inputs

- `.h5ad`
- 10x `.h5`
- 10x MTX directory

## Outputs

- `with_qc.h5ad`
- `filtered.h5ad`
- `qc_summary.json`
- `qc_metrics_before_filtering.png`
- `qc_metrics_after_filtering.png`
- `run_manifest.json`
- `report.md`

## Safety

- Default to planned/dry-run behavior unless `--approved true` is set.
- Do not modify source h5ad files in place.
- Do not install scanpy/anndata without explicit user approval.

## References

- Read `references/qc-metrics.md` when explaining metrics or gene patterns.
- Read `references/filtering-policy.md` when tuning thresholds.

| Task | Reference |
|---|---|
| Workflow diagram | `references/workflow.md` |
| QC metrics and gene patterns | `references/qc-metrics.md` |
| Filtering thresholds and policy | `references/filtering-policy.md` |
