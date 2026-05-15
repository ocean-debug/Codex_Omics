from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from common.env import inspect_scrna_qc_environment  # noqa: E402
from common.io import ensure_outdir, write_json  # noqa: E402
from common.manifest import base_manifest, write_manifest  # noqa: E402
from common.report import write_report  # noqa: E402


def approved(value: str | bool) -> bool:
    return value is True or str(value).lower() in {"1", "true", "yes", "y"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run or plan single-cell RNA-seq QC from a plugin-local script.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--config")
    parser.add_argument("--filter-mode", default="mad", choices=["mad", "fixed"])
    parser.add_argument("--species", default="auto", choices=["auto", "human", "mouse"])
    parser.add_argument("--counts-layer", default="counts")
    parser.add_argument("--max-pct-mito", type=float)
    parser.add_argument("--min-genes", type=int)
    parser.add_argument("--max-genes", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--approved", default="false")
    args = parser.parse_args()
    result = run_qc(args)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


def run_qc(args: argparse.Namespace) -> dict[str, Any]:
    outdir = ensure_outdir(args.output_dir)
    input_path = Path(args.input)
    env = inspect_scrna_qc_environment()
    parameters = {
        "filter_mode": args.filter_mode,
        "species": args.species,
        "counts_layer": args.counts_layer,
        "max_pct_mito": args.max_pct_mito,
        "min_genes": args.min_genes,
        "max_genes": args.max_genes,
    }
    outputs = {"outdir": str(outdir), "manifest": str(outdir / "run_manifest.json"), "report": str(outdir / "report.md")}
    if env["blockers"]:
        manifest = base_manifest(
            skill="single-cell-rna-qc",
            status="blocked",
            inputs={"path": str(input_path)},
            outputs=outputs,
            parameters=parameters,
            errors=env["blockers"],
            warnings=env["warnings"],
        )
        manifest["environment"] = env
        return finish(outdir, manifest, "Single-cell RNA-seq QC Report")
    if args.dry_run or not approved(args.approved):
        manifest = base_manifest(
            skill="single-cell-rna-qc",
            status="planned",
            inputs={"path": str(input_path), "exists": input_path.exists()},
            outputs=outputs,
            parameters=parameters,
            warnings=env["warnings"],
        )
        manifest["plan"] = {
            "will_load": str(input_path),
            "will_write": ["with_qc.h5ad", "filtered.h5ad", "qc_summary.json", "qc plots", "run_manifest.json", "report.md"],
            "approval_required": True,
        }
        return finish(outdir, manifest, "Single-cell RNA-seq QC Report")
    return execute_qc(input_path, outdir, parameters, env)


def execute_qc(input_path: Path, outdir: Path, parameters: dict[str, Any], env: dict[str, Any]) -> dict[str, Any]:
    import matplotlib.pyplot as plt
    import numpy as np
    import scanpy as sc
    import seaborn as sns

    adata = load_anndata(input_path, sc)
    counts_layer = parameters["counts_layer"]
    counts_check = inspect_counts_source(adata, counts_layer, np)
    if counts_layer not in adata.layers:
        adata.layers[counts_layer] = adata.X.copy()
    adata.raw = adata.copy()
    add_qc_flags(adata, parameters["species"])
    sc.pp.calculate_qc_metrics(adata, qc_vars=["mt", "ribo", "hb"], inplace=True, percent_top=None, log1p=False)
    before = summarize(adata, np)
    plot_qc(adata, outdir / "qc_metrics_before_filtering.png", plt, sns, "Before filtering")
    keep = build_filter_mask(adata, parameters, np)
    filtered = adata[keep].copy()
    sc.pp.filter_genes(filtered, min_cells=1)
    after = summarize(filtered, np)
    plot_qc(filtered, outdir / "qc_metrics_after_filtering.png", plt, sns, "After filtering")
    annotated = outdir / "with_qc.h5ad"
    filtered_path = outdir / "filtered.h5ad"
    adata.write_h5ad(annotated)
    filtered.write_h5ad(filtered_path)
    summary = {
        "before": before,
        "after": after,
        "removed_cells": int(adata.n_obs - filtered.n_obs),
        "counts_layer": counts_layer,
        "counts_source": counts_check["source"],
        "counts_check": counts_check,
        "filter_mode": parameters["filter_mode"],
        "filtering": filter_summary(adata, keep, parameters, np),
    }
    write_json(outdir / "qc_summary.json", summary)
    outputs = {
        "outdir": str(outdir),
        "manifest": str(outdir / "run_manifest.json"),
        "report": str(outdir / "report.md"),
        "annotated_h5ad": str(annotated),
        "filtered_h5ad": str(filtered_path),
        "summary": str(outdir / "qc_summary.json"),
    }
    manifest = base_manifest(
        skill="single-cell-rna-qc",
        status="completed",
        inputs={"path": str(input_path)},
        outputs=outputs,
        parameters=parameters,
        warnings=env["warnings"],
    )
    if counts_check["warnings"]:
        manifest["warnings"].extend(counts_check["warnings"])
    manifest["summary"] = summary
    return finish(outdir, manifest, "Single-cell RNA-seq QC Report")


def load_anndata(path: Path, sc: Any) -> Any:
    suffix = "".join(path.suffixes).lower()
    if suffix.endswith(".h5ad"):
        return sc.read_h5ad(path)
    if suffix.endswith(".h5"):
        return sc.read_10x_h5(path)
    if path.is_dir():
        return sc.read_10x_mtx(path)
    raise ValueError("Use .h5ad, 10x .h5, or a 10x MTX directory.")


def add_qc_flags(adata: Any, species: str) -> None:
    mt_pattern = "^mt-" if species == "mouse" else "^MT-"
    names = adata.var_names.astype(str)
    adata.var["mt"] = [bool(re.search(mt_pattern, name)) for name in names]
    adata.var["ribo"] = [bool(re.search(r"^RP[SL]|^Rp[sl]", name)) for name in names]
    adata.var["hb"] = [bool(re.search(r"^HB(?!P)|^Hb(?!p)", name)) for name in names]


def summarize(adata: Any, np: Any) -> dict[str, Any]:
    summary: dict[str, Any] = {"n_cells": int(adata.n_obs), "n_genes": int(adata.n_vars), "metrics": {}}
    for key in ["total_counts", "n_genes_by_counts", "pct_counts_mt", "pct_counts_ribo", "pct_counts_hb"]:
        if key in adata.obs:
            values = np.asarray(adata.obs[key], dtype=float)
            summary["metrics"][key] = {
                "min": float(np.nanmin(values)),
                "median": float(np.nanmedian(values)),
                "max": float(np.nanmax(values)),
            }
    return summary


def inspect_counts_source(adata: Any, counts_layer: str, np: Any) -> dict[str, Any]:
    source = f"layers['{counts_layer}']" if counts_layer in adata.layers else "X"
    matrix = adata.layers[counts_layer] if counts_layer in adata.layers else adata.X
    values = matrix.data if hasattr(matrix, "data") else np.asarray(matrix).ravel()
    sample = np.asarray(values[: min(values.size, 20000)], dtype=float) if values.size else np.asarray([], dtype=float)
    integer_like = bool(sample.size and np.nanmin(sample) >= 0 and np.allclose(sample, np.round(sample)))
    max_value = float(np.nanmax(sample)) if sample.size else 0.0
    warnings = []
    if not integer_like:
        warnings.append(
            {
                "warning_type": "NormalizedMatrixSuspected",
                "message": f"Selected counts source {source} is not non-negative integer-like.",
                "suggested_fix": "Use raw counts in a layer such as layers['counts'] before QC and downstream count-based modeling.",
            }
        )
    if integer_like and max_value <= 50:
        warnings.append(
            {
                "warning_type": "LowDynamicRangeCounts",
                "message": f"Selected counts source {source} has low maximum sampled count ({max_value}).",
                "suggested_fix": "Confirm the matrix is raw UMI counts, not log-normalized expression.",
            }
        )
    return {"source": source, "integer_like": integer_like, "sampled_max": max_value, "warnings": warnings}


def filter_summary(adata: Any, keep: Any, parameters: dict[str, Any], np: Any) -> dict[str, Any]:
    removed = ~keep
    reasons: dict[str, int] = {}
    if parameters["filter_mode"] == "mad":
        for key, n_mads, two_sided in [("total_counts", 5.0, True), ("n_genes_by_counts", 5.0, True), ("pct_counts_mt", 3.0, False)]:
            if key in adata.obs:
                reasons[f"{key}_mad"] = int(np.sum(mad_outliers(np.asarray(adata.obs[key], dtype=float), n_mads, np, two_sided)))
    if parameters.get("max_pct_mito") is not None and "pct_counts_mt" in adata.obs:
        reasons["max_pct_mito"] = int(np.sum(np.asarray(adata.obs["pct_counts_mt"], dtype=float) > float(parameters["max_pct_mito"])))
    if parameters.get("min_genes") is not None and "n_genes_by_counts" in adata.obs:
        reasons["min_genes"] = int(np.sum(np.asarray(adata.obs["n_genes_by_counts"], dtype=float) < int(parameters["min_genes"])))
    if parameters.get("max_genes") is not None and "n_genes_by_counts" in adata.obs:
        reasons["max_genes"] = int(np.sum(np.asarray(adata.obs["n_genes_by_counts"], dtype=float) > int(parameters["max_genes"])))
    batch_key = "batch" if "batch" in adata.obs else None
    batch_summary = {}
    if batch_key:
        for batch in sorted(set(map(str, adata.obs[batch_key]))):
            mask = np.asarray(adata.obs[batch_key].astype(str) == batch)
            batch_summary[batch] = {"before": int(np.sum(mask)), "after": int(np.sum(mask & keep)), "removed": int(np.sum(mask & removed))}
    return {"removed_total": int(np.sum(removed)), "reason_counts": reasons, "batch_key": batch_key, "batch_summary": batch_summary}


def build_filter_mask(adata: Any, parameters: dict[str, Any], np: Any) -> Any:
    keep = np.ones(adata.n_obs, dtype=bool)
    if parameters["filter_mode"] == "mad":
        for key, n_mads, two_sided in [("total_counts", 5.0, True), ("n_genes_by_counts", 5.0, True), ("pct_counts_mt", 3.0, False)]:
            if key in adata.obs:
                keep &= ~mad_outliers(np.asarray(adata.obs[key], dtype=float), n_mads, np, two_sided)
    if parameters.get("max_pct_mito") is not None and "pct_counts_mt" in adata.obs:
        keep &= np.asarray(adata.obs["pct_counts_mt"], dtype=float) <= float(parameters["max_pct_mito"])
    if parameters.get("min_genes") is not None and "n_genes_by_counts" in adata.obs:
        keep &= np.asarray(adata.obs["n_genes_by_counts"], dtype=float) >= int(parameters["min_genes"])
    if parameters.get("max_genes") is not None and "n_genes_by_counts" in adata.obs:
        keep &= np.asarray(adata.obs["n_genes_by_counts"], dtype=float) <= int(parameters["max_genes"])
    return keep


def mad_outliers(values: Any, n_mads: float, np: Any, two_sided: bool) -> Any:
    median = np.nanmedian(values)
    mad = np.nanmedian(np.abs(values - median))
    if mad == 0:
        return np.zeros(values.shape, dtype=bool)
    high = values > median + n_mads * mad
    if not two_sided:
        return high
    return high | (values < median - n_mads * mad)


def plot_qc(adata: Any, output: Path, plt: Any, sns: Any, title: str) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for axis, metric in zip(axes, ["total_counts", "n_genes_by_counts", "pct_counts_mt"]):
        if metric in adata.obs:
            sns.histplot(adata.obs[metric], ax=axis, bins=30)
            axis.set_title(metric)
        else:
            axis.set_axis_off()
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def finish(outdir: Path, manifest: dict[str, Any], title: str) -> dict[str, Any]:
    write_manifest(outdir / "run_manifest.json", manifest)
    write_report(outdir / "report.md", manifest, title=title)
    return manifest


if __name__ == "__main__":
    raise SystemExit(main())
