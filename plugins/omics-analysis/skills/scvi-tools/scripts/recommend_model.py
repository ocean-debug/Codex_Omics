from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from common.io import write_json  # noqa: E402


MODEL_REQUIREMENTS = {
    "SCVI": ["count matrix", "optional batch_key"],
    "SCANVI": ["labels_key", "unlabeled_category for unlabeled cells"],
    "TOTALVI": ["RNA count matrix", "protein expression in adata.obsm"],
    "PEAKVI": ["peak/accessibility matrix"],
    "MULTIVI": ["multiome modality metadata or paired RNA/ATAC inputs"],
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Recommend an scvi-tools model for an AnnData task.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--task", default="")
    parser.add_argument("--batch-key")
    parser.add_argument("--labels-key")
    parser.add_argument("--protein-obsm", default="protein_expression")
    parser.add_argument("--modality-key", default="modality")
    parser.add_argument("--out")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    result = recommend(args)
    if args.out:
        write_json(args.out, result)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


def recommend(args: argparse.Namespace) -> dict[str, Any]:
    metadata = inspect_anndata(Path(args.input), args.protein_obsm, args.modality_key)
    ranked = rank_models(args.task.lower(), metadata, args)
    return {
        "status": "ok",
        "input": args.input,
        "task": args.task,
        "recommended_model": ranked[0]["model"],
        "ranked_recommendations": ranked,
        "anndata_summary": metadata,
    }


def inspect_anndata(path: Path, protein_obsm: str, modality_key: str) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "exists": path.exists(),
        "readable": False,
        "n_obs": None,
        "n_vars": None,
        "obs_keys": [],
        "var_keys": [],
        "obsm_keys": [],
        "has_protein_obsm": False,
        "has_modality_metadata": False,
        "warnings": [],
    }
    if not path.exists():
        summary["warnings"].append("Input path does not exist; recommendation uses task text and supplied keys only.")
        return summary
    try:
        import anndata as ad

        adata = ad.read_h5ad(path, backed="r")
        summary.update(
            {
                "readable": True,
                "n_obs": int(adata.n_obs),
                "n_vars": int(adata.n_vars),
                "obs_keys": list(adata.obs.keys()),
                "var_keys": list(adata.var.keys()),
                "obsm_keys": list(adata.obsm.keys()),
                "has_protein_obsm": protein_obsm in adata.obsm,
                "has_modality_metadata": modality_key in adata.obs or modality_key in adata.var,
            }
        )
        try:
            adata.file.close()
        except Exception:
            pass
    except Exception as exc:
        summary["warnings"].append(f"Could not inspect AnnData: {exc}")
    return summary


def rank_models(task: str, metadata: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    scores = {model: 0 for model in MODEL_REQUIREMENTS}
    reasons: dict[str, list[str]] = {model: [] for model in MODEL_REQUIREMENTS}
    missing: dict[str, list[str]] = {model: [] for model in MODEL_REQUIREMENTS}

    if any(token in task for token in ["scanvi", "label transfer", "annotat", "cell type"]):
        scores["SCANVI"] += 8
        reasons["SCANVI"].append("Task mentions label transfer, annotation, or scANVI.")
    if args.labels_key:
        scores["SCANVI"] += 4
        reasons["SCANVI"].append("labels_key was provided.")
    else:
        missing["SCANVI"].append("--labels-key")

    if any(token in task for token in ["totalvi", "cite", "protein", "adt"]):
        scores["TOTALVI"] += 8
        reasons["TOTALVI"].append("Task mentions CITE-seq/protein/ADT or totalVI.")
    if metadata.get("has_protein_obsm"):
        scores["TOTALVI"] += 5
        reasons["TOTALVI"].append(f"AnnData contains protein obsm `{args.protein_obsm}`.")
    else:
        missing["TOTALVI"].append(f"adata.obsm['{args.protein_obsm}']")

    if any(token in task for token in ["peakvi", "atac", "accessibility", "peak"]):
        scores["PEAKVI"] += 8
        reasons["PEAKVI"].append("Task mentions ATAC/accessibility/peaks or PEAKVI.")

    if any(token in task for token in ["multivi", "multiome", "multi-modal", "multimodal"]):
        scores["MULTIVI"] += 8
        reasons["MULTIVI"].append("Task mentions multiome or MULTIVI.")
    if metadata.get("has_modality_metadata"):
        scores["MULTIVI"] += 4
        reasons["MULTIVI"].append(f"AnnData contains modality metadata `{args.modality_key}`.")
    else:
        missing["MULTIVI"].append(f"obs/var `{args.modality_key}`")

    if any(token in task for token in ["scvi", "integration", "batch", "latent", "denoise"]) or not task:
        scores["SCVI"] += 6
        reasons["SCVI"].append("SCVI is the default for scRNA integration, denoising, and latent embeddings.")
    if args.batch_key:
        scores["SCVI"] += 2
        reasons["SCVI"].append("batch_key was provided for integration.")

    ranked = []
    for model, score in scores.items():
        ranked.append(
            {
                "model": model,
                "score": score,
                "reasons": reasons[model] or ["Compatible as a fallback when its input requirements are met."],
                "requirements": MODEL_REQUIREMENTS[model],
                "missing_requirements": missing[model],
            }
        )
    return sorted(ranked, key=lambda item: (-item["score"], item["model"]))


if __name__ == "__main__":
    raise SystemExit(main())
