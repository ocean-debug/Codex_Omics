#!/usr/bin/env bash
# Project-local Java/Nextflow activation for Codex Omics.

set -euo pipefail

CODEX_OMICS_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export CODEX_OMICS_HOME

export JAVA_HOME="$CODEX_OMICS_HOME/tools/java/jdk-17"
export PATH="$JAVA_HOME/bin:$CODEX_OMICS_HOME/tools/nextflow:$PATH"
