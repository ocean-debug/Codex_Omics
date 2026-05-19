from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from check_environment import inspect_annotation_environment  # noqa: E402


def validate_input(args: argparse.Namespace) -> dict[str, Any]:
    path = Path(args.input)
    marker_reference = Path(args.marker_reference) if args.marker_reference else None
    model = Path(args.model) if args.model else None
    reference = Path(args.reference) if args.reference else None
    result: dict[str, Any] = {
        "input": str(path),
        "exists": path.exists(),
        "supported": path.exists() and "".join(path.suffixes).lower().endswith(".h5ad"),
        "backend": args.backend,
        "groupby": args.groupby,
        "marker_reference": str(marker_reference) if marker_reference else "",
        "model": str(model) if model else "",
        "reference": str(reference) if reference else "",
        "errors": [],
    }
    if not result["supported"]:
        result["errors"].append({"error_type": "UnsupportedInput", "message": "Use a preprocessed .h5ad file for annotation."})
        return result
    env = inspect_annotation_environment()
    result["environment_status"] = env["status"]
    if not env["blockers"]:
        result["anndata"] = inspect_h5ad(path, args.groupby)
    if args.backend == "marker-based":
        if marker_reference and marker_reference.exists():
            result["marker_reference_inventory"] = inspect_marker_reference(marker_reference)
        else:
            result["errors"].append({"error_type": "MissingMarkerReference", "message": "marker-based backend requires --marker-reference pointing to local CSV/TSV/GMT."})
    elif args.backend == "celltypist" and not (model and model.exists()):
        result["errors"].append({"error_type": "MissingCellTypistModel", "message": "CellTypist backend requires a local --model path; no download is attempted."})
    elif args.backend == "singler" and not (reference and reference.exists()):
        result["errors"].append({"error_type": "MissingSingleRReference", "message": "SingleR backend requires a local --reference path; no download is attempted."})
    elif args.backend == "scanvi" and not (model and model.exists()):
        result["errors"].append({"error_type": "MissingSCANVIModel", "message": "SCANVI backend requires a local --model path or a prepared scvi-tools handoff."})
    return result


def inspect_h5ad(path: Path, groupby: str) -> dict[str, Any]:
    import scanpy as sc

    adata = sc.read_h5ad(path, backed="r")
    group_counts: dict[str, int] = {}
    if groupby in adata.obs:
        counts = adata.obs[groupby].astype(str).value_counts()
        group_counts = {str(key): int(value) for key, value in counts.items()}
    return {
        "n_obs": int(adata.n_obs),
        "n_vars": int(adata.n_vars),
        "obs_columns": list(adata.obs.columns),
        "groupby_present": groupby in adata.obs,
        "group_counts": group_counts,
        "has_raw": adata.raw is not None,
    }


def inspect_marker_reference(path: Path) -> dict[str, Any]:
    markers = load_marker_reference_preview(path)
    return {
        "format": "gmt" if path.suffix.lower() == ".gmt" else path.suffix.lower().lstrip("."),
        "n_cell_types": len(markers),
        "n_marker_rows": sum(len(genes) for genes in markers.values()),
        "cell_types": sorted(markers)[:25],
    }


def load_marker_reference_preview(path: Path) -> dict[str, list[str]]:
    if path.suffix.lower() == ".gmt":
        result: dict[str, list[str]] = {}
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            parts = [part.strip() for part in line.split("\t") if part.strip()]
            if len(parts) >= 3:
                result[parts[0]] = parts[2:]
        return result
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    result: dict[str, list[str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        for row in reader:
            cell_type = row.get("cell_type") or row.get("label") or row.get("type")
            gene = row.get("gene") or row.get("marker") or row.get("symbol")
            if cell_type and gene:
                result.setdefault(cell_type, []).append(gene)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a single-cell annotation input.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--backend", default="marker-based", choices=["marker-based", "celltypist", "singler", "scanvi"])
    parser.add_argument("--groupby", default="leiden")
    parser.add_argument("--marker-reference")
    parser.add_argument("--model")
    parser.add_argument("--reference")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved", default="false")
    parser.add_argument("--write-manifest", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print(json.dumps(validate_input(args), indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
