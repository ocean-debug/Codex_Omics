#!/usr/bin/env bash
set -euo pipefail

ROOT="${CODEX_OMICS_ROOT:-$(pwd)}"
DATA_DIR="${CODEX_OMICS_DATA_DIR:-${ROOT}/data/test}"
RESULT_DIR="${CODEX_OMICS_RESULT_DIR:-${DATA_DIR}/result}"
mkdir -p "${RESULT_DIR}"
export CODEX_OMICS_ROOT="${ROOT}" CODEX_OMICS_DATA_DIR="${DATA_DIR}" CODEX_OMICS_RESULT_DIR="${RESULT_DIR}"

for project in scvi bulk_rna atac; do
  mkdir -p "${RESULT_DIR}/${project}"
  echo "===== START ${project} $(date -Is) =====" | tee -a "${RESULT_DIR}/run_all.log"
  if bash "${ROOT}/scripts/acceptance/run_${project}.sh" 2>&1 | tee "${RESULT_DIR}/${project}/run.log"; then
    exit_code=0
  else
    exit_code=$?
  fi
  echo "${exit_code}" > "${RESULT_DIR}/${project}/exit_code.txt"
  echo "===== END ${project} exit=${exit_code} $(date -Is) =====" | tee -a "${RESULT_DIR}/run_all.log"
done

python - <<'PY'
import json
import os
from pathlib import Path

root = Path(os.environ["CODEX_OMICS_RESULT_DIR"])
summary = {}


def read_int(path: Path) -> int | None:
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except Exception:
        return None


def error_markers(errors):
    markers = set()
    for error in errors or []:
        if isinstance(error, dict):
            if error.get("error_type"):
                markers.add(str(error["error_type"]))
            if error.get("classification"):
                markers.add(str(error["classification"]))
            details = error.get("details")
            if isinstance(details, dict) and details.get("classification"):
                markers.add(str(details["classification"]))
    return sorted(markers)


allowed_atac_markers = {
    "PipelinePullFailed",
    "PipelineConfigParseFailed",
    "ContainerPullFailed",
    "pipeline_pull_or_network",
    "pipeline_config_parse",
    "container_pull",
}

for name in ["scvi", "bulk_rna", "atac"]:
    manifest = root / name / "run_manifest.json"
    run_log = root / name / "run.log"
    exit_code = read_int(root / name / "exit_code.txt")
    if manifest.exists():
        payload = json.loads(manifest.read_text())
        errors = payload.get("errors", [])
        execution = payload.get("execution", {})
        logs = list(payload.get("logs") or [])
        logs.extend(str(path) for path in [execution.get("stdout"), execution.get("stderr"), execution.get("nextflow_log")] if path)
        if run_log.exists():
            logs.append(str(run_log))
        summary[name] = {
            "status": payload.get("status"),
            "manifest": str(manifest),
            "exit_code": exit_code,
            "errors": errors,
            "error_markers": error_markers(errors),
            "outputs": payload.get("outputs", {}),
            "commands": payload.get("commands", []),
            "logs": sorted(set(logs)),
        }
    else:
        summary[name] = {"status": "missing_manifest", "manifest": str(manifest), "exit_code": exit_code, "logs": [str(run_log)] if run_log.exists() else []}

failures = []
for required in ["scvi", "bulk_rna"]:
    item = summary[required]
    if item.get("status") != "completed" or item.get("exit_code") not in (0, None):
        failures.append({"project": required, "reason": "required_project_not_completed", "status": item.get("status"), "exit_code": item.get("exit_code")})

atac = summary["atac"]
atac_status = atac.get("status")
atac_markers = set(atac.get("error_markers", []))
atac_allowed_failure = atac_status in {"blocked", "failed"} and bool(atac_markers & allowed_atac_markers)
atac["allowed_failure"] = atac_allowed_failure
if atac_status == "completed":
    if atac.get("exit_code") not in (0, None):
        failures.append({"project": "atac", "reason": "completed_manifest_with_nonzero_exit", "status": atac_status, "exit_code": atac.get("exit_code")})
elif not atac_allowed_failure:
    failures.append({"project": "atac", "reason": "atac_not_completed_or_allowed_classified_failure", "status": atac_status, "exit_code": atac.get("exit_code"), "error_markers": sorted(atac_markers)})

summary["exit_policy"] = {
    "status": "failed" if failures else "passed",
    "required_completed": ["scvi", "bulk_rna"],
    "atac_allowed_failure_markers": sorted(allowed_atac_markers),
    "failures": failures,
}
(root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
raise SystemExit(1 if failures else 0)
PY
