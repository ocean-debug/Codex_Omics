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


def test_router_routes_single_cell_integration(tmp_path: Path) -> None:
    h5ad = tmp_path / "preprocessed cells.h5ad"
    h5ad.write_text("", encoding="utf-8")
    outdir = tmp_path / "route out"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/omics-router/scripts/route_omics.py",
            "--prompt",
            "integrate batches with combat batch correction",
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
    assert payload["selected_skill"] == "single-cell-integration"
    assert payload["router_plan"]["selected_skill"] == "single-cell-integration"
    assert "single_cell_integration" in payload["router_plan"]["detected_intents"]
    assert payload["plan"]["backend"] == "scanpy-combat"
    assert "single-cell-integration/scripts/plan.py" in payload["plan"]["commands"][2]
    assert "preprocessed cells.h5ad'" in payload["plan"]["commands"][1]


def test_router_routes_single_cell_marker_de(tmp_path: Path) -> None:
    h5ad = tmp_path / "preprocessed cells.h5ad"
    h5ad.write_text("", encoding="utf-8")
    outdir = tmp_path / "route out"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/omics-router/scripts/route_omics.py",
            "--prompt",
            "find marker genes for leiden clusters",
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
    assert payload["selected_skill"] == "single-cell-marker-de"
    assert payload["router_plan"]["selected_skill"] == "single-cell-marker-de"
    assert "single_cell_marker_de" in payload["router_plan"]["detected_intents"]
    assert "single-cell-marker-de/scripts/plan.py" in payload["plan"]["commands"][2]
    assert "preprocessed cells.h5ad'" in payload["plan"]["commands"][1]


def test_router_routes_single_cell_annotation(tmp_path: Path) -> None:
    h5ad = tmp_path / "preprocessed cells.h5ad"
    h5ad.write_text("", encoding="utf-8")
    marker_ref = tmp_path / "marker_reference.csv"
    marker_ref.write_text("cell_type,gene\nT cell,CD3D\n", encoding="utf-8")
    outdir = tmp_path / "route out"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/omics-router/scripts/route_omics.py",
            "--prompt",
            "annotate cell types for leiden clusters",
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
    assert payload["selected_skill"] == "single-cell-annotation"
    assert payload["router_plan"]["selected_skill"] == "single-cell-annotation"
    assert "single_cell_annotation" in payload["router_plan"]["detected_intents"]
    assert "single-cell-annotation/scripts/plan.py" in payload["plan"]["commands"][2]
    assert "marker_reference.csv" in payload["plan"]["commands"][1]


def test_router_routes_pathway_enrichment(tmp_path: Path) -> None:
    markers = tmp_path / "markers.csv"
    markers.write_text("group,names\n0,GeneA\n", encoding="utf-8")
    outdir = tmp_path / "route out"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/omics-router/scripts/route_omics.py",
            "--prompt",
            "run pathway enrichment for marker genes",
            "--input",
            str(markers),
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
    assert payload["selected_skill"] == "pathway-enrichment"
    assert payload["router_plan"]["selected_skill"] == "pathway-enrichment"
    assert "pathway_enrichment" in payload["router_plan"]["detected_intents"]
    assert "pathway-enrichment/scripts/plan.py" in payload["plan"]["commands"][2]
    assert "gene_sets.gmt" in payload["plan"]["commands"][1]


def test_router_routes_bulk_rna_de(tmp_path: Path) -> None:
    counts = tmp_path / "counts.csv"
    counts.write_text("gene,c1,c2,t1,t2\nGeneA,10,12,100,120\n", encoding="utf-8")
    (tmp_path / "metadata.csv").write_text("sample,condition\nc1,control\nc2,control\nt1,treatment\nt2,treatment\n", encoding="utf-8")
    outdir = tmp_path / "route out"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/omics-router/scripts/route_omics.py",
            "--prompt",
            "run bulk RNA differential expression from counts metadata contrast",
            "--input",
            str(counts),
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
    assert payload["selected_skill"] == "bulk-rna-de"
    assert payload["router_plan"]["selected_skill"] == "bulk-rna-de"
    assert "bulk_rna_de" in payload["router_plan"]["detected_intents"]
    assert "bulk-rna-de/scripts/plan.py" in payload["plan"]["commands"][2]
    assert "metadata.csv" in payload["plan"]["commands"][1]


def test_router_routes_scrna_standard_workflow(tmp_path: Path) -> None:
    h5ad = tmp_path / "cells.h5ad"
    h5ad.write_text("", encoding="utf-8")
    outdir = tmp_path / "route out"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/omics-router/scripts/route_omics.py",
            "--prompt",
            "plan an end-to-end scrna workflow with qc preprocess integrate annotate markers enrichment",
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
    assert payload["selected_skill"] == "scrna-standard-workflow"
    assert payload["router_plan"]["selected_skill"] == "scrna-standard-workflow"
    assert payload["router_plan"]["selected_pipeline"] == "scrna-standard-workflow"
    assert "scrna_standard_workflow" in payload["router_plan"]["detected_intents"]
    assert "scrna-standard-workflow/scripts/plan.py" in payload["plan"]["commands"][2]


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


def test_report_renderer_summarizes_single_cell_integration(tmp_path: Path) -> None:
    manifest = tmp_path / "run_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "skill": "single-cell-integration",
                "status": "completed",
                "run_id": "integration-test",
                "created_at": "now",
                "parameters": {"backend": "scanpy-combat", "batch_key": "batch"},
                "summary": {"backend": "scanpy-combat", "batch_key": "batch", "n_cells": 12, "n_genes": 8, "n_batches": 2, "embedding_key": "X_pca_integrated", "has_umap": True},
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
    assert "Backend: `scanpy-combat`" in text
    assert "Cells integrated: `12`" in text


def test_report_renderer_summarizes_scrna_standard_workflow(tmp_path: Path) -> None:
    manifest = tmp_path / "run_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "skill": "scrna-standard-workflow",
                "status": "planned",
                "run_id": "workflow-test",
                "created_at": "now",
                "summary": {"n_steps": 7, "step_ids": ["01_qc", "02_preprocess"], "plan_only": True},
                "parameters": {"plan_only": True},
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
    assert "Plan only: `True`" in text
    assert "Planned steps: `7`" in text


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
