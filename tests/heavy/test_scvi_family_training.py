from __future__ import annotations

import os

import pytest

from omics_codex.scvi.train import train_scvi


pytestmark = [
    pytest.mark.heavy,
    pytest.mark.skipif(os.environ.get("RUN_HEAVY_OMICS") != "1", reason="set RUN_HEAVY_OMICS=1 to run heavy GPU checks"),
]


@pytest.mark.parametrize(
    ("model", "setup"),
    [
        ("SCANVI", {"layer": "counts", "batch_key": "batch", "labels_key": "cell_type", "unlabeled_category": "Unknown"}),
        ("TOTALVI", {"layer": "counts", "batch_key": "batch", "protein_expression_obsm_key": "protein_expression"}),
        ("PEAKVI", {"layer": "counts", "batch_key": "batch"}),
        ("MULTIVI", {"layer": "counts", "batch_key": "batch", "modality_key": "modality"}),
    ],
)
def test_curated_scvi_family_light_training(tmp_path, model, setup) -> None:
    pytest.importorskip("scvi")
    suffix = ".h5mu" if model == "MULTIVI" else ".h5ad"
    spec = {
        "run": {"name": f"heavy_{model.lower()}", "type": "scvi_model", "skill": "scvi-universal"},
        "inputs": {"path": str(tmp_path / f"{model.lower()}{suffix}"), "type": suffix.lstrip("."), "synthetic": True},
        "scvi": {"model": model, "setup_anndata": setup, "train": {"max_epochs": 1}, "downstream": {"latent_key": f"X_{model.lower()}"}},
        "execution": {"mode": "command_and_run", "approved": True, "force": True},
        "outputs": {"outdir": str(tmp_path / "results" / model.lower())},
    }
    manifest = train_scvi(spec)
    assert manifest["status"] == "completed"
