from __future__ import annotations

import pytest

from omics_codex.scvi.train import validate_scvi


@pytest.mark.integration
def test_scvi_validate_synthetic(tmp_path) -> None:
    pytest.importorskip("anndata")
    spec = {
        "run": {"name": "synthetic_scvi", "type": "scvi_model", "skill": "scvi-universal"},
        "inputs": {"path": str(tmp_path / "synthetic.h5ad"), "type": "h5ad", "synthetic": True},
        "scvi": {"model": "SCVI", "setup_anndata": {"layer": "counts", "batch_key": "batch"}},
        "outputs": {"outdir": str(tmp_path / "results")},
    }
    result = validate_scvi(spec)
    assert result["valid"]


@pytest.mark.integration
@pytest.mark.parametrize(
    ("model", "setup"),
    [
        ("SCANVI", {"layer": "counts", "batch_key": "batch", "labels_key": "cell_type", "unlabeled_category": "Unknown"}),
        ("TOTALVI", {"layer": "counts", "batch_key": "batch", "protein_expression_obsm_key": "protein_expression"}),
        ("PEAKVI", {"layer": "counts", "batch_key": "batch"}),
        ("MULTIVI", {"layer": "counts", "batch_key": "batch", "modality_key": "modality"}),
    ],
)
def test_curated_scvi_adapters_validate_synthetic(tmp_path, model, setup) -> None:
    pytest.importorskip("anndata")
    spec = {
        "run": {"name": f"synthetic_{model.lower()}", "type": "scvi_model", "skill": "scvi-universal"},
        "inputs": {"path": str(tmp_path / f"{model.lower()}.h5ad"), "type": "h5ad", "synthetic": True},
        "scvi": {"model": model, "setup_anndata": setup},
        "outputs": {"outdir": str(tmp_path / "results" / model.lower())},
    }
    result = validate_scvi(spec)
    assert result["valid"], result.get("issues")
