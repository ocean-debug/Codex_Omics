---
name: scvi-universal
description: Run installed scvi-tools models through a registry and adapter system, including AnnData validation, setup_anndata configuration, training, model saving, latent extraction, downstream Scanpy analysis, summaries, and run manifests. Use for scVI, scANVI, totalVI, PeakVI, MultiVI, SOLO, AUTOZI, LDVAE, batch correction, label transfer, CITE-seq, scATAC-seq, multiome, spatial deconvolution, and scvi-tools-based single-cell modeling.
---

# Universal scvi-tools Skill

## Required workflow

1. List or inspect models with `omics-codex scvi list-models` or `omics-codex scvi inspect <MODEL>`.
2. Validate AnnData with `omics-codex scvi validate --config omics_run_spec.yaml`.
3. Confirm raw integer counts are in `adata.X` or the configured layer.
4. Confirm `batch_key`, labels, protein matrices, or accessibility matrices required by the selected model.
5. Train only when the run spec is approved and the environment is correct.
6. Save model directory, trained h5ad, `scvi_model_summary.json`, `report.md`, and `run_manifest.json`.

## Adapter policy

- Curated adapters cover `SCVI`, `SCANVI`, `TOTALVI`, `PEAKVI`, and `MULTIVI`.
- Other installed model classes use the generic adapter when they follow standard scvi-tools APIs.
- If a model lacks latent representation, differential expression, or modality-specific output, record that capability as unavailable.

## When to read references

- Read `references/model-adapters.md` when adding, debugging, or explaining model adapters.
- Read `references/anndata-requirements.md` when validating h5ad inputs or setup_anndata fields.

## Commands

```bash
omics-codex scvi list-models
omics-codex scvi inspect SCVI
omics-codex scvi validate --config omics_run_spec.yaml
omics-codex scvi train --config omics_run_spec.yaml
```
