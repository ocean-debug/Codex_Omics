from __future__ import annotations

import gzip

import pytest

from omics_codex.scrna_qc.workflow import run_scrna_qc


@pytest.mark.integration
def test_scrna_qc_synthetic(tmp_path) -> None:
    spec = {
        "run": {"name": "synthetic_qc", "type": "scrna_qc", "skill": "single-cell-rna-qc"},
        "inputs": {"path": str(tmp_path / "synthetic.h5ad"), "type": "h5ad", "synthetic": True},
        "scrna_qc": {"counts_layer": "counts", "filter": {"mode": "mad", "min_cells_per_gene": 1}},
        "execution": {"mode": "command_and_run", "approved": True},
        "outputs": {"outdir": str(tmp_path / "results"), "manifest": str(tmp_path / "results" / "run_manifest.json")},
    }
    manifest = run_scrna_qc(spec)
    assert manifest["status"] == "completed"
    assert (tmp_path / "results" / "filtered.h5ad").exists()


@pytest.mark.integration
def test_scrna_qc_fixed_threshold_synthetic(tmp_path) -> None:
    spec = {
        "run": {"name": "synthetic_qc_fixed", "type": "scrna_qc", "skill": "single-cell-rna-qc"},
        "inputs": {"path": str(tmp_path / "synthetic_fixed.h5ad"), "type": "h5ad", "synthetic": True},
        "scrna_qc": {
            "counts_layer": "counts",
            "filter": {"mode": "fixed", "min_counts": 1, "min_genes": 1, "max_pct_mito": 100, "min_cells_per_gene": 1},
        },
        "execution": {"mode": "command_and_run", "approved": True},
        "outputs": {"outdir": str(tmp_path / "fixed_results")},
    }
    manifest = run_scrna_qc(spec)
    assert manifest["status"] == "completed"
    assert (tmp_path / "fixed_results" / "qc_summary.json").exists()


@pytest.mark.integration
def test_scrna_qc_10x_mtx_fixture(tmp_path) -> None:
    pytest.importorskip("scanpy")
    scipy_io = pytest.importorskip("scipy.io")
    sparse = pytest.importorskip("scipy.sparse")
    mtx_dir = tmp_path / "mtx"
    mtx_dir.mkdir()
    matrix = sparse.coo_matrix([[1, 0, 3], [0, 2, 0], [4, 0, 1], [0, 1, 0]], dtype="int32")
    with gzip.open(mtx_dir / "matrix.mtx.gz", "wb") as handle:
        scipy_io.mmwrite(handle, matrix)
    with gzip.open(mtx_dir / "barcodes.tsv.gz", "wt", encoding="utf-8") as handle:
        handle.write("cell1\ncell2\ncell3\n")
    with gzip.open(mtx_dir / "features.tsv.gz", "wt", encoding="utf-8") as handle:
        for gene in ["MT-GENE1", "RPS1", "GENE1", "GENE2"]:
            handle.write(f"{gene}\t{gene}\tGene Expression\n")
    spec = {
        "run": {"name": "mtx_qc", "type": "scrna_qc", "skill": "single-cell-rna-qc"},
        "inputs": {"path": str(mtx_dir), "type": "10x_mtx"},
        "scrna_qc": {"counts_layer": "counts", "filter": {"mode": "fixed", "min_counts": 1, "min_genes": 1, "max_pct_mito": 100, "min_cells_per_gene": 1}},
        "execution": {"mode": "command_and_run", "approved": True},
        "outputs": {"outdir": str(tmp_path / "mtx_results")},
    }
    manifest = run_scrna_qc(spec)
    assert manifest["status"] == "completed"
