from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from common.env import inspect_scvi_environment  # noqa: E402
from common.io import ensure_outdir, write_json  # noqa: E402
from common.manifest import base_manifest, write_manifest  # noqa: E402
from common.report import write_report  # noqa: E402


def approved(value: str | bool) -> bool:
    return value is True or str(value).lower() in {"1", "true", "yes", "y"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Train or plan an scvi-tools model from a plugin-local script.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--config")
    parser.add_argument("--model", default="SCVI")
    parser.add_argument("--layer")
    parser.add_argument("--batch-key")
    parser.add_argument("--labels-key")
    parser.add_argument("--unlabeled-category", default="Unknown")
    parser.add_argument("--protein-obsm", default="protein_expression")
    parser.add_argument("--max-epochs", type=int, default=20)
    parser.add_argument("--accelerator", default="auto")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--approved", default="false")
    args = parser.parse_args()
    result = train_or_plan(args)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


def train_or_plan(args: argparse.Namespace) -> dict[str, Any]:
    outdir = ensure_outdir(args.output_dir)
    env = inspect_scvi_environment()
    parameters = {
        "model": args.model,
        "layer": args.layer,
        "batch_key": args.batch_key,
        "labels_key": args.labels_key,
        "unlabeled_category": args.unlabeled_category,
        "protein_obsm": args.protein_obsm,
        "max_epochs": args.max_epochs,
        "accelerator": args.accelerator,
        "seed": args.seed,
    }
    outputs = {"outdir": str(outdir), "manifest": str(outdir / "run_manifest.json"), "report": str(outdir / "report.md")}
    if env["blockers"]:
        manifest = base_manifest(
            skill="scvi-tools",
            status="blocked",
            inputs={"path": args.input},
            outputs=outputs,
            parameters=parameters,
            errors=env["blockers"],
            warnings=env["warnings"],
        )
        manifest["environment"] = env
        return finish(outdir, manifest)
    if args.dry_run or not approved(args.approved):
        manifest = base_manifest(
            skill="scvi-tools",
            status="planned",
            inputs={"path": args.input},
            outputs=outputs,
            parameters=parameters,
            warnings=env["warnings"],
        )
        manifest["plan"] = {"approval_required": True, "will_train": args.model, "will_write": ["model/", "adata_trained.h5ad", "scvi_model_summary.json", "diagnostics/"]}
        return finish(outdir, manifest)
    return execute_training(args, outdir, parameters, env)


def execute_training(args: argparse.Namespace, outdir: Path, parameters: dict[str, Any], env: dict[str, Any]) -> dict[str, Any]:
    import scanpy as sc
    import scvi

    set_random_seed(args.seed)
    start = time.perf_counter()
    gpu_before = gpu_memory_snapshot()
    adata = sc.read_h5ad(args.input)
    model_name = args.model.upper()
    cls = getattr(scvi.model, model_name)
    setup_kwargs = {}
    if args.layer:
        setup_kwargs["layer"] = args.layer
    if args.batch_key:
        setup_kwargs["batch_key"] = args.batch_key
    if model_name == "SCANVI" and args.labels_key:
        setup_kwargs["labels_key"] = args.labels_key
        setup_kwargs["unlabeled_category"] = args.unlabeled_category
    if model_name == "TOTALVI":
        setup_kwargs["protein_expression_obsm_key"] = args.protein_obsm
    if model_name == "SCANVI" and not args.labels_key:
        raise ValueError("SCANVI requires --labels-key.")
    if model_name == "TOTALVI" and args.protein_obsm not in adata.obsm:
        raise ValueError(f"TOTALVI requires adata.obsm['{args.protein_obsm}'].")
    if model_name == "MULTIVI" and "modality" not in adata.obs and "modality" not in adata.var:
        raise ValueError("MULTIVI requires modality metadata in adata.obs or adata.var.")
    cls.setup_anndata(adata, **setup_kwargs)
    model = cls(adata)
    model.train(max_epochs=args.max_epochs)
    training_time_seconds = time.perf_counter() - start
    gpu_after = gpu_memory_snapshot()
    latent_key = f"X_{model_name.lower()}"
    if hasattr(model, "get_latent_representation"):
        adata.obsm[latent_key] = model.get_latent_representation()
        try:
            sc.pp.neighbors(adata, use_rep=latent_key)
            sc.tl.umap(adata)
            sc.tl.leiden(adata)
        except Exception:
            pass
    model_dir = outdir / "model"
    model.save(model_dir, overwrite=True)
    trained = outdir / "adata_trained.h5ad"
    adata.write_h5ad(trained)
    model_specific_outputs = add_model_specific_outputs(model_name, model, adata, args, outdir)
    diagnostics = write_diagnostics(outdir, model, adata, args, latent_key, training_time_seconds, gpu_before, gpu_after)
    summary = {
        "model": model_name,
        "latent_key": latent_key,
        "max_epochs": args.max_epochs,
        "seed": args.seed,
        "training_time_seconds": training_time_seconds,
        "environment": env,
        "model_specific_outputs": model_specific_outputs,
        "diagnostics": diagnostics,
    }
    write_json(outdir / "scvi_model_summary.json", summary)
    outputs = {
        "outdir": str(outdir),
        "manifest": str(outdir / "run_manifest.json"),
        "report": str(outdir / "report.md"),
        "model_dir": str(model_dir),
        "trained_h5ad": str(trained),
        "summary": str(outdir / "scvi_model_summary.json"),
        "diagnostics": str(outdir / "diagnostics" / "diagnostics.json"),
    }
    manifest = base_manifest(
        skill="scvi-tools",
        status="completed",
        inputs={"path": args.input},
        outputs=outputs,
        parameters=parameters,
        warnings=env["warnings"],
    )
    manifest["summary"] = summary
    manifest["qc_summary"] = diagnostics.get("latent_qc", {})
    manifest["interpretation"] = diagnostics.get("interpretation", [])
    return finish(outdir, manifest)


def set_random_seed(seed: int) -> None:
    try:
        import scvi

        scvi.settings.seed = seed
    except Exception:
        pass
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            torch.cuda.reset_peak_memory_stats()
    except Exception:
        pass


def gpu_memory_snapshot() -> dict[str, Any]:
    try:
        import torch

        if not torch.cuda.is_available():
            return {"cuda_available": False}
        return {
            "cuda_available": True,
            "device": torch.cuda.get_device_name(0),
            "allocated_bytes": int(torch.cuda.memory_allocated()),
            "reserved_bytes": int(torch.cuda.memory_reserved()),
            "max_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        }
    except Exception as exc:
        return {"cuda_available": False, "error": str(exc)}


def write_diagnostics(
    outdir: Path,
    model: Any,
    adata: Any,
    args: argparse.Namespace,
    latent_key: str,
    training_time_seconds: float,
    gpu_before: dict[str, Any],
    gpu_after: dict[str, Any],
) -> dict[str, Any]:
    diagnostics_dir = ensure_outdir(outdir / "diagnostics")
    history = extract_history(model)
    if history:
        write_json(diagnostics_dir / "training_history.json", history)
        write_history_csv(diagnostics_dir / "training_history.csv", history)
        maybe_plot_history(diagnostics_dir / "training_history.png", history)
    latent_qc = latent_embedding_qc(adata, latent_key, args.batch_key, args.labels_key)
    diagnostics = {
        "seed": args.seed,
        "training_time_seconds": training_time_seconds,
        "gpu_memory": {"before": gpu_before, "after": gpu_after},
        "history_files": {
            "json": str(diagnostics_dir / "training_history.json") if history else None,
            "csv": str(diagnostics_dir / "training_history.csv") if history else None,
            "plot": str(diagnostics_dir / "training_history.png") if (diagnostics_dir / "training_history.png").exists() else None,
        },
        "history_keys": sorted(history.keys()),
        "latent_qc": latent_qc,
        "reconstruction_diagnostics": reconstruction_diagnostics(model),
        "interpretation": interpret_diagnostics(latent_qc, history),
    }
    write_json(diagnostics_dir / "diagnostics.json", diagnostics)
    return diagnostics


def extract_history(model: Any) -> dict[str, list[float]]:
    history: dict[str, list[float]] = {}
    raw = getattr(model, "history", None)
    if raw is None:
        return history
    try:
        for key, value in raw.items():
            series = getattr(value, "values", value)
            flattened = []
            for item in list(series):
                try:
                    flattened.append(float(item))
                except Exception:
                    continue
            if flattened:
                history[str(key)] = flattened
    except Exception:
        return {}
    return history


def write_history_csv(path: Path, history: dict[str, list[float]]) -> None:
    keys = sorted(history)
    max_len = max((len(values) for values in history.values()), default=0)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["epoch", *keys])
        writer.writeheader()
        for index in range(max_len):
            row: dict[str, Any] = {"epoch": index}
            for key in keys:
                values = history[key]
                row[key] = values[index] if index < len(values) else ""
            writer.writerow(row)


def maybe_plot_history(path: Path, history: dict[str, list[float]]) -> None:
    try:
        import matplotlib.pyplot as plt

        for key, values in history.items():
            plt.plot(range(len(values)), values, label=key)
        plt.xlabel("epoch")
        plt.ylabel("value")
        plt.legend()
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
    except Exception:
        return


def latent_embedding_qc(adata: Any, latent_key: str, batch_key: str | None, labels_key: str | None) -> dict[str, Any]:
    latent = adata.obsm.get(latent_key) if latent_key in adata.obsm else None
    qc: dict[str, Any] = {
        "latent_key": latent_key,
        "latent_shape": list(getattr(latent, "shape", [])) if latent is not None else [],
        "has_umap": "X_umap" in adata.obsm,
        "has_leiden": "leiden" in adata.obs,
        "metric_type": "lightweight_proxy",
    }
    if batch_key and batch_key in adata.obs:
        counts = adata.obs[batch_key].value_counts()
        qc["batch_mixing_proxy"] = {"key": batch_key, "n_batches": int(counts.shape[0]), "min_batch_fraction": float((counts / counts.sum()).min())}
    if labels_key and labels_key in adata.obs:
        counts = adata.obs[labels_key].value_counts()
        qc["cell_type_conservation_proxy"] = {"key": labels_key, "n_labels": int(counts.shape[0]), "min_label_fraction": float((counts / counts.sum()).min())}
    return qc


def reconstruction_diagnostics(model: Any) -> dict[str, Any]:
    diagnostics = {"available": False}
    if hasattr(model, "get_reconstruction_error"):
        try:
            value = model.get_reconstruction_error()
            diagnostics = {"available": True, "reconstruction_error": float(value)}
        except Exception as exc:
            diagnostics = {"available": False, "error": str(exc)}
    return diagnostics


def interpret_diagnostics(latent_qc: dict[str, Any], history: dict[str, list[float]]) -> list[str]:
    interpretation = []
    if latent_qc.get("latent_shape"):
        interpretation.append(f"Latent embedding `{latent_qc['latent_key']}` was written with shape {latent_qc['latent_shape']}.")
    if history:
        interpretation.append("Training history was captured for loss or ELBO review.")
    if latent_qc.get("batch_mixing_proxy"):
        interpretation.append("Batch mixing proxy was recorded; use a formal benchmark for publication-grade integration claims.")
    if latent_qc.get("cell_type_conservation_proxy"):
        interpretation.append("Cell type conservation proxy was recorded; validate label preservation before downstream claims.")
    return interpretation or ["Diagnostics were recorded, but no latent embedding or training history was available for interpretation."]


def add_model_specific_outputs(model_name: str, model: Any, adata: Any, args: argparse.Namespace, outdir: Path) -> list[str]:
    outputs: list[str] = []
    if model_name == "SCANVI" and hasattr(model, "predict"):
        predictions = model.predict()
        adata.obs["scanvi_predicted_labels"] = predictions
        write_json(outdir / "scanvi_predictions_summary.json", {"obs_key": "scanvi_predicted_labels", "n_predictions": int(len(predictions))})
        outputs.append("scanvi_predictions_summary.json")
    if model_name == "TOTALVI" and hasattr(model, "get_normalized_expression"):
        try:
            _, protein = model.get_normalized_expression(return_numpy=True)
            write_json(outdir / "totalvi_protein_summary.json", {"protein_obsm": args.protein_obsm, "shape": list(getattr(protein, "shape", []))})
            outputs.append("totalvi_protein_summary.json")
        except Exception as exc:
            write_json(outdir / "totalvi_protein_summary.json", {"error": str(exc)})
            outputs.append("totalvi_protein_summary.json")
    if model_name == "PEAKVI":
        write_json(outdir / "peakvi_accessibility_summary.json", {"latent_key": f"X_{model_name.lower()}", "matrix": "chromatin_accessibility"})
        outputs.append("peakvi_accessibility_summary.json")
    if model_name == "MULTIVI":
        write_json(outdir / "multivi_modality_summary.json", {"latent_key": f"X_{model_name.lower()}", "modalities": sorted({str(x) for x in adata.obs.get("modality", [])}) if "modality" in adata.obs else []})
        outputs.append("multivi_modality_summary.json")
    return outputs


def finish(outdir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    write_manifest(outdir / "run_manifest.json", manifest)
    write_report(outdir / "report.md", manifest, title="scvi-tools Model Report")
    return manifest


if __name__ == "__main__":
    raise SystemExit(main())
