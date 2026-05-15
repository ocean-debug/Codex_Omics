---
name: scvi-universal
description: Compatibility alias for the migrated scvi-tools skill. Use the scvi-tools skill for plugin-local scripts, dependency checks, AnnData validation, approved training, manifests, and reports.
---

# scvi-universal migrated

Use `plugins/omics-analysis/skills/scvi-tools/` instead.

The supported plugin-local entrypoints are:

```bash
python plugins/omics-analysis/skills/scvi-tools/scripts/check_environment.py --json
python plugins/omics-analysis/skills/scvi-tools/scripts/list_models.py --json
python plugins/omics-analysis/skills/scvi-tools/scripts/validate_adata.py --input cells.h5ad --model SCVI --json
python plugins/omics-analysis/skills/scvi-tools/scripts/train_model.py --input cells.h5ad --output-dir results/scvi --dry-run --json
```
