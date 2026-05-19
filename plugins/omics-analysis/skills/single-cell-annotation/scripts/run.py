from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from check_environment import inspect_annotation_environment  # noqa: E402
from common.errors import blocker, warning  # noqa: E402
from common.io import ensure_outdir, write_json  # noqa: E402
from common.manifest import base_manifest, now_iso, write_manifest  # noqa: E402
from common.report import write_report  # noqa: E402


def approved(value: str | bool) -> bool:
    return value is True or str(value).lower() in {"1", "true", "yes", "y"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan or run single-cell cell type annotation.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--backend", default="marker-based", choices=["marker-based", "celltypist", "singler", "scanvi"])
    parser.add_argument("--groupby", default="leiden")
    parser.add_argument("--marker-reference")
    parser.add_argument("--model")
    parser.add_argument("--reference")
    parser.add_argument("--annotation-key", default="predicted_cell_type")
    parser.add_argument("--confidence-key", default="annotation_confidence")
    parser.add_argument("--min-score", type=float, default=0.0)
    parser.add_argument("--min-score-ratio", type=float, default=1.25)
    parser.add_argument("--use-raw", default="auto", choices=["auto", "true", "false"])
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
    result = run_annotation(args)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


def run_annotation(args: argparse.Namespace) -> dict[str, Any]:
    outdir = ensure_outdir(args.output_dir)
    input_path = Path(args.input)
    env = inspect_annotation_environment()
    parameters = parameters_from_args(args)
    outputs = base_outputs(outdir)
    if env["blockers"]:
        manifest = base_manifest(
            skill="single-cell-annotation",
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
            skill="single-cell-annotation",
            status="planned",
            inputs=base_inputs(input_path, parameters),
            outputs=outputs,
            parameters=parameters,
            warnings=env["warnings"],
        )
        manifest["environment"] = env
        manifest["plan"] = {
            "will_load": [str(input_path), backend_resource(parameters)],
            "will_write": ["annotated.h5ad", "annotations.csv", "annotation_confidence.csv", "annotation_summary.json", "run_manifest.json", "report.md"],
            "approval_required": True,
            "steps": backend_steps(str(parameters["backend"])),
        }
        manifest["methods_text"] = methods_text(parameters)
        return finish(outdir, manifest)
    if args.backend != "marker-based":
        return blocked_backend_manifest(input_path, outdir, parameters, env)
    return execute_marker_based(input_path, outdir, parameters, env)


def parameters_from_args(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "backend": args.backend,
        "groupby": args.groupby,
        "marker_reference": args.marker_reference or "",
        "model": args.model or "",
        "reference": args.reference or "",
        "annotation_key": args.annotation_key,
        "confidence_key": args.confidence_key,
        "min_score": args.min_score,
        "min_score_ratio": args.min_score_ratio,
        "use_raw": args.use_raw,
    }


def base_inputs(input_path: Path, parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(input_path),
        "exists": input_path.exists(),
        "backend": parameters["backend"],
        "groupby": parameters["groupby"],
        "marker_reference": parameters["marker_reference"],
        "model": parameters["model"],
        "reference": parameters["reference"],
    }


def base_outputs(outdir: Path) -> dict[str, str]:
    return {
        "outdir": str(outdir),
        "manifest": str(outdir / "run_manifest.json"),
        "report": str(outdir / "report.md"),
        "annotated_h5ad": str(outdir / "annotated.h5ad"),
        "annotations_csv": str(outdir / "annotations.csv"),
        "confidence_csv": str(outdir / "annotation_confidence.csv"),
        "summary": str(outdir / "annotation_summary.json"),
    }


def backend_resource(parameters: dict[str, Any]) -> str:
    backend = str(parameters["backend"])
    if backend == "marker-based":
        return str(parameters["marker_reference"])
    if backend in {"celltypist", "scanvi"}:
        return str(parameters["model"])
    if backend == "singler":
        return str(parameters["reference"])
    return ""


def backend_steps(backend: str) -> list[str]:
    if backend == "marker-based":
        return ["load_h5ad", "load_marker_reference", "score_cell_types_by_group", "write_annotations", "write_annotated_h5ad"]
    if backend == "celltypist":
        return ["check_celltypist", "load_local_model", "predict_labels", "write_annotations"]
    if backend == "singler":
        return ["check_rscript_singler", "load_local_reference", "predict_labels", "write_annotations"]
    return ["check_scvi_tools", "load_local_scanvi_model", "predict_labels", "write_annotations"]


def blocked_backend_manifest(input_path: Path, outdir: Path, parameters: dict[str, Any], env: dict[str, Any]) -> dict[str, Any]:
    backend = str(parameters["backend"])
    errors: list[dict[str, Any]] = []
    if backend == "celltypist":
        model = Path(str(parameters["model"])) if parameters["model"] else None
        packages = env.get("python_packages", {})
        if not isinstance(packages, dict) or not packages.get("celltypist", {}).get("available"):
            errors.append(blocker("CellTypistUnavailable", "celltypist is not available in the active environment.", "Install CellTypist only after approval, or use --backend marker-based.", "check_backend"))
        if not (model and model.exists()):
            errors.append(blocker("MissingCellTypistModel", "CellTypist backend requires a local model path.", "Provide --model pointing to a local CellTypist model; no model is downloaded automatically.", "check_backend"))
    elif backend == "singler":
        reference = Path(str(parameters["reference"])) if parameters["reference"] else None
        commands = env.get("commands", {})
        rscript = commands.get("Rscript", {}) if isinstance(commands, dict) else {}
        if not rscript.get("available"):
            errors.append(blocker("SingleRUnavailable", "Rscript is not available in the active environment.", "Load an R environment with SingleR, or use --backend marker-based.", "check_backend"))
        if not (reference and reference.exists()):
            errors.append(blocker("MissingSingleRReference", "SingleR backend requires a local reference path.", "Provide --reference pointing to a local SingleR reference; no reference is downloaded automatically.", "check_backend"))
    elif backend == "scanvi":
        model = Path(str(parameters["model"])) if parameters["model"] else None
        packages = env.get("python_packages", {})
        if not isinstance(packages, dict) or not packages.get("scvi-tools", {}).get("available"):
            errors.append(blocker("SCANVIUnavailable", "scvi-tools is not available in the active environment.", "Activate a scvi-tools environment or use --backend marker-based.", "check_backend"))
        if not (model and model.exists()):
            errors.append(blocker("MissingSCANVIModel", "SCANVI backend requires a local model path or prepared handoff.", "Provide --model pointing to a local SCANVI model; no reference is downloaded automatically.", "check_backend"))
    if not errors:
        errors.append(blocker("BackendExecutionDeferred", f"{backend} execution is interface-only in this release.", "Use marker-based for approved smoke testing, or add backend execution in a later task.", "check_backend"))
    manifest = base_manifest(
        skill="single-cell-annotation",
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


def execute_marker_based(input_path: Path, outdir: Path, parameters: dict[str, Any], env: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    import pandas as pd
    import scanpy as sc

    warnings: list[dict[str, Any]] = list(env["warnings"])
    errors: list[dict[str, Any]] = []
    if not input_path.exists() or not "".join(input_path.suffixes).lower().endswith(".h5ad"):
        errors.append(blocker("UnsupportedInput", "Use an existing preprocessed .h5ad file for annotation.", "Run preprocessing first or provide a valid .h5ad.", "load_input"))
        return failed_manifest(input_path, outdir, parameters, env, errors, warnings)
    marker_reference = Path(str(parameters["marker_reference"])) if parameters["marker_reference"] else None
    if marker_reference is None or not marker_reference.exists():
        errors.append(blocker("MissingMarkerReference", "marker-based annotation requires a local marker reference.", "Provide --marker-reference in CSV/TSV/GMT format.", "load_marker_reference"))
        return failed_manifest(input_path, outdir, parameters, env, errors, warnings)

    started = now_iso()
    adata = sc.read_h5ad(input_path)
    groupby = str(parameters["groupby"])
    if groupby not in adata.obs:
        errors.append(blocker("MissingGroupBy", f"Grouping column obs['{groupby}'] is not present.", "Use --groupby with an existing obs column, or run preprocessing/clustering first.", "validate_groupby"))
        return failed_manifest(input_path, outdir, parameters, env, errors, warnings)
    marker_sets = load_marker_reference(marker_reference)
    if not marker_sets:
        errors.append(blocker("EmptyMarkerReference", "No marker rows were detected in the marker reference.", "Use columns cell_type,gene,weight or GMT rows with cell type as term.", "load_marker_reference"))
        return failed_manifest(input_path, outdir, parameters, env, errors, warnings)

    matrix, var_names = expression_matrix(adata, str(parameters["use_raw"]))
    gene_index = {str(gene): idx for idx, gene in enumerate(var_names)}
    group_scores = score_groups(np, adata, matrix, gene_index, marker_sets, groupby, parameters)
    annotations = assign_annotations(pd, group_scores, parameters)
    write_annotation_tables(annotations, outdir)
    apply_annotations(adata, annotations, groupby, str(parameters["annotation_key"]), str(parameters["confidence_key"]))
    adata.write_h5ad(outdir / "annotated.h5ad")
    summary = build_summary(adata, annotations, marker_sets, parameters, warnings, started)
    write_json(outdir / "annotation_summary.json", summary)
    manifest = base_manifest(
        skill="single-cell-annotation",
        status="completed",
        inputs={**base_inputs(input_path, parameters), "groups": sorted(annotations["group"].astype(str).tolist())},
        outputs=base_outputs(outdir),
        parameters=parameters,
        warnings=warnings,
    )
    manifest["environment"] = env
    manifest["summary"] = summary
    manifest["qc_summary"] = {
        "annotation_counts": summary["annotation_counts"],
        "low_confidence_fraction": summary["low_confidence_fraction"],
    }
    manifest["interpretation"] = interpretation(summary)
    manifest["methods_text"] = methods_text(parameters)
    manifest["started_at"] = started
    manifest["completed_at"] = now_iso()
    return finish(outdir, manifest)


def failed_manifest(input_path: Path, outdir: Path, parameters: dict[str, Any], env: dict[str, Any], errors: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> dict[str, Any]:
    manifest = base_manifest(
        skill="single-cell-annotation",
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


def load_marker_reference(path: Path) -> dict[str, dict[str, float]]:
    if path.suffix.lower() == ".gmt":
        result: dict[str, dict[str, float]] = {}
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            parts = [part.strip() for part in line.split("\t") if part.strip()]
            if len(parts) >= 3:
                result[parts[0]] = {gene: 1.0 for gene in parts[2:]}
        return result
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    result: dict[str, dict[str, float]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        for row in reader:
            cell_type = row.get("cell_type") or row.get("label") or row.get("type")
            gene = row.get("gene") or row.get("marker") or row.get("symbol")
            if not cell_type or not gene:
                continue
            result.setdefault(str(cell_type).strip(), {})[str(gene).strip()] = safe_float(row.get("weight"), 1.0)
    return result


def expression_matrix(adata: Any, use_raw: str) -> tuple[Any, list[str]]:
    if use_raw == "true" or (use_raw == "auto" and adata.raw is not None):
        return adata.raw.X, [str(gene) for gene in adata.raw.var_names]
    return adata.X, [str(gene) for gene in adata.var_names]


def score_groups(np: Any, adata: Any, matrix: Any, gene_index: dict[str, int], marker_sets: dict[str, dict[str, float]], groupby: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    groups = sorted(adata.obs[groupby].astype(str).unique())
    for group in groups:
        mask = (adata.obs[groupby].astype(str) == group).to_numpy()
        group_matrix = matrix[mask, :]
        scores = []
        for cell_type, genes in marker_sets.items():
            present = [(gene, weight) for gene, weight in genes.items() if gene in gene_index]
            if not present:
                scores.append({"cell_type": cell_type, "score": 0.0, "matched_genes": []})
                continue
            indices = [gene_index[gene] for gene, _ in present]
            weights = np.array([weight for _, weight in present], dtype=float)
            values = group_matrix[:, indices]
            if hasattr(values, "toarray"):
                values = values.toarray()
            mean_expression = np.asarray(values).mean(axis=0)
            score = float(np.dot(mean_expression, weights) / max(float(weights.sum()), 1e-9))
            scores.append({"cell_type": cell_type, "score": score, "matched_genes": [gene for gene, _ in present]})
        scores = sorted(scores, key=lambda item: (-float(item["score"]), str(item["cell_type"])))
        top = scores[0]
        second = float(scores[1]["score"]) if len(scores) > 1 else 0.0
        ratio = float(top["score"]) / max(second, 1e-9) if second > 0 else math.inf if float(top["score"]) > 0 else 0.0
        rows.append(
            {
                "group": group,
                "predicted_cell_type": top["cell_type"] if float(top["score"]) > float(parameters["min_score"]) else "Unknown",
                "score": float(top["score"]),
                "second_best_score": second,
                "score_ratio": ratio,
                "matched_genes": ";".join(top["matched_genes"]),
                "confidence_level": confidence_level(float(top["score"]), ratio, parameters),
            }
        )
    return rows


def confidence_level(score: float, ratio: float, parameters: dict[str, Any]) -> str:
    if score <= float(parameters["min_score"]):
        return "low"
    if ratio >= float(parameters["min_score_ratio"]) * 1.5:
        return "high"
    if ratio >= float(parameters["min_score_ratio"]):
        return "medium"
    return "low"


def assign_annotations(pd: Any, rows: list[dict[str, Any]], parameters: dict[str, Any]) -> Any:
    columns = ["group", "predicted_cell_type", "score", "second_best_score", "score_ratio", "matched_genes", "confidence_level"]
    frame = pd.DataFrame(rows, columns=columns)
    return frame.sort_values(["group"]).reset_index(drop=True)


def write_annotation_tables(annotations: Any, outdir: Path) -> None:
    annotations.to_csv(outdir / "annotations.csv", index=False)
    annotations[["group", "predicted_cell_type", "confidence_level", "score", "score_ratio"]].to_csv(outdir / "annotation_confidence.csv", index=False)


def apply_annotations(adata: Any, annotations: Any, groupby: str, annotation_key: str, confidence_key: str) -> None:
    label_map = {str(row["group"]): str(row["predicted_cell_type"]) for _, row in annotations.iterrows()}
    confidence_map = {str(row["group"]): str(row["confidence_level"]) for _, row in annotations.iterrows()}
    adata.obs[annotation_key] = adata.obs[groupby].astype(str).map(label_map).fillna("Unknown")
    adata.obs[confidence_key] = adata.obs[groupby].astype(str).map(confidence_map).fillna("low")


def build_summary(adata: Any, annotations: Any, marker_sets: dict[str, dict[str, float]], parameters: dict[str, Any], warnings: list[dict[str, Any]], started: str) -> dict[str, Any]:
    annotation_counts = {str(key): int(value) for key, value in adata.obs[str(parameters["annotation_key"])].astype(str).value_counts().items()}
    low_conf = int((adata.obs[str(parameters["confidence_key"])].astype(str) == "low").sum())
    return {
        "backend": parameters["backend"],
        "n_cells": int(adata.n_obs),
        "n_genes": int(adata.n_vars),
        "groupby": parameters["groupby"],
        "n_groups": int(len(annotations)),
        "n_cell_types": int(len(annotation_counts)),
        "marker_reference_cell_types": int(len(marker_sets)),
        "annotation_counts": annotation_counts,
        "low_confidence_fraction": float(low_conf / max(int(adata.n_obs), 1)),
        "top_annotations": annotations[["group", "predicted_cell_type", "confidence_level", "score"]].to_dict(orient="records"),
        "warnings": warnings,
        "started_at": started,
        "completed_at": now_iso(),
    }


def interpretation(summary: dict[str, Any]) -> list[str]:
    notes = [
        f"Annotation used backend {summary.get('backend', 'unknown')} over {summary.get('n_groups', 'unknown')} group(s).",
        f"Assigned {summary.get('n_cell_types', 'unknown')} predicted cell type(s) across {summary.get('n_cells', 'unknown')} cells.",
        f"Low-confidence cell fraction: {summary.get('low_confidence_fraction', 'unknown')}.",
    ]
    for row in list(summary.get("top_annotations") or [])[:5]:
        notes.append(f"Group {row.get('group')} -> {row.get('predicted_cell_type')} ({row.get('confidence_level')}).")
    return notes


def methods_text(parameters: dict[str, Any]) -> str:
    backend = parameters["backend"]
    if backend == "marker-based":
        return (
            "Cell type annotation was performed with a local marker reference. "
            f"Cells were grouped by obs['{parameters['groupby']}']; marker expression was scored per group, "
            "top labels were assigned to all cells in each group, and confidence was derived from top-vs-second score separation."
        )
    return (
        f"Cell type annotation was planned for backend {backend}. "
        "This release validates local dependencies and reference/model paths but does not download resources automatically."
    )


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def finish(outdir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    write_manifest(outdir / "run_manifest.json", manifest)
    write_report(outdir / "report.md", manifest, title="Single-cell Annotation Report")
    return manifest


if __name__ == "__main__":
    raise SystemExit(main())
