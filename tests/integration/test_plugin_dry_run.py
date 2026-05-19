from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_scrna_qc_dry_run_writes_manifest(tmp_path: Path) -> None:
    input_path = tmp_path / "cells.h5ad"
    input_path.write_text("", encoding="utf-8")
    outdir = tmp_path / "out"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py",
            "--input",
            str(input_path),
            "--output-dir",
            str(outdir),
            "--dry-run",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((outdir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["skill"] == "single-cell-rna-qc"
    assert manifest["status"] in {"planned", "blocked"}
    assert (outdir / "report.md").exists()


def test_single_cell_preprocess_dry_run_writes_manifest(tmp_path: Path) -> None:
    input_path = tmp_path / "filtered.h5ad"
    input_path.write_text("", encoding="utf-8")
    outdir = tmp_path / "preprocess"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/single-cell-preprocess/scripts/run.py",
            "--input",
            str(input_path),
            "--output-dir",
            str(outdir),
            "--dry-run",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((outdir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["skill"] == "single-cell-preprocess"
    assert manifest["status"] in {"planned", "blocked"}
    assert "preprocessed.h5ad" in manifest.get("plan", {}).get("will_write", []) or manifest["status"] == "blocked"
    assert (outdir / "report.md").exists()


def test_single_cell_integration_dry_run_writes_manifest(tmp_path: Path) -> None:
    input_path = tmp_path / "preprocessed.h5ad"
    input_path.write_text("", encoding="utf-8")
    outdir = tmp_path / "integration"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/single-cell-integration/scripts/run.py",
            "--input",
            str(input_path),
            "--output-dir",
            str(outdir),
            "--dry-run",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((outdir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["skill"] == "single-cell-integration"
    assert manifest["status"] in {"planned", "blocked"}
    assert "integrated.h5ad" in manifest.get("plan", {}).get("will_write", []) or manifest["status"] == "blocked"
    assert (outdir / "report.md").exists()


def test_single_cell_integration_scanpy_combat_approved_smoke(tmp_path: Path) -> None:
    import anndata as ad
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(7)
    matrix = rng.normal(loc=4.0, scale=0.5, size=(12, 8))
    matrix[:6, :4] += 1.5
    matrix[6:, 4:] += 1.5
    matrix = np.clip(matrix, 0.01, None)
    adata = ad.AnnData(
        X=matrix,
        obs=pd.DataFrame({"batch": ["A"] * 6 + ["B"] * 6, "leiden": ["0", "0", "1", "1", "2", "2"] * 2}, index=[f"cell{i}" for i in range(12)]),
        var=pd.DataFrame(index=[f"Gene{i}" for i in range(8)]),
    )
    input_path = tmp_path / "preprocessed.h5ad"
    adata.write_h5ad(input_path)
    outdir = tmp_path / "integration"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/single-cell-integration/scripts/run.py",
            "--input",
            str(input_path),
            "--output-dir",
            str(outdir),
            "--backend",
            "scanpy-combat",
            "--batch-key",
            "batch",
            "--n-pcs",
            "3",
            "--approved",
            "true",
            "--write-manifest",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((outdir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "completed"
    assert (outdir / "integrated.h5ad").exists()
    assert (outdir / "integration_summary.json").exists()
    assert (outdir / "batch_diagnostics.csv").exists()
    assert manifest["summary"]["n_batches"] == 2


def test_single_cell_integration_optional_backend_blocks_without_execution(tmp_path: Path) -> None:
    import anndata as ad
    import numpy as np
    import pandas as pd

    adata = ad.AnnData(
        X=np.ones((6, 4)),
        obs=pd.DataFrame({"batch": ["A", "A", "A", "B", "B", "B"]}, index=[f"cell{i}" for i in range(6)]),
        var=pd.DataFrame(index=[f"Gene{i}" for i in range(4)]),
    )
    input_path = tmp_path / "preprocessed.h5ad"
    adata.write_h5ad(input_path)
    outdir = tmp_path / "integration"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/single-cell-integration/scripts/run.py",
            "--input",
            str(input_path),
            "--output-dir",
            str(outdir),
            "--backend",
            "harmony",
            "--approved",
            "true",
            "--write-manifest",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((outdir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["skill"] == "single-cell-integration"
    assert manifest["status"] == "blocked"
    error_types = {error["error_type"] for error in manifest.get("errors", [])}
    assert "HarmonyUnavailable" in error_types or "BackendExecutionDeferred" in error_types


def test_single_cell_marker_de_dry_run_writes_manifest(tmp_path: Path) -> None:
    input_path = tmp_path / "preprocessed.h5ad"
    input_path.write_text("", encoding="utf-8")
    outdir = tmp_path / "markers"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/single-cell-marker-de/scripts/run.py",
            "--input",
            str(input_path),
            "--output-dir",
            str(outdir),
            "--dry-run",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((outdir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["skill"] == "single-cell-marker-de"
    assert manifest["status"] in {"planned", "blocked"}
    assert "markers.csv" in manifest.get("plan", {}).get("will_write", []) or manifest["status"] == "blocked"
    assert (outdir / "report.md").exists()


def test_single_cell_annotation_dry_run_writes_manifest(tmp_path: Path) -> None:
    input_path = tmp_path / "preprocessed.h5ad"
    input_path.write_text("", encoding="utf-8")
    marker_reference = tmp_path / "marker_reference.csv"
    marker_reference.write_text("cell_type,gene\nT cell,CD3D\n", encoding="utf-8")
    outdir = tmp_path / "annotation"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/single-cell-annotation/scripts/run.py",
            "--input",
            str(input_path),
            "--output-dir",
            str(outdir),
            "--backend",
            "marker-based",
            "--marker-reference",
            str(marker_reference),
            "--dry-run",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((outdir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["skill"] == "single-cell-annotation"
    assert manifest["status"] in {"planned", "blocked"}
    assert "annotated.h5ad" in manifest.get("plan", {}).get("will_write", []) or manifest["status"] == "blocked"
    assert (outdir / "report.md").exists()


def test_single_cell_annotation_marker_based_approved_smoke(tmp_path: Path) -> None:
    import anndata as ad
    import numpy as np
    import pandas as pd

    matrix = np.array(
        [
            [8, 7, 0, 0],
            [9, 8, 0, 0],
            [7, 8, 0, 0],
            [0, 0, 8, 7],
            [0, 0, 9, 8],
            [0, 0, 7, 8],
        ],
        dtype=float,
    )
    adata = ad.AnnData(
        X=matrix,
        obs=pd.DataFrame({"leiden": ["0", "0", "0", "1", "1", "1"]}, index=[f"cell{i}" for i in range(6)]),
        var=pd.DataFrame(index=["CD3D", "CD3E", "MS4A1", "CD79A"]),
    )
    input_path = tmp_path / "preprocessed.h5ad"
    adata.write_h5ad(input_path)
    marker_reference = tmp_path / "marker_reference.csv"
    marker_reference.write_text(
        "cell_type,gene,weight\n"
        "T cell,CD3D,1\n"
        "T cell,CD3E,1\n"
        "B cell,MS4A1,1\n"
        "B cell,CD79A,1\n",
        encoding="utf-8",
    )
    outdir = tmp_path / "annotation"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/single-cell-annotation/scripts/run.py",
            "--input",
            str(input_path),
            "--output-dir",
            str(outdir),
            "--backend",
            "marker-based",
            "--marker-reference",
            str(marker_reference),
            "--groupby",
            "leiden",
            "--approved",
            "true",
            "--write-manifest",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((outdir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "completed"
    assert (outdir / "annotated.h5ad").exists()
    assert (outdir / "annotations.csv").exists()
    assert (outdir / "annotation_summary.json").exists()
    assert manifest["summary"]["n_cell_types"] == 2


def test_single_cell_annotation_optional_backend_blocks_without_resources(tmp_path: Path) -> None:
    input_path = tmp_path / "preprocessed.h5ad"
    input_path.write_text("", encoding="utf-8")
    outdir = tmp_path / "annotation"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/single-cell-annotation/scripts/run.py",
            "--input",
            str(input_path),
            "--output-dir",
            str(outdir),
            "--backend",
            "celltypist",
            "--approved",
            "true",
            "--write-manifest",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((outdir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["skill"] == "single-cell-annotation"
    assert manifest["status"] in {"blocked", "failed"}
    error_types = {error["error_type"] for error in manifest.get("errors", [])}
    assert "MissingCellTypistModel" in error_types or "UnsupportedInput" in error_types or "MissingSoftware" in error_types


def test_pathway_enrichment_dry_run_writes_manifest(tmp_path: Path) -> None:
    input_path = tmp_path / "markers.csv"
    input_path.write_text("group,names\n0,GeneA\n", encoding="utf-8")
    gene_sets = tmp_path / "gene_sets.gmt"
    gene_sets.write_text("PathwayA\tna\tGeneA\tGeneB\n", encoding="utf-8")
    outdir = tmp_path / "enrichment"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/pathway-enrichment/scripts/run.py",
            "--input",
            str(input_path),
            "--gene-sets",
            str(gene_sets),
            "--output-dir",
            str(outdir),
            "--dry-run",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((outdir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["skill"] == "pathway-enrichment"
    assert manifest["status"] == "planned"
    assert "enrichment.csv" in manifest.get("plan", {}).get("will_write", [])
    assert (outdir / "report.md").exists()


def test_bulk_rna_de_dry_run_writes_manifest(tmp_path: Path) -> None:
    counts = tmp_path / "counts.csv"
    counts.write_text("gene,c1,c2,t1,t2\nGeneA,10,12,100,120\n", encoding="utf-8")
    metadata = tmp_path / "metadata.csv"
    metadata.write_text("sample,condition\nc1,control\nc2,control\nt1,treatment\nt2,treatment\n", encoding="utf-8")
    outdir = tmp_path / "bulk_de"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/bulk-rna-de/scripts/run.py",
            "--counts",
            str(counts),
            "--metadata",
            str(metadata),
            "--contrast",
            "condition:control:treatment",
            "--output-dir",
            str(outdir),
            "--dry-run",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((outdir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["skill"] == "bulk-rna-de"
    assert manifest["status"] == "planned"
    assert "de_results.csv" in manifest.get("plan", {}).get("will_write", [])
    assert (outdir / "report.md").exists()


def test_scrna_standard_workflow_dry_run_writes_plan(tmp_path: Path) -> None:
    input_path = tmp_path / "cells.h5ad"
    input_path.write_text("", encoding="utf-8")
    outdir = tmp_path / "scrna_workflow"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/scrna-standard-workflow/scripts/run.py",
            "--input",
            str(input_path),
            "--output-dir",
            str(outdir),
            "--dry-run",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((outdir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["skill"] == "scrna-standard-workflow"
    assert manifest["status"] in {"planned", "blocked"}
    assert (outdir / "workflow_plan.json").exists()
    assert (outdir / "workflow_plan.md").exists()
    assert (outdir / "report.md").exists()
    plan = json.loads((outdir / "workflow_plan.json").read_text(encoding="utf-8"))
    assert plan["plan_only"] is True
    assert any(step["skill"] == "single-cell-integration" for step in plan["steps"])


def test_scrna_standard_workflow_skip_marker_de_also_skips_enrichment(tmp_path: Path) -> None:
    input_path = tmp_path / "cells.h5ad"
    input_path.write_text("", encoding="utf-8")
    outdir = tmp_path / "scrna_workflow"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/scrna-standard-workflow/scripts/run.py",
            "--input",
            str(input_path),
            "--output-dir",
            str(outdir),
            "--skip-marker-de",
            "--dry-run",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((outdir / "run_manifest.json").read_text(encoding="utf-8"))
    plan = json.loads((outdir / "workflow_plan.json").read_text(encoding="utf-8"))
    skills = [step["skill"] for step in plan["steps"]]
    assert "single-cell-marker-de" not in skills
    assert "pathway-enrichment" not in skills
    assert manifest["parameters"]["skip_enrichment"] is True
    warning_types = {item["warning_type"] for item in manifest.get("warnings", [])}
    assert "EnrichmentSkipped" in warning_types


def test_bulk_rna_de_approved_smoke_writes_results(tmp_path: Path) -> None:
    counts = tmp_path / "counts.csv"
    counts.write_text(
        "gene,c1,c2,t1,t2\n"
        "GeneA,100,110,1000,1100\n"
        "GeneB,900,920,100,120\n"
        "GeneC,300,310,320,330\n",
        encoding="utf-8",
    )
    metadata = tmp_path / "metadata.csv"
    metadata.write_text("sample,condition\nc1,control\nc2,control\nt1,treatment\nt2,treatment\n", encoding="utf-8")
    outdir = tmp_path / "bulk_de"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/bulk-rna-de/scripts/run.py",
            "--counts",
            str(counts),
            "--metadata",
            str(metadata),
            "--contrast",
            "condition:control:treatment",
            "--output-dir",
            str(outdir),
            "--approved",
            "true",
            "--write-manifest",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((outdir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "completed"
    assert (outdir / "de_results.csv").exists()
    assert (outdir / "de_summary.json").exists()
    assert manifest["summary"]["n_genes_tested"] >= 1
