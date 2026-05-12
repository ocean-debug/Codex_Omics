from __future__ import annotations

import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

from ..common.io import write_text
from ..common.manifest import base_manifest, write_manifest
from ..common.paths import prepare_outdir
from .outputs import verify_pipeline_outputs


def build_nextflow_command(spec: dict[str, Any], test_profile: bool = False) -> str:
    nfcore = spec.get("nfcore", {})
    execution = spec.get("execution", {})
    outputs = spec.get("outputs", {})
    pipeline = str(nfcore.get("pipeline", "")).replace("nf-core/", "")
    if not pipeline:
        raise ValueError("nfcore.pipeline is required")
    requested_version = str(nfcore.get("version", "latest"))
    version = requested_version
    profile = nfcore.get("profile") or execution.get("profile") or "docker"
    params = dict(nfcore.get("params") or {})
    if "outdir" not in params and outputs.get("outdir"):
        params["outdir"] = outputs["outdir"]
    command = ["nextflow", "run", f"nf-core/{pipeline}"]
    if version != "latest":
        command.extend(["-r", str(version)])
    if test_profile:
        command.extend(["-profile", f"test,{profile}"])
    else:
        command.extend(["-profile", str(profile)])
    for key, value in sorted(params.items()):
        if value is None:
            continue
        flag = f"--{key.replace('_', '-')}"
        if isinstance(value, bool):
            if value:
                command.append(flag)
        else:
            command.extend([flag, str(value)])
    if execution.get("resume", True):
        command.append("-resume")
    return " ".join(shlex.quote(part) for part in command)


def build_test_profile_command(spec: dict[str, Any]) -> str:
    return build_nextflow_command(spec, test_profile=True)


def _java_version_text() -> str:
    java = shutil.which("java")
    if not java:
        return ""
    completed = subprocess.run([java, "-version"], text=True, capture_output=True, check=False)
    return "\n".join(part for part in [completed.stdout, completed.stderr] if part).strip()


def _java_major_version(version_text: str) -> int | None:
    import re

    match = re.search(r'version "(\d+)(?:\.(\d+))?', version_text)
    if not match:
        return None
    first = int(match.group(1))
    if first == 1 and match.group(2):
        return int(match.group(2))
    return first


def runtime_blockers(spec: dict[str, Any]) -> list[dict[str, Any]]:
    nfcore = spec.get("nfcore", {})
    profile = str(nfcore.get("profile") or spec.get("execution", {}).get("profile") or "docker")
    errors: list[dict[str, Any]] = []
    if not shutil.which("nextflow"):
        errors.append(
            {
                "error_type": "MissingSoftware",
                "message": "Nextflow is not available on PATH.",
                "suggested_fix": "Install Nextflow in the active remote environment and ensure Java 17+ is available.",
                "failed_step": "preflight_nextflow",
            }
        )
    java_text = _java_version_text()
    java_major = _java_major_version(java_text)
    if java_major is None:
        errors.append(
            {
                "error_type": "MissingSoftware",
                "message": "Java is not available or its version could not be detected.",
                "suggested_fix": "Install Java 17+ and expose it through JAVA_HOME or PATH before running Nextflow.",
                "failed_step": "preflight_java",
            }
        )
    elif java_major < 17:
        errors.append(
            {
                "error_type": "UnsupportedRuntime",
                "message": f"Java {java_major} was detected, but current Nextflow requires Java 17+.",
                "suggested_fix": "Install Java 17+ and expose it through JAVA_HOME or PATH before running nf-core pipelines.",
                "failed_step": "preflight_java",
            }
        )
    if "apptainer" in profile and not shutil.which("apptainer"):
        errors.append(
            {
                "error_type": "MissingSoftware",
                "message": "The selected profile uses apptainer, but apptainer is not available on PATH.",
                "suggested_fix": "Install apptainer or use an available singularity profile.",
                "failed_step": "preflight_container",
            }
        )
    if "singularity" in profile and not shutil.which("singularity"):
        errors.append(
            {
                "error_type": "MissingSoftware",
                "message": "The selected profile uses singularity, but singularity is not available on PATH.",
                "suggested_fix": "Install singularity or switch to an available execution profile.",
                "failed_step": "preflight_container",
            }
        )
    return errors


def run_nfcore(spec: dict[str, Any]) -> dict[str, Any]:
    outputs = spec.get("outputs", {})
    execution = spec.get("execution", {})
    outdir = prepare_outdir(outputs.get("outdir", "./results/nfcore"), force=bool(execution.get("force", False)))
    command = build_test_profile_command(spec) if execution.get("mode") == "test_profile" else build_nextflow_command(spec)
    write_text(outdir / "command.sh", command + "\n")
    manifest_path = Path(outputs.get("manifest") or outdir / "run_manifest.json")
    approved = bool(execution.get("approved", False))
    runnable = execution.get("mode") in {"command_and_run", "test_profile"} and approved
    status = "planned"
    errors: list[dict[str, Any]] = []
    if runnable:
        run_cwd = Path(execution.get("workdir") or Path.cwd()).resolve()
        blockers = runtime_blockers(spec)
        if blockers:
            status = "blocked"
            errors.extend(blockers)
            completed = None
        else:
            completed = subprocess.run(command, shell=True, cwd=run_cwd, text=True, capture_output=True, check=False)
            write_text(outdir / "nextflow.stdout.log", completed.stdout)
            write_text(outdir / "nextflow.stderr.log", completed.stderr)
            nextflow_log = run_cwd / ".nextflow.log"
            if nextflow_log.exists():
                shutil.copyfile(nextflow_log, outdir / ".nextflow.log")
            status = "completed" if completed.returncode == 0 else "failed"
            if completed.returncode != 0:
                errors.append(
                    {
                        "error_type": "NextflowExecutionFailed",
                        "message": f"Nextflow exited with status {completed.returncode}",
                        "failed_step": "run_nextflow",
                    }
                )
    else:
        run_cwd = Path(execution.get("workdir") or Path.cwd()).resolve()
        completed = None
    manifest = base_manifest(
        skill="nf-core-universal",
        status=status,
        inputs=spec.get("inputs", {}),
        outputs={**outputs, "outdir": str(outdir), "command": str(outdir / "command.sh")},
        parameters=spec.get("nfcore", {}),
        commands=[command],
        errors=errors,
    )
    manifest["execution"] = {
        "approved": approved,
        "mode": execution.get("mode", "command_only"),
        "workdir": str(run_cwd),
        "returncode": completed.returncode if completed is not None else None,
        "nextflow_log": str(outdir / ".nextflow.log") if (outdir / ".nextflow.log").exists() else None,
        "stdout": str(outdir / "nextflow.stdout.log") if (outdir / "nextflow.stdout.log").exists() else None,
        "stderr": str(outdir / "nextflow.stderr.log") if (outdir / "nextflow.stderr.log").exists() else None,
    }
    manifest["logs"] = [path for path in [manifest["execution"]["stdout"], manifest["execution"]["stderr"], manifest["execution"]["nextflow_log"]] if path]
    if status == "completed":
        manifest["outputs"]["verification"] = verify_pipeline_outputs(spec.get("nfcore", {}).get("pipeline", ""), outdir)
    write_manifest(manifest_path, manifest)
    return manifest
