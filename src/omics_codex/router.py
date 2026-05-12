from __future__ import annotations

from pathlib import Path
from typing import Any


def choose_skill(prompt: str, input_path: str | None = None) -> str:
    text = f"{prompt} {input_path or ''}".lower()
    if any(token in text for token in ["nf-core", "nextflow", "fastq", "bam", "cram", "sra", "geo", "rnaseq", "sarek", "atacseq"]):
        return "nf-core-universal"
    if any(token in text for token in ["scvi", "scanvi", "totalvi", "peakvi", "multivi", "batch correction", "latent"]):
        return "scvi-universal"
    if any(token in text for token in ["h5ad", "10x", "scrna", "single-cell", "single cell", "qc", "mitochondrial"]):
        return "single-cell-rna-qc"
    if any(token in text for token in ["new skill", "add skill", "authoring", "template"]):
        return "skill-authoring-kit"
    return "omics-router"


def build_run_spec(prompt: str, input_path: str | None = None, outdir: str = "./results/omics") -> dict[str, Any]:
    skill = choose_skill(prompt, input_path)
    run_type = {
        "nf-core-universal": "nfcore_pipeline",
        "single-cell-rna-qc": "scrna_qc",
        "scvi-universal": "scvi_model",
        "omics-report": "omics_report",
        "skill-authoring-kit": "new_skill",
    }.get(skill, "omics_report")
    inspection = inspect_input_path(input_path)
    spec: dict[str, Any] = {
        "run": {
            "name": "omics_request",
            "description": prompt,
            "type": run_type,
            "skill": skill,
        },
        "inputs": {"path": input_path or "", "type": inspection["type"], "inspection": inspection},
        "execution": {"mode": "plan_then_execute", "approved": False},
        "outputs": {
            "outdir": outdir,
            "report": str(Path(outdir) / "report.md"),
            "manifest": str(Path(outdir) / "run_manifest.json"),
        },
    }
    if skill == "nf-core-universal":
        pipeline = infer_nfcore_pipeline(prompt, input_path)
        spec["nfcore"] = {
            "pipeline": pipeline,
            "version": "latest",
            "profile": "docker",
            "params": infer_nfcore_params(pipeline, input_path, outdir),
        }
    elif skill == "single-cell-rna-qc":
        spec["scrna_qc"] = {
            "preserve_raw_counts": True,
            "counts_layer": "counts",
            "filter": {"mode": "mad", "n_mads_counts": 5, "n_mads_genes": 5, "n_mads_mito": 3, "max_pct_mito": 20, "min_cells_per_gene": 1},
            "gene_patterns": {"mt": "^MT-", "ribo": "^RP[SL]", "hb": "^HB[^(P)]"},
        }
    elif skill == "scvi-universal":
        model = infer_scvi_model(prompt)
        setup = {"layer": "counts", "batch_key": "batch"}
        if model == "SCANVI":
            setup.update({"labels_key": "cell_type", "unlabeled_category": "Unknown"})
        if model == "TOTALVI":
            setup["protein_expression_obsm_key"] = "protein_expression"
        spec["scvi"] = {
            "model": model,
            "setup_anndata": setup,
            "model_kwargs": {"n_latent": 10},
            "train": {"max_epochs": 20},
            "downstream": {"latent_key": f"X_{model.lower()}", "neighbors": True, "umap": True},
        }
    return spec


def infer_input_type(path: str | None) -> str:
    if not path:
        return "unknown"
    suffixes = "".join(Path(path).suffixes).lower()
    if suffixes.endswith(".h5ad"):
        return "h5ad"
    if suffixes.endswith(".h5"):
        return "10x_h5"
    if suffixes.endswith(".fastq.gz") or suffixes.endswith(".fq.gz"):
        return "fastq"
    if Path(path).is_dir():
        return "directory"
    return "unknown"


def inspect_input_path(path: str | None) -> dict[str, Any]:
    inferred = infer_input_type(path)
    result: dict[str, Any] = {"path": path or "", "type": inferred, "exists": False}
    if not path:
        return result
    source = Path(path)
    result["exists"] = source.exists()
    if source.is_dir():
        result["fastq_files"] = len([item for item in source.rglob("*") if item.is_file() and "".join(item.suffixes).lower().endswith((".fastq.gz", ".fq.gz"))])
        result["children"] = len(list(source.iterdir()))
    elif source.exists():
        result["size_bytes"] = source.stat().st_size
        if inferred == "h5ad":
            try:
                import anndata as ad

                adata = ad.read_h5ad(source, backed="r")
                result["n_obs"] = int(adata.n_obs)
                result["n_vars"] = int(adata.n_vars)
                result["obs_keys"] = list(map(str, adata.obs.columns))
                result["layers"] = list(map(str, adata.layers.keys()))
                adata.file.close()
            except Exception as exc:
                result["h5ad_warning"] = str(exc)
    return result


def infer_nfcore_pipeline(prompt: str, input_path: str | None = None) -> str:
    text = f"{prompt} {input_path or ''}".lower()
    if "sarek" in text or any(token in text for token in ["bam", "cram", "variant", "vcf"]):
        return "sarek"
    if "atac" in text or "peak" in text:
        return "atacseq"
    return "rnaseq"


def infer_nfcore_params(pipeline: str, input_path: str | None, outdir: str) -> dict[str, Any]:
    params: dict[str, Any] = {"outdir": outdir}
    if input_path:
        params["input"] = input_path
    if pipeline in {"rnaseq", "atacseq"}:
        params.setdefault("genome", "GRCh38")
    if pipeline == "rnaseq":
        params.setdefault("aligner", "star_salmon")
    return params


def infer_scvi_model(prompt: str) -> str:
    text = prompt.lower()
    for model in ["MULTIVI", "TOTALVI", "PEAKVI", "SCANVI", "SCVI"]:
        if model.lower() in text:
            return model
    return "SCVI"
