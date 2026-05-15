---
name: omics-report
description: Render or summarize Codex-Omics plugin-local run manifests, reports, command logs, scRNA QC summaries, scvi-tools model summaries, and Nextflow output inventories.
---

# Omics Report

Use plugin-local outputs:

- `run_manifest.json`
- `report.md`
- `logs/`
- `command.sh`
- task-specific summaries

Prefer existing `report.md` when present. If a manifest exists without a report, use `plugins/omics-analysis/scripts/common/report.py` as the reference implementation for expected sections.
