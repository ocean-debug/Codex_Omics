---
name: single-cell-preprocess
description: Plan or run plugin-local single-cell RNA preprocessing from filtered h5ad inputs. Use for normalization, log1p, highly variable genes, scaling, PCA, neighbors, UMAP, Leiden clustering, preprocessed AnnData outputs, manifests, reports, and scanpy/anndata dependency diagnostics.
---

# Single-cell Preprocess

Use plugin-local scripts only. This task skill starts after QC and prepares a filtered AnnData object for integration, annotation, marker discovery, and reporting.

## Workflow

1. Check dependencies:
   `python plugins/omics-analysis/skills/single-cell-preprocess/scripts/check_environment.py --json`
2. Validate input:
   `python plugins/omics-analysis/skills/single-cell-preprocess/scripts/validate_input.py --input filtered.h5ad --json`
3. Plan preprocessing first:
   `python plugins/omics-analysis/skills/single-cell-preprocess/scripts/plan.py --input filtered.h5ad --output-dir results/preprocess --dry-run --json`
4. Run only after explicit approval:
   `python plugins/omics-analysis/skills/single-cell-preprocess/scripts/run.py --input filtered.h5ad --output-dir results/preprocess --approved true --write-manifest`
5. Review `run_manifest.json`, `report.md`, and `preprocess_summary.json` before downstream analysis.

## Inputs

- Filtered `.h5ad`

## Outputs

- `preprocessed.h5ad`
- `preprocess_summary.json`
- `run_manifest.json`
- `report.md`

## Safety

- Default to planned/dry-run behavior unless `--approved true` is set.
- Do not modify source h5ad files in place.
- Do not install scanpy/anndata without explicit user approval.
- Keep QC and preprocessing separate: use `single-cell-rna-qc` for filtering decisions and this skill for downstream representation building.

## References

| Task | Reference |
|---|---|
| Workflow diagram | `references/workflow.md` |
| Method summary | `references/method.md` |
| Parameter policy | `references/parameter_policy.md` |
| Troubleshooting | `references/troubleshooting.md` |
