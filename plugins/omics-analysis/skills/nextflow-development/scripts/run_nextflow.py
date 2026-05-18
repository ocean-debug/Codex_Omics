from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common.env import inspect_nextflow_environment  # noqa: E402
from common.error_recovery import attach_auto_fix_plan  # noqa: E402
from common.io import ensure_outdir, load_json_or_simple_yaml, write_text  # noqa: E402
from common.manifest import base_manifest, write_manifest  # noqa: E402
from common.report import write_report  # noqa: E402
from common.safe_run import run_command  # noqa: E402
from summarize_multiqc import summarize_multiqc  # noqa: E402


def approved(value: str | bool) -> bool:
    return value is True or str(value).lower() in {"1", "true", "yes", "y"}


def classify_failure(text: str) -> dict[str, str]:
    lowered = text.lower()
    if "github.com" in lowered and any(token in lowered for token in ["connection failed", "timed out", "could not resolve", "unable to access"]):
        return attach_auto_fix_plan({"error_type": "PipelinePullFailed", "message": "Nextflow could not pull the nf-core pipeline.", "suggested_fix": "Pre-cache the pipeline with `nextflow pull nf-core/<pipeline>` and rerun with -resume."})
    if "ribotish" in lowered and (
        "wrong cds annotation" in lowered
        or "cds_region_trans" in lowered
        or "nonetype" in lowered and "int" in lowered
    ):
        return attach_auto_fix_plan({
            "error_type": "RiboTishAnnotationIncompatibility",
            "message": "Ribo-TISH failed while parsing CDS annotation records.",
            "suggested_fix": "Use `--skip_ribotish true` for a QC/quantification-focused run, or clean/replace the GTF before rerunning Ribo-TISH with -resume.",
        })
    if "failed to find the gene identifier attribute" in lowered or "featurecounts_group_type" in lowered:
        return attach_auto_fix_plan({
            "error_type": "InvalidAnnotationAttributes",
            "message": "featureCounts could not find the requested GTF attribute.",
            "suggested_fix": "Use a GTF-compatible attribute such as `--gencode` or `--featurecounts_group_type gene_type`, then rerun with -resume.",
        })
    if "pulltimeout" in lowered or ("status : 143" in lowered and "downloading network image" in lowered):
        return attach_auto_fix_plan({
            "error_type": "ContainerPullTimeout",
            "message": "A Singularity/Apptainer container download exceeded the configured Nextflow pull timeout.",
            "suggested_fix": "Pre-cache the image or increase `singularity.pullTimeout` / `apptainer.pullTimeout`, then rerun with -resume.",
        })
    container_failure_tokens = [
        "failed to pull singularity image",
        "failed to pull apptainer image",
        "failed to create container",
        "could not pull",
        "error pulling image",
        "singularity image pull failed",
        "apptainer pull failed",
    ]
    if any(token in lowered for token in container_failure_tokens):
        return attach_auto_fix_plan({"error_type": "ContainerPullFailed", "message": "A container image could not be pulled or prepared.", "suggested_fix": "Check Singularity/Apptainer cache and network access, then rerun with -resume."})
    if "java" in lowered:
        return attach_auto_fix_plan({"error_type": "UnsupportedRuntime", "message": "Nextflow reported a Java runtime problem.", "suggested_fix": "Use Java 17+."})
    if "unknown parameter" in lowered or "invalid parameter" in lowered or "schema" in lowered:
        return attach_auto_fix_plan({"error_type": "InvalidPipelineParameters", "message": "Nextflow reported invalid pipeline parameters.", "suggested_fix": "Validate the run against the nf-core pipeline schema before rerunning."})
    return attach_auto_fix_plan({"error_type": "NextflowExecutionFailed", "message": "Nextflow execution failed.", "suggested_fix": "Inspect logs, fix the issue, and rerun with -resume."})


def inventory_outputs(outdir: Path) -> dict[str, list[str]]:
    patterns = {
        "multiqc_reports": ["**/multiqc_report.html", "**/*multiqc*.html"],
        "nextflow_logs": [".nextflow.log", "**/.nextflow.log"],
        "trace_files": ["**/trace.txt", "**/*trace*.txt"],
        "reports": ["**/report.html", "**/report.md"],
    }
    inventory: dict[str, list[str]] = {}
    for key, globs in patterns.items():
        found: list[str] = []
        for pattern in globs:
            found.extend(str(path) for path in outdir.glob(pattern) if path.is_file())
        inventory[key] = sorted(set(found))
    return inventory


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an approved Nextflow command from a plugin-local plan.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--approved", default="false")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    config = load_json_or_simple_yaml(args.config)
    outdir = ensure_outdir(config.get("outdir", config.get("output_dir", "results/nextflow")))
    command = config.get("command")
    if not command and config.get("command_file"):
        command = Path(config["command_file"]).read_text(encoding="utf-8").strip()
    if not command:
        raise SystemExit("--config must contain command or command_file")
    write_text(outdir / "command.sh", command + "\n")
    env = inspect_nextflow_environment()
    status = "planned"
    errors = []
    execution = {"approved": approved(args.approved), "returncode": None}
    if env["blockers"]:
        status = "blocked"
        errors.extend(env["blockers"])
    elif args.dry_run or not approved(args.approved):
        status = "planned"
    else:
        result = run_command(command, outdir=outdir)
        execution.update(result)
        status = "completed" if result["returncode"] == 0 else "failed"
        if status == "failed":
            stderr = Path(result["stderr"]).read_text(encoding="utf-8", errors="replace")
            stdout = Path(result["stdout"]).read_text(encoding="utf-8", errors="replace")
            failure_text = stdout + "\n" + stderr
            if Path(".nextflow.log").exists():
                failure_text += "\n" + Path(".nextflow.log").read_text(encoding="utf-8", errors="replace")
            errors.append(classify_failure(failure_text))
        if Path(".nextflow.log").exists():
            shutil.copyfile(".nextflow.log", outdir / ".nextflow.log")
            execution["nextflow_log"] = str(outdir / ".nextflow.log")
    manifest = base_manifest(
        skill="nextflow-development",
        status=status,
        inputs={"config": args.config},
        outputs={"outdir": str(outdir), "command": str(outdir / "command.sh"), "manifest": str(outdir / "run_manifest.json"), "report": str(outdir / "report.md")},
        parameters=config,
        commands=[command],
        errors=errors,
        warnings=env["warnings"],
    )
    manifest["environment"] = env
    manifest["execution"] = execution
    manifest["output_inventory"] = inventory_outputs(outdir)
    multiqc = summarize_multiqc(outdir)
    manifest["qc_summary"] = multiqc.get("summary", {})
    manifest["interpretation"] = multiqc.get("interpretation", [])
    manifest["auto_fix_plan"] = [item for error in errors for item in error.get("auto_fix_plan", [])] if errors else []
    write_manifest(outdir / "run_manifest.json", manifest)
    write_report(outdir / "report.md", manifest, title="Nextflow Workflow Report")
    print(json.dumps(manifest, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
