# Single-cell RNA-seq QC metrics

Use this reference when interpreting QC results, changing metric definitions, or explaining generated plots.

## Core metrics

- `total_counts`: total UMI/read count per cell.
- `n_genes_by_counts`: number of detected genes per cell.
- `pct_counts_mt`: percentage of counts assigned to mitochondrial genes.
- `pct_counts_ribo`: percentage of counts assigned to ribosomal genes.
- `pct_counts_hb`: percentage of counts assigned to hemoglobin genes.

## Gene pattern defaults

Human defaults:

```yaml
scrna_qc:
  gene_patterns:
    mt: "^MT-"
    ribo: "^RP[SL]"
    hb: "^HB[^(P)]"
```

Mouse mitochondrial genes often use `^mt-`. Confirm species or inspect gene names when possible.

## Raw count preservation

- Preserve raw counts in `adata.raw`.
- Preserve or create a counts layer, default `counts`.
- Do not overwrite the input h5ad.
- Write a separate filtered h5ad and an annotated-with-QC h5ad.

## Plot expectations

The default report should include before/after distributions for:

- total counts;
- number of genes;
- mitochondrial percentage.

Threshold overlays are useful when users tune filtering, but absence of overlays should not block basic QC output.

## Interpretation cautions

- High mitochondrial percentage may be biological in some tissues.
- Low counts can reflect small cells, nuclei, or damaged cells depending on protocol.
- Aggressive filtering can remove rare populations.
- QC metrics are not a substitute for downstream doublet, ambient RNA, and batch checks.
