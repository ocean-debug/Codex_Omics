from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from check_environment import inspect_integration_environment  # noqa: E402


def validate_input(path: Path, batch_key: str, label_key: str, backend: str) -> dict[str, Any]:
    suffix = "".join(path.suffixes).lower()
    supported = suffix.endswith(".h5ad")
    result: dict[str, Any] = {
        "input": str(path),
        "exists": path.exists(),
        "supported": bool(path.exists() and supported),
        "backend": backend,
        "batch_key": batch_key,
        "label_key": label_key,
        "errors": [] if path.exists() and supported else [{"error_type": "UnsupportedInput", "message": "Use a preprocessed .h5ad file for integration."}],
    }
    env = inspect_integration_environment()
    result["environment_status"] = env["status"]
    if path.exists() and supported and not env["blockers"]:
        result["anndata"] = inspect_h5ad(path, batch_key, label_key)
    return result


def inspect_h5ad(path: Path, batch_key: str, label_key: str) -> dict[str, Any]:
    import scanpy as sc

    adata = sc.read_h5ad(path, backed="r")
    obs_columns = list(adata.obs.columns)
    batch_counts: dict[str, int] = {}
    if batch_key in adata.obs:
        counts = adata.obs[batch_key].astype(str).value_counts()
        batch_counts = {str(key): int(value) for key, value in counts.items()}
    return {
        "n_obs": int(adata.n_obs),
        "n_vars": int(adata.n_vars),
        "obs_columns": obs_columns,
        "batch_key_present": batch_key in adata.obs,
        "label_key_present": bool(label_key and label_key in adata.obs),
        "batch_counts": batch_counts,
        "layers": list(adata.layers.keys()),
        "obsm_keys": list(adata.obsm.keys()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a single-cell integration h5ad input.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--batch-key", default="batch")
    parser.add_argument("--label-key", default="")
    parser.add_argument("--backend", default="scanpy-combat", choices=["scanpy-combat", "scvi", "harmony", "scanorama"])
    parser.add_argument("--config")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved", default="false")
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate_input(Path(args.input), args.batch_key, args.label_key, args.backend), indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
