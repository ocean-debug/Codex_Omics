from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def validate_input(counts: Path, metadata: Path, contrast: str, sample_column: str, gene_column: str) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    result: dict[str, Any] = {
        "counts": str(counts),
        "counts_exists": counts.exists(),
        "metadata": str(metadata),
        "metadata_exists": metadata.exists(),
        "contrast": parse_contrast(contrast),
        "errors": errors,
    }
    if not counts.exists():
        errors.append({"error_type": "MissingCounts", "message": "Count matrix does not exist."})
    else:
        result["counts_inventory"] = inspect_counts(counts, gene_column)
    if not metadata.exists():
        errors.append({"error_type": "MissingMetadata", "message": "Sample metadata does not exist."})
    else:
        result["metadata_inventory"] = inspect_metadata(metadata, sample_column, result["contrast"])
    if not result["contrast"].get("variable"):
        errors.append({"error_type": "InvalidContrast", "message": "Contrast must use variable:reference:target format."})
    return result


def parse_contrast(value: str) -> dict[str, str]:
    parts = [part.strip() for part in value.split(":")]
    if len(parts) != 3 or not all(parts):
        return {"variable": "", "reference": "", "target": "", "raw": value}
    return {"variable": parts[0], "reference": parts[1], "target": parts[2], "raw": value}


def inspect_counts(path: Path, requested_gene_column: str) -> dict[str, Any]:
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        columns = reader.fieldnames or []
        rows = list(reader)
    gene_column = resolve_gene_column(columns, requested_gene_column)
    return {"format": path.suffix.lower().lstrip("."), "columns": columns, "gene_column": gene_column, "n_genes": len(rows), "n_samples": max(0, len(columns) - 1)}


def resolve_gene_column(columns: list[str], requested: str) -> str:
    if requested != "auto":
        return requested if requested in columns else ""
    for candidate in ["gene", "gene_id", "gene_name", "symbol", "feature", "id"]:
        if candidate in columns:
            return candidate
    return columns[0] if columns else ""


def inspect_metadata(path: Path, sample_column: str, contrast: dict[str, str]) -> dict[str, Any]:
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        rows = list(reader)
        columns = reader.fieldnames or []
    variable = contrast.get("variable", "")
    levels = sorted({row.get(variable, "") for row in rows if variable in row})
    return {
        "format": path.suffix.lower().lstrip("."),
        "columns": columns,
        "sample_column_present": sample_column in columns,
        "n_samples": len(rows),
        "contrast_variable_present": variable in columns,
        "contrast_levels": levels,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate bulk RNA DE inputs.")
    parser.add_argument("--counts", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--contrast", required=True)
    parser.add_argument("--sample-column", default="sample")
    parser.add_argument("--gene-column", default="auto")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved", default="false")
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    result = validate_input(Path(args.counts), Path(args.metadata), args.contrast, args.sample_column, args.gene_column)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
