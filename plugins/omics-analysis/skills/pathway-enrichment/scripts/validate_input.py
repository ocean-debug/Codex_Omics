from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))


def validate_input(input_path: Path, gene_sets: Path | None, gene_column: str, group_column: str) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    result: dict[str, Any] = {
        "input": str(input_path),
        "exists": input_path.exists(),
        "gene_sets": str(gene_sets) if gene_sets else "",
        "gene_sets_exists": bool(gene_sets and gene_sets.exists()),
        "gene_column": gene_column,
        "group_column": group_column,
        "errors": errors,
    }
    if not input_path.exists():
        errors.append({"error_type": "MissingInput", "message": "Input gene list or marker table does not exist."})
        return result
    result["input_inventory"] = inspect_gene_input(input_path, gene_column, group_column)
    if gene_sets:
        if gene_sets.exists():
            result["gene_set_inventory"] = inspect_gene_sets(gene_sets)
        else:
            errors.append({"error_type": "MissingGeneSets", "message": "Gene set file does not exist."})
    return result


def inspect_gene_input(path: Path, gene_column: str, group_column: str) -> dict[str, Any]:
    if path.suffix.lower() in {".csv", ".tsv"}:
        delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            rows = list(reader)
        columns = reader.fieldnames or []
        resolved_gene_column = resolve_gene_column(columns, gene_column)
        groups = sorted({row.get(group_column, "all") or "all" for row in rows}) if group_column in columns else ["all"]
        return {
            "format": path.suffix.lower().lstrip("."),
            "columns": columns,
            "n_rows": len(rows),
            "resolved_gene_column": resolved_gene_column,
            "group_column_present": group_column in columns,
            "groups": groups[:25],
        }
    genes = [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip() and not line.startswith("#")]
    return {"format": "gene_list", "n_rows": len(genes), "resolved_gene_column": "line", "group_column_present": False, "groups": ["all"]}


def inspect_gene_sets(path: Path) -> dict[str, Any]:
    gene_sets = load_gene_sets_preview(path)
    return {
        "format": "gmt" if path.suffix.lower() == ".gmt" else path.suffix.lower().lstrip("."),
        "n_terms": len(gene_sets),
        "sample_terms": list(gene_sets)[:10],
    }


def resolve_gene_column(columns: list[str], requested: str) -> str:
    if requested != "auto":
        return requested if requested in columns else ""
    for candidate in ["names", "gene", "genes", "symbol", "gene_symbol", "feature"]:
        if candidate in columns:
            return candidate
    return columns[0] if columns else ""


def load_gene_sets_preview(path: Path) -> dict[str, list[str]]:
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
            term = row.get("term") or row.get("pathway") or row.get("set")
            gene = row.get("gene") or row.get("genes") or row.get("symbol")
            if term and gene:
                result.setdefault(term, []).append(gene)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate pathway enrichment inputs.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--gene-sets")
    parser.add_argument("--gene-column", default="auto")
    parser.add_argument("--group-column", default="group")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved", default="false")
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    gene_sets = Path(args.gene_sets) if args.gene_sets else None
    print(json.dumps(validate_input(Path(args.input), gene_sets, args.gene_column, args.group_column), indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
