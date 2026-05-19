---
name: single-cell-integration
description: Plan or run plugin-local single-cell batch integration from preprocessed h5ad inputs. Use for batch correction, dataset integration, scanpy ComBat, scVI/Harmony/Scanorama handoff planning, integrated AnnData outputs, batch diagnostics, manifests, and reports.
---

# Single-cell Integration

Use plugin-local scripts only. This task skill starts after preprocessing and prepares a batch-aware integrated AnnData object for annotation, marker discovery, and reporting.

## Workflow

1. Check dependencies:
   `python plugins/omics-analysis/skills/single-cell-integration/scripts/check_environment.py --json`
2. Validate input:
   `python plugins/omics-analysis/skills/single-cell-integration/scripts/validate_input.py --input preprocessed.h5ad --batch-key batch --json`
3. Plan integration first:
   `python plugins/omics-analysis/skills/single-cell-integration/scripts/plan.py --input preprocessed.h5ad --output-dir results/integration --batch-key batch --backend scanpy-combat --dry-run --json`
4. Run only after explicit approval:
   `python plugins/omics-analysis/skills/single-cell-integration/scripts/run.py --input preprocessed.h5ad --output-dir results/integration --batch-key batch --backend scanpy-combat --approved true --write-manifest`
5. Review `integrated.h5ad`, `integration_summary.json`, `batch_diagnostics.csv`, `run_manifest.json`, and `report.md`.

## Inputs

- Preprocessed `.h5ad`
- Batch column in `.obs`; default is `batch`

## Outputs

- `integrated.h5ad`
- `integration_summary.json`
- `batch_diagnostics.csv`
- `run_manifest.json`
- `report.md`

## Safety

- Default to planned/dry-run behavior unless `--approved true` is set.
- Do not modify source h5ad files in place.
- Do not install scvi-tools, Harmony, Scanorama, or GPU packages without explicit approval.
- Treat integration as a technical correction; verify that biological structure is not over-corrected.

## References

| Task | Reference |
|---|---|
| Workflow diagram | `references/workflow.md` |
| Method summary | `references/method.md` |
| Parameter policy | `references/parameter_policy.md` |
| Troubleshooting | `references/troubleshooting.md` |
