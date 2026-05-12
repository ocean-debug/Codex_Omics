from __future__ import annotations

from omics_codex.scvi.registry import inspect_model, list_models


def test_registry_reports_curated_models() -> None:
    names = {model["name"] for model in list_models()}
    assert "SCVI" in names


def test_inspect_missing_or_available_model() -> None:
    model = inspect_model("SCVI")
    assert model["name"] == "SCVI"
    assert "capabilities" in model
