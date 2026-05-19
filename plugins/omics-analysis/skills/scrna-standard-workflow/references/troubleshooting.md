# Troubleshooting

- Missing child script: run release checks and confirm the referenced skill exists in `plugins/omics-analysis/skills/`.
- Missing marker reference: provide `--marker-reference` before executing annotation.
- Missing gene sets: provide `--gene-sets` before executing enrichment.
- Batch key missing: run integration validation with the intended `--batch-key` before approved integration.
- Unexpected workflow output: inspect `workflow_plan.json` first, then the child step manifest.
