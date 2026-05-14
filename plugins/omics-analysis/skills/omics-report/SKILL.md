---
name: omics-report
description: Generate concise methods-ready reports from Codex Omics run manifests, nf-core logs, scRNA QC summaries, scvi model summaries, output file inventories, commands, software versions, and structured errors. Use after nf-core, single-cell QC, or scvi-tools workflows to summarize outputs and reproducibility details.
---

# Omics Report

## Required workflow

1. Read `run_manifest.json`.
2. Load optional summaries such as `qc_summary.json`, `scvi_model_summary.json`, or nf-core output inventory.
3. Render `report.md` with methods summary, key parameters, key outputs, inputs, outputs, commands, software, status, errors, failure interpretation, summaries, and next steps.
4. Keep biological interpretation separate unless the user asks for evidence synthesis.

## Command

```bash
omics-codex report --manifest run_manifest.json --out report.md
```
