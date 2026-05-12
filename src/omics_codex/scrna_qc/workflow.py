from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..common.errors import OmicsError
from ..common.io import write_json, write_text
from ..common.manifest import base_manifest, write_manifest
from ..common.paths import assert_not_input_overwrite, prepare_outdir


def run_scrna_qc(spec: dict[str, Any]) -> dict[str, Any]:
    ad, sc, np, pd, scipy_sparse, plt, sns = import_scverse()
    inputs = spec.get("inputs", {})
    outputs = spec.get("outputs", {})
    qc_spec = spec.get("scrna_qc", {})
    outdir = prepare_outdir(outputs.get("outdir", "./results/scrna_qc"), force=bool(spec.get("execution", {}).get("force", False)))
    input_path = Path(inputs.get("path", ""))
    if inputs.get("synthetic") or (not input_path.exists() and "examples" in str(input_path)):
        create_synthetic_h5ad(input_path, ad=ad, np=np, pd=pd, scipy_sparse=scipy_sparse)
    if not input_path.exists():
        raise OmicsError("InputNotFound", f"AnnData input does not exist: {input_path}", "Check inputs.path.", "scrna_qc")
    adata = load_anndata(input_path, sc=sc)
    counts_layer = qc_spec.get("counts_layer", "counts")
    preserve_counts(adata, counts_layer=counts_layer, strict=bool(qc_spec.get("preserve_raw_counts", True)))
    calculate_metrics(adata, sc=sc, np=np, patterns=qc_spec.get("gene_patterns", {}))
    summary_before = summarize_qc(adata, np=np)
    plot_qc(adata, outdir / "qc_metrics_before_filtering.png", plt=plt, sns=sns, title="Before filtering")
    filtered, filter_summary = filter_cells_and_genes(adata, qc_spec, np=np, sc=sc)
    summary_after = summarize_qc(filtered, np=np)
    batch_key = qc_spec.get("batch_key") or inputs.get("batch_key") or "batch"
    plot_qc(filtered, outdir / "qc_metrics_after_filtering.png", plt=plt, sns=sns, title="After filtering")
    filtered_path = outdir / "filtered.h5ad"
    annotated_path = outdir / "with_qc.h5ad"
    assert_not_input_overwrite(input_path, filtered_path)
    filtered.write_h5ad(filtered_path)
    adata.write_h5ad(annotated_path)
    summary = {
        "before": summary_before,
        "after": summary_after,
        "filtering": filter_summary,
        "counts_layer": counts_layer,
        "raw_counts_validated": True,
        "batch_key": batch_key if batch_key in adata.obs else None,
        "by_batch_before": summarize_qc_by_group(adata, batch_key, np=np) if batch_key in adata.obs else {},
        "by_batch_after": summarize_qc_by_group(filtered, batch_key, np=np) if batch_key in filtered.obs else {},
        "optional_checks": optional_qc_notes(qc_spec),
    }
    write_json(outdir / "qc_summary.json", summary)
    write_text(outdir / "report.md", render_qc_report(summary))
    manifest = base_manifest(
        skill="single-cell-rna-qc",
        status="completed",
        inputs=inputs,
        outputs={
            **outputs,
            "outdir": str(outdir),
            "filtered_h5ad": str(filtered_path),
            "annotated_h5ad": str(annotated_path),
            "summary": str(outdir / "qc_summary.json"),
            "report": str(outdir / "report.md"),
        },
        parameters=qc_spec,
    )
    write_manifest(outputs.get("manifest") or outdir / "run_manifest.json", manifest)
    return manifest


def import_scverse():
    try:
        import anndata as ad
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
        import scanpy as sc
        import seaborn as sns
        from scipy import sparse as scipy_sparse
    except ImportError as exc:
        raise OmicsError(
            "MissingSoftware",
            f"scRNA QC dependencies are missing: {exc}",
            "Install the scverse extra in the codex-omics conda environment.",
            "import_scverse",
        ) from exc
    return ad, sc, np, pd, scipy_sparse, plt, sns


def create_synthetic_h5ad(path: Path, *, ad: Any, np: Any, pd: Any, scipy_sparse: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    counts = rng.poisson(lam=2.0, size=(80, 60)).astype("int32")
    counts[:3, :5] += 8
    genes = [f"MT-GENE{i}" for i in range(5)] + [f"RPS{i}" for i in range(5)] + [f"GENE{i}" for i in range(50)]
    obs = pd.DataFrame({"batch": ["batch1"] * 40 + ["batch2"] * 40})
    adata = ad.AnnData(X=scipy_sparse.csr_matrix(counts), obs=obs)
    adata.var_names = genes
    adata.obs_names = [f"cell{i}" for i in range(adata.n_obs)]
    adata.layers["counts"] = adata.X.copy()
    adata.write_h5ad(path)
    return path


def load_anndata(path: Path, *, sc: Any):
    suffix = "".join(path.suffixes).lower()
    if suffix.endswith(".h5ad"):
        return sc.read_h5ad(path)
    if suffix.endswith(".h5"):
        return sc.read_10x_h5(path)
    if path.is_dir():
        return sc.read_10x_mtx(path)
    raise OmicsError("UnsupportedInputFormat", f"Unsupported single-cell input: {path}", "Use h5ad, 10x h5, or 10x MTX.", "load_anndata")


def preserve_counts(adata: Any, counts_layer: str = "counts", strict: bool = True) -> None:
    matrix = adata.layers[counts_layer] if counts_layer in adata.layers else adata.X
    if strict and not looks_integer_counts(matrix):
        raise OmicsError(
            "RawCountsValidationFailed",
            "The selected matrix does not look like non-negative integer raw counts.",
            "Provide raw counts in adata.X or scrna_qc.counts_layer, or set preserve_raw_counts=false for exploratory use.",
            "preserve_counts",
        )
    if counts_layer not in adata.layers:
        adata.layers[counts_layer] = adata.X.copy()
    adata.raw = adata.copy()


def calculate_metrics(adata: Any, *, sc: Any, np: Any, patterns: dict[str, str]) -> None:
    mt_pattern = patterns.get("mt") or "^MT-"
    ribo_pattern = patterns.get("ribo") or "^RP[SL]"
    hb_pattern = patterns.get("hb") or "^HB[^(P)]"
    names = adata.var_names.astype(str)
    adata.var["mt"] = [bool(re.search(mt_pattern, name)) for name in names]
    adata.var["ribo"] = [bool(re.search(ribo_pattern, name)) for name in names]
    adata.var["hb"] = [bool(re.search(hb_pattern, name)) for name in names]
    sc.pp.calculate_qc_metrics(adata, qc_vars=["mt", "ribo", "hb"], inplace=True, percent_top=None, log1p=False)
    if "pct_counts_mt" not in adata.obs:
        adata.obs["pct_counts_mt"] = 0.0


def summarize_qc(adata: Any, *, np: Any) -> dict[str, Any]:
    metrics = {}
    for key in ["total_counts", "n_genes_by_counts", "pct_counts_mt", "pct_counts_ribo", "pct_counts_hb"]:
        if key in adata.obs:
            values = np.asarray(adata.obs[key], dtype=float)
            metrics[key] = {
                "min": float(np.nanmin(values)),
                "median": float(np.nanmedian(values)),
                "max": float(np.nanmax(values)),
            }
    return {"n_cells": int(adata.n_obs), "n_genes": int(adata.n_vars), "metrics": metrics}


def summarize_qc_by_group(adata: Any, group_key: str, *, np: Any) -> dict[str, Any]:
    if group_key not in adata.obs:
        return {}
    grouped: dict[str, Any] = {}
    for group in sorted(map(str, adata.obs[group_key].astype(str).unique())):
        subset = adata[adata.obs[group_key].astype(str) == group]
        grouped[group] = summarize_qc(subset, np=np)
    return grouped


def optional_qc_notes(qc_spec: dict[str, Any]) -> dict[str, Any]:
    optional = qc_spec.get("optional_checks", {})
    notes: dict[str, Any] = {}
    if optional.get("doublet_detection"):
        notes["doublet_detection"] = {
            "status": "planned",
            "message": "Doublet detection is not run by default; add and validate a project-specific scrublet/scvi SOLO step before filtering.",
        }
    if optional.get("ambient_rna"):
        notes["ambient_rna"] = {
            "status": "planned",
            "message": "Ambient RNA correction is not run by default; add a CellBender/SoupX-compatible workflow when raw droplets are available.",
        }
    return notes


def filter_cells_and_genes(adata: Any, qc_spec: dict[str, Any], *, np: Any, sc: Any):
    filter_spec = qc_spec.get("filter", {})
    mode = filter_spec.get("mode", "mad")
    keep = np.ones(adata.n_obs, dtype=bool)
    masks: dict[str, int] = {}
    thresholds: dict[str, Any] = {"mode": mode}
    if mode == "mad":
        for metric, n_mads in [
            ("total_counts", filter_spec.get("n_mads_counts", 5)),
            ("n_genes_by_counts", filter_spec.get("n_mads_genes", 5)),
        ]:
            mask = ~mad_outliers(np.asarray(adata.obs[metric], dtype=float), float(n_mads), np=np, two_sided=True)
            keep &= mask
            masks[metric] = int((~mask).sum())
            thresholds[f"{metric}_n_mads"] = float(n_mads)
        if "pct_counts_mt" in adata.obs:
            mt_mask = ~mad_outliers(np.asarray(adata.obs["pct_counts_mt"], dtype=float), float(filter_spec.get("n_mads_mito", 3)), np=np, two_sided=False)
            keep &= mt_mask
            masks["pct_counts_mt_mad"] = int((~mt_mask).sum())
            thresholds["pct_counts_mt_n_mads"] = float(filter_spec.get("n_mads_mito", 3))
    elif mode != "fixed":
        raise OmicsError("InvalidFilterMode", f"Unsupported scRNA QC filter mode: {mode}", "Use 'mad' or 'fixed'.", "filter_cells_and_genes")
    fixed_limits = [
        ("pct_counts_mt", filter_spec.get("max_pct_mito"), "max"),
        ("total_counts", filter_spec.get("max_counts"), "max"),
        ("total_counts", filter_spec.get("min_counts"), "min"),
        ("n_genes_by_counts", filter_spec.get("max_genes"), "max"),
        ("n_genes_by_counts", filter_spec.get("min_genes"), "min"),
    ]
    for metric, limit, direction in fixed_limits:
        if limit is None or metric not in adata.obs:
            continue
        values = np.asarray(adata.obs[metric], dtype=float)
        mask = values <= float(limit) if direction == "max" else values >= float(limit)
        keep &= mask
        masks[f"{metric}_{direction}"] = int((~mask).sum())
        thresholds[f"{metric}_{direction}"] = float(limit)
    filtered = adata[keep].copy()
    min_cells = int(filter_spec.get("min_cells_per_gene", 1))
    if min_cells > 0:
        sc.pp.filter_genes(filtered, min_cells=min_cells)
    return filtered, {
        "mode": mode,
        "removed_cells": int((~keep).sum()),
        "remaining_cells": int(filtered.n_obs),
        "remaining_genes": int(filtered.n_vars),
        "thresholds": thresholds,
        "masks": masks,
    }


def mad_outliers(values: Any, n_mads: float, *, np: Any, two_sided: bool) -> Any:
    median = np.nanmedian(values)
    mad = np.nanmedian(np.abs(values - median))
    if mad == 0:
        return np.zeros(values.shape, dtype=bool)
    high = values > median + n_mads * mad
    if not two_sided:
        return high
    low = values < median - n_mads * mad
    return high | low


def plot_qc(adata: Any, output: Path, *, plt: Any, sns: Any, title: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    metrics = ["total_counts", "n_genes_by_counts", "pct_counts_mt"]
    for axis, metric in zip(axes, metrics):
        if metric in adata.obs:
            sns.histplot(adata.obs[metric], ax=axis, bins=30)
            axis.set_title(metric)
        else:
            axis.set_axis_off()
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def render_qc_report(summary: dict[str, Any]) -> str:
    before = summary.get("before", {})
    after = summary.get("after", {})
    filtering = summary.get("filtering", {})
    lines = [
        "# Single-cell RNA-seq QC Report",
        "",
        f"- Cells: `{before.get('n_cells', 'NA')}` -> `{after.get('n_cells', 'NA')}`",
        f"- Genes: `{before.get('n_genes', 'NA')}` -> `{after.get('n_genes', 'NA')}`",
        f"- Filter mode: `{filtering.get('mode', 'unknown')}`",
        f"- Counts layer: `{summary.get('counts_layer', 'counts')}`",
        f"- Batch key: `{summary.get('batch_key') or 'none'}`",
        "",
        "## Full Summary",
        "",
        "```json",
        json.dumps(summary, indent=2, sort_keys=True),
        "```",
    ]
    return "\n".join(lines) + "\n"


def looks_integer_counts(matrix: Any) -> bool:
    import numpy as np

    values = matrix.data if hasattr(matrix, "data") else np.asarray(matrix).ravel()
    if values.size == 0:
        return False
    sample = values[: min(values.size, 10000)]
    if np.nanmin(sample) < 0:
        return False
    return bool(np.allclose(sample, np.round(sample)))
