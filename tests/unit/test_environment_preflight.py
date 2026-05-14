from __future__ import annotations

from omics_codex.common.environment import assess_nfcore_environment, assess_scvi_environment
from omics_codex.nfcore.command import classify_nextflow_failure


def test_scvi_environment_reports_uv_install_hints_when_scvi_missing() -> None:
    result = assess_scvi_environment(
        {
            "python_packages": {
                "torch": {"available": True, "cuda_available": True},
                "scvi": {"available": False, "error": "No module named scvi"},
                "anndata": {"available": True},
                "scanpy": {"available": True},
            },
            "gpu": {"available": True, "gpus": [{"name": "NVIDIA A100"}]},
        }
    )

    assert result["status"] == "blocked"
    assert any(blocker["message"].endswith("scvi-tools") for blocker in result["blockers"])
    assert any("uv pip install scvi-tools" in hint for hint in result["install_hints"])


def test_scvi_environment_warns_when_gpu_visible_but_torch_cpu_only() -> None:
    result = assess_scvi_environment(
        {
            "python_packages": {
                "torch": {"available": True, "cuda_available": False},
                "scvi": {"available": True},
                "anndata": {"available": True},
                "scanpy": {"available": True},
            },
            "gpu": {"available": True, "gpus": [{"name": "NVIDIA A100"}]},
        }
    )

    assert result["status"] == "warning"
    assert result["warnings"][0]["error_type"] == "TorchCudaUnavailable"


def test_nfcore_environment_blocks_missing_runtime_components() -> None:
    result = assess_nfcore_environment(
        {
            "java": {"available": False},
            "nextflow": {"available": False},
            "nf-core": {"available": False},
            "git": {"available": False},
            "singularity": {"available": False},
            "apptainer": {"available": False},
            "docker": {"available": False},
            "environment": {},
        }
    )

    assert result["status"] == "blocked"
    assert {blocker["failed_step"] for blocker in result["blockers"]} >= {"inspect_environment"}
    assert any("activate-nextflow.sh" in hint for hint in result["install_hints"])


def test_nextflow_github_timeout_is_classified_as_pipeline_pull() -> None:
    failure = classify_nextflow_failure("https://github.com/nf-core/atacseq.git: connection failed\nConnection timed out github.com")

    assert failure["classification"] == "pipeline_pull_or_network"
    assert failure["error_type"] == "PipelinePullFailed"
    assert "nextflow pull nf-core/<pipeline>" in failure["suggested_fix"]


def test_nextflow_config_parse_failure_is_not_misclassified_as_java() -> None:
    failure = classify_nextflow_failure("ERROR ~ Config parsing failed\nUnexpected input: '('\ndef check_max(obj, type)\njava.base/java.util.Iterator")

    assert failure["classification"] == "pipeline_config_parse"
    assert failure["error_type"] == "PipelineConfigParseFailed"
