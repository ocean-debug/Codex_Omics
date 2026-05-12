# Single-cell RNA-seq filtering policy

Use this reference when choosing filtering thresholds or explaining why defaults are permissive.

## Filtering modes

### MAD mode

MAD mode uses median absolute deviation outlier detection.

Recommended defaults:

```yaml
scrna_qc:
  filter:
    mode: mad
    n_mads_counts: 5
    n_mads_genes: 5
    n_mads_mito: 3
    max_pct_mito: 20
    min_cells_per_gene: 1
```

Use two-sided outliers for `total_counts` and `n_genes_by_counts`; use high-side filtering for mitochondrial percentage.

### Fixed-threshold mode

Use fixed thresholds when the user supplies protocol-specific limits:

```yaml
scrna_qc:
  filter:
    mode: fixed
    min_counts: 500
    max_counts: 50000
    min_genes: 200
    max_pct_mito: 10
```

## Output contract

Each filtering run should write:

- `filtered.h5ad`;
- `with_qc.h5ad`;
- `qc_summary.json`;
- `qc_metrics_before_filtering.png`;
- `qc_metrics_after_filtering.png`;
- `report.md`;
- `run_manifest.json`.

## Required summary fields

Record:

- number of cells and genes before filtering;
- number of cells and genes after filtering;
- thresholds used;
- number of cells removed by each mask;
- counts layer used;
- gene patterns used.

## When to ask the user

Ask only when the missing choice materially changes the output:

- organism cannot be inferred and mitochondrial gene prefixes are ambiguous;
- protocol has known high mitochondrial content;
- user requests strict filtering but gives no acceptable thresholds;
- input matrix appears normalized rather than raw counts.
