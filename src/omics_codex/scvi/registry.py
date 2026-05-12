from __future__ import annotations

import inspect
from typing import Any


CURATED_MODELS = {
    "SCVI": {"modality": "rna", "latent": True, "normalized_expression": True},
    "LinearSCVI": {"modality": "rna", "latent": True, "normalized_expression": True},
    "SCANVI": {"modality": "rna", "latent": True, "label_transfer": True},
    "TOTALVI": {"modality": "cite_seq", "latent": True, "protein": True},
    "PEAKVI": {"modality": "atac", "latent": True},
    "MULTIVI": {"modality": "multiome", "latent": True},
    "SOLO": {"modality": "rna", "doublet_detection": True},
    "AUTOZI": {"modality": "rna", "latent": False},
    "LDVAE": {"modality": "rna", "latent": True},
    "DestVI": {"modality": "spatial", "latent": False},
    "Stereoscope": {"modality": "spatial", "latent": False},
    "Tangram": {"modality": "spatial", "latent": False},
}


def list_models() -> list[dict[str, Any]]:
    try:
        import scvi as scvi_pkg
    except ImportError:
        return [
            {
                "name": name,
                "available": False,
                "curated": True,
                "capabilities": capabilities,
                "reason": "scvi-tools is not installed",
            }
            for name, capabilities in sorted(CURATED_MODELS.items())
        ]
    discovered: dict[str, dict[str, Any]] = {}
    for name, cls in inspect.getmembers(scvi_pkg.model, inspect.isclass):
        if name.startswith("_") or cls.__module__.split(".")[0] != "scvi":
            continue
        has_setup = hasattr(cls, "setup_anndata")
        has_train = hasattr(cls, "train")
        discovered[name] = {
            "name": name,
            "available": True,
            "curated": name in CURATED_MODELS,
            "capabilities": {
                **CURATED_MODELS.get(name, {}),
                "setup_anndata": has_setup,
                "train": has_train,
                "save": hasattr(cls, "save"),
                "latent": CURATED_MODELS.get(name, {}).get("latent", hasattr(cls, "get_latent_representation")),
            },
            "module": cls.__module__,
        }
    for name, capabilities in CURATED_MODELS.items():
        discovered.setdefault(
            name,
            {
                "name": name,
                "available": False,
                "curated": True,
                "capabilities": capabilities,
                "reason": "model class absent in installed scvi-tools",
            },
        )
    return [discovered[name] for name in sorted(discovered)]


def get_model_class(model_name: str):
    import scvi as scvi_pkg

    try:
        return getattr(scvi_pkg.model, model_name)
    except AttributeError as exc:
        from ..common.errors import ModelUnavailable

        raise ModelUnavailable(model_name) from exc


def inspect_model(model_name: str) -> dict[str, Any]:
    for model in list_models():
        if model["name"].lower() == model_name.lower():
            return model
    return {
        "name": model_name,
        "available": False,
        "curated": False,
        "capabilities": {},
        "reason": "model not found in registry",
    }
