---
name: scvi-tools
description: Validate AnnData and run approved scvi-tools workflows through plugin-local scripts. Use for SCVI, SCANVI, TOTALVI, PEAKVI, MULTIVI, batch correction, label transfer, CITE-seq, scATAC-seq, multiome, latent embeddings, UMAP, Leiden, GPU/PyTorch diagnostics, manifests, and reports.
---

# scvi-tools

Use plugin-local scripts only.

## Workflow

1. Check the environment:
   `python plugins/omics-analysis/skills/scvi-tools/scripts/check_environment.py --json`
2. List available scvi-tools models if the user has not selected one.
3. Validate AnnData before training.
4. Use dry-run for training plans.
5. Train only after explicit approval with `--approved true`.
6. Save model outputs, `run_manifest.json`, and `report.md`.

## Commands

```bash
python plugins/omics-analysis/skills/scvi-tools/scripts/check_environment.py --json
python plugins/omics-analysis/skills/scvi-tools/scripts/list_models.py --json
python plugins/omics-analysis/skills/scvi-tools/scripts/validate_adata.py --input cells.h5ad --model SCVI --json
python plugins/omics-analysis/skills/scvi-tools/scripts/train_model.py --input cells.h5ad --output-dir results/scvi --model SCVI --dry-run --json
python plugins/omics-analysis/skills/scvi-tools/scripts/train_model.py --input cells.h5ad --output-dir results/scvi --model SCVI --approved true
```

## Safety

- Training requires `--approved true`.
- Do not install scvi-tools, torch, or GPU PyTorch without explicit user approval.
- If GPU hardware is visible but `torch.cuda.is_available()` is false, report the mismatch and suggest matching PyTorch installation.

## References

- Read `references/anndata-requirements.md` before validating input matrices.
- Read `references/model-adapters.md` when choosing model-specific fields.
