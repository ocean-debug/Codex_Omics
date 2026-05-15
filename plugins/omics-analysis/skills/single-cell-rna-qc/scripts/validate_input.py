from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from common.env import inspect_scrna_qc_environment  # noqa: E402


def validate_input(path: Path) -> dict[str, object]:
    suffix = "".join(path.suffixes).lower()
    supported = suffix.endswith(".h5ad") or suffix.endswith(".h5") or path.is_dir()
    result: dict[str, Any] = {
        "input": str(path),
        "exists": path.exists(),
        "supported": bool(path.exists() and supported),
        "format": "h5ad" if suffix.endswith(".h5ad") else ("10x_h5" if suffix.endswith(".h5") else ("10x_mtx_dir" if path.is_dir() else "unknown")),
        "errors": [] if path.exists() and supported else [{"error_type": "UnsupportedInput", "message": "Use .h5ad, 10x .h5, or a 10x MTX directory."}],
    }
    env = inspect_scrna_qc_environment()
    result["environment_status"] = env["status"]
    if path.exists() and suffix.endswith(".h5ad") and not env["blockers"]:
        result["anndata"] = inspect_h5ad(path)
    return result


def inspect_h5ad(path: Path) -> dict[str, Any]:
    import scanpy as sc
    import numpy as np

    adata = sc.read_h5ad(path, backed="r")
    layers = list(adata.layers.keys())
    matrix = adata.layers["counts"] if "counts" in layers else adata.X
    values = matrix.data if hasattr(matrix, "data") else np.asarray(matrix).ravel()
    sample = np.asarray(values[: min(values.size, 20000)], dtype=float) if values.size else np.asarray([], dtype=float)
    integer_like = bool(sample.size and np.nanmin(sample) >= 0 and np.allclose(sample, np.round(sample)))
    return {
        "n_obs": int(adata.n_obs),
        "n_vars": int(adata.n_vars),
        "layers": layers,
        "obs_columns": list(adata.obs.columns),
        "counts_source": "layers['counts']" if "counts" in layers else "X",
        "integer_like_counts": integer_like,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a single-cell RNA-seq QC input path.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--config")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved", default="false")
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate_input(Path(args.input)), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
