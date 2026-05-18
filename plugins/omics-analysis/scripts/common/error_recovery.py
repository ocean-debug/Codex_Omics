from __future__ import annotations

from typing import Any


RECOVERY_PLANS: dict[str, list[str]] = {
    "PipelinePullFailed": [
        "Confirm GitHub/network access from the execution node.",
        "Pre-cache the pipeline with `nextflow pull nf-core/<pipeline>`.",
        "Rerun the same command with `-resume` after the pipeline is available.",
    ],
    "RiboTishAnnotationIncompatibility": [
        "For QC/quantification-focused nf-core/riboseq runs, rebuild the plan with `--skip-ribotish`.",
        "For ORF prediction, clean or replace the GTF CDS annotations before rerunning.",
        "Keep the work directory and rerun with `-resume`.",
    ],
    "InvalidAnnotationAttributes": [
        "Inspect the GTF attributes used by featureCounts.",
        "Set a compatible attribute option such as `--featurecounts_group_type gene_type` or pipeline-specific `--gencode` when appropriate.",
        "Rerun with `-resume` after updating parameters.",
    ],
    "ContainerPullTimeout": [
        "Use `--pull-timeout \"4 h\"` and rebuild the Nextflow command.",
        "Use `--singularity-pull-docker-container` when the nf-core pipeline supports Docker/OCI fallback.",
        "Pre-cache the missing image in the configured Singularity/Apptainer cache and rerun with `-resume`.",
    ],
    "ContainerPullFailed": [
        "Check Singularity/Apptainer cache permissions and network access.",
        "Pre-cache the failed image when the registry is slow or blocked.",
        "Rerun with `-resume` after the image is available.",
    ],
    "UnsupportedRuntime": [
        "Use Java 17 or newer for Nextflow.",
        "Confirm `nextflow -version` works in the same environment used by the run.",
    ],
    "InvalidPipelineParameters": [
        "Validate parameters against the nf-core pipeline schema when available.",
        "Regenerate `params.yaml` and `command.sh` from the plugin planner.",
        "Rerun with `-resume` after correcting invalid parameters.",
    ],
    "NextflowExecutionFailed": [
        "Inspect `.nextflow.log`, stdout, stderr, and the failing process work directory.",
        "Fix the first concrete process error before rerunning.",
        "Rerun with `-resume` to avoid repeating completed tasks.",
    ],
}


def attach_auto_fix_plan(error: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(error)
    enriched["auto_fix_plan"] = RECOVERY_PLANS.get(
        str(error.get("error_type", "")),
        ["Inspect logs, correct the root cause, and rerun with `-resume` when safe."],
    )
    return enriched
