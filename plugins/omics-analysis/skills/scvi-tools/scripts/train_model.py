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
    if model_name == "TOTALVI":
        setup_kwargs["protein_expression_obsm_key"] = args.protein_obsm
    cls.setup_anndata(adata, **setup_kwargs)
    if model_name == "SCANVI":
        model = cls(adata, unlabeled_category="Unknown")
    else:
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
    summary = {"model": model_name, "latent_key": latent_key, "max_epochs": args.max_epochs, "environment": env}
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


def finish(outdir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    write_manifest(outdir / "run_manifest.json", manifest)
    write_report(outdir / "report.md", manifest, title="scvi-tools Model Report")
    return manifest


if __name__ == "__main__":
    raise SystemExit(main())
