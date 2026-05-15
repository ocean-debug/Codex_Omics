from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from common.env import inspect_scvi_environment  # noqa: E402


def validate_counts(matrix: Any, np: Any) -> bool:
    values = matrix.data if hasattr(matrix, "data") else np.asarray(matrix).ravel()
    if values.size == 0:
        return False
    sample = values[: min(values.size, 10000)]
    return bool(np.nanmin(sample) >= 0 and np.allclose(sample, np.round(sample)))


def validate(args: argparse.Namespace) -> dict[str, Any]:
    env = inspect_scvi_environment()
    if env["blockers"]:
        return {"valid": False, "issues": env["blockers"], "warnings": env["warnings"], "environment": env}
    import scanpy as sc
    import numpy as np

    adata = sc.read_h5ad(args.input)
    matrix = adata.layers[args.layer] if args.layer and args.layer in adata.layers else adata.X
    issues = []
    if not validate_counts(matrix, np):
        issues.append({"error_type": "RawCountsValidationFailed", "message": "Selected matrix is not non-negative integer-like counts."})
    if args.batch_key and args.batch_key not in adata.obs:
        issues.append({"error_type": "MissingBatchKey", "message": f"batch key not found: {args.batch_key}"})
    if args.labels_key and args.labels_key not in adata.obs:
        issues.append({"error_type": "MissingLabelsKey", "message": f"labels key not found: {args.labels_key}"})
    if args.model.upper() == "TOTALVI" and args.protein_obsm not in adata.obsm:
        issues.append({"error_type": "MissingProteinObsm", "message": f"TOTALVI expects protein data in obsm['{args.protein_obsm}']."})
    if args.model.upper() == "SCANVI":
        if not args.labels_key:
            issues.append({"error_type": "MissingLabelsKey", "message": "SCANVI requires --labels-key."})
        elif args.labels_key in adata.obs and args.unlabeled_category not in set(map(str, adata.obs[args.labels_key])):
            warnings = env["warnings"] + [{"warning_type": "NoUnlabeledCategory", "message": f"SCANVI labels do not contain '{args.unlabeled_category}'.", "suggested_fix": "Confirm labels include the unlabeled category or adjust --unlabeled-category."}]
            env["warnings"] = warnings
    if args.model.upper() == "PEAKVI" and not looks_like_peak_matrix(adata):
        issues.append({"error_type": "PeakMatrixValidationFailed", "message": "PEAKVI expects a binary or count-like chromatin accessibility matrix."})
    if args.model.upper() == "MULTIVI":
        has_modality = "modality" in adata.obs or "modality" in adata.var or any(key.lower().startswith("modality") for key in adata.uns.keys())
        if not has_modality:
            issues.append({"error_type": "MissingModalityMetadata", "message": "MULTIVI expects modality metadata in obs, var, or uns."})
    return {
        "valid": not issues,
        "model": args.model,
        "input": args.input,
        "n_obs": int(adata.n_obs),
        "n_vars": int(adata.n_vars),
        "issues": issues,
        "warnings": env["warnings"],
    }


def looks_like_peak_matrix(adata: Any) -> bool:
    names = [str(name) for name in list(adata.var_names[: min(adata.n_vars, 100)])]
    if any(":" in name and "-" in name for name in names):
        return True
    return "peak" in {str(column).lower() for column in adata.var.columns}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AnnData for scvi-tools training.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--config")
    parser.add_argument("--model", default="SCVI")
    parser.add_argument("--layer")
    parser.add_argument("--batch-key")
    parser.add_argument("--labels-key")
    parser.add_argument("--unlabeled-category", default="Unknown")
    parser.add_argument("--protein-obsm", default="protein_expression")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved", default="false")
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate(args), indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
