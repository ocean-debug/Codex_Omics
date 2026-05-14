#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import json
import os
import re
from pathlib import Path
from typing import Any


ROOT = Path(os.environ.get("CODEX_OMICS_ROOT", Path.cwd())).resolve()
DATA_DIR = Path(os.environ.get("CODEX_OMICS_DATA_DIR", ROOT / "data/test")).resolve()
RESULT_DIR = Path(os.environ.get("CODEX_OMICS_RESULT_DIR", DATA_DIR / "result")).resolve()
READS_PER_FASTQ = int(os.environ.get("CODEX_OMICS_READS_PER_FASTQ", "20000"))


def subset_fastq(src: Path, dst: Path, reads: int = READS_PER_FASTQ) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and dst.stat().st_size > 0:
        return
    with gzip.open(src, "rt", encoding="utf-8", errors="replace") as handle, gzip.open(dst, "wt", encoding="utf-8") as out:
        for index, line in enumerate(handle):
            if index >= reads * 4:
                break
            out.write(line)


def genome_paths() -> dict[str, str]:
    genome_root = DATA_DIR / "nf-core/genome"
    fasta = os.environ.get("CODEX_OMICS_FASTA") or first_existing(genome_root, ["*.fa", "*.fasta"])
    gtf = os.environ.get("CODEX_OMICS_GTF") or first_existing(genome_root, ["*.gtf"])
    return {"fasta": str(fasta or ""), "gtf": str(gtf or "")}


def first_existing(root: Path, patterns: list[str]) -> Path | None:
    for pattern in patterns:
        matches = sorted(root.rglob(pattern)) if root.exists() else []
        if matches:
            return matches[0]
    return None


def prepare_rna() -> dict[str, Any]:
    out = RESULT_DIR / "bulk_rna"
    subset_dir = out / "subset_fastq"
    rows = []
    for r1 in sorted((DATA_DIR / "nf-core/rna").glob("*_1.fq.gz")):
        r2 = Path(str(r1).replace("_1.fq.gz", "_2.fq.gz"))
        if not r2.exists():
            continue
        sample = r1.name.replace("_1.fq.gz", "")
        dst1 = subset_dir / r1.name
        dst2 = subset_dir / r2.name
        subset_fastq(r1, dst1)
        subset_fastq(r2, dst2)
        rows.append({"sample": sample, "fastq_1": str(dst1), "fastq_2": str(dst2), "strandedness": "auto"})
    sheet = out / "samplesheet.csv"
    write_csv(sheet, ["sample", "fastq_1", "fastq_2", "strandedness"], rows)
    return write_summary(out, {"project": "bulk_rna", "reads_per_fastq": READS_PER_FASTQ, "samples": len(rows), "samplesheet": str(sheet), **genome_paths()})


def prepare_atac() -> dict[str, Any]:
    out = RESULT_DIR / "atac"
    subset_dir = out / "subset_fastq"
    rows = []
    for r1 in sorted((DATA_DIR / "nf-core/atac").glob("*_R1.fastq.gz")):
        r2 = Path(str(r1).replace("_R1.fastq.gz", "_R2.fastq.gz"))
        if not r2.exists():
            continue
        sample = r1.name.replace("_R1.fastq.gz", "")
        dst1 = subset_dir / r1.name
        dst2 = subset_dir / r2.name
        subset_fastq(r1, dst1)
        subset_fastq(r2, dst2)
        match = re.match(r"(\d+)-", sample)
        rows.append({"sample": sample, "fastq_1": str(dst1), "fastq_2": str(dst2), "replicate": match.group(1) if match else "1"})
    sheet = out / "samplesheet.csv"
    write_csv(sheet, ["sample", "fastq_1", "fastq_2", "replicate"], rows)
    return write_summary(out, {"project": "atac", "reads_per_fastq": READS_PER_FASTQ, "samples": len(rows), "samplesheet": str(sheet), **genome_paths()})


def prepare_scvi() -> dict[str, Any]:
    import anndata as ad

    source = Path(os.environ.get("CODEX_OMICS_SCVI_H5AD", DATA_DIR / "scvi/lung_atlas_preprocessed.h5ad")).resolve()
    out = RESULT_DIR / "scvi"
    out.mkdir(parents=True, exist_ok=True)
    subset = out / "scvi_subset.h5ad"
    n_obs = int(os.environ.get("CODEX_OMICS_SCVI_N_OBS", "3000"))
    if not subset.exists():
        adata = ad.read_h5ad(source)
        adata[: min(n_obs, adata.n_obs), :].copy().write_h5ad(subset)
    adata = ad.read_h5ad(subset, backed="r")
    return write_summary(
        out,
        {
            "project": "scvi",
            "source": str(source),
            "subset": str(subset),
            "shape": list(adata.shape),
            "layers": list(adata.layers.keys()),
            "obs_columns": list(adata.obs.columns),
        },
    )


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(outdir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "input_summary.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare small real-data acceptance inputs for Codex Omics.")
    parser.add_argument("project", choices=["bulk_rna", "atac", "scvi", "all"])
    args = parser.parse_args()
    result: dict[str, Any] = {}
    if args.project in {"bulk_rna", "all"}:
        result["bulk_rna"] = prepare_rna()
    if args.project in {"atac", "all"}:
        result["atac"] = prepare_atac()
    if args.project in {"scvi", "all"}:
        result["scvi"] = prepare_scvi()
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
