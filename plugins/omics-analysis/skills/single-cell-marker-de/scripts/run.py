from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from common.env import inspect_scrna_qc_environment  # noqa: E402
from common.errors import blocker, warning  # noqa: E402
from common.io import ensure_outdir, write_json  # noqa: E402
from common.manifest import base_manifest, now_iso, write_manifest  # noqa: E402
from common.report import write_report  # noqa: E402


def approved(value: str | bool) -> bool:
    return value is True or str(value).lower() in {"1", "true", "yes", "y"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan or run single-cell marker/DE analysis from a preprocessed h5ad.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--config")
    parser.add_argument("--groupby", default="leiden")
    parser.add_argument("--method", default="wilcoxon", choices=["wilcoxon", "t-test", "t-test_overestim_var", "logreg"])
    parser.add_argument("--reference", default="rest")
    parser.add_argument("--groups", default="", help="Comma-separated groups to test. Empty means all groups.")
    parser.add_argument("--n-genes", type=int, default=100)
    parser.add_argument("--min-cells-per-group", type=int, default=3)
    parser.add_argument("--layer")
    parser.add_argument("--use-raw", default="auto", choices=["auto", "true", "false"])
    parser.add_argument("--make-plots", action="store_true")
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
    result = run_marker_de(args)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


def run_marker_de(args: argparse.Namespace) -> dict[str, Any]:
    outdir = ensure_outdir(args.output_dir)
    input_path = Path(args.input)
    env = inspect_scrna_qc_environment()
    parameters = parameters_from_args(args)
    outputs = base_outputs(outdir)
    if env["blockers"]:
        manifest = base_manifest(
            skill="single-cell-marker-de",
            status="blocked",
            inputs={"path": str(input_path), "exists": input_path.exists()},
            outputs=outputs,
            parameters=parameters,
            errors=env["blockers"],
            warnings=env["warnings"],
        )
        manifest["environment"] = env
        return finish(outdir, manifest)
    if args.dry_run or not approved(args.approved):
        manifest = base_manifest(
            skill="single-cell-marker-de",
            status="planned",
            inputs={"path": str(input_path), "exists": input_path.exists()},
            outputs=outputs,
            parameters=parameters,
            warnings=env["warnings"],
        )
        manifest["plan"] = {
            "will_load": str(input_path),
            "will_write": ["markers.csv", "de_summary.json", "run_manifest.json", "report.md"],
            "optional_writes": ["rank_genes_groups.png"] if args.make_plots else [],
            "approval_required": True,
            "steps": ["validate_groupby", "rank_genes_groups", "export_marker_table", "summarize_markers"],
        }
        manifest["methods_text"] = methods_text(parameters)
        return finish(outdir, manifest)
    return execute_marker_de(input_path, outdir, parameters, env)


def parameters_from_args(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "groupby": args.groupby,
        "method": args.method,
        "reference": args.reference,
        "groups": [item.strip() for item in args.groups.split(",") if item.strip()],
        "n_genes": args.n_genes,
        "min_cells_per_group": args.min_cells_per_group,
        "layer": args.layer,
        "use_raw": args.use_raw,
        "make_plots": bool(args.make_plots),
    }


def base_outputs(outdir: Path) -> dict[str, str]:
    return {
        "outdir": str(outdir),
        "manifest": str(outdir / "run_manifest.json"),
        "report": str(outdir / "report.md"),
        "markers_csv": str(outdir / "markers.csv"),
        "summary": str(outdir / "de_summary.json"),
    }


def execute_marker_de(input_path: Path, outdir: Path, parameters: dict[str, Any], env: dict[str, Any]) -> dict[str, Any]:
    import scanpy as sc

    warnings: list[dict[str, Any]] = list(env["warnings"])
    errors: list[dict[str, Any]] = []
    if not input_path.exists() or not "".join(input_path.suffixes).lower().endswith(".h5ad"):
        errors.append(blocker("UnsupportedInput", "Use an existing preprocessed .h5ad file for marker/DE analysis.", "Run single-cell-preprocess first or provide a valid .h5ad.", "load_input"))
        return failed_manifest(input_path, outdir, parameters, env, errors, warnings)

    started = now_iso()
    adata = sc.read_h5ad(input_path)
    groupby = str(parameters["groupby"])
    if groupby not in adata.obs:
        errors.append(blocker("MissingGroupBy", f"Grouping column obs['{groupby}'] is not present.", "Use --groupby with an existing obs column, or run preprocessing/clustering first.", "validate_groupby"))
        return failed_manifest(input_path, outdir, parameters, env, errors, warnings)
    if parameters.get("layer") and parameters["layer"] not in adata.layers:
        errors.append(blocker("MissingLayer", f"Requested layer '{parameters['layer']}' is not present.", "Choose an existing layer or omit --layer.", "validate_layer"))
        return failed_manifest(input_path, outdir, parameters, env, errors, warnings)

    group_counts = group_counts_for(adata, groupby)
    usable_groups = [group for group, count in group_counts.items() if count >= int(parameters["min_cells_per_group"])]
    if len(usable_groups) < 2:
        errors.append(blocker("InsufficientGroups", "At least two groups with enough cells are required for marker/DE analysis.", "Lower --min-cells-per-group only if statistically appropriate, or choose a different grouping column.", "validate_group_counts"))
        return failed_manifest(input_path, outdir, parameters, env, errors, warnings)

    requested_groups = parameters["groups"] or usable_groups
    missing_groups = [group for group in requested_groups if group not in group_counts]
    if missing_groups:
        errors.append(blocker("UnknownGroup", f"Requested groups are not present: {', '.join(missing_groups)}", "Use groups from the selected obs column.", "validate_groups"))
        return failed_manifest(input_path, outdir, parameters, env, errors, warnings)

    use_raw = resolve_use_raw(parameters["use_raw"], adata)
    if parameters["use_raw"] == "auto" and use_raw is False and adata.raw is None:
        warnings.append(warning("RawUnavailable", "AnnData.raw is not available; marker/DE uses X or the selected layer.", "Confirm that the selected matrix contains normalized/log-transformed expression."))

    sc.tl.rank_genes_groups(
        adata,
        groupby=groupby,
        groups=requested_groups,
        reference=str(parameters["reference"]),
        method=str(parameters["method"]),
        n_genes=int(parameters["n_genes"]),
        layer=parameters.get("layer"),
        use_raw=use_raw,
    )
    markers = marker_dataframe(sc, adata, groupby)
    markers_path = outdir / "markers.csv"
    markers.to_csv(markers_path, index=False)
    plots = maybe_write_plots(sc, adata, outdir, parameters, warnings)
    summary = build_summary(adata, markers, group_counts, parameters, warnings, started, plots)
    write_json(outdir / "de_summary.json", summary)

    manifest = base_manifest(
        skill="single-cell-marker-de",
        status="completed",
        inputs={"path": str(input_path), "groupby": groupby, "group_counts": group_counts},
        outputs={**base_outputs(outdir), "plots": [str(path) for path in plots]},
        parameters=parameters,
        warnings=warnings,
    )
    manifest["environment"] = env
    manifest["summary"] = summary
    manifest["qc_summary"] = {"group_counts": group_counts, "top_markers": summary["top_markers"]}
    manifest["interpretation"] = interpretation(summary)
    manifest["methods_text"] = methods_text(parameters)
    manifest["started_at"] = started
    manifest["completed_at"] = now_iso()
    return finish(outdir, manifest)


def failed_manifest(input_path: Path, outdir: Path, parameters: dict[str, Any], env: dict[str, Any], errors: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> dict[str, Any]:
    manifest = base_manifest(
        skill="single-cell-marker-de",
        status="failed",
        inputs={"path": str(input_path), "exists": input_path.exists()},
        outputs=base_outputs(outdir),
        parameters=parameters,
        errors=errors,
        warnings=warnings,
    )
    manifest["environment"] = env
    return finish(outdir, manifest)


def group_counts_for(adata: Any, groupby: str) -> dict[str, int]:
    counts = adata.obs[groupby].astype(str).value_counts()
    return {str(key): int(value) for key, value in counts.items()}


def resolve_use_raw(value: str, adata: Any) -> bool | None:
    if value == "true":
        return True
    if value == "false":
        return False
    return True if adata.raw is not None else False


def marker_dataframe(sc: Any, adata: Any, groupby: str) -> Any:
    frames = []
    for group in adata.uns["rank_genes_groups"]["names"].dtype.names or []:
        frame = sc.get.rank_genes_groups_df(adata, group=group)
        frame.insert(0, "groupby", groupby)
        frame.insert(1, "group", str(group))
        frames.append(frame)
    if not frames:
        import pandas as pd

        return pd.DataFrame(columns=["groupby", "group", "names", "scores", "logfoldchanges", "pvals", "pvals_adj"])
    import pandas as pd

    return pd.concat(frames, ignore_index=True)


def maybe_write_plots(sc: Any, adata: Any, outdir: Path, parameters: dict[str, Any], warnings: list[dict[str, Any]]) -> list[Path]:
    if not parameters.get("make_plots"):
        return []
    try:
        import matplotlib.pyplot as plt

        sc.pl.rank_genes_groups(adata, n_genes=min(10, int(parameters["n_genes"])), show=False)
        target = outdir / "rank_genes_groups.png"
        plt.savefig(target, bbox_inches="tight", dpi=160)
        plt.close("all")
        return [target]
    except Exception as exc:
        warnings.append(warning("PlotSkipped", f"Marker plot generation failed: {exc}", "Inspect marker tables directly or install plotting dependencies after approval."))
        return []


def build_summary(adata: Any, markers: Any, group_counts: dict[str, int], parameters: dict[str, Any], warnings: list[dict[str, Any]], started: str, plots: list[Path]) -> dict[str, Any]:
    top_markers: dict[str, list[str]] = {}
    if not markers.empty and "group" in markers and "names" in markers:
        for group, frame in markers.groupby("group"):
            top_markers[str(group)] = [str(name) for name in frame["names"].head(5).tolist()]
    return {
        "n_cells": int(adata.n_obs),
        "n_genes": int(adata.n_vars),
        "groupby": parameters["groupby"],
        "group_counts": group_counts,
        "method": parameters["method"],
        "reference": parameters["reference"],
        "n_markers": int(len(markers)),
        "top_markers": top_markers,
        "plots": [str(path) for path in plots],
        "warnings": warnings,
        "started_at": started,
        "completed_at": now_iso(),
    }


def interpretation(summary: dict[str, Any]) -> list[str]:
    notes = [
        f"Marker/DE analysis tested groups from obs['{summary.get('groupby', 'unknown')}'].",
        f"Exported {summary.get('n_markers', 'unknown')} marker rows across {len(summary.get('group_counts', {}))} groups.",
    ]
    for group, markers in list((summary.get("top_markers") or {}).items())[:5]:
        notes.append(f"Top markers for {group}: {', '.join(markers) if markers else 'none recorded'}.")
    return notes


def methods_text(parameters: dict[str, Any]) -> str:
    return (
        "Marker genes were ranked with Scanpy rank_genes_groups using "
        f"groupby={parameters['groupby']}, method={parameters['method']}, reference={parameters['reference']}, "
        f"n_genes={parameters['n_genes']}, and use_raw={parameters['use_raw']}."
    )


def finish(outdir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    write_manifest(outdir / "run_manifest.json", manifest)
    write_report(outdir / "report.md", manifest, title="Single-cell Marker DE Report")
    return manifest


if __name__ == "__main__":
    raise SystemExit(main())
