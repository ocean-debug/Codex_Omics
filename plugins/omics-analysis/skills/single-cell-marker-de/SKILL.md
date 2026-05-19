---
name: single-cell-marker-de
description: Plan or run plugin-local single-cell marker gene detection and differential expression from preprocessed h5ad inputs. Use for cluster markers, cell type markers, Scanpy rank_genes_groups, marker tables, optional plots, manifests, reports, and scanpy/anndata dependency diagnostics.
---

# Single-cell Marker DE

Use plugin-local scripts only. This task skill starts after preprocessing and produces marker or differential expression tables for a grouping column such as `leiden` or cell type.

## Workflow

1. Check dependencies:
   `python plugins/omics-analysis/skills/single-cell-marker-de/scripts/check_environment.py --json`
2. Validate input:
   `python plugins/omics-analysis/skills/single-cell-marker-de/scripts/validate_input.py --input preprocessed.h5ad --groupby leiden --json`
3. Plan marker detection first:
   `python plugins/omics-analysis/skills/single-cell-marker-de/scripts/plan.py --input preprocessed.h5ad --output-dir results/markers --groupby leiden --dry-run --json`
4. Run only after explicit approval:
   `python plugins/omics-analysis/skills/single-cell-marker-de/scripts/run.py --input preprocessed.h5ad --output-dir results/markers --groupby leiden --approved true --write-manifest`
5. Review `markers.csv`, `de_summary.json`, `run_manifest.json`, and `report.md` before downstream interpretation.

## Inputs

- Preprocessed `.h5ad`
- A grouping column in `.obs`; default is `leiden`

## Outputs

- `markers.csv`
- `de_summary.json`
- Optional plots when `--make-plots` is used and plotting dependencies work
- `run_manifest.json`
- `report.md`

## Safety

- Default to planned/dry-run behavior unless `--approved true` is set.
- Do not modify source h5ad files in place.
- Do not install scanpy/anndata or plotting packages without explicit user approval.
- Treat marker/DE output as exploratory until reviewed against QC, annotation, and experimental design.

## References

| Task | Reference |
|---|---|
| Workflow diagram | `references/workflow.md` |
| Method summary | `references/method.md` |
| Parameter policy | `references/parameter_policy.md` |
| Troubleshooting | `references/troubleshooting.md` |
