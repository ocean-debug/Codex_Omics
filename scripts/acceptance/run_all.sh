#!/usr/bin/env bash
set -euo pipefail

ROOT="${CODEX_OMICS_ROOT:-$(pwd)}"
DATA_DIR="${CODEX_OMICS_DATA_DIR:-${ROOT}/data/test}"
RESULT_DIR="${CODEX_OMICS_RESULT_DIR:-${DATA_DIR}/result}"
mkdir -p "${RESULT_DIR}"
export CODEX_OMICS_ROOT="${ROOT}" CODEX_OMICS_DATA_DIR="${DATA_DIR}" CODEX_OMICS_RESULT_DIR="${RESULT_DIR}"

for project in scvi bulk_rna atac; do
  echo "===== START ${project} $(date -Is) =====" | tee -a "${RESULT_DIR}/run_all.log"
  bash "${ROOT}/scripts/acceptance/run_${project}.sh" 2>&1 | tee "${RESULT_DIR}/${project}/run.log" || true
  echo "===== END ${project} $(date -Is) =====" | tee -a "${RESULT_DIR}/run_all.log"
done

python - <<'PY'
import json
import os
from pathlib import Path

root = Path(os.environ["CODEX_OMICS_RESULT_DIR"])
summary = {}
for name in ["scvi", "bulk_rna", "atac"]:
    manifest = root / name / "run_manifest.json"
    if manifest.exists():
        payload = json.loads(manifest.read_text())
        summary[name] = {
            "status": payload.get("status"),
            "manifest": str(manifest),
            "errors": payload.get("errors", []),
            "outputs": payload.get("outputs", {}),
        }
    else:
        summary[name] = {"status": "missing_manifest", "manifest": str(manifest)}
(root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
PY
