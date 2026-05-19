---
name: pathway-enrichment
description: Plan or run plugin-local pathway enrichment from marker tables, differential expression tables, or gene lists. Use for lightweight ORA with local GMT/CSV gene sets, enrichment tables, result summaries, methods text, manifests, and reports without installing enrichment backends.
---

# Pathway Enrichment

Use plugin-local scripts only. This task skill consumes marker/DE outputs or gene lists and performs lightweight over-representation analysis against a local gene set file.

## Workflow

1. Check dependencies:
   `python plugins/omics-analysis/skills/pathway-enrichment/scripts/check_environment.py --json`
2. Validate inputs:
   `python plugins/omics-analysis/skills/pathway-enrichment/scripts/validate_input.py --input markers.csv --gene-sets pathways.gmt --json`
3. Plan enrichment first:
   `python plugins/omics-analysis/skills/pathway-enrichment/scripts/plan.py --input markers.csv --gene-sets pathways.gmt --output-dir results/enrichment --dry-run --json`
4. Run only after explicit approval:
   `python plugins/omics-analysis/skills/pathway-enrichment/scripts/run.py --input markers.csv --gene-sets pathways.gmt --output-dir results/enrichment --approved true --write-manifest`
5. Review `enrichment.csv`, `enrichment_summary.json`, `run_manifest.json`, and `report.md`.

## Inputs

- Marker/DE CSV or TSV, such as `single-cell-marker-de` `markers.csv`
- Plain text gene list with one gene per line
- Local gene set file in GMT or CSV/TSV format

## Outputs

- `enrichment.csv`
- `enrichment_summary.json`
- `run_manifest.json`
- `report.md`

## Safety

- Default to planned/dry-run behavior unless `--approved true` is set.
- Do not download GO, KEGG, Reactome, or MSigDB gene sets automatically.
- Do not install enrichment packages without explicit user approval.
- Treat ORA as exploratory and review the marker/DE input before biological claims.

## References

| Task | Reference |
|---|---|
| Workflow diagram | `references/workflow.md` |
| Method summary | `references/method.md` |
| Parameter policy | `references/parameter_policy.md` |
| Troubleshooting | `references/troubleshooting.md` |
