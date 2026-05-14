from __future__ import annotations

from types import SimpleNamespace

from omics_codex.common.io import load_yaml_or_json
from omics_codex.nfcore import command as command_module
from omics_codex.nfcore.command import build_nextflow_command
from omics_codex.nfcore.outputs import verify_pipeline_outputs
from omics_codex.nfcore.schema_tools import validate_params


def test_build_nextflow_command_from_example() -> None:
    spec = load_yaml_or_json("examples/nfcore_rnaseq/omics_run_spec.yaml")
    command = build_nextflow_command(spec)
    assert "nextflow run nf-core/rnaseq" in command
    assert "--input" in command
    assert "--genome GRCh38" in command
    assert "--max_cpus 12" in command
    assert "-resume" in command


def test_build_nextflow_command_preserves_underscored_params_and_config() -> None:
    spec = {
        "nfcore": {"pipeline": "rnaseq", "profile": "singularity", "params": {"max_cpus": 4}},
        "execution": {"nextflow_configs": ["envs/nextflow-singularity.config", "extra.config"]},
    }
    command = build_nextflow_command(spec)
    assert "-c envs/nextflow-singularity.config" in command
    assert "-c extra.config" in command
    assert "--max_cpus 4" in command
    assert "--max-cpus" not in command


def test_nfcore_param_validation_required_and_enum() -> None:
    schema = {
        "definitions": {
            "input_output_options": {
                "type": "object",
                "required": ["input"],
                "properties": {
                    "input": {"type": "string"},
                    "aligner": {"type": "string", "enum": ["star_salmon", "salmon"]},
                },
            }
        }
    }
    assert validate_params(schema, {"input": "samplesheet.csv", "aligner": "star_salmon"}) == []
    errors = validate_params(schema, {"aligner": "bad"})
    assert any("'input' is a required property" in error for error in errors)
    assert any("'bad' is not one of" in error for error in errors)


def test_verify_pipeline_outputs(tmp_path) -> None:
    report = tmp_path / "sample_multiqc_report.html"
    report.write_text("<html></html>", encoding="utf-8")
    result = verify_pipeline_outputs("rnaseq", tmp_path)
    assert result["exists"]
    assert result["has_multiqc"]


def test_run_nfcore_failed_execution_preserves_log_tails(tmp_path, monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        (kwargs["cwd"] / ".nextflow.log").write_text("nextflow diagnostic\nroot cause", encoding="utf-8")
        return SimpleNamespace(returncode=1, stdout="stdout line", stderr="stderr root cause")

    monkeypatch.setattr(command_module, "runtime_blockers", lambda spec: [])
    monkeypatch.setattr(command_module.subprocess, "run", fake_run)
    spec = {
        "run": {"name": "nfcore_failure", "type": "nfcore_pipeline", "skill": "nf-core-universal"},
        "inputs": {"path": "", "type": "test_profile"},
        "nfcore": {"pipeline": "rnaseq", "profile": "singularity", "params": {"outdir": str(tmp_path / "rnaseq")}},
        "execution": {"mode": "test_profile", "approved": True, "force": True, "workdir": str(tmp_path)},
        "outputs": {"outdir": str(tmp_path / "rnaseq"), "manifest": str(tmp_path / "rnaseq" / "run_manifest.json")},
    }

    manifest = command_module.run_nfcore(spec)

    assert manifest["status"] == "failed"
    assert manifest["errors"][0]["details"]["stderr_tail"] == "stderr root cause"
    assert "root cause" in manifest["errors"][0]["details"]["nextflow_log_tail"]


def test_runtime_blockers_rejects_unparseable_java_version(monkeypatch) -> None:
    monkeypatch.setattr(command_module, "_java_version_text", lambda: "java version unknown")
    monkeypatch.setattr(
        command_module.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in {"nextflow", "nf-core", "singularity"} else None,
    )

    errors = command_module.runtime_blockers({"nfcore": {"profile": "singularity"}})

    assert any(error["failed_step"] == "preflight_java" and error["error_type"] == "UnsupportedRuntime" for error in errors)
