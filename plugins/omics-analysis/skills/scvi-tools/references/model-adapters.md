# scvi-tools Model Adapters

Curated models:

- `SCVI`: RNA count model with latent representation.
- `SCANVI`: semi-supervised label transfer; requires labels.
- `TOTALVI`: CITE-seq RNA + protein; requires protein expression in `obsm`.
- `PEAKVI`: scATAC-seq accessibility model.
- `MULTIVI`: multiome RNA + ATAC model.

For unsupported installed model classes, validate inputs conservatively and report unavailable capabilities rather than fabricating outputs.
