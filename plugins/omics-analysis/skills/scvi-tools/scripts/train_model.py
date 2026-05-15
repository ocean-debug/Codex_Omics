from __future__ import annotations

import argparse
import json
import sys
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
        manifest["plan"] = {"approval_required": True, "will_train": args.model, "will_write": ["model/", "adata_trained.h5ad", "scvi_model_summary.json"]}
        return finish(outdir, manifest)
    return execute_training(args, outdir, parameters, env)


def execute_training(args: argparse.Namespace, outdir: Path, parameters: dict[str, Any], env: dict[str, Any]) -> dict[str, Any]:
    import scanpy as sc
    import scvi

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
    summary = {"model": model_name, "latent_key": latent_key, "max_epochs": args.max_epochs, "environment": env, "model_specific_outputs": model_specific_outputs}
    write_json(outdir / "scvi_model_summary.json", summary)
    outputs = {
        "outdir": str(outdir),
        "manifest": str(outdir / "run_manifest.json"),
        "report": str(outdir / "report.md"),
        "model_dir": str(model_dir),
        "trained_h5ad": str(trained),
        "summary": str(outdir / "scvi_model_summary.json"),
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
    return finish(outdir, manifest)


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
