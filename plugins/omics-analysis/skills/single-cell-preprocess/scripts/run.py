from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from common.env import inspect_scrna_qc_environment  # noqa: E402
from common.errors import blocker, warning  # noqa: E402
from common.io import ensure_outdir, write_json  # noqa: E402
from common.manifest import base_manifest, now_iso, write_manifest  # noqa: E402
from common.report import write_report  # noqa: E402


def approved(value: str | bool) -> bool:
    return value is True or str(value).lower() in {"1", "true", "yes", "y"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan or run single-cell preprocessing from a filtered h5ad.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--config")
    parser.add_argument("--target-sum", type=float, default=10000.0)
    parser.add_argument("--hvg-flavor", default="seurat", choices=["seurat", "cell_ranger", "seurat_v3"])
    parser.add_argument("--n-top-genes", type=int, default=2000)
    parser.add_argument("--scale-max-value", type=float, default=10.0)
    parser.add_argument("--n-pcs", type=int, default=50)
    parser.add_argument("--n-neighbors", type=int, default=15)
    parser.add_argument("--resolution", type=float, default=1.0)
    parser.add_argument("--random-state", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--approved", default="false")
    return parser


def main(force_plan: bool = False) -> int:
    parser = build_parser()
    args = parser.parse_args()
    if force_plan:
        args.dry_run = True
    result = run_preprocess(args)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


def run_preprocess(args: argparse.Namespace) -> dict[str, Any]:
    outdir = ensure_outdir(args.output_dir)
    input_path = Path(args.input)
    env = inspect_scrna_qc_environment()
    parameters = parameters_from_args(args)
    outputs = base_outputs(outdir)
    if env["blockers"]:
        manifest = base_manifest(
            skill="single-cell-preprocess",
            status="blocked",
            inputs={"path": str(input_path), "exists": input_path.exists()},
            outputs=outputs,
            parameters=parameters,
            errors=env["blockers"],
            warnings=env["warnings"],
        )
        manifest["environment"] = env
        return finish(outdir, manifest)
    if args.dry_run or not approved(args.approved):
        manifest = base_manifest(
            skill="single-cell-preprocess",
            status="planned",
            inputs={"path": str(input_path), "exists": input_path.exists()},
            outputs=outputs,
            parameters=parameters,
            warnings=env["warnings"],
        )
        manifest["plan"] = {
            "will_load": str(input_path),
            "will_write": ["preprocessed.h5ad", "preprocess_summary.json", "run_manifest.json", "report.md"],
            "approval_required": True,
            "steps": ["normalize_total", "log1p", "highly_variable_genes", "scale", "pca", "neighbors", "umap", "leiden"],
        }
        manifest["methods_text"] = methods_text(parameters)
        return finish(outdir, manifest)
    return execute_preprocess(input_path, outdir, parameters, env)


def parameters_from_args(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "target_sum": args.target_sum,
        "hvg_flavor": args.hvg_flavor,
        "n_top_genes": args.n_top_genes,
        "scale_max_value": args.scale_max_value,
        "n_pcs": args.n_pcs,
        "n_neighbors": args.n_neighbors,
        "resolution": args.resolution,
        "random_state": args.random_state,
    }


def base_outputs(outdir: Path) -> dict[str, str]:
    return {
        "outdir": str(outdir),
        "manifest": str(outdir / "run_manifest.json"),
        "report": str(outdir / "report.md"),
        "preprocessed_h5ad": str(outdir / "preprocessed.h5ad"),
        "summary": str(outdir / "preprocess_summary.json"),
    }


def execute_preprocess(input_path: Path, outdir: Path, parameters: dict[str, Any], env: dict[str, Any]) -> dict[str, Any]:
    import scanpy as sc

    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = list(env["warnings"])
    if not input_path.exists() or not "".join(input_path.suffixes).lower().endswith(".h5ad"):
        errors.append(blocker("UnsupportedInput", "Use an existing filtered .h5ad file for preprocessing.", "Run single-cell-rna-qc first or provide a valid .h5ad.", "load_input"))
        manifest = base_manifest(
            skill="single-cell-preprocess",
            status="failed",
            inputs={"path": str(input_path), "exists": input_path.exists()},
            outputs=base_outputs(outdir),
            parameters=parameters,
            errors=errors,
            warnings=warnings,
        )
        return finish(outdir, manifest)

    started = now_iso()
    adata = sc.read_h5ad(input_path)
    before = summarize_adata(adata)
    if adata.n_obs < 3 or adata.n_vars < 3:
        warnings.append(warning("SmallDataset", "Dataset is too small for stable PCA/neighbors/UMAP preprocessing.", "Use a larger dataset or inspect the input before downstream analysis."))
        write_basic_outputs(adata, outdir, before, before, parameters, warnings, started)
        manifest = completed_manifest(input_path, outdir, parameters, env, before, before, warnings, started)
        return finish(outdir, manifest)

    if "counts" not in adata.layers:
        adata.layers["counts"] = adata.X.copy()
        warnings.append(warning("CountsLayerCreated", "No layers['counts'] was present; the original X matrix was copied to layers['counts'] before normalization.", "Confirm X contains raw counts if count-scale values are needed later."))

    sc.pp.normalize_total(adata, target_sum=float(parameters["target_sum"]))
    sc.pp.log1p(adata)
    adata.raw = adata.copy()
    sc.pp.highly_variable_genes(adata, n_top_genes=int(parameters["n_top_genes"]), flavor=str(parameters["hvg_flavor"]))
    n_hvg = int(adata.var.get("highly_variable", []).sum()) if "highly_variable" in adata.var else 0
    if n_hvg == 0:
        warnings.append(warning("NoHighlyVariableGenes", "No highly variable genes were selected.", "Check input normalization and hvg parameters."))

    sc.pp.scale(adata, max_value=float(parameters["scale_max_value"]))
    n_comps = valid_n_pcs(adata.n_obs, adata.n_vars, int(parameters["n_pcs"]))
    if n_comps >= 1:
        sc.tl.pca(adata, n_comps=n_comps, use_highly_variable=bool(n_hvg), random_state=int(parameters["random_state"]))
        try:
            sc.pp.neighbors(adata, n_neighbors=min(int(parameters["n_neighbors"]), max(2, adata.n_obs - 1)), n_pcs=n_comps)
        except Exception as exc:
            warnings.append(warning("NeighborsSkipped", f"Neighbor graph construction failed: {exc}", "Check PCA output and Scanpy neighbor dependencies."))
        if "neighbors" in adata.uns:
            try:
                sc.tl.umap(adata, random_state=int(parameters["random_state"]))
            except Exception as exc:
                warnings.append(warning("UmapSkipped", f"UMAP failed: {exc}", "Install or repair UMAP dependencies, or continue with PCA outputs."))
            try:
                sc.tl.leiden(adata, resolution=float(parameters["resolution"]), key_added="leiden")
            except ImportError as exc:
                warnings.append(warning("LeidenSkipped", f"Leiden clustering dependency is missing: {exc}", "Install leidenalg only after explicit approval, or continue without Leiden clusters."))
            except Exception as exc:
                warnings.append(warning("LeidenSkipped", f"Leiden clustering failed: {exc}", "Inspect the neighbor graph and clustering dependencies."))
    else:
        warnings.append(warning("PcaSkipped", "PCA and graph-based steps were skipped because there are not enough cells or genes.", "Use a larger filtered h5ad."))

    after = summarize_adata(adata)
    summary = write_basic_outputs(adata, outdir, before, after, parameters, warnings, started)
    manifest = completed_manifest(input_path, outdir, parameters, env, before, after, warnings, started)
    manifest["summary"] = summary
    return finish(outdir, manifest)


def valid_n_pcs(n_obs: int, n_vars: int, requested: int) -> int:
    upper = min(n_obs - 1, n_vars - 1, requested)
    return max(0, int(upper))


def summarize_adata(adata: Any) -> dict[str, Any]:
    return {
        "n_cells": int(adata.n_obs),
        "n_genes": int(adata.n_vars),
        "n_hvg": int(adata.var["highly_variable"].sum()) if "highly_variable" in adata.var else 0,
        "obsm_keys": list(adata.obsm.keys()),
        "obs_columns": list(adata.obs.columns),
        "has_pca": "X_pca" in adata.obsm,
        "has_umap": "X_umap" in adata.obsm,
        "has_neighbors": "neighbors" in adata.uns,
        "has_leiden": "leiden" in adata.obs,
        "leiden_clusters": int(adata.obs["leiden"].nunique()) if "leiden" in adata.obs else 0,
    }


def write_basic_outputs(adata: Any, outdir: Path, before: dict[str, Any], after: dict[str, Any], parameters: dict[str, Any], warnings: list[dict[str, Any]], started: str) -> dict[str, Any]:
    preprocessed = outdir / "preprocessed.h5ad"
    adata.write_h5ad(preprocessed)
    summary = {
        "before": before,
        "after": after,
        "parameters": parameters,
        "warnings": warnings,
        "started_at": started,
        "completed_at": now_iso(),
    }
    write_json(outdir / "preprocess_summary.json", summary)
    return summary


def completed_manifest(input_path: Path, outdir: Path, parameters: dict[str, Any], env: dict[str, Any], before: dict[str, Any], after: dict[str, Any], warnings: list[dict[str, Any]], started: str) -> dict[str, Any]:
    manifest = base_manifest(
        skill="single-cell-preprocess",
        status="completed",
        inputs={"path": str(input_path)},
        outputs=base_outputs(outdir),
        parameters=parameters,
        warnings=warnings,
    )
    manifest["environment"] = env
    manifest["summary"] = {"before": before, "after": after}
    manifest["qc_summary"] = {"preprocess": after}
    manifest["interpretation"] = interpretation(after)
    manifest["methods_text"] = methods_text(parameters)
    manifest["started_at"] = started
    manifest["completed_at"] = now_iso()
    return manifest


def interpretation(after: dict[str, Any]) -> list[str]:
    notes = [
        f"Preprocessed AnnData contains {after.get('n_cells', 'unknown')} cells and {after.get('n_genes', 'unknown')} genes.",
        f"Highly variable genes selected: {after.get('n_hvg', 'unknown')}.",
    ]
    if after.get("has_umap"):
        notes.append("UMAP coordinates were written to obsm['X_umap'].")
    if after.get("has_leiden"):
        notes.append(f"Leiden clusters were written to obs['leiden'] with {after.get('leiden_clusters', 'unknown')} clusters.")
    return notes


def methods_text(parameters: dict[str, Any]) -> str:
    return (
        "Filtered single-cell RNA-seq data were normalized with Scanpy normalize_total "
        f"(target_sum={parameters['target_sum']}), log-transformed with log1p, annotated for highly variable genes "
        f"using the {parameters['hvg_flavor']} method, scaled with max_value={parameters['scale_max_value']}, "
        f"and embedded with PCA, neighborhood graph construction, UMAP, and Leiden clustering when enough cells and genes were available."
    )


def finish(outdir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    write_manifest(outdir / "run_manifest.json", manifest)
    write_report(outdir / "report.md", manifest, title="Single-cell Preprocess Report")
    return manifest


if __name__ == "__main__":
    raise SystemExit(main())
