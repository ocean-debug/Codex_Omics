---
name: omics-report
description: Render or summarize Codex-Omics plugin-local run manifests, reports, command logs, scRNA QC summaries, scvi-tools model summaries, and Nextflow output inventories.
---

# Omics Report

## Command

```bash
python plugins/omics-analysis/skills/omics-report/scripts/render_report.py --manifest results/run_manifest.json --out results/report.md
```

Use plugin-local outputs:

- `run_manifest.json`
- `report.md`
- `logs/`
- `command.sh`
- task-specific summaries

Prefer existing `report.md` when present. If a manifest exists without a report, render one from the manifest with the plugin-local report script.
