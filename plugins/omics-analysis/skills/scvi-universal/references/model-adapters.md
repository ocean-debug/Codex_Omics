# scvi-tools model adapters

Use this reference when adding a model adapter, debugging registry output, or explaining model capabilities.

## Adapter contract

Each adapter should provide:

```python
validate_input(adata, run_spec)
setup_anndata(adata, run_spec)
build_model(adata, run_spec)
train(model, run_spec)
collect_outputs(model, adata, run_spec)
```

The generic adapter handles model classes that expose the standard scvi-tools API:

- class method `setup_anndata`;
- constructor accepting `adata`;
- `train`;
- `save`;
- optional `get_latent_representation`.

## Curated adapters

Curated adapters should provide extra validation for:

- `SCVI`: raw RNA counts, optional `batch_key`.
- `SCANVI`: labels key and unlabeled category when semi-supervised training is requested.
- `TOTALVI`: RNA counts plus protein matrix in `adata.obsm`.
- `PEAKVI`: peak/accessibility count matrix.
- `MULTIVI`: paired or unpaired multimodal structure.

## Capability recording

Never pretend a model supports an unavailable output. Record capability status explicitly:

```json
{
  "latent": true,
  "normalized_expression": true,
  "protein": false,
  "label_transfer": false
}
```

If an installed model lacks `get_latent_representation`, save the model and report `latent_unavailable: true`.

## Registry behavior

- Inspect `scvi.model` at runtime.
- Include curated models even when absent, marked `available: false`.
- Do not fail `list-models` when `scvi-tools` is absent; return curated models as unavailable.
- Fail training when the selected model class is unavailable.

## Version compatibility

scvi-tools model availability changes across versions. Tests should assert registry behavior and core curated models only when installed.
