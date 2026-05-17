# CITE-seq with TOTALVI

Use this reference when the input combines RNA counts with antibody-derived tag
or protein measurements and the user asks for `TOTALVI`, CITE-seq integration,
protein denoising, or joint RNA/protein latent embeddings.

## Input Requirements

- RNA counts must be non-negative and integer-like in `X` or a configured layer.
- Protein expression must be present in `adata.obsm` under the key selected for
  training.
- Protein feature names should be unique and stable.
- `batch_key` should be provided when antibody panels, donors, or runs differ.

## Plugin Workflow

```bash
python plugins/omics-analysis/skills/scvi-tools/scripts/check_environment.py --json
python plugins/omics-analysis/skills/scvi-tools/scripts/validate_adata.py --input cells.h5ad --model TOTALVI --json
python plugins/omics-analysis/skills/scvi-tools/scripts/train_model.py --input cells.h5ad --output-dir results/totalvi --model TOTALVI --dry-run --json
```

Use dry-run output to confirm that the protein matrix was found before asking
for approval to train.

## Common Failures

- Missing protein matrix in `obsm`.
- Protein matrix row count does not match `adata.n_obs`.
- RNA matrix is normalized or log-transformed instead of raw counts.
- CUDA is installed but unavailable to PyTorch.
- Sparse protein matrices or mixed dtypes cause model setup errors.

## Maintenance Notes

Keep this page focused on data contract and plugin commands. Detailed model
math and biological interpretation should stay in official scvi-tools
documentation or user-specific analysis reports.
