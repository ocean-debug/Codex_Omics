from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from common.env import detect_python_environment, inspect_packages  # noqa: E402
from common.errors import missing_software, warning  # noqa: E402


def inspect_integration_environment() -> dict[str, object]:
    py_env = detect_python_environment()
    packages = inspect_packages(
        [
            ("anndata", "anndata"),
            ("scanpy", "scanpy"),
            ("numpy", "numpy"),
            ("pandas", "pandas"),
            ("scipy", "scipy"),
            ("scvi-tools", "scvi"),
            ("harmonypy", "harmonypy"),
            ("scanorama", "scanorama"),
        ]
    )
    commands = py_env["install_commands"]
    blockers = []
    for name in ["anndata", "scanpy", "numpy", "pandas", "scipy"]:
        if not packages.get(name, {}).get("available"):
            blockers.append(missing_software(name, f"Install scRNA dependencies: {commands['scrna_qc'][0]}"))
    warnings = []
    if not packages.get("scvi-tools", {}).get("available"):
        warnings.append(warning("SCVIUnavailable", "scvi-tools is not available; scvi backend will be blocked.", "Use scanpy-combat or activate a scvi-tools environment."))
    if not packages.get("harmonypy", {}).get("available"):
        warnings.append(warning("HarmonyUnavailable", "harmonypy is not available; harmony backend will be blocked.", "Use scanpy-combat or install Harmony after approval."))
    if not packages.get("scanorama", {}).get("available"):
        warnings.append(warning("ScanoramaUnavailable", "scanorama is not available; scanorama backend will be blocked.", "Use scanpy-combat or install Scanorama after approval."))
    return {
        "status": "blocked" if blockers else ("warning" if warnings else "ready"),
        "python_environment": py_env,
        "python_packages": packages,
        "blockers": blockers,
        "warnings": warnings,
        "install_hints": [commands["scrna_qc"][0], "Ask the user before installing integration backends or GPU packages."],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check single-cell integration dependencies.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved", default="false")
    parser.add_argument("--write-manifest", action="store_true")
    parser.parse_args()
    print(json.dumps(inspect_integration_environment(), indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
