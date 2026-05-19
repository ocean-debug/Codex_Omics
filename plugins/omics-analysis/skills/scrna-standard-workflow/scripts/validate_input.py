from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def validate_input(input_path: Path, marker_reference: Path | None, gene_sets: Path | None) -> dict[str, Any]:
    errors = []
    suffix = "".join(input_path.suffixes).lower()
    if not input_path.exists() or not suffix.endswith(".h5ad"):
        errors.append({"error_type": "UnsupportedInput", "message": "Use an existing .h5ad file as the workflow input."})
    if marker_reference is not None and not marker_reference.exists():
        errors.append({"error_type": "MissingMarkerReference", "message": f"Marker reference does not exist: {marker_reference}"})
    if gene_sets is not None and not gene_sets.exists():
        errors.append({"error_type": "MissingGeneSets", "message": f"Gene set file does not exist: {gene_sets}"})
    return {
        "input": str(input_path),
        "exists": input_path.exists(),
        "supported": input_path.exists() and suffix.endswith(".h5ad") and not errors,
        "marker_reference": str(marker_reference) if marker_reference else "",
        "gene_sets": str(gene_sets) if gene_sets else "",
        "errors": errors,
    }


def optional_path(value: str) -> Path | None:
    return Path(value) if value else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate scRNA standard workflow inputs.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--marker-reference", default="")
    parser.add_argument("--gene-sets", default="")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved", default="false")
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate_input(Path(args.input), optional_path(args.marker_reference), optional_path(args.gene_sets)), indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
