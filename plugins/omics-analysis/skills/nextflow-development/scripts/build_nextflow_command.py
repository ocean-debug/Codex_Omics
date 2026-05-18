from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from common.io import ensure_outdir, write_text  # noqa: E402
from common.manifest import base_manifest, write_manifest  # noqa: E402
from common.report import write_report  # noqa: E402


DEFAULT_REVISIONS = {"riboseq": "1.2.0", "scrnaseq": "4.1.0", "spatialvi": "dev"}


def parse_extra_params(values: list[str] | None) -> dict[str, str]:
    params: dict[str, str] = {}
    for value in values or []:
        if "=" not in value:
            raise ValueError(f"--extra-param must use KEY=VALUE syntax: {value}")
        key, param_value = value.split("=", 1)
        key = key.strip().removeprefix("--")
        if not key:
            raise ValueError(f"--extra-param key cannot be empty: {value}")
        params[key] = param_value
    return params


def build_command(args: argparse.Namespace) -> str:
    pipeline = args.pipeline.replace("nf-core/", "")
    short_pipeline = pipeline.lower()
    revision = args.revision or DEFAULT_REVISIONS.get(short_pipeline)
    command = ["nextflow"]
    if args.nextflow_config:
        command.extend(["-c", args.nextflow_config])
    command.extend(["run", f"nf-core/{pipeline}", "-profile", args.profile])
    if revision:
        command.extend(["-r", revision])
    command.extend(["--input", args.input, "--outdir", args.outdir])
    if args.genome:
        command.extend(["--genome", args.genome])
    if args.aligner:
        command.extend(["--aligner", args.aligner])
    if args.protocol:
        command.extend(["--protocol", args.protocol])
    if args.fasta:
        command.extend(["--fasta", args.fasta])
    if args.gtf:
        command.extend(["--gtf", args.gtf])
    if args.cellranger_index:
        command.extend(["--cellranger_index", args.cellranger_index])
    if args.contrasts:
        command.extend(["--contrasts", args.contrasts])
    if args.spaceranger_reference:
        command.extend(["--spaceranger_reference", args.spaceranger_reference])
    if args.spaceranger_probeset:
        command.extend(["--spaceranger_probeset", args.spaceranger_probeset])
    if args.hd_bin_size:
        command.extend(["--hd_bin_size", str(args.hd_bin_size)])
    if args.skip_integration:
        command.extend(["--skip_integration", "true"])
    if args.skip_downstream:
        command.extend(["--skip_downstream", "true"])
    if args.skip_ribotish and short_pipeline == "riboseq":
        command.extend(["--skip_ribotish", "true"])
    for key, value in args.extra_params.items():
        command.extend([f"--{key}", value])
    if args.max_cpus:
        command.extend(["--max_cpus", str(args.max_cpus)])
    if args.max_memory:
        command.extend(["--max_memory", args.max_memory])
    if args.resume:
        command.append("-resume")
    return " ".join(shlex.quote(part) for part in command)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a safe Nextflow command without executing it.")
    parser.add_argument("--pipeline", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--config")
    parser.add_argument("--profile", default="singularity")
    parser.add_argument("--genome")
    parser.add_argument("--revision")
    parser.add_argument("--aligner", help="nf-core/scrnaseq aligner, such as cellranger, starsolo, simpleaf, or kallisto.")
    parser.add_argument("--protocol", help="nf-core/scrnaseq protocol value, when required by the selected aligner and data.")
    parser.add_argument("--fasta", help="Reference FASTA path for pipelines such as nf-core/riboseq.")
    parser.add_argument("--gtf", help="Reference GTF path for pipelines such as nf-core/riboseq.")
    parser.add_argument("--cellranger-index", help="Cell Ranger reference index path for nf-core/scrnaseq.")
    parser.add_argument("--contrasts", help="Optional contrasts CSV for nf-core/riboseq translational efficiency analysis.")
    parser.add_argument("--skip-ribotish", action="store_true", help="Skip Ribo-TISH QC and ORF prediction in nf-core/riboseq.")
    parser.add_argument("--spaceranger-reference", help="Space Ranger reference path for nf-core/spatialvi raw mode.")
    parser.add_argument("--spaceranger-probeset", help="Space Ranger probe set CSV for nf-core/spatialvi when required.")
    parser.add_argument("--hd-bin-size", type=int, help="Visium HD bin size for nf-core/spatialvi.")
    parser.add_argument("--skip-integration", action="store_true", help="Skip nf-core/spatialvi integration steps.")
    parser.add_argument("--skip-downstream", action="store_true", help="Skip nf-core/spatialvi downstream analysis steps.")
    parser.add_argument("--extra-param", action="append", default=[], help="Repeatable passthrough nf-core parameter in KEY=VALUE form.")
    parser.add_argument("--max-cpus", type=int)
    parser.add_argument("--max-memory")
    parser.add_argument("--pull-timeout", help="Optional Singularity/Apptainer pull timeout, for example '4 h' or '240 min'.")
    parser.add_argument("--singularity-pull-docker-container", action="store_true", help="Use Docker/OCI container names instead of depot.galaxyproject.org Singularity URLs when nf-core modules support task.ext.singularity_pull_docker_container.")
    parser.add_argument("--overwrite-reports", action="store_true", help="Allow Nextflow report, timeline, trace, and DAG files to be overwritten on resume.")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--approved", default="false")
    args = parser.parse_args()
    pipeline = args.pipeline.replace("nf-core/", "").lower()
    if args.skip_ribotish and pipeline != "riboseq":
        parser.error("--skip-ribotish is only supported with --pipeline riboseq.")
    if (args.spaceranger_reference or args.spaceranger_probeset or args.hd_bin_size or args.skip_integration or args.skip_downstream) and pipeline != "spatialvi":
        parser.error("spatialvi-specific options are only supported with --pipeline spatialvi.")
    try:
        args.extra_params = parse_extra_params(args.extra_param)
    except ValueError as exc:
        parser.error(str(exc))
    outdir = ensure_outdir(args.outdir)
    nextflow_config = None
    if args.pull_timeout or args.singularity_pull_docker_container or args.overwrite_reports:
        nextflow_config = outdir / "nextflow.config"
        lines = []
        if args.pull_timeout:
            timeout = args.pull_timeout.replace("'", "\\'")
            lines.extend(
                [
                    "singularity {",
                    f"  pullTimeout = '{timeout}'",
                    "}",
                    "apptainer {",
                    f"  pullTimeout = '{timeout}'",
                    "}",
                ]
            )
        if args.singularity_pull_docker_container:
            lines.extend(
                [
                    "process {",
                    "  ext.singularity_pull_docker_container = true",
                    "}",
                ]
            )
        if args.overwrite_reports:
            lines.extend(
                [
                    "report { overwrite = true }",
                    "timeline { overwrite = true }",
                    "trace { overwrite = true }",
                    "dag { overwrite = true }",
                ]
            )
        write_text(nextflow_config, "\n".join(lines) + "\n")
    args.nextflow_config = str(nextflow_config) if nextflow_config else None
    effective_revision = args.revision or DEFAULT_REVISIONS.get(pipeline)
    command = build_command(args)
    write_text(outdir / "command.sh", command + "\n")
    manifest = base_manifest(
        skill="nextflow-development",
        status="planned",
        inputs={"samplesheet": args.input, "fasta": args.fasta, "gtf": args.gtf, "contrasts": args.contrasts},
        outputs={"outdir": str(outdir), "command": str(outdir / "command.sh"), "nextflow_config": args.nextflow_config, "manifest": str(outdir / "run_manifest.json"), "report": str(outdir / "report.md")},
        parameters={
            "pipeline": args.pipeline,
            "profile": args.profile,
            "genome": args.genome,
            "revision": effective_revision,
            "aligner": args.aligner,
            "protocol": args.protocol,
            "fasta": args.fasta,
            "gtf": args.gtf,
            "cellranger_index": args.cellranger_index,
            "contrasts": args.contrasts,
            "skip_ribotish": args.skip_ribotish,
            "spaceranger_reference": args.spaceranger_reference,
            "spaceranger_probeset": args.spaceranger_probeset,
            "hd_bin_size": args.hd_bin_size,
            "skip_integration": args.skip_integration,
            "skip_downstream": args.skip_downstream,
            "extra_params": args.extra_params,
            "pull_timeout": args.pull_timeout,
            "singularity_pull_docker_container": args.singularity_pull_docker_container,
            "overwrite_reports": args.overwrite_reports,
        },
        commands=[command],
    )
    manifest["plan"] = {"approval_required": True, "will_execute": False, "schema_validation": "Use nf-core/nf-schema validation before approved execution when available."}
    write_manifest(outdir / "run_manifest.json", manifest)
    write_report(outdir / "report.md", manifest, title="Nextflow Workflow Plan")
    print(json.dumps({"command": command, "manifest": str(outdir / "run_manifest.json"), "report": str(outdir / "report.md")}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
