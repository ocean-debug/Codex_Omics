#!/usr/bin/env bash
set -euo pipefail

ROOT="${CODEX_OMICS_ROOT:-$(pwd)}"
DATA_DIR="${CODEX_OMICS_DATA_DIR:-${ROOT}/data/test}"
RESULT_DIR="${CODEX_OMICS_RESULT_DIR:-${DATA_DIR}/result}"
OUT="${RESULT_DIR}/atac"
mkdir -p "${OUT}/work"
export CODEX_OMICS_ROOT="${ROOT}" CODEX_OMICS_DATA_DIR="${DATA_DIR}" CODEX_OMICS_RESULT_DIR="${RESULT_DIR}"
NFCORE_PROFILE="${CODEX_OMICS_NFCORE_PROFILE:-singularity}"
MAX_CPUS="${CODEX_OMICS_MAX_CPUS:-12}"
MAX_MEMORY="${CODEX_OMICS_MAX_MEMORY:-48.GB}"

python "${ROOT}/scripts/acceptance/prepare_test_inputs.py" atac | tee "${OUT}/prepare.log"

FASTA="${CODEX_OMICS_FASTA:-$(find "${DATA_DIR}/nf-core/genome" \( -name '*.fa' -o -name '*.fasta' \) -type f | sort | head -1)}"
GTF="${CODEX_OMICS_GTF:-$(find "${DATA_DIR}/nf-core/genome" -name '*.gtf' -type f | sort | head -1)}"
if [[ -z "${FASTA}" || -z "${GTF}" ]]; then
  echo "Missing genome FASTA/GTF. Set CODEX_OMICS_FASTA and CODEX_OMICS_GTF or place files under ${DATA_DIR}/nf-core/genome." >&2
  exit 2
fi

cat > "${OUT}/atacseq_params.config" <<'EOF'
params {
    skip_peak_qc = true
}
EOF

cat > "${OUT}/atac_real_subset.yaml" <<EOF
run:
  name: atac_real_subset_acceptance
  type: nfcore_pipeline
  skill: nf-core-universal
inputs:
  path: ${DATA_DIR}/nf-core/atac
  type: fastq_subset
nfcore:
  pipeline: atacseq
  version: latest
  profile: ${NFCORE_PROFILE}
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
  max_cpus: ${MAX_CPUS}
  max_memory: ${MAX_MEMORY}
  nextflow_configs:
    - ${ROOT}/envs/nextflow-singularity.config
    - ${OUT}/atacseq_params.config
outputs:
  outdir: ${OUT}/nfcore_out
  manifest: ${OUT}/run_manifest.json
  report: ${OUT}/report.md
EOF

omics-codex inspect-env --kind nfcore | tee "${OUT}/inspect_env.json"
omics-codex nfcore build-command --config "${OUT}/atac_real_subset.yaml" | tee "${OUT}/omics_codex_nfcore_build_command.json"
omics-codex nfcore run --config "${OUT}/atac_real_subset.yaml" | tee "${OUT}/omics_codex_nfcore_run.json"
omics-codex report --manifest "${OUT}/run_manifest.json" > "${OUT}/report.md"
