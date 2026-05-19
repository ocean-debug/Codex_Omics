from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from check_environment import inspect_integration_environment  # noqa: E402
from common.errors import blocker, warning  # noqa: E402
from common.io import ensure_outdir, write_json  # noqa: E402
from common.manifest import base_manifest, now_iso, write_manifest  # noqa: E402
from common.report import write_report  # noqa: E402


def approved(value: str | bool) -> bool:
    return value is True or str(value).lower() in {"1", "true", "yes", "y"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan or run single-cell batch integration from a preprocessed h5ad.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--backend", default="scanpy-combat", choices=["scanpy-combat", "scvi", "harmony", "scanorama"])
    parser.add_argument("--batch-key", default="batch")
    parser.add_argument("--label-key", default="")
    parser.add_argument("--n-pcs", type=int, default=20)
    parser.add_argument("--neighbors", type=int, default=10)
    parser.add_argument("--embedding-key", default="X_pca_integrated")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--approved", default="false")
    parser.add_argument("--config")
    return parser


def main(force_plan: bool = False) -> int:
    parser = build_parser()
    args = parser.parse_args()
    if force_plan:
        args.dry_run = True
    result = run_integration(args)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


def run_integration(args: argparse.Namespace) -> dict[str, Any]:
    outdir = ensure_outdir(args.output_dir)
    input_path = Path(args.input)
    env = inspect_integration_environment()
    parameters = parameters_from_args(args)
    outputs = base_outputs(outdir)
    if env["blockers"]:
        manifest = base_manifest(
            skill="single-cell-integration",
            status="blocked",
            inputs=base_inputs(input_path, parameters),
            outputs=outputs,
            parameters=parameters,
            errors=env["blockers"],
            warnings=env["warnings"],
        )
        manifest["environment"] = env
        return finish(outdir, manifest)
    if args.dry_run or not approved(args.approved):
        manifest = base_manifest(
            skill="single-cell-integration",
            status="planned",
            inputs=base_inputs(input_path, parameters),
            outputs=outputs,
            parameters=parameters,
            warnings=env["warnings"],
        )
        manifest["environment"] = env
        manifest["plan"] = {
            "will_load": str(input_path),
            "will_write": ["integrated.h5ad", "integration_summary.json", "batch_diagnostics.csv", "run_manifest.json", "report.md"],
            "approval_required": True,
            "steps": backend_steps(str(parameters["backend"])),
        }
        manifest["methods_text"] = methods_text(parameters)
        return finish(outdir, manifest)
    if args.backend != "scanpy-combat":
        return blocked_backend_manifest(input_path, outdir, parameters, env)
    return execute_scanpy_combat(input_path, outdir, parameters, env)


def parameters_from_args(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "backend": args.backend,
        "batch_key": args.batch_key,
        "label_key": args.label_key,
        "n_pcs": args.n_pcs,
        "neighbors": args.neighbors,
        "embedding_key": args.embedding_key,
    }


def base_inputs(input_path: Path, parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(input_path),
        "exists": input_path.exists(),
        "backend": parameters["backend"],
        "batch_key": parameters["batch_key"],
        "label_key": parameters["label_key"],
    }


def base_outputs(outdir: Path) -> dict[str, str]:
    return {
        "outdir": str(outdir),
        "manifest": str(outdir / "run_manifest.json"),
        "report": str(outdir / "report.md"),
        "integrated_h5ad": str(outdir / "integrated.h5ad"),
        "summary": str(outdir / "integration_summary.json"),
        "batch_diagnostics": str(outdir / "batch_diagnostics.csv"),
    }


def backend_steps(backend: str) -> list[str]:
    if backend == "scanpy-combat":
        return ["load_h5ad", "validate_batch_key", "run_scanpy_combat", "compute_pca_neighbors_umap_if_possible", "write_integrated_h5ad"]
    if backend == "scvi":
        return ["check_scvi_tools", "handoff_to_scvi_tools", "record_blocked_or_handoff_plan"]
    if backend == "harmony":
        return ["check_harmonypy", "run_harmony_or_block"]
    return ["check_scanorama", "run_scanorama_or_block"]


def blocked_backend_manifest(input_path: Path, outdir: Path, parameters: dict[str, Any], env: dict[str, Any]) -> dict[str, Any]:
    backend = str(parameters["backend"])
    packages = env.get("python_packages", {})
    errors: list[dict[str, Any]] = []
    if backend == "scvi":
        if not isinstance(packages, dict) or not packages.get("scvi-tools", {}).get("available"):
            errors.append(blocker("SCVIUnavailable", "scvi-tools is not available in the active environment.", "Activate scvi-tools or use --backend scanpy-combat.", "check_backend"))
        errors.append(blocker("BackendExecutionDeferred", "scvi integration should be executed through the scvi-tools adapter in this release.", "Use scvi-tools train_model.py for approved SCVI runs, or add a handoff executor later.", "check_backend"))
    elif backend == "harmony":
        if not isinstance(packages, dict) or not packages.get("harmonypy", {}).get("available"):
            errors.append(blocker("HarmonyUnavailable", "harmonypy is not available in the active environment.", "Install Harmony only after approval, or use --backend scanpy-combat.", "check_backend"))
        else:
            errors.append(blocker("BackendExecutionDeferred", "Harmony execution is interface-only in this release.", "Use scanpy-combat for approved smoke testing, or add Harmony execution later.", "check_backend"))
    elif backend == "scanorama":
        if not isinstance(packages, dict) or not packages.get("scanorama", {}).get("available"):
            errors.append(blocker("ScanoramaUnavailable", "scanorama is not available in the active environment.", "Install Scanorama only after approval, or use --backend scanpy-combat.", "check_backend"))
        else:
            errors.append(blocker("BackendExecutionDeferred", "Scanorama execution is interface-only in this release.", "Use scanpy-combat for approved smoke testing, or add Scanorama execution later.", "check_backend"))
    manifest = base_manifest(
        skill="single-cell-integration",
        status="blocked",
        inputs=base_inputs(input_path, parameters),
        outputs=base_outputs(outdir),
        parameters=parameters,
        errors=errors,
        warnings=env["warnings"],
    )
    manifest["environment"] = env
    manifest["auto_fix_plan"] = [error["suggested_fix"] for error in errors if error.get("suggested_fix")]
    manifest["methods_text"] = methods_text(parameters)
    return finish(outdir, manifest)


def execute_scanpy_combat(input_path: Path, outdir: Path, parameters: dict[str, Any], env: dict[str, Any]) -> dict[str, Any]:
    import scanpy as sc

    warnings: list[dict[str, Any]] = list(env["warnings"])
    errors: list[dict[str, Any]] = []
    if not input_path.exists() or not "".join(input_path.suffixes).lower().endswith(".h5ad"):
        errors.append(blocker("UnsupportedInput", "Use an existing preprocessed .h5ad file for integration.", "Run single-cell-preprocess first or provide a valid .h5ad.", "load_input"))
        return failed_manifest(input_path, outdir, parameters, env, errors, warnings)
    started = now_iso()
    adata = sc.read_h5ad(input_path)
    batch_key = str(parameters["batch_key"])
    if batch_key not in adata.obs:
        errors.append(blocker("MissingBatchKey", f"Batch column obs['{batch_key}'] is not present.", "Use --batch-key with an existing obs column.", "validate_batch_key"))
        return failed_manifest(input_path, outdir, parameters, env, errors, warnings)
    batch_counts = batch_counts_for(adata, batch_key)
    if len(batch_counts) < 2:
        warnings.append(warning("SingleBatch", "Only one batch was detected; ComBat integration may not change the data.", "Confirm the correct --batch-key."))
    before = diagnostics_for(adata, batch_key, "before")
    try:
        sc.pp.combat(adata, key=batch_key)
    except Exception as exc:
        errors.append(blocker("CombatFailed", f"scanpy.pp.combat failed: {exc}", "Check matrix values and batch labels; use another integration backend if needed.", "run_combat"))
        return failed_manifest(input_path, outdir, parameters, env, errors, warnings)
    after = diagnostics_for(adata, batch_key, "after")
    maybe_compute_embedding(sc, adata, parameters, warnings)
    adata.write_h5ad(outdir / "integrated.h5ad")
    write_batch_diagnostics(outdir / "batch_diagnostics.csv", before + after)
    summary = build_summary(adata, batch_counts, before, after, parameters, warnings, started)
    write_json(outdir / "integration_summary.json", summary)
    manifest = base_manifest(
        skill="single-cell-integration",
        status="completed",
        inputs={**base_inputs(input_path, parameters), "batch_counts": batch_counts},
        outputs=base_outputs(outdir),
        parameters=parameters,
        warnings=warnings,
    )
    manifest["environment"] = env
    manifest["summary"] = summary
    manifest["qc_summary"] = {"batch_counts": batch_counts, "has_umap": summary["has_umap"], "embedding_key": summary["embedding_key"]}
    manifest["interpretation"] = interpretation(summary)
    manifest["methods_text"] = methods_text(parameters)
    manifest["started_at"] = started
    manifest["completed_at"] = now_iso()
    return finish(outdir, manifest)


def failed_manifest(input_path: Path, outdir: Path, parameters: dict[str, Any], env: dict[str, Any], errors: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> dict[str, Any]:
    manifest = base_manifest(
        skill="single-cell-integration",
        status="failed",
        inputs=base_inputs(input_path, parameters),
        outputs=base_outputs(outdir),
        parameters=parameters,
        errors=errors,
        warnings=warnings,
    )
    manifest["environment"] = env
    manifest["auto_fix_plan"] = [error["suggested_fix"] for error in errors if error.get("suggested_fix")]
    return finish(outdir, manifest)


def batch_counts_for(adata: Any, batch_key: str) -> dict[str, int]:
    counts = adata.obs[batch_key].astype(str).value_counts()
    return {str(key): int(value) for key, value in counts.items()}


def diagnostics_for(adata: Any, batch_key: str, stage: str) -> list[dict[str, Any]]:
    rows = []
    for batch, count in batch_counts_for(adata, batch_key).items():
        rows.append({"stage": stage, "batch": batch, "n_cells": count, "n_genes": int(adata.n_vars)})
    return rows


def maybe_compute_embedding(sc: Any, adata: Any, parameters: dict[str, Any], warnings: list[dict[str, Any]]) -> None:
    if int(adata.n_obs) < 3 or int(adata.n_vars) < 2:
        warnings.append(warning("EmbeddingSkipped", "PCA/neighbors/UMAP were skipped because the dataset is too small.", "Use a larger h5ad for embedding diagnostics."))
        return
    try:
        n_comps = min(int(parameters["n_pcs"]), int(adata.n_obs) - 1, int(adata.n_vars) - 1)
        if n_comps < 1:
            warnings.append(warning("EmbeddingSkipped", "PCA was skipped because n_pcs resolved below 1.", "Use a larger h5ad or lower --n-pcs."))
            return
        sc.pp.pca(adata, n_comps=n_comps)
        adata.obsm[str(parameters["embedding_key"])] = adata.obsm["X_pca"].copy()
        sc.pp.neighbors(adata, n_neighbors=min(int(parameters["neighbors"]), max(2, int(adata.n_obs) - 1)), n_pcs=n_comps)
        sc.tl.umap(adata)
    except Exception as exc:
        warnings.append(warning("EmbeddingSkipped", f"Integrated embedding diagnostics failed: {exc}", "Inspect integrated.h5ad directly or install optional dependencies."))


def write_batch_diagnostics(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = ["stage", "batch", "n_cells", "n_genes"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_summary(adata: Any, batch_counts: dict[str, int], before: list[dict[str, Any]], after: list[dict[str, Any]], parameters: dict[str, Any], warnings: list[dict[str, Any]], started: str) -> dict[str, Any]:
    return {
        "backend": parameters["backend"],
        "batch_key": parameters["batch_key"],
        "label_key": parameters["label_key"],
        "n_cells": int(adata.n_obs),
        "n_genes": int(adata.n_vars),
        "n_batches": int(len(batch_counts)),
        "batch_counts": batch_counts,
        "embedding_key": parameters["embedding_key"] if parameters["embedding_key"] in adata.obsm else "",
        "has_umap": "X_umap" in adata.obsm,
        "diagnostics_rows": len(before) + len(after),
        "warnings": warnings,
        "started_at": started,
        "completed_at": now_iso(),
    }


def interpretation(summary: dict[str, Any]) -> list[str]:
    notes = [
        f"Integration used backend {summary.get('backend', 'unknown')} with batch key {summary.get('batch_key', 'unknown')}.",
        f"Integrated {summary.get('n_cells', 'unknown')} cells across {summary.get('n_batches', 'unknown')} batches.",
        f"Integrated embedding available: {bool(summary.get('embedding_key'))}; UMAP available: {summary.get('has_umap', 'unknown')}.",
    ]
    return notes


def methods_text(parameters: dict[str, Any]) -> str:
    if parameters["backend"] == "scanpy-combat":
        return (
            "Single-cell integration was performed with Scanpy ComBat using "
            f"obs['{parameters['batch_key']}'] as the batch covariate. The corrected AnnData was written to a new h5ad, "
            "with optional PCA/neighbors/UMAP diagnostics when feasible."
        )
    return (
        f"Single-cell integration was planned for backend {parameters['backend']}. "
        "This release validates dependency readiness and records a blocked/handoff manifest unless backend execution is explicitly implemented."
    )


def finish(outdir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    write_manifest(outdir / "run_manifest.json", manifest)
    write_report(outdir / "report.md", manifest, title="Single-cell Integration Report")
    return manifest


if __name__ == "__main__":
    raise SystemExit(main())
