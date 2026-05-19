from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from statistics import mean, variance
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
    parser = argparse.ArgumentParser(description="Plan or run exploratory bulk RNA differential expression.")
    parser.add_argument("--counts", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--contrast", required=True, help="Format: variable:reference:target")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--config")
    parser.add_argument("--gene-column", default="auto")
    parser.add_argument("--sample-column", default="sample")
    parser.add_argument("--min-count", type=float, default=10.0)
    parser.add_argument("--min-samples", type=int, default=2)
    parser.add_argument("--padj-threshold", type=float, default=0.05)
    parser.add_argument("--lfc-threshold", type=float, default=1.0)
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
    result = run_bulk_de(args)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


def run_bulk_de(args: argparse.Namespace) -> dict[str, Any]:
    outdir = ensure_outdir(args.output_dir)
    counts = Path(args.counts)
    metadata = Path(args.metadata)
    contrast = parse_contrast(args.contrast)
    env = inspect_environment()
    parameters = parameters_from_args(args, contrast)
    outputs = base_outputs(outdir)
    warnings = list(env["warnings"])
    if args.dry_run or not approved(args.approved):
        manifest = base_manifest(
            skill="bulk-rna-de",
            status="planned",
            inputs={"counts": str(counts), "counts_exists": counts.exists(), "metadata": str(metadata), "metadata_exists": metadata.exists()},
            outputs=outputs,
            parameters=parameters,
            warnings=warnings,
        )
        manifest["environment"] = env
        manifest["plan"] = {
            "will_load": [str(counts), str(metadata)],
            "will_write": ["de_results.csv", "de_summary.json", "run_manifest.json", "report.md"],
            "approval_required": True,
            "steps": ["validate_counts_metadata", "normalize_log2_cpm", "welch_style_test", "bh_adjust", "summarize_de"],
        }
        manifest["methods_text"] = methods_text(parameters)
        return finish(outdir, manifest)
    return execute_bulk_de(counts, metadata, outdir, parameters, env, warnings)


def inspect_environment() -> dict[str, Any]:
    return {
        "status": "ready",
        "python_environment": detect_python_environment(),
        "python_packages": {},
        "blockers": [],
        "warnings": [
            warning(
                "ExploratoryMethod",
                "Built-in execution uses a lightweight log2-CPM Welch-style screen.",
                "Use DESeq2/edgeR/limma for publication-grade bulk RNA differential expression.",
            )
        ],
        "install_hints": ["No extra packages are required for exploratory execution."],
    }


def parse_contrast(value: str) -> dict[str, str]:
    parts = [part.strip() for part in value.split(":")]
    if len(parts) != 3 or not all(parts):
        return {"variable": "", "reference": "", "target": "", "raw": value}
    return {"variable": parts[0], "reference": parts[1], "target": parts[2], "raw": value}


def parameters_from_args(args: argparse.Namespace, contrast: dict[str, str]) -> dict[str, Any]:
    return {
        "contrast": contrast,
        "gene_column": args.gene_column,
        "sample_column": args.sample_column,
        "min_count": args.min_count,
        "min_samples": args.min_samples,
        "padj_threshold": args.padj_threshold,
        "lfc_threshold": args.lfc_threshold,
        "method": "exploratory_log2_cpm_welch",
    }


def base_outputs(outdir: Path) -> dict[str, str]:
    return {
        "outdir": str(outdir),
        "manifest": str(outdir / "run_manifest.json"),
        "report": str(outdir / "report.md"),
        "de_results": str(outdir / "de_results.csv"),
        "summary": str(outdir / "de_summary.json"),
    }


def execute_bulk_de(counts_path: Path, metadata_path: Path, outdir: Path, parameters: dict[str, Any], env: dict[str, Any], warnings: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    started = now_iso()
    if not counts_path.exists():
        errors.append(blocker("MissingCounts", "Count matrix does not exist.", "Provide --counts pointing to a CSV/TSV count matrix.", "load_counts"))
    if not metadata_path.exists():
        errors.append(blocker("MissingMetadata", "Sample metadata does not exist.", "Provide --metadata pointing to a CSV/TSV metadata table.", "load_metadata"))
    contrast = parameters["contrast"]
    if not contrast.get("variable"):
        errors.append(blocker("InvalidContrast", "Contrast must use variable:reference:target format.", "Example: --contrast condition:control:treatment", "parse_contrast"))
    if errors:
        return failed_manifest(counts_path, metadata_path, outdir, parameters, env, errors, warnings)

    counts = load_counts(counts_path, str(parameters["gene_column"]))
    metadata = load_metadata(metadata_path, str(parameters["sample_column"]))
    sample_groups = samples_for_contrast(metadata, str(parameters["sample_column"]), contrast)
    validate_counts_design(counts, sample_groups, int(parameters["min_samples"]), errors)
    if errors:
        return failed_manifest(counts_path, metadata_path, outdir, parameters, env, errors, warnings)

    rows = differential_expression(counts, sample_groups, parameters)
    write_rows(outdir / "de_results.csv", rows)
    summary = build_summary(counts, sample_groups, rows, parameters, warnings, started)
    write_json(outdir / "de_summary.json", summary)
    manifest = base_manifest(
        skill="bulk-rna-de",
        status="completed",
        inputs={"counts": str(counts_path), "metadata": str(metadata_path), "contrast": contrast, "samples": sample_groups},
        outputs=base_outputs(outdir),
        parameters=parameters,
        warnings=warnings,
    )
    manifest["environment"] = env
    manifest["summary"] = summary
    manifest["qc_summary"] = {"sample_counts": {key: len(value) for key, value in sample_groups.items()}, "n_significant": summary["n_significant"]}
    manifest["interpretation"] = interpretation(summary)
    manifest["methods_text"] = methods_text(parameters)
    manifest["started_at"] = started
    manifest["completed_at"] = now_iso()
    return finish(outdir, manifest)


def failed_manifest(counts_path: Path, metadata_path: Path, outdir: Path, parameters: dict[str, Any], env: dict[str, Any], errors: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> dict[str, Any]:
    manifest = base_manifest(
        skill="bulk-rna-de",
        status="failed",
        inputs={"counts": str(counts_path), "counts_exists": counts_path.exists(), "metadata": str(metadata_path), "metadata_exists": metadata_path.exists()},
        outputs=base_outputs(outdir),
        parameters=parameters,
        errors=errors,
        warnings=warnings,
    )
    manifest["environment"] = env
    manifest["auto_fix_plan"] = [error.get("suggested_fix", "") for error in errors if error.get("suggested_fix")]
    return finish(outdir, manifest)


def load_counts(path: Path, requested_gene_column: str) -> dict[str, dict[str, float]]:
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        columns = reader.fieldnames or []
        gene_column = resolve_gene_column(columns, requested_gene_column)
        sample_columns = [column for column in columns if column != gene_column]
        result: dict[str, dict[str, float]] = {}
        for row in reader:
            gene = str(row.get(gene_column, "")).strip()
            if not gene:
                continue
            result[gene] = {sample: safe_float(row.get(sample)) for sample in sample_columns}
    return result


def resolve_gene_column(columns: list[str], requested: str) -> str:
    if requested != "auto":
        return requested if requested in columns else columns[0] if columns else ""
    for candidate in ["gene", "gene_id", "gene_name", "symbol", "feature", "id"]:
        if candidate in columns:
            return candidate
    return columns[0] if columns else ""


def load_metadata(path: Path, sample_column: str) -> list[dict[str, str]]:
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        rows = []
        for row in reader:
            normalized = {str(key): str(value).strip() for key, value in row.items()}
            if normalized.get(sample_column):
                rows.append(normalized)
        return rows


def samples_for_contrast(metadata: list[dict[str, str]], sample_column: str, contrast: dict[str, str]) -> dict[str, list[str]]:
    variable = contrast["variable"]
    reference = contrast["reference"]
    target = contrast["target"]
    return {
        "reference": [row[sample_column] for row in metadata if row.get(variable) == reference],
        "target": [row[sample_column] for row in metadata if row.get(variable) == target],
    }


def validate_counts_design(counts: dict[str, dict[str, float]], sample_groups: dict[str, list[str]], min_samples: int, errors: list[dict[str, Any]]) -> None:
    if not counts:
        errors.append(blocker("EmptyCounts", "No genes were detected in the count matrix.", "Check the count matrix header and gene column.", "load_counts"))
        return
    available_samples = set(next(iter(counts.values())).keys())
    for group, samples in sample_groups.items():
        if len(samples) < min_samples:
            errors.append(blocker("InsufficientReplicates", f"{group} group has fewer than {min_samples} samples.", "Provide enough biological replicates or lower --min-samples only for smoke testing.", "validate_design"))
        missing = [sample for sample in samples if sample not in available_samples]
        if missing:
            errors.append(blocker("SampleMismatch", f"{group} metadata samples are missing from counts: {', '.join(missing)}", "Make count matrix sample columns match metadata sample ids.", "validate_design"))


def differential_expression(counts: dict[str, dict[str, float]], sample_groups: dict[str, list[str]], parameters: dict[str, Any]) -> list[dict[str, Any]]:
    reference = sample_groups["reference"]
    target = sample_groups["target"]
    library_sizes = library_sizes_for(counts)
    rows: list[dict[str, Any]] = []
    for gene, values in counts.items():
        total_counts = sum(values.values())
        expressed_samples = sum(1 for value in values.values() if value >= float(parameters["min_count"]))
        if total_counts < float(parameters["min_count"]) or expressed_samples < int(parameters["min_samples"]):
            continue
        ref_values = [log2_cpm(values[sample], library_sizes[sample]) for sample in reference]
        target_values = [log2_cpm(values[sample], library_sizes[sample]) for sample in target]
        mean_ref = mean(ref_values)
        mean_target = mean(target_values)
        log2fc = mean_target - mean_ref
        pvalue = welch_pvalue(ref_values, target_values)
        rows.append(
            {
                "gene": gene,
                "base_mean": total_counts / max(1, len(values)),
                "mean_reference_log2_cpm": mean_ref,
                "mean_target_log2_cpm": mean_target,
                "log2_fold_change": log2fc,
                "pvalue": pvalue,
                "padj": 1.0,
            }
        )
    adjust_bh(rows)
    return sorted(rows, key=lambda row: (float(row["padj"]), float(row["pvalue"]), str(row["gene"])))


def library_sizes_for(counts: dict[str, dict[str, float]]) -> dict[str, float]:
    samples = list(next(iter(counts.values())).keys())
    sizes = {sample: 0.0 for sample in samples}
    for values in counts.values():
        for sample in samples:
            sizes[sample] += max(0.0, values.get(sample, 0.0))
    return {sample: size if size > 0 else 1.0 for sample, size in sizes.items()}


def log2_cpm(count: float, library_size: float) -> float:
    return math.log2((max(0.0, count) / library_size) * 1_000_000.0 + 1.0)


def welch_pvalue(group_a: list[float], group_b: list[float]) -> float:
    if len(group_a) < 2 or len(group_b) < 2:
        return 1.0
    var_a = variance(group_a)
    var_b = variance(group_b)
    denom = math.sqrt(var_a / len(group_a) + var_b / len(group_b))
    if denom == 0:
        return 1.0
    z = abs((mean(group_b) - mean(group_a)) / denom)
    return max(0.0, min(1.0, math.erfc(z / math.sqrt(2.0))))


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
    fieldnames = ["gene", "base_mean", "mean_reference_log2_cpm", "mean_target_log2_cpm", "log2_fold_change", "pvalue", "padj"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_summary(counts: dict[str, dict[str, float]], sample_groups: dict[str, list[str]], rows: list[dict[str, Any]], parameters: dict[str, Any], warnings: list[dict[str, Any]], started: str) -> dict[str, Any]:
    padj_threshold = float(parameters["padj_threshold"])
    lfc_threshold = float(parameters["lfc_threshold"])
    significant = [row for row in rows if float(row["padj"]) <= padj_threshold and abs(float(row["log2_fold_change"])) >= lfc_threshold]
    up = [row for row in significant if float(row["log2_fold_change"]) > 0]
    down = [row for row in significant if float(row["log2_fold_change"]) < 0]
    return {
        "method": parameters["method"],
        "contrast": parameters["contrast"],
        "n_genes_input": len(counts),
        "n_genes_tested": len(rows),
        "n_significant": len(significant),
        "n_up": len(up),
        "n_down": len(down),
        "sample_counts": {key: len(value) for key, value in sample_groups.items()},
        "top_genes": [str(row["gene"]) for row in rows[:10]],
        "warnings": warnings,
        "started_at": started,
        "completed_at": now_iso(),
    }


def interpretation(summary: dict[str, Any]) -> list[str]:
    contrast = summary.get("contrast", {})
    return [
        f"Exploratory DE compared {contrast.get('target', 'target')} against {contrast.get('reference', 'reference')} for variable {contrast.get('variable', 'unknown')}.",
        f"Tested {summary.get('n_genes_tested', 'unknown')} genes and flagged {summary.get('n_significant', 'unknown')} genes using the configured adjusted-p and log2FC thresholds.",
        f"Top ranked genes: {', '.join(summary.get('top_genes', [])[:5]) if summary.get('top_genes') else 'none recorded'}.",
    ]


def methods_text(parameters: dict[str, Any]) -> str:
    contrast = parameters["contrast"]
    return (
        "Bulk RNA differential expression was run as an exploratory log2-CPM screen from a local count matrix. "
        f"The contrast was {contrast.get('variable')}={contrast.get('target')} versus {contrast.get('reference')}; "
        "genes were filtered by total count and sample count, tested with a normal-approximation Welch statistic, "
        "and adjusted with Benjamini-Hochberg correction."
    )


def safe_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def finish(outdir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    write_manifest(outdir / "run_manifest.json", manifest)
    write_report(outdir / "report.md", manifest, title="Bulk RNA DE Report")
    return manifest


if __name__ == "__main__":
    raise SystemExit(main())
