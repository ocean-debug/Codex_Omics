---
name: bulk-rna-de
description: Plan or run plugin-local bulk RNA differential expression from count matrices, sample metadata, and explicit contrasts. Use for exploratory count-table DE, manifests, methods text, summaries, and reports without installing R/DESeq2/edgeR.
---

# Bulk RNA DE

Use plugin-local scripts only. This task skill consumes a local gene-by-sample count table, sample metadata, and an explicit two-group contrast.

## Workflow

1. Check dependencies:
   `python plugins/omics-analysis/skills/bulk-rna-de/scripts/check_environment.py --json`
2. Validate inputs:
   `python plugins/omics-analysis/skills/bulk-rna-de/scripts/validate_input.py --counts counts.csv --metadata metadata.csv --contrast condition:control:treatment --json`
3. Plan first:
   `python plugins/omics-analysis/skills/bulk-rna-de/scripts/plan.py --counts counts.csv --metadata metadata.csv --contrast condition:control:treatment --output-dir results/bulk_de --dry-run --json`
4. Run only after explicit approval:
   `python plugins/omics-analysis/skills/bulk-rna-de/scripts/run.py --counts counts.csv --metadata metadata.csv --contrast condition:control:treatment --output-dir results/bulk_de --approved true --write-manifest`
5. Review `de_results.csv`, `de_summary.json`, `run_manifest.json`, and `report.md`.

## Inputs

- Count matrix CSV/TSV with first column as gene id and remaining columns as sample ids.
- Metadata CSV/TSV with a `sample` column and the contrast variable.
- Contrast string formatted as `variable:reference:target`.

## Outputs

- `de_results.csv`
- `de_summary.json`
- `run_manifest.json`
- `report.md`

## Safety

- Default to planned/dry-run behavior unless `--approved true` is set.
- Do not install R, DESeq2, edgeR, limma, or Python statistics packages automatically.
- Treat the built-in method as exploratory log2-CPM Welch-style screening, not a replacement for a full DESeq2/edgeR publication workflow.
- Require explicit contrasts; do not infer experimental design automatically.

## References

| Task | Reference |
|---|---|
| Workflow diagram | `references/workflow.md` |
| Method summary | `references/method.md` |
| Parameter policy | `references/parameter_policy.md` |
| Troubleshooting | `references/troubleshooting.md` |
