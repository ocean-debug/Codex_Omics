#!/usr/bin/env bash
# Project-local Java/Nextflow activation for Codex Omics.

set -euo pipefail

CODEX_OMICS_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export CODEX_OMICS_HOME

export JAVA_HOME="$CODEX_OMICS_HOME/tools/java/jdk-17"
export NXF_HOME="$CODEX_OMICS_HOME/tools/nextflow/.nextflow"
export NXF_SINGULARITY_CACHEDIR="${NXF_SINGULARITY_CACHEDIR:-$CODEX_OMICS_HOME/tools/nextflow/singularity-cache}"
export APPTAINER_CACHEDIR="${APPTAINER_CACHEDIR:-$CODEX_OMICS_HOME/tools/nextflow/apptainer-cache}"
export SINGULARITY_CACHEDIR="${SINGULARITY_CACHEDIR:-$APPTAINER_CACHEDIR}"
export GIT_PYTHON_REFRESH="${GIT_PYTHON_REFRESH:-quiet}"
export PATH="$JAVA_HOME/bin:$CODEX_OMICS_HOME/tools/nextflow:$PATH"

mkdir -p "$NXF_HOME" "$NXF_SINGULARITY_CACHEDIR" "$APPTAINER_CACHEDIR"
