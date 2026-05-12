from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..common.errors import OmicsError
from .registry import get_model_class, inspect_model


@dataclass
class ScviModelAdapter:
    model_name: str

    def validate_input(self, adata: Any, run_spec: dict[str, Any]) -> dict[str, Any]:
        scvi_spec = run_spec.get("scvi", {})
        setup = scvi_spec.get("setup_anndata", {})
        layer = setup.get("layer")
        batch_key = setup.get("batch_key")
        label_key = setup.get("labels_key") or setup.get("label_key")
        issues: list[dict[str, str]] = []
        if layer and layer not in adata.layers:
            issues.append(
                {
                    "error_type": "MissingCountsLayer",
                    "message": f"Layer '{layer}' was not found in adata.layers.",
                    "suggested_fix": "Use a raw counts layer or omit layer to use adata.X.",
                }
            )
        matrix = adata.layers[layer] if layer and layer in adata.layers else adata.X
        if not looks_integer_counts(matrix):
            issues.append(
                {
                    "error_type": "AnnDataValidationFailed",
                    "message": "Selected matrix does not look like integer raw counts.",
                    "suggested_fix": "Provide raw counts in adata.X or a counts layer.",
                }
            )
        if batch_key and batch_key not in adata.obs:
            issues.append(
                {
                    "error_type": "MissingBatchKey",
                    "message": f"batch_key='{batch_key}' was not found in adata.obs.",
                    "suggested_fix": "Add the batch column or change scvi.setup_anndata.batch_key.",
                }
            )
        if label_key and label_key not in adata.obs:
            issues.append(
                {
                    "error_type": "MissingLabelKey",
                    "message": f"labels_key='{label_key}' was not found in adata.obs.",
                    "suggested_fix": "Add labels or choose an unsupervised model.",
                }
            )
        return {
            "valid": not issues,
            "issues": issues,
            "n_obs": int(adata.n_obs),
            "n_vars": int(adata.n_vars),
            "obs_keys": sorted(map(str, adata.obs.columns)),
            "layers": sorted(map(str, adata.layers.keys())),
            "obsm_keys": sorted(map(str, adata.obsm.keys())),
        }

    def setup_anndata(self, adata: Any, run_spec: dict[str, Any]):
        model_cls = get_model_class(self.model_name)
        setup = dict(run_spec.get("scvi", {}).get("setup_anndata", {}))
        if "label_key" in setup and "labels_key" not in setup:
            setup["labels_key"] = setup.pop("label_key")
        model_cls.setup_anndata(adata, **setup)
        return adata

    def build_model(self, adata: Any, run_spec: dict[str, Any]):
        model_cls = get_model_class(self.model_name)
        kwargs = dict(run_spec.get("scvi", {}).get("model_kwargs", {}))
        return model_cls(adata, **kwargs)

    def train(self, model: Any, run_spec: dict[str, Any]) -> None:
        train_kwargs = dict(run_spec.get("scvi", {}).get("train", {}))
        model.train(**train_kwargs)

    def collect_outputs(self, model: Any, adata: Any, run_spec: dict[str, Any]) -> dict[str, Any]:
        downstream = run_spec.get("scvi", {}).get("downstream", {})
        summary = {"model": self.model_name, "capabilities": inspect_model(self.model_name).get("capabilities", {})}
        if hasattr(model, "get_latent_representation"):
            latent_key = downstream.get("latent_key", "X_scvi")
            adata.obsm[latent_key] = model.get_latent_representation()
            summary["latent_key"] = latent_key
            summary.update(run_downstream_scanpy(adata, latent_key, downstream))
        else:
            summary["latent_unavailable"] = True
        if downstream.get("normalized_expression", False) and hasattr(model, "get_normalized_expression"):
            try:
                expression = model.get_normalized_expression()
                layer_key = downstream.get("normalized_layer", "scvi_normalized")
                adata.layers[layer_key] = expression.to_numpy() if hasattr(expression, "to_numpy") else expression
                summary["normalized_layer"] = layer_key
            except Exception as exc:
                summary["normalized_expression_unavailable"] = str(exc)
        return summary


class ScanVIAdapter(ScviModelAdapter):
    def validate_input(self, adata: Any, run_spec: dict[str, Any]) -> dict[str, Any]:
        result = super().validate_input(adata, run_spec)
        setup = run_spec.get("scvi", {}).get("setup_anndata", {})
        label_key = setup.get("labels_key") or setup.get("label_key")
        unlabeled = setup.get("unlabeled_category")
        if not label_key:
            result["valid"] = False
            result["issues"].append(
                {
                    "error_type": "MissingLabelKey",
                    "message": "SCANVI requires setup_anndata.labels_key.",
                    "suggested_fix": "Set scvi.setup_anndata.labels_key to an obs column containing cell labels.",
                }
            )
        elif unlabeled is not None and label_key in adata.obs and unlabeled not in set(map(str, adata.obs[label_key].astype(str))):
            result.setdefault("warnings", []).append(
                {
                    "error_type": "MissingUnlabeledCategory",
                    "message": f"unlabeled_category='{unlabeled}' was not observed in adata.obs['{label_key}'].",
                    "suggested_fix": "Use an existing unlabeled category or omit unlabeled_category.",
                }
            )
        return result

    def collect_outputs(self, model: Any, adata: Any, run_spec: dict[str, Any]) -> dict[str, Any]:
        summary = super().collect_outputs(model, adata, run_spec)
        if hasattr(model, "predict"):
            key = run_spec.get("scvi", {}).get("downstream", {}).get("prediction_key", "scanvi_predicted_labels")
            try:
                adata.obs[key] = model.predict()
                summary["prediction_key"] = key
                summary["predicted_label_counts"] = adata.obs[key].astype(str).value_counts().to_dict()
            except Exception as exc:
                summary["prediction_unavailable"] = str(exc)
        return summary


class TotalVIAdapter(ScviModelAdapter):
    def validate_input(self, adata: Any, run_spec: dict[str, Any]) -> dict[str, Any]:
        result = super().validate_input(adata, run_spec)
        protein_obsm_key = run_spec.get("scvi", {}).get("setup_anndata", {}).get("protein_expression_obsm_key")
        if not protein_obsm_key:
            result["valid"] = False
            result["issues"].append(
                {
                    "error_type": "MissingProteinObsmKey",
                    "message": "TOTALVI requires setup_anndata.protein_expression_obsm_key.",
                    "suggested_fix": "Set protein_expression_obsm_key to an adata.obsm key containing protein counts.",
                }
            )
        elif protein_obsm_key not in adata.obsm:
            result["valid"] = False
            result["issues"].append(
                {
                    "error_type": "MissingProteinObsm",
                    "message": f"Protein matrix '{protein_obsm_key}' was not found in adata.obsm.",
                    "suggested_fix": "Add CITE-seq protein expression to adata.obsm or use SCVI.",
                }
            )
        return result

    def collect_outputs(self, model: Any, adata: Any, run_spec: dict[str, Any]) -> dict[str, Any]:
        summary = super().collect_outputs(model, adata, run_spec)
        protein_obsm_key = run_spec.get("scvi", {}).get("setup_anndata", {}).get("protein_expression_obsm_key")
        if protein_obsm_key and protein_obsm_key in adata.obsm:
            matrix = adata.obsm[protein_obsm_key]
            summary["protein_obsm_key"] = protein_obsm_key
            summary["protein_shape"] = list(getattr(matrix, "shape", []))
            summary["protein_features"] = list(getattr(matrix, "columns", []))[:50]
        return summary


class PeakVIAdapter(ScviModelAdapter):
    def validate_input(self, adata: Any, run_spec: dict[str, Any]) -> dict[str, Any]:
        result = super().validate_input(adata, run_spec)
        if adata.n_vars < 10:
            result["valid"] = False
            result["issues"].append(
                {
                    "error_type": "TooFewPeaks",
                    "message": "PEAKVI input should contain an ATAC peak-by-cell count matrix.",
                    "suggested_fix": "Provide an AnnData object with peaks in var and cells in obs.",
                }
            )
        return result

    def collect_outputs(self, model: Any, adata: Any, run_spec: dict[str, Any]) -> dict[str, Any]:
        summary = super().collect_outputs(model, adata, run_spec)
        summary["n_peaks"] = int(adata.n_vars)
        summary["accessibility_latent"] = summary.get("latent_key")
        return summary


class MultiVIAdapter(ScviModelAdapter):
    def validate_input(self, adata: Any, run_spec: dict[str, Any]) -> dict[str, Any]:
        if hasattr(adata, "mod"):
            issues: list[dict[str, str]] = []
            for modality in ["rna", "atac"]:
                if modality not in adata.mod:
                    issues.append(
                        {
                            "error_type": "MissingModality",
                            "message": f"MULTIVI synthetic MuData requires modality '{modality}'.",
                            "suggested_fix": "Provide MuData with RNA and ATAC modalities or choose SCVI/PEAKVI.",
                        }
                    )
            return {
                "valid": not issues,
                "issues": issues,
                "n_obs": int(adata.n_obs),
                "n_vars": int(adata.n_vars),
                "modalities": sorted(map(str, adata.mod.keys())),
            }
        result = super().validate_input(adata, run_spec)
        setup = run_spec.get("scvi", {}).get("setup_anndata", {})
        modality_key = setup.get("modality_key") or run_spec.get("scvi", {}).get("modality_key") or "modality"
        has_var_modality = modality_key in adata.var
        has_protein = bool(setup.get("protein_expression_obsm_key") and setup.get("protein_expression_obsm_key") in adata.obsm)
        if not has_var_modality and not has_protein:
            result["valid"] = False
            result["issues"].append(
                {
                    "error_type": "MissingMultiModalAnnotation",
                    "message": f"MULTIVI requires modality annotations in adata.var['{modality_key}'] or configured protein obsm counts.",
                    "suggested_fix": "Add RNA/ATAC modality annotations or choose SCVI/PEAKVI for single-modality data.",
                }
            )
        return result

    def setup_anndata(self, adata: Any, run_spec: dict[str, Any]):
        model_cls = get_model_class(self.model_name)
        if hasattr(adata, "mod"):
            setup = dict(run_spec.get("scvi", {}).get("setup_anndata", {}))
            model_cls.setup_mudata(
                adata,
                rna_layer=setup.get("rna_layer", setup.get("layer", "counts")),
                atac_layer=setup.get("atac_layer", setup.get("layer", "counts")),
                batch_key=setup.get("batch_key"),
                modalities=setup.get("modalities", {"rna_layer": "rna", "atac_layer": "atac", "batch_key": "rna"}),
            )
            return adata
        return super().setup_anndata(adata, run_spec)

    def collect_outputs(self, model: Any, adata: Any, run_spec: dict[str, Any]) -> dict[str, Any]:
        summary = super().collect_outputs(model, adata, run_spec)
        if hasattr(adata, "mod"):
            summary["modalities"] = sorted(map(str, adata.mod.keys()))
            summary["modality_shapes"] = {key: list(value.shape) for key, value in adata.mod.items()}
            return summary
        modality_key = run_spec.get("scvi", {}).get("setup_anndata", {}).get("modality_key") or "modality"
        if modality_key in adata.var:
            summary["modality_key"] = modality_key
            summary["modality_counts"] = adata.var[modality_key].astype(str).value_counts().to_dict()
        return summary


ADAPTERS = {
    "SCANVI": ScanVIAdapter,
    "TOTALVI": TotalVIAdapter,
    "PEAKVI": PeakVIAdapter,
    "MULTIVI": MultiVIAdapter,
}


def get_adapter(model_name: str) -> ScviModelAdapter:
    canonical = model_name.upper()
    adapter_cls = ADAPTERS.get(canonical, ScviModelAdapter)
    return adapter_cls(model_name=model_name)


def looks_integer_counts(matrix: Any) -> bool:
    import numpy as np

    values = matrix.data if hasattr(matrix, "data") else np.asarray(matrix).ravel()
    if values.size == 0:
        return False
    sample = values[: min(values.size, 10000)]
    if np.nanmin(sample) < 0:
        return False
    return bool(np.allclose(sample, np.round(sample)))


def run_downstream_scanpy(adata: Any, latent_key: str, downstream: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    if not any(downstream.get(name, False) for name in ["neighbors", "umap", "leiden"]):
        return summary
    try:
        import scanpy as sc
    except ImportError as exc:
        summary["downstream_unavailable"] = f"scanpy import failed: {exc}"
        return summary
    try:
        if downstream.get("neighbors", False):
            sc.pp.neighbors(adata, use_rep=latent_key)
            summary["neighbors"] = True
        if downstream.get("umap", False):
            sc.tl.umap(adata)
            summary["umap_key"] = "X_umap"
        if downstream.get("leiden", False):
            key = downstream.get("leiden_key", "leiden")
            sc.tl.leiden(adata, key_added=key)
            summary["leiden_key"] = key
    except Exception as exc:
        summary["downstream_warning"] = str(exc)
    return summary


def assert_validation(result: dict[str, Any]) -> None:
    if result.get("valid"):
        return
    first = result.get("issues", [{}])[0]
    raise OmicsError(
        first.get("error_type", "AnnDataValidationFailed"),
        first.get("message", "AnnData validation failed."),
        first.get("suggested_fix"),
        "validate_adata",
    )
