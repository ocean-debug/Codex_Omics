#!/usr/bin/env bash
set -euo pipefail

ROOT="${CODEX_OMICS_ROOT:-$(pwd)}"
DATA_DIR="${CODEX_OMICS_DATA_DIR:-${ROOT}/data/test}"
RESULT_DIR="${CODEX_OMICS_RESULT_DIR:-${DATA_DIR}/result}"
OUT="${RESULT_DIR}/bulk_rna"
mkdir -p "${OUT}/work"
export CODEX_OMICS_ROOT="${ROOT}" CODEX_OMICS_DATA_DIR="${DATA_DIR}" CODEX_OMICS_RESULT_DIR="${RESULT_DIR}"

python "${ROOT}/scripts/acceptance/prepare_test_inputs.py" bulk_rna | tee "${OUT}/prepare.log"

FASTA="${CODEX_OMICS_FASTA:-$(find "${DATA_DIR}/nf-core/genome" \( -name '*.fa' -o -name '*.fasta' \) -type f | sort | head -1)}"
GTF="${CODEX_OMICS_GTF:-$(find "${DATA_DIR}/nf-core/genome" -name '*.gtf' -type f | sort | head -1)}"

cat > "${OUT}/rnaseq_params.config" <<'EOF'
params {
    skip_alignment = true
    skip_pseudo_alignment = true
    skip_quantification_merge = true
}
EOF

cat > "${OUT}/rnaseq_real_subset.yaml" <<EOF
run:
  name: bulk_rna_real_subset_acceptance
  type: nfcore_pipeline
  skill: nf-core-universal
inputs:
  path: ${DATA_DIR}/nf-core/rna
  type: fastq_subset
nfcore:
  pipeline: rnaseq
  version: latest
  profile: singularity
  params:
    input: ${OUT}/samplesheet.csv
    outdir: ${OUT}/nfcore_out
    fasta: ${FASTA}
    gtf: ${GTF}
execution:
  mode: command_and_run
  approved: true
  resume: true
  force: true
  workdir: ${OUT}/work
  max_cpus: 12
  max_memory: 48.GB
  nextflow_configs:
    - ${ROOT}/envs/nextflow-singularity.config
    - ${OUT}/rnaseq_params.config
outputs:
  outdir: ${OUT}/nfcore_out
  manifest: ${OUT}/run_manifest.json
  report: ${OUT}/report.md
EOF

omics-codex inspect-env --kind nfcore | tee "${OUT}/inspect_env.json"
omics-codex nfcore run --config "${OUT}/rnaseq_real_subset.yaml" | tee "${OUT}/omics_codex_nfcore_run.json"
omics-codex report --manifest "${OUT}/run_manifest.json" > "${OUT}/report.md" || true
