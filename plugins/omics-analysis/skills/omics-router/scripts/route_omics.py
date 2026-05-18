from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from common.env import inspect_nextflow_environment, inspect_scrna_qc_environment, inspect_scvi_environment  # noqa: E402
from common.io import ensure_outdir, write_json  # noqa: E402
from common.registry import skill_entries  # noqa: E402


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
    registry = skill_entries()
    detected_intents = detect_intents(prompt_l)
    constraints = detect_constraints(prompt_l)
    candidate_scores = score_candidates(prompt_l, inventory, registry)
    skill = candidate_scores[0]["skill_id"] if candidate_scores and candidate_scores[0]["score"] > 0 else "omics-router"
    if skill == "scvi-tools":
        env = inspect_scvi_environment()
        plan = scvi_plan(input_path, outdir, prompt_l)
    elif skill == "single-cell-rna-qc":
        env = inspect_scrna_qc_environment()
        plan = scrna_qc_plan(input_path, outdir)
    elif skill == "nextflow-development":
        env = inspect_nextflow_environment()
        plan = nextflow_plan(input_path, outdir, prompt_l)
    elif skill == "omics-report":
        env = {"status": "ok", "blockers": [], "warnings": []}
        plan = report_plan(input_path, outdir)
    elif skill == "skill-authoring-kit":
        env = {"status": "ok", "blockers": [], "warnings": []}
        plan = authoring_plan(prompt)
    else:
        env = {"status": "warning", "blockers": [], "warnings": [{"warning_type": "AmbiguousInput", "message": "No omics workflow could be selected confidently.", "suggested_fix": "Provide a prompt mentioning QC, scVI, rnaseq, scrnaseq, riboseq, spatialvi, atacseq, sarek, FASTQ, h5ad, Visium, 10x, report, or new skill."}]}
        plan = {"approval_required": False, "commands": []}
    selected_pipeline = plan.get("pipeline") or plan.get("model")
    blockers = env.get("blockers", [])
    warnings = env.get("warnings", [])
    selection_reason = explain_selection(skill, candidate_scores, inventory, detected_intents)
    router_plan = {
        "detected_intents": detected_intents,
        "input_inventory": inventory,
        "constraints": constraints,
        "candidate_scores": candidate_scores,
        "selected_skill": skill,
        "selected_pipeline": selected_pipeline,
        "selection_reason": selection_reason,
        "blockers": blockers,
        "warnings": warnings,
        "next_actions": plan.get("commands", []),
    }
    return {
        "status": "planned",
        "selected_skill": skill,
        "selected_pipeline": selected_pipeline,
        "approved": False,
        "input": str(input_path),
        "input_inventory": inventory,
        "router_plan": router_plan,
        "environment_status": env.get("status"),
        "environment_requirements": requirements_for(skill),
        "environment_blockers": blockers,
        "environment_warnings": warnings,
        "plan": plan,
    }


def detect_intents(prompt: str) -> list[str]:
    intents: list[str] = []
    intent_tokens = {
        "model_training": ["scvi", "scanvi", "totalvi", "peakvi", "multivi", "train", "latent", "batch correction", "label transfer"],
        "quality_control": ["qc", "quality control", "filter", "mitochondrial"],
        "nextflow_workflow": ["nextflow", "nf-core", "rnaseq", "scrnaseq", "riboseq", "spatialvi", "atacseq", "sarek", "fastq"],
        "reporting": ["report", "manifest", "methods", "interpret"],
        "skill_authoring": ["new skill", "add workflow", "bulk-rna-de", "go-enrichment", "cellchat", "grn", "author skill"],
    }
    for intent, tokens in intent_tokens.items():
        if any(token in prompt for token in tokens):
            intents.append(intent)
    return intents or ["unspecified"]


def detect_constraints(prompt: str) -> dict[str, bool]:
    return {
        "dry_run_requested": any(token in prompt for token in ["dry-run", "dry run", "plan only", "只生成"]),
        "approved_execution_requested": any(token in prompt for token in ["approved true", "--approved true", "real run", "真实运行"]),
        "report_requested": any(token in prompt for token in ["report", "methods", "interpret"]),
    }


def score_candidates(prompt: str, inventory: dict[str, Any], registry: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    scores: list[dict[str, Any]] = []
    format_counts = inventory.get("formats", {})
    observed_formats = {key for key, count in format_counts.items() if count}
    for skill_id, entry in registry.items():
        if skill_id == "omics-router":
            continue
        keyword_hits = [token for token in entry.get("router_keywords", []) if keyword_matches(prompt, str(token).lower())]
        input_hits = sorted(observed_formats.intersection(set(entry.get("input_formats", []))))
        score = len(keyword_hits) * 3 + len(input_hits) * 2
        if skill_id == "single-cell-rna-qc" and {"h5ad", "tenx_h5", "tenx_mtx"}.intersection(observed_formats):
            score += 4
        if skill_id == "nextflow-development" and "fastq" in observed_formats:
            score += 4
        if skill_id == "scvi-tools" and "h5ad" in observed_formats and any(token in prompt for token in ["scvi", "scanvi", "totalvi", "peakvi", "multivi", "batch", "latent"]):
            score += 4
        if skill_id == "skill-authoring-kit" and keyword_hits:
            score += 4
        scores.append(
            {
                "skill_id": skill_id,
                "score": score,
                "intent_match": len(keyword_hits),
                "input_compatibility": len(input_hits),
                "environment_readiness": "not_checked_until_selected",
                "approval_required": bool(entry.get("approval", {}).get("required_for_execution", False)),
                "known_task_support": entry.get("tasks", []),
                "matched_keywords": keyword_hits[:10],
                "matched_input_formats": input_hits,
            }
        )
    return sorted(scores, key=lambda item: (-item["score"], item["skill_id"]))


def keyword_matches(prompt: str, keyword: str) -> bool:
    if not keyword:
        return False
    if re.search(r"[^a-z0-9]", keyword):
        return keyword in prompt
    return re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", prompt) is not None


def explain_selection(skill: str, candidate_scores: list[dict[str, Any]], inventory: dict[str, Any], intents: list[str]) -> str:
    if not candidate_scores or skill == "omics-router":
        return "No registered skill had enough intent or input evidence for a confident handoff."
    selected = next((item for item in candidate_scores if item["skill_id"] == skill), candidate_scores[0])
    return (
        f"Selected {skill} from intents {', '.join(intents)} with score {selected['score']}; "
        f"matched keywords {selected['matched_keywords']} and input formats {selected['matched_input_formats']}."
    )


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
            f"python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py --input {quote_arg(input_path)} --output-dir {quote_arg(qc_out)} --dry-run --json",
        ],
        "approved_command": f"python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py --input {quote_arg(input_path)} --output-dir {quote_arg(qc_out)} --approved true --write-manifest",
    }


def scvi_plan(input_path: Path, outdir: Path, prompt: str) -> dict[str, Any]:
    model = "SCANVI" if "scanvi" in prompt else "TOTALVI" if "totalvi" in prompt else "PEAKVI" if "peakvi" in prompt else "MULTIVI" if "multivi" in prompt else "SCVI"
    scvi_out = outdir / "scvi"
    return {
        "approval_required": True,
        "model": model,
        "commands": [
            "python plugins/omics-analysis/skills/scvi-tools/scripts/check_environment.py --json",
            f"python plugins/omics-analysis/skills/scvi-tools/scripts/recommend_model.py --input {quote_arg(input_path)} --task {quote_arg(prompt[:80])} --json",
            f"python plugins/omics-analysis/skills/scvi-tools/scripts/train_model.py --input {quote_arg(input_path)} --output-dir {quote_arg(scvi_out)} --model {model} --dry-run --json",
        ],
        "approved_command": f"python plugins/omics-analysis/skills/scvi-tools/scripts/train_model.py --input {quote_arg(input_path)} --output-dir {quote_arg(scvi_out)} --model {model} --approved true",
    }


def report_plan(input_path: Path, outdir: Path) -> dict[str, Any]:
    report = outdir / "report.md"
    return {
        "approval_required": False,
        "commands": [
            f"python plugins/omics-analysis/skills/omics-report/scripts/render_report.py --manifest {quote_arg(input_path)} --out {quote_arg(report)}",
        ],
    }


def authoring_plan(prompt: str) -> dict[str, Any]:
    return {
        "approval_required": False,
        "commands": [],
        "guidance": "Use skill-authoring-kit for new skills, or nextflow-development nf-core adapter template for nf-core pipelines.",
        "request": prompt,
    }


def nextflow_plan(input_path: Path, outdir: Path, prompt: str) -> dict[str, Any]:
    pipeline = (
        "spatialvi"
        if any(token in prompt for token in ["spatialvi", "spatial transcriptomics", "visium", "spaceranger", "space ranger"])
        else "scrnaseq"
        if any(token in prompt for token in ["scrnaseq", "single-cell fastq", "cellranger", "cell ranger", "simpleaf", "star-solo", "starsolo", "kallisto", "10x"])
        else "riboseq"
        if any(token in prompt for token in ["riboseq", "ribo-seq", "ribosome profiling", "translational efficiency", "tiseq"])
        else "atacseq"
        if "atac" in prompt
        else "sarek"
        if "sarek" in prompt
        else "rnaseq"
    )
    nf_out = outdir / pipeline
    sheet = nf_out / "samplesheet.csv"
    revision = " --revision 1.2.0" if pipeline == "riboseq" else " --revision 4.1.0" if pipeline == "scrnaseq" else " --revision dev" if pipeline == "spatialvi" else ""
    metadata = f" --metadata {quote_arg(input_path / 'metadata.csv')}" if pipeline == "spatialvi" else ""
    return {
        "approval_required": True,
        "pipeline": pipeline,
        "commands": [
            "python plugins/omics-analysis/skills/nextflow-development/scripts/check_environment.py --json",
            f"python plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py --pipeline {pipeline} --input {quote_arg(input_path)} --out {quote_arg(sheet)}{metadata}",
            f"python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py --pipeline {pipeline} --input {quote_arg(sheet)} --outdir {quote_arg(nf_out)} --profile singularity{revision} --dry-run --json",
        ],
    }


def quote_arg(value: str | Path) -> str:
    return shlex.quote(str(value))


def requirements_for(skill: str) -> list[str]:
    return {
        "single-cell-rna-qc": ["scanpy", "anndata", "numpy", "scipy", "pandas", "matplotlib", "seaborn"],
        "scvi-tools": ["scvi-tools", "torch", "scanpy", "anndata", "GPU optional but recommended"],
        "nextflow-development": ["Java 17+", "Nextflow", "nf-core", "git", "Singularity/Apptainer or Docker"],
    }.get(skill, [])


if __name__ == "__main__":
    raise SystemExit(main())
