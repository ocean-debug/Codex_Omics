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
            "profile": infer_execution_profile(prompt),
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


def build_request_spec(prompt: str, input_path: str | None = None, outdir: str = "./results/omics") -> dict[str, Any]:
    if wants_scrna_scvi_workflow(prompt):
        return build_scrna_scvi_workflow_spec(prompt, input_path, outdir)
    return build_run_spec(prompt, input_path, outdir)


def wants_scrna_scvi_workflow(prompt: str) -> bool:
    text = prompt.lower()
    has_qc = any(token in text for token in ["qc", "quality control", "filter"])
    has_scvi = any(token in text for token in ["scvi", "scanvi", "batch correction", "latent", "integration"])
    return "workflow" in text or (has_qc and has_scvi)


def build_scrna_scvi_workflow_spec(prompt: str, input_path: str | None, outdir: str) -> dict[str, Any]:
    inspection = inspect_input_path(input_path)
    scrna_out = str(Path(outdir) / "scrna_qc")
    scvi_out = str(Path(outdir) / "scvi")
    return {
        "workflow": {
            "name": "scrna_qc_scvi_request",
            "description": prompt,
            "outdir": outdir,
            "stop_on_failure": True,
            "execution": {"mode": "plan_then_execute", "approved": False},
            "stages": [
                {
                    "name": "scrna_qc",
                    "spec": {
                        "run": {"name": "scrna_qc", "type": "scrna_qc", "skill": "single-cell-rna-qc"},
                        "inputs": {"path": input_path or "", "type": inspection["type"], "inspection": inspection},
                        "scrna_qc": {
                            "preserve_raw_counts": True,
                            "counts_layer": "counts",
                            "filter": {"mode": "mad", "n_mads_counts": 5, "n_mads_genes": 5, "n_mads_mito": 3, "max_pct_mito": 20, "min_cells_per_gene": 1},
                            "gene_patterns": {"mt": "^MT-", "ribo": "^RP[SL]", "hb": "^HB[^(P)]"},
                        },
                        "outputs": {"outdir": scrna_out, "report": str(Path(scrna_out) / "report.md"), "manifest": str(Path(scrna_out) / "run_manifest.json")},
                    },
                },
                {
                    "name": "scvi",
                    "connect_from": {"stage": "scrna_qc", "output": "filtered_h5ad"},
                    "spec": {
                        "run": {"name": "scvi", "type": "scvi_model", "skill": "scvi-universal"},
                        "inputs": {"path": "", "type": "h5ad"},
                        "scvi": {
                            "model": infer_scvi_model(prompt),
                            "setup_anndata": {"layer": "counts", "batch_key": "batch"},
                            "model_kwargs": {"n_latent": 10},
                            "train": {"max_epochs": 20},
                            "downstream": {"latent_key": "X_scvi", "neighbors": True, "umap": True},
                        },
                        "outputs": {"outdir": scvi_out, "report": str(Path(scvi_out) / "report.md"), "manifest": str(Path(scvi_out) / "run_manifest.json")},
                    },
                },
            ],
        }
    }


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
        fastq_files = [item for item in source.rglob("*") if item.is_file() and "".join(item.suffixes).lower().endswith((".fastq.gz", ".fq.gz"))]
        mtx_files = [item for item in source.rglob("*") if item.is_file() and "".join(item.suffixes).lower().endswith((".mtx", ".mtx.gz"))]
        result["fastq_files"] = len(fastq_files)
        result["mtx_files"] = len(mtx_files)
        result["children"] = len(list(source.iterdir()))
        if mtx_files:
            result["type"] = "10x_mtx"
            result["has_10x_mtx"] = True
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


def infer_execution_profile(prompt: str) -> str:
    text = prompt.lower()
    if "docker" in text:
        return "docker"
    if "apptainer" in text:
        return "apptainer"
    return "singularity"


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
