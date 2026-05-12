from __future__ import annotations

from omics_codex.common.io import load_yaml_or_json
from omics_codex.nfcore.command import build_nextflow_command
from omics_codex.nfcore.outputs import verify_pipeline_outputs
from omics_codex.nfcore.schema_tools import validate_params


def test_build_nextflow_command_from_example() -> None:
    spec = load_yaml_or_json("examples/nfcore_rnaseq/omics_run_spec.yaml")
    command = build_nextflow_command(spec)
    assert "nextflow run nf-core/rnaseq" in command
    assert "--input" in command
    assert "--genome GRCh38" in command
    assert "-resume" in command


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
    report = tmp_path / "multiqc_report.html"
    report.write_text("<html></html>", encoding="utf-8")
    result = verify_pipeline_outputs("rnaseq", tmp_path)
    assert result["exists"]
    assert result["has_multiqc"]
