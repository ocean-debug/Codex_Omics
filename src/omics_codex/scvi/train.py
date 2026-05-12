from __future__ import annotations

from pathlib import Path
from typing import Any

from ..common.io import write_json, write_text
from ..common.environment import inspect_environment
from ..common.manifest import base_manifest, write_manifest
from ..common.paths import prepare_outdir
from .adapters import assert_validation, get_adapter
from .registry import inspect_model


def import_anndata_stack():
    try:
        import anndata as ad
        import mudata as md
        import numpy as np
        import pandas as pd
        import scanpy as sc
        from scipy import sparse as scipy_sparse
    except ImportError as exc:
        from ..common.errors import OmicsError

        raise OmicsError(
            "MissingSoftware",
            f"scVI dependencies are missing: {exc}",
            "Install the scvi extra in the codex-omics conda environment.",
            "import_scvi_stack",
        ) from exc
    return ad, md, np, pd, sc, scipy_sparse


def create_synthetic_h5ad(path: Path, *, model_name: str, ad: Any, np: Any, pd: Any, scipy_sparse: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(7)
    model = model_name.upper()
    n_vars = 120 if model in {"PEAKVI", "MULTIVI"} else 80
    lam = 0.7 if model in {"PEAKVI", "MULTIVI"} else 1.8
    counts = rng.poisson(lam=lam, size=(90, n_vars)).astype("int32")
    adata = ad.AnnData(X=scipy_sparse.csr_matrix(counts))
    adata.obs_names = [f"cell{i}" for i in range(adata.n_obs)]
    adata.var_names = [f"peak{i}" if model == "PEAKVI" else f"gene{i}" for i in range(adata.n_vars)]
    adata.obs["batch"] = ["batch1"] * 45 + ["batch2"] * 45
    adata.obs["cell_type"] = ["T cell"] * 30 + ["B cell"] * 30 + ["Unknown"] * 30
    adata.layers["counts"] = adata.X.copy()
    if model == "TOTALVI":
        proteins = rng.poisson(lam=1.2, size=(adata.n_obs, 8)).astype("int32")
        adata.obsm["protein_expression"] = pd.DataFrame(
            proteins,
            index=adata.obs_names,
            columns=[f"protein{i}" for i in range(proteins.shape[1])],
        )
    if model == "MULTIVI":
        modalities = ["Gene Expression"] * 60 + ["Peaks"] * (adata.n_vars - 60)
        adata.var["modality"] = modalities
    adata.write_h5ad(path)
    return path


def create_synthetic_h5mu(path: Path, *, md: Any, ad: Any, np: Any, scipy_sparse: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(11)
    obs = {"batch": ["batch1"] * 45 + ["batch2"] * 45}
    rna_counts = rng.poisson(lam=1.8, size=(90, 60)).astype("int32")
    atac_counts = rng.poisson(lam=0.6, size=(90, 80)).astype("int32")
    rna = ad.AnnData(X=scipy_sparse.csr_matrix(rna_counts), obs=obs)
    atac = ad.AnnData(X=scipy_sparse.csr_matrix(atac_counts), obs=obs)
    rna.obs_names = [f"cell{i}" for i in range(rna.n_obs)]
    atac.obs_names = list(rna.obs_names)
    rna.var_names = [f"gene{i}" for i in range(rna.n_vars)]
    atac.var_names = [f"peak{i}" for i in range(atac.n_vars)]
    rna.layers["counts"] = rna.X.copy()
    atac.layers["counts"] = atac.X.copy()
    mdata = md.MuData({"rna": rna, "atac": atac})
    mdata.write_h5mu(path)
    return path


def load_or_create_adata(spec: dict[str, Any]):
    ad, md, np, pd, sc, scipy_sparse = import_anndata_stack()
    input_path = Path(spec.get("inputs", {}).get("path", ""))
    model_name = spec.get("scvi", {}).get("model", "SCVI")
    if spec.get("inputs", {}).get("synthetic") or (not input_path.exists() and "examples" in str(input_path)):
        if model_name.upper() == "MULTIVI":
            create_synthetic_h5mu(input_path, md=md, ad=ad, np=np, scipy_sparse=scipy_sparse)
            return md.read_h5mu(input_path)
        else:
            create_synthetic_h5ad(input_path, model_name=model_name, ad=ad, np=np, pd=pd, scipy_sparse=scipy_sparse)
    if "".join(input_path.suffixes).lower().endswith(".h5mu"):
        return md.read_h5mu(input_path)
    return sc.read_h5ad(input_path)


def validate_scvi(spec: dict[str, Any]) -> dict[str, Any]:
    adata = load_or_create_adata(spec)
    model_name = spec.get("scvi", {}).get("model", "SCVI")
    model_info = inspect_model(model_name)
    adapter = get_adapter(model_name)
    result = adapter.validate_input(adata, spec)
    result["model"] = model_info
    if not model_info.get("available"):
        result.setdefault("warnings", []).append(
            {
                "error_type": "ModelUnavailable",
                "message": f"Model '{model_name}' is unavailable in the active scvi-tools installation.",
                "suggested_fix": "Install scvi-tools through conda-forge before training or choose another registered model.",
            }
        )
    return result


def train_scvi(spec: dict[str, Any]) -> dict[str, Any]:
    adata = load_or_create_adata(spec)
    outputs = spec.get("outputs", {})
    execution = spec.get("execution", {})
    outdir = prepare_outdir(outputs.get("outdir", "./results/scvi"), force=bool(execution.get("force", False)))
    model_name = spec.get("scvi", {}).get("model", "SCVI")
    adapter = get_adapter(model_name)
    validation = adapter.validate_input(adata, spec)
    assert_validation(validation)
    adapter.setup_anndata(adata, spec)
    model = adapter.build_model(adata, spec)
    adapter.train(model, spec)
    summary = adapter.collect_outputs(model, adata, spec)
    summary["model_class"] = model.__class__.__name__
    summary["train"] = spec.get("scvi", {}).get("train", {})
    summary["environment"] = inspect_environment("scvi").get("scvi", {})
    model_dir = outdir / "model"
    model.save(model_dir, overwrite=True)
    if hasattr(adata, "write_h5mu"):
        trained_path = outdir / "adata_trained.h5mu"
        adata.write_h5mu(trained_path)
        trained_key = "trained_h5mu"
    else:
        trained_path = outdir / "adata_trained.h5ad"
        adata.write_h5ad(trained_path)
        trained_key = "trained_h5ad"
    write_json(outdir / "scvi_model_summary.json", {**summary, "validation": validation})
    write_text(outdir / "report.md", render_scvi_report(model_name, summary, validation))
    trained_outputs = {"trained_data": str(trained_path), trained_key: str(trained_path)}
    manifest = base_manifest(
        skill="scvi-universal",
        status="completed",
        inputs=spec.get("inputs", {}),
        outputs={
            **outputs,
            "outdir": str(outdir),
            "model_dir": str(model_dir),
            **trained_outputs,
            "summary": str(outdir / "scvi_model_summary.json"),
            "report": str(outdir / "report.md"),
        },
        parameters=spec.get("scvi", {}),
    )
    write_manifest(outputs.get("manifest") or outdir / "run_manifest.json", manifest)
    return manifest


def render_scvi_report(model_name: str, summary: dict[str, Any], validation: dict[str, Any]) -> str:
    return (
        "# scvi-tools Model Report\n\n"
        f"- Model: `{model_name}`\n"
        f"- Latent key: `{summary.get('latent_key', 'unavailable')}`\n"
        f"- Observations: `{validation.get('n_obs', 'NA')}`\n"
        f"- Variables: `{validation.get('n_vars', 'NA')}`\n\n"
        "## Summary\n\n"
        "```json\n"
        + __import__("json").dumps(summary, indent=2, sort_keys=True, default=str)
        + "\n```\n"
    )
