from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from common.env import command_version, detect_python_environment, inspect_packages  # noqa: E402
from common.errors import missing_software, warning  # noqa: E402


def inspect_annotation_environment() -> dict[str, object]:
    py_env = detect_python_environment()
    packages = inspect_packages(
        [
            ("anndata", "anndata"),
            ("scanpy", "scanpy"),
            ("numpy", "numpy"),
            ("pandas", "pandas"),
            ("celltypist", "celltypist"),
            ("scvi-tools", "scvi"),
        ]
    )
    rscript = command_version("Rscript", ["--version"])
    blockers = []
    commands = py_env["install_commands"]
    for name in ["anndata", "scanpy", "numpy", "pandas"]:
        if not packages.get(name, {}).get("available"):
            blockers.append(missing_software(name, f"Install scRNA dependencies: {commands['scrna_qc'][0]}"))
    warnings = []
    if not packages.get("celltypist", {}).get("available"):
        warnings.append(warning("CellTypistUnavailable", "celltypist is not available; CellTypist backend will be blocked unless installed and a local model is provided.", "Use marker-based annotation or install CellTypist after approval."))
    if not rscript.get("available"):
        warnings.append(warning("SingleRUnavailable", "Rscript is not available; SingleR backend will be blocked.", "Use marker-based annotation or load an R environment with SingleR."))
    if not packages.get("scvi-tools", {}).get("available"):
        warnings.append(warning("SCANVIUnavailable", "scvi-tools is not available; SCANVI backend will be blocked unless a prepared environment is active.", "Use marker-based annotation or activate the scvi-tools environment."))
    return {
        "status": "blocked" if blockers else ("warning" if warnings else "ready"),
        "python_environment": py_env,
        "python_packages": packages,
        "commands": {"Rscript": rscript},
        "blockers": blockers,
        "warnings": warnings,
        "install_hints": [commands["scrna_qc"][0], "Ask the user before installing CellTypist, SingleR, scvi-tools, models, or references."],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check single-cell annotation dependencies.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved", default="false")
    parser.add_argument("--write-manifest", action="store_true")
    parser.parse_args()
    print(json.dumps(inspect_annotation_environment(), indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
