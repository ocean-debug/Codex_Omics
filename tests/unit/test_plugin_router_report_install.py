from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def test_router_generates_safe_nextflow_plan(tmp_path: Path) -> None:
    (tmp_path / "sample_R1.fastq.gz").write_text("", encoding="utf-8")
    (tmp_path / "sample_R2.fastq.gz").write_text("", encoding="utf-8")
    outdir = tmp_path / "route"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/omics-router/scripts/route_omics.py",
            "--prompt",
            "run rnaseq workflow",
            "--input",
            str(tmp_path),
            "--outdir",
            str(outdir),
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["selected_skill"] == "nextflow-development"
    assert payload["approved"] is False
    assert payload["plan"]["approval_required"] is True
    assert payload["router_plan"]["selected_skill"] == "nextflow-development"
    assert payload["router_plan"]["candidate_scores"][0]["skill_id"] == "nextflow-development"


def test_router_generates_riboseq_nextflow_plan(tmp_path: Path) -> None:
    (tmp_path / "sample_R1.fastq.gz").write_text("", encoding="utf-8")
    outdir = tmp_path / "route"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/omics-router/scripts/route_omics.py",
            "--prompt",
            "run riboseq translational efficiency",
            "--input",
            str(tmp_path),
            "--outdir",
            str(outdir),
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["selected_skill"] == "nextflow-development"
    assert payload["plan"]["pipeline"] == "riboseq"
    assert payload["router_plan"]["selected_pipeline"] == "riboseq"
    assert "--revision 1.2.0" in payload["plan"]["commands"][2]


def test_router_generates_scrnaseq_nextflow_plan(tmp_path: Path) -> None:
    (tmp_path / "sample_R1.fastq.gz").write_text("", encoding="utf-8")
    (tmp_path / "sample_R2.fastq.gz").write_text("", encoding="utf-8")
    outdir = tmp_path / "route"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/omics-router/scripts/route_omics.py",
            "--prompt",
            "run scrnaseq with cellranger",
            "--input",
            str(tmp_path),
            "--outdir",
            str(outdir),
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["selected_skill"] == "nextflow-development"
    assert payload["plan"]["pipeline"] == "scrnaseq"
    assert payload["router_plan"]["selected_pipeline"] == "scrnaseq"
    assert "--revision 4.1.0" in payload["plan"]["commands"][2]


def test_router_generates_spatialvi_nextflow_plan(tmp_path: Path) -> None:
    (tmp_path / "metadata.csv").write_text("sample,spaceranger_dir\nvisium1,/outs\n", encoding="utf-8")
    outdir = tmp_path / "route"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/omics-router/scripts/route_omics.py",
            "--prompt",
            "run spatialvi for visium spaceranger data",
            "--input",
            str(tmp_path),
            "--outdir",
            str(outdir),
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["selected_skill"] == "nextflow-development"
    assert payload["plan"]["pipeline"] == "spatialvi"
    assert payload["router_plan"]["selection_reason"].startswith("Selected nextflow-development")
    assert "--metadata" in payload["plan"]["commands"][1]
    assert "--revision dev" in payload["plan"]["commands"][2]


def test_router_routes_report_requests(tmp_path: Path) -> None:
    manifest = tmp_path / "run manifest.json"
    manifest.write_text('{"skill":"x","status":"completed"}', encoding="utf-8")
    outdir = tmp_path / "route out"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/omics-router/scripts/route_omics.py",
            "--prompt",
            "render report and interpret results",
            "--input",
            str(manifest),
            "--outdir",
            str(outdir),
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["selected_skill"] == "omics-report"
    assert payload["router_plan"]["detected_intents"] == ["reporting"]
    assert "--manifest '" in payload["plan"]["commands"][0]
    assert "run manifest.json'" in payload["plan"]["commands"][0]
    assert "route out" in payload["plan"]["commands"][0]


def test_router_routes_new_skill_authoring_requests(tmp_path: Path) -> None:
    (tmp_path / "cells.h5ad").write_text("", encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/omics-router/scripts/route_omics.py",
            "--prompt",
            "add new skill for bulk-rna-de",
            "--input",
            str(tmp_path),
            "--outdir",
            str(tmp_path / "route"),
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["selected_skill"] == "skill-authoring-kit"
    assert payload["router_plan"]["candidate_scores"][0]["skill_id"] == "skill-authoring-kit"


def test_router_routes_h5ad_scvi_and_qc_intents(tmp_path: Path) -> None:
    h5ad = tmp_path / "cells.h5ad"
    h5ad.write_text("", encoding="utf-8")
    for prompt, expected in [("run scvi batch correction", "scvi-tools"), ("run qc filtering", "single-cell-rna-qc")]:
        completed = subprocess.run(
            [
                sys.executable,
                "plugins/omics-analysis/skills/omics-router/scripts/route_omics.py",
                "--prompt",
                prompt,
                "--input",
                str(h5ad),
                "--outdir",
                str(tmp_path / prompt.replace(" ", "_")),
                "--json",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        payload = json.loads(completed.stdout)
        assert payload["selected_skill"] == expected
        assert payload["router_plan"]["selected_skill"] == expected


def test_router_routes_single_cell_preprocess(tmp_path: Path) -> None:
    h5ad = tmp_path / "filtered cells.h5ad"
    h5ad.write_text("", encoding="utf-8")
    outdir = tmp_path / "route out"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/omics-router/scripts/route_omics.py",
            "--prompt",
            "preprocess single-cell h5ad with normalization hvg umap leiden",
            "--input",
            str(h5ad),
            "--outdir",
            str(outdir),
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["selected_skill"] == "single-cell-preprocess"
    assert payload["router_plan"]["selected_skill"] == "single-cell-preprocess"
    assert "single_cell_preprocessing" in payload["router_plan"]["detected_intents"]
    assert "single-cell-preprocess/scripts/plan.py" in payload["plan"]["commands"][2]
    assert "filtered cells.h5ad'" in payload["plan"]["commands"][1]


def test_report_renderer_from_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "run_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "skill": "single-cell-rna-qc",
                "status": "completed",
                "run_id": "test",
                "created_at": "now",
                "summary": {"before": {"n_cells": 10}, "after": {"n_cells": 8}, "removed_cells": 2, "counts_source": "X", "filter_mode": "mad"},
            }
        ),
        encoding="utf-8",
    )
    report = tmp_path / "report.md"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/omics-report/scripts/render_report.py",
            "--manifest",
            str(manifest),
            "--out",
            str(report),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    text = report.read_text(encoding="utf-8")
    for section in [
        "## Analysis Overview",
        "## Input Data Summary",
        "## Environment and Dependencies",
        "## Methods and Parameters",
        "## Results and QC Interpretation",
        "## Warnings / Failures / Suggested Fixes",
        "## Reproducibility Appendix",
    ]:
        assert section in text
    assert "Cells before filtering" in text
    assert "Removed cells" in text


def test_report_renderer_preserves_failed_manifest_details(tmp_path: Path) -> None:
    manifest = tmp_path / "run_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "skill": "nextflow-development",
                "status": "failed",
                "run_id": "failed-test",
                "created_at": "now",
                "inputs": {"samplesheet": "samplesheet.csv"},
                "parameters": {"pipeline": "rnaseq"},
                "outputs": {"outdir": "results"},
                "commands": ["nextflow run nf-core/rnaseq"],
                "qc_summary": {"samples_in_general_stats": 2},
                "interpretation": ["MultiQC parsed."],
                "warnings": [{"warning_type": "ExampleWarning", "message": "warning"}],
                "errors": [{"error_type": "InvalidPipelineParameters", "message": "bad param", "auto_fix_plan": ["Regenerate params.yaml"]}],
            }
        ),
        encoding="utf-8",
    )
    report = tmp_path / "report.md"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/omics-report/scripts/render_report.py",
            "--manifest",
            str(manifest),
            "--out",
            str(report),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    text = report.read_text(encoding="utf-8")
    assert "## Warnings / Failures / Suggested Fixes" in text
    assert "InvalidPipelineParameters" in text
    assert "Regenerate params.yaml" in text
    assert "MultiQC parsed." in text
    assert "nextflow run nf-core/rnaseq" in text


def test_scvi_recommend_model_from_task_without_anndata(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/scvi-tools/scripts/recommend_model.py",
            "--input",
            str(tmp_path / "missing.h5ad"),
            "--task",
            "CITE-seq protein ADT analysis",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["recommended_model"] == "TOTALVI"
    assert payload["ranked_recommendations"][0]["model"] == "TOTALVI"
    assert payload["anndata_summary"]["readable"] is False


def test_lightweight_schema_validation_reports_missing_key() -> None:
    sys.path.insert(0, str(Path("plugins/omics-analysis/scripts")))
    from common.schema_validation import lightweight_validate

    result = lightweight_validate({"status": "planned"}, {"required": ["status", "selected_skill"], "properties": {"status": {"type": "string"}}})
    assert result["mode"] == "lightweight"
    assert result["valid"] is False
    assert "Missing required key: selected_skill" in result["errors"]


def test_scvi_diagnostics_helpers_are_dependency_light(tmp_path: Path) -> None:
    sys.path.insert(0, str(Path("plugins/omics-analysis/scripts")))
    script = Path("plugins/omics-analysis/skills/scvi-tools/scripts/train_model.py")
    spec = importlib.util.spec_from_file_location("train_model", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    class FakeHistory:
        history = {"elbo_train": [3, 2, 1], "reconstruction_loss_train": [5.0, 4.0]}

    history = module.extract_history(FakeHistory())
    assert history["elbo_train"] == [3.0, 2.0, 1.0]
    out = tmp_path / "history.csv"
    module.write_history_csv(out, history)
    assert "elbo_train" in out.read_text(encoding="utf-8")
    interpretation = module.interpret_diagnostics({"latent_key": "X_scvi", "latent_shape": [10, 5]}, history)
    assert any("Latent embedding" in item for item in interpretation)


def test_install_planner_is_plan_only_by_default(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/scripts/common/install_planner.py",
            "--task",
            "scvi",
            "--output-dir",
            str(tmp_path),
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    payload = json.loads(completed.stdout)
    assert payload["approval_required"] is True
    assert payload["execution"]["executed"] is False
