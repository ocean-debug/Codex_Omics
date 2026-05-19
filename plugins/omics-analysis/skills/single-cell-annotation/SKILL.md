---
name: single-cell-annotation
description: Plan or run plugin-local single-cell cell type annotation from preprocessed h5ad inputs. Use for marker-based annotation, CellTypist plans, SingleR plans, SCANVI label-transfer handoff, predicted cell type labels, annotation confidence, manifests, reports, and dependency/resource diagnostics.
---

# Single-cell Annotation

Use plugin-local scripts only. This task skill starts after preprocessing or integration and assigns interpretable cell type labels without mutating the source h5ad in place.

## Workflow

1. Check dependencies:
   `python plugins/omics-analysis/skills/single-cell-annotation/scripts/check_environment.py --json`
2. Validate input:
   `python plugins/omics-analysis/skills/single-cell-annotation/scripts/validate_input.py --input preprocessed.h5ad --backend marker-based --marker-reference markers.csv --groupby leiden --json`
3. Plan annotation first:
   `python plugins/omics-analysis/skills/single-cell-annotation/scripts/plan.py --input preprocessed.h5ad --output-dir results/annotation --backend marker-based --marker-reference markers.csv --groupby leiden --dry-run --json`
4. Run only after explicit approval:
   `python plugins/omics-analysis/skills/single-cell-annotation/scripts/run.py --input preprocessed.h5ad --output-dir results/annotation --backend marker-based --marker-reference markers.csv --groupby leiden --approved true --write-manifest`
5. Review `annotated.h5ad`, `annotations.csv`, `annotation_summary.json`, `run_manifest.json`, and `report.md`.

## Inputs

- Preprocessed `.h5ad`
- Grouping column in `.obs`, default `leiden`
- Backend-specific reference:
  - `marker-based`: local CSV/TSV/GMT marker reference
  - `celltypist`: local CellTypist model path
  - `singler`: local SingleR reference path and available R packages
  - `scanvi`: local SCANVI model/reference information

## Outputs

- `annotated.h5ad`
- `annotations.csv`
- `annotation_summary.json`
- `annotation_confidence.csv`
- `run_manifest.json`
- `report.md`

## Safety

- Default to planned/dry-run behavior unless `--approved true` is set.
- Do not modify source h5ad files in place.
- Do not download CellTypist models, SingleR references, SCANVI references, or ontology resources automatically.
- Treat annotations as hypotheses until reviewed against marker evidence, QC, experimental design, and biological context.

## References

| Task | Reference |
|---|---|
| Workflow diagram | `references/workflow.md` |
| Method summary | `references/method.md` |
| Parameter policy | `references/parameter_policy.md` |
| Troubleshooting | `references/troubleshooting.md` |
