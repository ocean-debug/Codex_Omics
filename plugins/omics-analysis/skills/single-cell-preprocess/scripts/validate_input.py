from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from common.env import inspect_scrna_qc_environment  # noqa: E402


def validate_input(path: Path) -> dict[str, Any]:
    suffix = "".join(path.suffixes).lower()
    supported = suffix.endswith(".h5ad")
    result: dict[str, Any] = {
        "input": str(path),
        "exists": path.exists(),
        "supported": bool(path.exists() and supported),
        "format": "h5ad" if supported else "unknown",
        "errors": [] if path.exists() and supported else [{"error_type": "UnsupportedInput", "message": "Use a filtered .h5ad file for preprocessing."}],
    }
    env = inspect_scrna_qc_environment()
    result["environment_status"] = env["status"]
    if path.exists() and supported and not env["blockers"]:
        result["anndata"] = inspect_h5ad(path)
    return result


def inspect_h5ad(path: Path) -> dict[str, Any]:
    import scanpy as sc

    adata = sc.read_h5ad(path, backed="r")
    return {
        "n_obs": int(adata.n_obs),
        "n_vars": int(adata.n_vars),
        "layers": list(adata.layers.keys()),
        "obs_columns": list(adata.obs.columns),
        "obsm_keys": list(adata.obsm.keys()),
        "var_columns": list(adata.var.columns),
        "has_pca": "X_pca" in adata.obsm,
        "has_umap": "X_umap" in adata.obsm,
        "has_neighbors": "neighbors" in adata.uns,
        "has_leiden": "leiden" in adata.obs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a single-cell preprocessing h5ad input.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--config")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved", default="false")
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate_input(Path(args.input)), indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
