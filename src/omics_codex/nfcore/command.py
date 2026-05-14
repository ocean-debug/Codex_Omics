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
    for resource_key in ("max_cpus", "max_memory", "max_time"):
        if resource_key not in params and execution.get(resource_key) is not None:
            params[resource_key] = execution[resource_key]
    if "outdir" not in params and outputs.get("outdir"):
        params["outdir"] = outputs["outdir"]
    command = ["nextflow", "run", f"nf-core/{pipeline}"]
    for config_path in _nextflow_config_paths(spec):
        command.extend(["-c", str(config_path)])
    if version != "latest":
        command.extend(["-r", str(version)])
    if test_profile:
        command.extend(["-profile", f"test,{profile}"])
    else:
        command.extend(["-profile", str(profile)])
    for key, value in sorted(params.items()):
        if value is None:
            continue
        flag = f"--{key}"
        if isinstance(value, bool):
            command.extend([flag, "true" if value else "false"])
        else:
            command.extend([flag, str(value)])
    if execution.get("resume", True):
        command.append("-resume")
    return " ".join(shlex.quote(part) for part in command)


def _nextflow_config_paths(spec: dict[str, Any]) -> list[str]:
    nfcore = spec.get("nfcore", {})
    execution = spec.get("execution", {})
    paths: list[str] = []
    for raw in (nfcore.get("config"), nfcore.get("configs"), execution.get("nextflow_config"), execution.get("nextflow_configs")):
        if raw is None:
            continue
        if isinstance(raw, (str, Path)):
            paths.append(str(raw))
        else:
            paths.extend(str(path) for path in raw)
    return paths


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
    if not shutil.which("nf-core"):
        errors.append(
            {
                "error_type": "MissingSoftware",
                "message": "nf-core CLI is not available on PATH.",
                "suggested_fix": "Install nf-core in the active environment, for example: python -m pip install nf-core.",
                "failed_step": "preflight_nfcore",
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


def _tail_text(path: Path, max_lines: int = 40, max_chars: int = 6000) -> str:
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    text = "\n".join(lines[-max_lines:])
    if len(text) > max_chars:
        return text[-max_chars:]
    return text


def _nextflow_failure_error(returncode: int, outdir: Path) -> dict[str, Any]:
    stderr_tail = _tail_text(outdir / "nextflow.stderr.log")
    stdout_tail = _tail_text(outdir / "nextflow.stdout.log")
    nextflow_tail = _tail_text(outdir / ".nextflow.log")
    details = {
        "stdout": str(outdir / "nextflow.stdout.log") if (outdir / "nextflow.stdout.log").exists() else None,
        "stderr": str(outdir / "nextflow.stderr.log") if (outdir / "nextflow.stderr.log").exists() else None,
        "nextflow_log": str(outdir / ".nextflow.log") if (outdir / ".nextflow.log").exists() else None,
        "stderr_tail": stderr_tail or None,
        "stdout_tail": stdout_tail or None,
        "nextflow_log_tail": nextflow_tail or None,
    }
    failure = classify_nextflow_failure("\n".join(str(value) for value in details.values() if value))
    return {
        "error_type": failure["error_type"],
        "message": failure["message"] or f"Nextflow exited with status {returncode}",
        "suggested_fix": failure["suggested_fix"],
        "failed_step": "run_nextflow",
        "details": {**{key: value for key, value in details.items() if value}, "classification": failure["classification"]},
    }


def classify_nextflow_failure(text: str) -> dict[str, str]:
    lowered = text.lower()
    if ("github.com" in lowered or "nf-core/" in lowered) and any(token in lowered for token in ["connection failed", "connection timed out", "could not resolve host", "unable to access"]):
        return {
            "classification": "pipeline_pull_or_network",
            "error_type": "PipelinePullFailed",
            "message": "Nextflow could not pull the nf-core pipeline from GitHub or the remote pipeline source.",
            "suggested_fix": "Pre-cache the pipeline on a node with network access using `nextflow pull nf-core/<pipeline>`, then rerun the saved command.sh with -resume.",
        }
    if any(token in lowered for token in ["singularity", "apptainer", "container"]) and any(token in lowered for token in ["failed to pull", "image pull", "download", "timeout"]):
        return {
            "classification": "container_pull",
            "error_type": "ContainerPullFailed",
            "message": "Nextflow failed while pulling or preparing a container image.",
            "suggested_fix": "Check the Singularity/Apptainer cache and network access, pre-pull required images if needed, then rerun with -resume.",
        }
    if any(token in lowered for token in ["validation of pipeline parameters failed", "unknown option", "unknown parameter", "missing required"]):
        return {
            "classification": "input_or_parameter",
            "error_type": "PipelineInputFailed",
            "message": "Nextflow rejected one or more pipeline inputs or parameters.",
            "suggested_fix": "Inspect the saved command.sh and pipeline schema, fix the samplesheet or params, then rerun with -resume.",
        }
    if any(token in lowered for token in ["config parsing failed", "unexpected input", "multiplecompilationerrorsexception"]):
        return {
            "classification": "pipeline_config_parse",
            "error_type": "PipelineConfigParseFailed",
            "message": "Nextflow could not parse the pipeline configuration.",
            "suggested_fix": "Check whether the nf-core pipeline revision is compatible with the installed Nextflow version; try a pinned pipeline revision or a compatible Nextflow release, then rerun with -resume.",
        }
    if "java" in lowered and any(token in lowered for token in ["unsupported java", "requires java", "java version", "unsupported class file"]):
        return {
            "classification": "java_runtime",
            "error_type": "UnsupportedRuntime",
            "message": "Nextflow failed because of a Java runtime problem.",
            "suggested_fix": "Activate envs/activate-nextflow.sh or install Java 17+ for this project, then rerun with -resume.",
        }
    return {
        "classification": "nextflow_execution",
        "error_type": "NextflowExecutionFailed",
        "message": "",
        "suggested_fix": "Inspect the preserved Nextflow logs, then rerun the saved command.sh with -resume after fixing the environment or pipeline input issue.",
    }


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
                errors.append(_nextflow_failure_error(completed.returncode, outdir))
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
