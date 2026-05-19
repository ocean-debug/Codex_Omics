from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from common.env import detect_python_environment  # noqa: E402
from common.errors import blocker, warning  # noqa: E402
from common.io import ensure_outdir, write_json  # noqa: E402
from common.manifest import base_manifest, now_iso, write_manifest  # noqa: E402
from common.report import write_report  # noqa: E402


def approved(value: str | bool) -> bool:
    return value is True or str(value).lower() in {"1", "true", "yes", "y"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan or run lightweight pathway enrichment from marker tables or gene lists.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--gene-sets")
    parser.add_argument("--config")
    parser.add_argument("--mode", default="ora", choices=["ora", "gsea"])
    parser.add_argument("--gene-column", default="auto")
    parser.add_argument("--group-column", default="group")
    parser.add_argument("--score-column", default="")
    parser.add_argument("--top-n", type=int, default=100)
    parser.add_argument("--min-overlap", type=int, default=2)
    parser.add_argument("--min-set-size", type=int, default=3)
    parser.add_argument("--max-set-size", type=int, default=500)
    parser.add_argument("--padj-threshold", type=float, default=0.05)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--approved", default="false")
    return parser


def main(force_plan: bool = False) -> int:
    parser = build_parser()
    args = parser.parse_args()
    if force_plan:
        args.dry_run = True
    result = run_enrichment(args)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


def run_enrichment(args: argparse.Namespace) -> dict[str, Any]:
    outdir = ensure_outdir(args.output_dir)
    input_path = Path(args.input)
    gene_sets = Path(args.gene_sets) if args.gene_sets else None
    env = inspect_environment()
    parameters = parameters_from_args(args)
    outputs = base_outputs(outdir)
    if args.dry_run or not approved(args.approved):
        manifest = base_manifest(
            skill="pathway-enrichment",
            status="planned",
            inputs={"path": str(input_path), "exists": input_path.exists(), "gene_sets": str(gene_sets) if gene_sets else "", "gene_sets_exists": bool(gene_sets and gene_sets.exists())},
            outputs=outputs,
            parameters=parameters,
            warnings=env["warnings"],
        )
        manifest["environment"] = env
        manifest["plan"] = {
            "will_load": [str(input_path), str(gene_sets) if gene_sets else ""],
            "will_write": ["enrichment.csv", "enrichment_summary.json", "run_manifest.json", "report.md"],
            "approval_required": True,
            "steps": ["load_gene_lists", "load_gene_sets", "hypergeometric_ora", "bh_adjust", "summarize_enrichment"],
        }
        manifest["methods_text"] = methods_text(parameters)
        return finish(outdir, manifest)
    return execute_enrichment(input_path, gene_sets, outdir, parameters, env)


def inspect_environment() -> dict[str, Any]:
    return {
        "status": "ready",
        "python_environment": detect_python_environment(),
        "python_packages": {},
        "blockers": [],
        "warnings": [],
        "install_hints": ["No extra packages are required for lightweight ORA."],
    }


def parameters_from_args(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "mode": args.mode,
        "gene_column": args.gene_column,
        "group_column": args.group_column,
        "score_column": args.score_column,
        "top_n": args.top_n,
        "min_overlap": args.min_overlap,
        "min_set_size": args.min_set_size,
        "max_set_size": args.max_set_size,
        "padj_threshold": args.padj_threshold,
    }


def base_outputs(outdir: Path) -> dict[str, str]:
    return {
        "outdir": str(outdir),
        "manifest": str(outdir / "run_manifest.json"),
        "report": str(outdir / "report.md"),
        "enrichment_csv": str(outdir / "enrichment.csv"),
        "summary": str(outdir / "enrichment_summary.json"),
    }


def execute_enrichment(input_path: Path, gene_sets_path: Path | None, outdir: Path, parameters: dict[str, Any], env: dict[str, Any]) -> dict[str, Any]:
    warnings: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    if parameters["mode"] != "ora":
        errors.append(blocker("UnsupportedMode", "Only ORA execution is supported in this lightweight implementation.", "Use --mode ora, or add an approved GSEA backend in a future task.", "validate_mode"))
        return failed_manifest(input_path, gene_sets_path, outdir, parameters, env, errors, warnings)
    if not input_path.exists():
        errors.append(blocker("MissingInput", "Input marker table or gene list does not exist.", "Provide markers.csv, a DE table, or a plain text gene list.", "load_input"))
    if gene_sets_path is None or not gene_sets_path.exists():
        errors.append(blocker("MissingGeneSets", "A local GMT/CSV/TSV gene set file is required for approved enrichment.", "Provide --gene-sets pointing to a local gene set file.", "load_gene_sets"))
    if errors:
        return failed_manifest(input_path, gene_sets_path, outdir, parameters, env, errors, warnings)

    started = now_iso()
    query_groups = load_query_groups(input_path, parameters, warnings)
    gene_sets = load_gene_sets(gene_sets_path)
    if not query_groups:
        errors.append(blocker("NoGenes", "No input genes were detected.", "Check --gene-column or provide a non-empty gene list.", "load_gene_lists"))
    if not gene_sets:
        errors.append(blocker("NoGeneSets", "No gene sets were detected.", "Check GMT/CSV formatting.", "load_gene_sets"))
    if errors:
        return failed_manifest(input_path, gene_sets_path, outdir, parameters, env, errors, warnings)

    rows = run_ora(query_groups, gene_sets, parameters)
    write_rows(outdir / "enrichment.csv", rows)
    summary = build_summary(query_groups, gene_sets, rows, parameters, warnings, started)
    write_json(outdir / "enrichment_summary.json", summary)

    manifest = base_manifest(
        skill="pathway-enrichment",
        status="completed",
        inputs={"path": str(input_path), "gene_sets": str(gene_sets_path), "groups": sorted(query_groups)},
        outputs=base_outputs(outdir),
        parameters=parameters,
        warnings=warnings,
    )
    manifest["environment"] = env
    manifest["summary"] = summary
    manifest["qc_summary"] = {"top_terms": summary["top_terms"], "n_significant": summary["n_significant"]}
    manifest["interpretation"] = interpretation(summary)
    manifest["methods_text"] = methods_text(parameters)
    manifest["started_at"] = started
    manifest["completed_at"] = now_iso()
    return finish(outdir, manifest)


def failed_manifest(input_path: Path, gene_sets_path: Path | None, outdir: Path, parameters: dict[str, Any], env: dict[str, Any], errors: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> dict[str, Any]:
    manifest = base_manifest(
        skill="pathway-enrichment",
        status="failed",
        inputs={"path": str(input_path), "exists": input_path.exists(), "gene_sets": str(gene_sets_path) if gene_sets_path else "", "gene_sets_exists": bool(gene_sets_path and gene_sets_path.exists())},
        outputs=base_outputs(outdir),
        parameters=parameters,
        errors=errors,
        warnings=warnings,
    )
    manifest["environment"] = env
    return finish(outdir, manifest)


def load_query_groups(path: Path, parameters: dict[str, Any], warnings: list[dict[str, Any]]) -> dict[str, list[str]]:
    if path.suffix.lower() in {".csv", ".tsv"}:
        delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            rows = list(reader)
        columns = reader.fieldnames or []
        gene_column = resolve_gene_column(columns, str(parameters["gene_column"]))
        if not gene_column:
            warnings.append(warning("GeneColumnNotResolved", "Could not resolve a gene column from the table.", "Pass --gene-column explicitly."))
            return {}
        group_column = str(parameters["group_column"])
        score_column = str(parameters["score_column"])
        if score_column and score_column in columns:
            rows.sort(key=lambda row: safe_float(row.get(score_column)), reverse=True)
        grouped: dict[str, list[str]] = {}
        for row in rows:
            group = row.get(group_column, "all") if group_column in columns else "all"
            gene = normalize_gene(row.get(gene_column, ""))
            if gene:
                grouped.setdefault(group or "all", []).append(gene)
        return {group: unique_preserve_order(genes)[: int(parameters["top_n"])] for group, genes in grouped.items()}
    genes = [normalize_gene(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip() and not line.startswith("#")]
    return {"all": unique_preserve_order([gene for gene in genes if gene])[: int(parameters["top_n"])]}


def resolve_gene_column(columns: list[str], requested: str) -> str:
    if requested != "auto":
        return requested if requested in columns else ""
    for candidate in ["names", "gene", "genes", "symbol", "gene_symbol", "feature"]:
        if candidate in columns:
            return candidate
    return columns[0] if columns else ""


def load_gene_sets(path: Path) -> dict[str, set[str]]:
    if path.suffix.lower() == ".gmt":
        gene_sets: dict[str, set[str]] = {}
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            parts = [part.strip() for part in line.split("\t") if part.strip()]
            if len(parts) >= 3:
                gene_sets[parts[0]] = {normalize_gene(gene) for gene in parts[2:] if normalize_gene(gene)}
        return gene_sets
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    gene_sets: dict[str, set[str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        for row in reader:
            term = row.get("term") or row.get("pathway") or row.get("set")
            gene = row.get("gene") or row.get("genes") or row.get("symbol")
            if term and gene:
                gene_sets.setdefault(term, set()).add(normalize_gene(gene))
    return gene_sets


def run_ora(query_groups: dict[str, list[str]], gene_sets: dict[str, set[str]], parameters: dict[str, Any]) -> list[dict[str, Any]]:
    background = set().union(*gene_sets.values())
    universe_size = len(background)
    rows: list[dict[str, Any]] = []
    for group, genes in query_groups.items():
        query = set(genes).intersection(background)
        for term, geneset in gene_sets.items():
            if len(geneset) < int(parameters["min_set_size"]) or len(geneset) > int(parameters["max_set_size"]):
                continue
            overlap = sorted(query.intersection(geneset))
            if len(overlap) < int(parameters["min_overlap"]):
                continue
            pvalue = hypergeom_sf(universe_size, len(geneset), len(query), len(overlap))
            rows.append(
                {
                    "group": group,
                    "term": term,
                    "overlap": len(overlap),
                    "query_size": len(query),
                    "term_size": len(geneset),
                    "universe_size": universe_size,
                    "pvalue": pvalue,
                    "padj": 1.0,
                    "genes": ";".join(overlap),
                }
            )
    adjust_bh(rows)
    return sorted(rows, key=lambda row: (str(row["group"]), float(row["padj"]), float(row["pvalue"]), str(row["term"])))


def hypergeom_sf(universe_size: int, term_size: int, query_size: int, overlap: int) -> float:
    denominator = math.comb(universe_size, query_size)
    if denominator == 0:
        return 1.0
    upper = min(term_size, query_size)
    total = 0
    for k in range(overlap, upper + 1):
        if query_size - k <= universe_size - term_size:
            total += math.comb(term_size, k) * math.comb(universe_size - term_size, query_size - k)
    return min(1.0, float(total / denominator))


def adjust_bh(rows: list[dict[str, Any]]) -> None:
    ordered = sorted(enumerate(rows), key=lambda item: float(item[1]["pvalue"]))
    m = len(ordered)
    running = 1.0
    for rank_from_end, (index, row) in enumerate(reversed(ordered), start=1):
        rank = m - rank_from_end + 1
        adjusted = min(running, float(row["pvalue"]) * m / rank)
        running = adjusted
        rows[index]["padj"] = adjusted


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = ["group", "term", "overlap", "query_size", "term_size", "universe_size", "pvalue", "padj", "genes"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_summary(query_groups: dict[str, list[str]], gene_sets: dict[str, set[str]], rows: list[dict[str, Any]], parameters: dict[str, Any], warnings: list[dict[str, Any]], started: str) -> dict[str, Any]:
    threshold = float(parameters["padj_threshold"])
    significant = [row for row in rows if float(row["padj"]) <= threshold]
    top_terms: dict[str, list[str]] = {}
    for row in rows:
        group = str(row["group"])
        top_terms.setdefault(group, [])
        if len(top_terms[group]) < 5:
            top_terms[group].append(str(row["term"]))
    return {
        "mode": parameters["mode"],
        "n_groups": len(query_groups),
        "n_gene_sets": len(gene_sets),
        "n_results": len(rows),
        "n_significant": len(significant),
        "padj_threshold": threshold,
        "query_sizes": {group: len(genes) for group, genes in query_groups.items()},
        "top_terms": top_terms,
        "warnings": warnings,
        "started_at": started,
        "completed_at": now_iso(),
    }


def interpretation(summary: dict[str, Any]) -> list[str]:
    notes = [
        f"ORA tested {summary.get('n_groups', 'unknown')} gene group(s) against {summary.get('n_gene_sets', 'unknown')} gene sets.",
        f"Detected {summary.get('n_significant', 'unknown')} enriched terms at adjusted p <= {summary.get('padj_threshold', 'unknown')}.",
    ]
    for group, terms in list((summary.get("top_terms") or {}).items())[:5]:
        notes.append(f"Top terms for {group}: {', '.join(terms) if terms else 'none recorded'}.")
    return notes


def methods_text(parameters: dict[str, Any]) -> str:
    return (
        "Pathway enrichment was performed as over-representation analysis using local gene sets, "
        f"top_n={parameters['top_n']} input genes per group, min_overlap={parameters['min_overlap']}, "
        "a hypergeometric test, and Benjamini-Hochberg multiple testing correction."
    )


def normalize_gene(value: str) -> str:
    return str(value).strip()


def unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def safe_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def finish(outdir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    write_manifest(outdir / "run_manifest.json", manifest)
    write_report(outdir / "report.md", manifest, title="Pathway Enrichment Report")
    return manifest


if __name__ == "__main__":
    raise SystemExit(main())
