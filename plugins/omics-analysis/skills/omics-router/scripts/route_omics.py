from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from common.env import inspect_nextflow_environment, inspect_scrna_qc_environment, inspect_scvi_environment  # noqa: E402
from common.io import ensure_outdir, write_json  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Route an omics request to a Codex-Omics plugin-local skill.")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--input", required=True)
    parser.add_argument("--outdir", default="results/omics_route")
    parser.add_argument("--out")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved", default="false")
    args = parser.parse_args()

    outdir = ensure_outdir(args.outdir)
    route = route_request(args.prompt, Path(args.input), outdir)
    target = Path(args.out) if args.out else outdir / "omics_route_plan.json"
    write_json(target, route)
    print(json.dumps(route, indent=2, sort_keys=True, default=str))
    return 0


def route_request(prompt: str, input_path: Path, outdir: Path) -> dict[str, Any]:
    prompt_l = prompt.lower()
    inventory = inspect_input(input_path)
    if any(token in prompt_l for token in ["scvi", "scanvi", "totalvi", "peakvi", "multivi", "batch correction", "latent"]):
        skill = "scvi-tools"
        env = inspect_scvi_environment()
        plan = scvi_plan(input_path, outdir, prompt_l)
    elif inventory["formats"].get("h5ad") or inventory["formats"].get("tenx_h5") or inventory["formats"].get("tenx_mtx") or "qc" in prompt_l:
        skill = "single-cell-rna-qc"
        env = inspect_scrna_qc_environment()
        plan = scrna_qc_plan(input_path, outdir)
    elif inventory["formats"].get("fastq") or any(token in prompt_l for token in ["rnaseq", "atacseq", "sarek", "fastq", "nextflow", "nf-core"]):
        skill = "nextflow-development"
        env = inspect_nextflow_environment()
        plan = nextflow_plan(input_path, outdir, prompt_l)
    else:
        skill = "omics-router"
        env = {"status": "warning", "blockers": [], "warnings": [{"warning_type": "AmbiguousInput", "message": "No omics workflow could be selected confidently.", "suggested_fix": "Provide a prompt mentioning QC, scVI, rnaseq, atacseq, sarek, FASTQ, h5ad, or 10x."}]}
        plan = {"approval_required": False, "commands": []}
    return {
        "status": "planned",
        "selected_skill": skill,
        "approved": False,
        "input": str(input_path),
        "input_inventory": inventory,
        "environment_status": env.get("status"),
        "environment_requirements": requirements_for(skill),
        "environment_blockers": env.get("blockers", []),
        "environment_warnings": env.get("warnings", []),
        "plan": plan,
    }


def inspect_input(path: Path) -> dict[str, Any]:
    formats = {"h5ad": 0, "tenx_h5": 0, "tenx_mtx": 0, "fastq": 0, "reference_fasta": 0, "reference_gtf": 0}
    files: list[str] = []
    candidates = [path] if path.is_file() else sorted(path.rglob("*"))[:1000] if path.exists() else []
    for item in candidates:
        if not item.is_file():
            continue
        name = item.name.lower()
        files.append(str(item))
        if name.endswith(".h5ad"):
            formats["h5ad"] += 1
        elif name.endswith(".h5"):
            formats["tenx_h5"] += 1
        elif name.endswith((".fastq.gz", ".fq.gz", ".fastq", ".fq")):
            formats["fastq"] += 1
        elif name in {"matrix.mtx", "matrix.mtx.gz"}:
            formats["tenx_mtx"] += 1
        elif name.endswith((".fa", ".fasta", ".fa.gz", ".fasta.gz")):
            formats["reference_fasta"] += 1
        elif name.endswith((".gtf", ".gtf.gz", ".gff", ".gff3")):
            formats["reference_gtf"] += 1
    return {"exists": path.exists(), "formats": formats, "sample_files": files[:25]}


def scrna_qc_plan(input_path: Path, outdir: Path) -> dict[str, Any]:
    qc_out = outdir / "single_cell_rna_qc"
    return {
        "approval_required": True,
        "commands": [
            f"python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/check_environment.py --json",
            f"python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py --input {input_path} --output-dir {qc_out} --dry-run --json",
        ],
        "approved_command": f"python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py --input {input_path} --output-dir {qc_out} --approved true --write-manifest",
    }


def scvi_plan(input_path: Path, outdir: Path, prompt: str) -> dict[str, Any]:
    model = "SCANVI" if "scanvi" in prompt else "TOTALVI" if "totalvi" in prompt else "PEAKVI" if "peakvi" in prompt else "MULTIVI" if "multivi" in prompt else "SCVI"
    scvi_out = outdir / "scvi"
    return {
        "approval_required": True,
        "model": model,
        "commands": [
            "python plugins/omics-analysis/skills/scvi-tools/scripts/check_environment.py --json",
            f"python plugins/omics-analysis/skills/scvi-tools/scripts/train_model.py --input {input_path} --output-dir {scvi_out} --model {model} --dry-run --json",
        ],
        "approved_command": f"python plugins/omics-analysis/skills/scvi-tools/scripts/train_model.py --input {input_path} --output-dir {scvi_out} --model {model} --approved true",
    }


def nextflow_plan(input_path: Path, outdir: Path, prompt: str) -> dict[str, Any]:
    pipeline = "atacseq" if "atac" in prompt else "sarek" if "sarek" in prompt else "rnaseq"
    nf_out = outdir / pipeline
    sheet = nf_out / "samplesheet.csv"
    return {
        "approval_required": True,
        "pipeline": pipeline,
        "commands": [
            "python plugins/omics-analysis/skills/nextflow-development/scripts/check_environment.py --json",
            f"python plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py --pipeline {pipeline} --input {input_path} --out {sheet}",
            f"python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py --pipeline {pipeline} --input {sheet} --outdir {nf_out} --profile singularity --dry-run --json",
        ],
    }


def requirements_for(skill: str) -> list[str]:
    return {
        "single-cell-rna-qc": ["scanpy", "anndata", "numpy", "scipy", "pandas", "matplotlib", "seaborn"],
        "scvi-tools": ["scvi-tools", "torch", "scanpy", "anndata", "GPU optional but recommended"],
        "nextflow-development": ["Java 17+", "Nextflow", "nf-core", "git", "Singularity/Apptainer or Docker"],
    }.get(skill, [])


if __name__ == "__main__":
    raise SystemExit(main())
