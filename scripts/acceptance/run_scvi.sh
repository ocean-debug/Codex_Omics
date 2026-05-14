#!/usr/bin/env bash
set -euo pipefail

ROOT="${CODEX_OMICS_ROOT:-$(pwd)}"
DATA_DIR="${CODEX_OMICS_DATA_DIR:-${ROOT}/data/test}"
RESULT_DIR="${CODEX_OMICS_RESULT_DIR:-${DATA_DIR}/result}"
OUT="${RESULT_DIR}/scvi"
mkdir -p "${OUT}"
export CODEX_OMICS_ROOT="${ROOT}" CODEX_OMICS_DATA_DIR="${DATA_DIR}" CODEX_OMICS_RESULT_DIR="${RESULT_DIR}"

python "${ROOT}/scripts/acceptance/prepare_test_inputs.py" scvi | tee "${OUT}/prepare.log"

cat > "${OUT}/scvi_real_subset.yaml" <<EOF
run:
  name: scvi_real_subset_acceptance
  type: scvi_model
  skill: scvi-universal
inputs:
  path: ${OUT}/scvi_subset.h5ad
  type: h5ad
scvi:
  model: SCVI
  setup_anndata:
    layer: counts
    batch_key: batch
  model_kwargs:
    n_latent: 10
    n_layers: 1
  train:
    max_epochs: 2
    accelerator: auto
    devices: auto
    enable_progress_bar: false
  downstream:
    latent_key: X_scvi_real_test
    neighbors: true
    umap: true
    leiden: true
outputs:
  outdir: ${OUT}/model_run
  manifest: ${OUT}/run_manifest.json
  report: ${OUT}/report.md
execution:
  approved: true
  force: true
EOF

omics-codex inspect-env --kind scvi | tee "${OUT}/inspect_env.json"
omics-codex scvi validate --config "${OUT}/scvi_real_subset.yaml" | tee "${OUT}/scvi_validate.json"
omics-codex scvi train --config "${OUT}/scvi_real_subset.yaml" | tee "${OUT}/scvi_train.json"
omics-codex report --manifest "${OUT}/run_manifest.json" > "${OUT}/report.md"
