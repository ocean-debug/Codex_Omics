---
name: scrna-standard-workflow
description: Build a plan-only standard scRNA-seq workflow that composes QC, preprocessing, integration, annotation, marker detection, pathway enrichment, and reporting skills without executing long-running steps.
---

# scRNA Standard Workflow

Use this workflow skill when the user asks for an end-to-end single-cell RNA-seq analysis plan. It composes existing task skills instead of reimplementing analysis logic.

## Workflow

1. Check local workflow scripts:
   `python plugins/omics-analysis/skills/scrna-standard-workflow/scripts/check_environment.py --json`
2. Validate workflow inputs:
   `python plugins/omics-analysis/skills/scrna-standard-workflow/scripts/validate_input.py --input cells.h5ad --json`
3. Generate a plan first:
   `python plugins/omics-analysis/skills/scrna-standard-workflow/scripts/plan.py --input cells.h5ad --output-dir results/scrna_workflow --dry-run --json`
4. Review `workflow_plan.json`, `workflow_plan.md`, `run_manifest.json`, and `report.md`.
5. Execute child skill commands manually only after explicit approval for each heavy step.

## Inputs

- `.h5ad` input from raw or filtered single-cell data
- Optional marker reference CSV for annotation
- Optional local gene set GMT/CSV for enrichment
- Optional `batch` column for integration

## Outputs

- `workflow_plan.json`
- `workflow_plan.md`
- `run_manifest.json`
- `report.md`

## Safety

- This first version is plan-only.
- It does not execute QC, preprocessing, integration, annotation, marker detection, or enrichment.
- It records child commands so each step remains auditable and separately approvable.

## References

| Task | Reference |
|---|---|
| Workflow diagram | `references/workflow.md` |
| Method summary | `references/method.md` |
| Parameter policy | `references/parameter_policy.md` |
| Troubleshooting | `references/troubleshooting.md` |
