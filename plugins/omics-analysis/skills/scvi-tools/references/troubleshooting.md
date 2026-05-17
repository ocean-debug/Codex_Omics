# scvi-tools Troubleshooting

Use this reference when scvi-tools validation, setup, or training fails.

## Raw Count Problems

Symptoms:

- Validation reports non-integer or negative values.
- Training loss becomes NaN early.
- Model setup rejects the selected layer.

Actions:

- Confirm whether raw counts are in `adata.X`, `adata.raw`, or a named layer.
- Prefer a stable counts layer and pass that layer through the selected script
  option when supported.
- Do not train on log-normalized values unless the selected model explicitly
  supports that input.

## AnnData Schema Problems

Symptoms:

- `batch_key`, `labels_key`, or protein data cannot be found.
- Matrix dimensions do not match metadata dimensions.
- Duplicate observation or variable names cause setup failures.

Actions:

- Run `validate_adata.py` before training.
- Confirm requested keys exist in `adata.obs`, `adata.var`, `adata.layers`, or
  `adata.obsm` as appropriate.
- Keep model-specific requirements in `model-adapters.md` synchronized with
  validation behavior.

## CUDA and PyTorch Problems

Symptoms:

- GPU hardware exists but `torch.cuda.is_available()` is false.
- Training silently falls back to CPU.
- CUDA library mismatch appears in stderr.

Actions:

- Report the mismatch from `check_environment.py --json`.
- Do not install GPU PyTorch automatically.
- Ask the user to approve an environment-specific installation plan before
  changing torch, CUDA, or drivers.

## Memory Problems

Symptoms:

- Out-of-memory errors on CPU or GPU.
- Training starts but fails after loading batches.

Actions:

- Reduce batch size when the training script exposes that option.
- Prefer HVG-filtered input for RNA workflows.
- Use CPU only for small validation runs when GPU setup is unavailable.

## Execution Policy

Always start with:

```bash
python plugins/omics-analysis/skills/scvi-tools/scripts/check_environment.py --json
python plugins/omics-analysis/skills/scvi-tools/scripts/validate_adata.py --input cells.h5ad --model SCVI --json
```

Use `train_model.py --dry-run --json` before approved training. Real training
requires `--approved true`.
