from __future__ import annotations

import re
from pathlib import Path
from typing import Any


TEMPLATE_ALIASES = {
    "bulk-rna": "bulk-rna",
    "bulk_rna": "bulk-rna",
    "rnaseq": "bulk-rna",
    "rna-seq": "bulk-rna",
    "atac": "atac",
    "atacseq": "atac",
    "atac-seq": "atac",
    "scrna-qc": "scrna-qc",
    "scrna_qc": "scrna-qc",
    "single-cell-qc": "scrna-qc",
    "scrna-qc-scvi": "scrna-qc-scvi",
    "scrna_scvi": "scrna-qc-scvi",
    "qc-scvi": "scrna-qc-scvi",
    "scvi": "scvi",
    "scvi-only": "scvi",
}

TEMPLATE_DESCRIPTIONS = {
    "bulk-rna": "Bulk RNA-seq nf-core/rnaseq workflow template.",
    "atac": "ATAC-seq nf-core/atacseq workflow template.",
    "scrna-qc": "Single-cell RNA-seq QC run template.",
    "scrna-qc-scvi": "Single-cell RNA-seq QC followed by scVI workflow template.",
    "scvi": "scVI-only model training run template.",
}


def choose_skill(prompt: str, input_path: str | None = None) -> str:
    text = f"{prompt} {input_path or ''}".lower()
    inspection = inspect_input_path(input_path)
    if any(token in text for token in ["nf-core", "nextflow", "fastq", "bam", "cram", "sra", "geo", "rnaseq", "rna-seq", "rna seq", "bulk rna", "sarek", "atacseq", "atac-seq", "atac seq"]):
        return "nf-core-universal"
    if any(token in text for token in ["scvi", "scanvi", "totalvi", "peakvi", "multivi", "batch correction", "latent"]):
        return "scvi-universal"
    if any(token in text for token in ["h5ad", "10x", "scrna", "single-cell", "single cell", "qc", "mitochondrial"]):
        return "single-cell-rna-qc"
    if inspection.get("fastq_pairs", 0) > 0 or inspection.get("fastq_files", 0) > 0:
        return "nf-core-universal"
    if inspection.get("h5ad_files", 0) > 0 or inspection.get("type") == "h5ad":
        return "single-cell-rna-qc"
    if inspection.get("type") in {"10x_h5", "10x_mtx"}:
        return "single-cell-rna-qc"
    if any(token in text for token in ["new skill", "add skill", "authoring", "template"]):
        return "skill-authoring-kit"
    return "omics-router"


def build_run_spec(prompt: str, input_path: str | None = None, outdir: str = "./results/omics") -> dict[str, Any]:
    inspection = inspect_input_path(input_path)
    skill = choose_skill(prompt, input_path)
    selected_input = select_primary_input_path(input_path, inspection, skill)
    input_type = infer_input_type(selected_input) if selected_input and selected_input != input_path else inspection["type"]
    run_type = {
        "nf-core-universal": "nfcore_pipeline",
        "single-cell-rna-qc": "scrna_qc",
        "scvi-universal": "scvi_model",
        "omics-report": "omics_report",
        "skill-authoring-kit": "new_skill",
    }.get(skill, "omics_report")
    spec: dict[str, Any] = {
        "run": {
            "name": "omics_request",
            "description": prompt,
            "type": run_type,
            "skill": skill,
        },
        "inputs": {"path": selected_input or "", "type": input_type, "inspection": inspection},
        "execution": {"mode": "plan_then_execute", "approved": False},
        "requirements": requirements_for_skill(skill),
        "outputs": {
            "outdir": outdir,
            "report": str(Path(outdir) / "report.md"),
            "manifest": str(Path(outdir) / "run_manifest.json"),
        },
        "codex_user_path": user_path_steps(kind="run", out_path="<generated-spec.yaml>", result_dir=outdir, skill=skill),
    }
    if skill == "nf-core-universal":
        pipeline = infer_nfcore_pipeline(prompt, input_path)
        spec["nfcore"] = {
            "pipeline": pipeline,
            "version": "latest",
            "profile": infer_execution_profile(prompt),
            "params": infer_nfcore_params(pipeline, selected_input, outdir, inspection),
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
    if wants_nfcore_workflow(prompt, input_path):
        pipeline = infer_nfcore_pipeline(prompt, input_path)
        return build_nfcore_workflow_spec(prompt, input_path, outdir, pipeline)
    return build_run_spec(prompt, input_path, outdir)


def wants_scrna_scvi_workflow(prompt: str) -> bool:
    text = prompt.lower()
    has_qc = any(token in text for token in ["qc", "quality control", "filter"])
    has_scvi = any(token in text for token in ["scvi", "scanvi", "batch correction", "latent", "integration"])
    has_single_cell = any(token in text for token in ["scrna", "single-cell", "single cell", "h5ad", "10x"])
    return (has_qc and has_scvi) or ("workflow" in text and has_scvi and has_single_cell)


def wants_nfcore_workflow(prompt: str, input_path: str | None = None) -> bool:
    text = prompt.lower()
    if "workflow" not in text and "pipeline" not in text:
        return False
    return choose_skill(prompt, input_path) == "nf-core-universal"


def list_templates() -> list[dict[str, str]]:
    return [
        {"name": name, "description": description}
        for name, description in sorted(TEMPLATE_DESCRIPTIONS.items())
    ]


def build_template_spec(template: str, input_path: str | None = None, outdir: str = "./results/omics", prompt: str | None = None) -> dict[str, Any]:
    name = normalize_template_name(template)
    template_prompt = prompt or TEMPLATE_DESCRIPTIONS[name]
    if name == "bulk-rna":
        return build_nfcore_workflow_spec(template_prompt, input_path, outdir, "rnaseq")
    if name == "atac":
        return build_nfcore_workflow_spec(template_prompt, input_path, outdir, "atacseq")
    if name == "scrna-qc":
        return build_run_spec(f"{template_prompt} scRNA QC", input_path, outdir)
    if name == "scrna-qc-scvi":
        return build_scrna_scvi_workflow_spec(template_prompt, input_path, outdir)
    if name == "scvi":
        return build_run_spec(f"{template_prompt} scvi", input_path, outdir)
    raise ValueError(f"Unsupported template: {template}")


def normalize_template_name(template: str) -> str:
    key = template.strip().lower()
    if key not in TEMPLATE_ALIASES:
        valid = ", ".join(sorted(TEMPLATE_DESCRIPTIONS))
        raise ValueError(f"Unknown template '{template}'. Choose one of: {valid}.")
    return TEMPLATE_ALIASES[key]


def build_nfcore_workflow_spec(prompt: str, input_path: str | None, outdir: str, pipeline: str) -> dict[str, Any]:
    run_out = str(Path(outdir) / pipeline)
    spec = build_run_spec(f"{prompt} nf-core/{pipeline}", input_path, run_out)
    spec["run"]["name"] = f"nfcore_{pipeline}"
    spec["nfcore"]["pipeline"] = pipeline
    spec["nfcore"]["params"] = infer_nfcore_params(pipeline, spec["inputs"].get("path"), run_out, spec["inputs"].get("inspection", {}))
    return {
        "workflow": {
            "name": f"{pipeline}_workflow",
            "description": prompt,
            "outdir": outdir,
            "requirements": requirements_for_skill("nf-core-universal"),
            "stop_on_failure": True,
            "execution": {"mode": "plan_then_execute", "approved": False},
            "stages": [{"name": pipeline, "spec": spec}],
        },
        "codex_user_path": user_path_steps(kind="workflow", out_path="<generated-workflow.yaml>", result_dir=outdir, skill="nf-core-universal"),
    }


def build_scrna_scvi_workflow_spec(prompt: str, input_path: str | None, outdir: str) -> dict[str, Any]:
    inspection = inspect_input_path(input_path)
    selected_input = select_primary_input_path(input_path, inspection, "single-cell-rna-qc")
    input_type = infer_input_type(selected_input) if selected_input and selected_input != input_path else inspection["type"]
    scrna_out = str(Path(outdir) / "scrna_qc")
    scvi_out = str(Path(outdir) / "scvi")
    return {
        "workflow": {
            "name": "scrna_qc_scvi_request",
            "description": prompt,
            "outdir": outdir,
            "requirements": {
                "software": [
                    "scverse stack for scRNA QC",
                    "scvi-tools plus a PyTorch build compatible with the target CPU/GPU runtime",
                ],
                "notes": ["Generated workflows are safe by default and keep approved: false until explicitly changed."],
            },
            "stop_on_failure": True,
            "execution": {"mode": "plan_then_execute", "approved": False},
            "stages": [
                {
                    "name": "scrna_qc",
                    "spec": {
                        "run": {"name": "scrna_qc", "type": "scrna_qc", "skill": "single-cell-rna-qc"},
                        "inputs": {"path": selected_input or "", "type": input_type, "inspection": inspection},
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
        },
        "codex_user_path": user_path_steps(kind="workflow", out_path="<generated-workflow.yaml>", result_dir=outdir, skill="scvi-universal"),
    }


def user_path_steps(kind: str, out_path: str, result_dir: str, skill: str) -> dict[str, Any]:
    env_kind = "all"
    if skill == "nf-core-universal":
        env_kind = "nfcore"
    elif skill == "scvi-universal":
        env_kind = "scvi"
    elif skill == "single-cell-rna-qc":
        env_kind = "scrna_qc"
    plan_command = f"omics-codex workflow plan --config {out_path}" if kind == "workflow" else f"omics-codex validate --config {out_path}"
    run_command = f"omics-codex workflow run --config {out_path}" if kind == "workflow" else f"omics-codex run --config {out_path}"
    manifest_name = "workflow_manifest.json" if kind == "workflow" else "run_manifest.json"
    manifest_path = f"{result_dir.rstrip('/')}/{manifest_name}"
    return {
        "summary": "inspect-env -> inspect-data -> route/template -> plan/validate -> approved run -> report",
        "safe_default": "Generated specs keep approved: false. Review and explicitly set approved: true before real execution.",
        "commands": [
            f"omics-codex inspect-env --kind {env_kind}",
            "omics-codex inspect-data --input <input-path>",
            plan_command,
            run_command,
            f"omics-codex report --manifest {manifest_path}",
        ],
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
        fastq_pairs = detect_fastq_pairs(fastq_files)
        h5ad_files = sorted(item for item in source.rglob("*.h5ad") if item.is_file())
        mtx_files = [item for item in source.rglob("*") if item.is_file() and "".join(item.suffixes).lower().endswith((".mtx", ".mtx.gz"))]
        fasta_files = sorted(item for item in source.rglob("*") if item.is_file() and item.suffix.lower() in {".fa", ".fasta"})
        gtf_files = sorted(item for item in source.rglob("*.gtf") if item.is_file())
        result["fastq_files"] = len(fastq_files)
        result["fastq_pairs"] = len(fastq_pairs)
        result["fastq_pair_examples"] = fastq_pairs[:10]
        result["h5ad_files"] = len(h5ad_files)
        result["h5ad_paths"] = [str(item) for item in h5ad_files[:20]]
        result["mtx_files"] = len(mtx_files)
        result["reference_files"] = {
            "fasta": [str(item) for item in fasta_files[:20]],
            "gtf": [str(item) for item in gtf_files[:20]],
        }
        result["children"] = len(list(source.iterdir()))
        if mtx_files:
            result["type"] = "10x_mtx"
            result["has_10x_mtx"] = True
        elif h5ad_files:
            result["type"] = "h5ad_dir"
        elif fastq_files:
            result["type"] = "fastq_dir"
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


def detect_fastq_pairs(fastq_files: list[Path]) -> list[dict[str, str]]:
    by_name = {item.name: item for item in fastq_files}
    pairs: list[dict[str, str]] = []
    for r1 in sorted(fastq_files):
        mate_name = fastq_mate_name(r1.name)
        if not mate_name or mate_name not in by_name:
            continue
        pairs.append({"sample": fastq_sample_name(r1.name), "fastq_1": str(r1), "fastq_2": str(by_name[mate_name])})
    return pairs


def fastq_mate_name(name: str) -> str | None:
    replacements = [
        (r"_R1(_\d+)?\.(fastq|fq)\.gz$", r"_R2\1.\2.gz"),
        (r"_1\.(fastq|fq)\.gz$", r"_2.\1.gz"),
    ]
    for pattern, replacement in replacements:
        if re.search(pattern, name):
            return re.sub(pattern, replacement, name)
    return None


def fastq_sample_name(name: str) -> str:
    for pattern in [r"_R1(_\d+)?\.(fastq|fq)\.gz$", r"_1\.(fastq|fq)\.gz$"]:
        name = re.sub(pattern, "", name)
    return name


def select_primary_input_path(input_path: str | None, inspection: dict[str, Any], skill: str) -> str | None:
    if skill in {"single-cell-rna-qc", "scvi-universal"} and inspection.get("h5ad_paths"):
        return str(inspection["h5ad_paths"][0])
    return input_path


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


def infer_nfcore_params(pipeline: str, input_path: str | None, outdir: str, inspection: dict[str, Any] | None = None) -> dict[str, Any]:
    params: dict[str, Any] = {"outdir": outdir}
    if input_path:
        params["input"] = input_path
    if pipeline in {"rnaseq", "atacseq"}:
        params.setdefault("genome", "GRCh38")
        references = (inspection or {}).get("reference_files", {})
        if references.get("fasta"):
            params["fasta"] = references["fasta"][0]
        if references.get("gtf"):
            params["gtf"] = references["gtf"][0]
    if pipeline == "rnaseq":
        params.setdefault("aligner", "star_salmon")
    return params


def infer_scvi_model(prompt: str) -> str:
    text = prompt.lower()
    for model in ["MULTIVI", "TOTALVI", "PEAKVI", "SCANVI", "SCVI"]:
        if model.lower() in text:
            return model
    return "SCVI"


def requirements_for_skill(skill: str) -> dict[str, list[str]]:
    if skill == "nf-core-universal":
        return {
            "software": [
                "Java 17+ with Nextflow on PATH",
                "nf-core CLI",
                "Singularity or Apptainer on HPC, or an explicitly selected container profile",
                "git access or pre-cached nf-core pipelines",
            ],
            "notes": ["Run `omics-codex inspect-env --kind nfcore` before real execution."],
        }
    if skill == "scvi-universal":
        return {
            "software": [
                "scvi-tools in the active Python/UV environment",
                "PyTorch build compatible with the requested CPU/GPU runtime",
                "anndata and scanpy",
            ],
            "notes": ["Run `omics-codex inspect-env --kind scvi` before training."],
        }
    if skill == "single-cell-rna-qc":
        return {
            "software": ["scverse stack with anndata and scanpy"],
            "notes": ["QC plans are generated with `approved: false` unless explicitly changed."],
        }
    return {"software": [], "notes": []}
