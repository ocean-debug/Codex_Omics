#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(os.environ.get("CODEX_OMICS_ROOT", Path.cwd())).resolve()
DATA_DIR = Path(os.environ.get("CODEX_OMICS_DATA_DIR", ROOT / "data/test")).resolve()
RESULT_DIR = Path(os.environ.get("CODEX_OMICS_RESULT_DIR", DATA_DIR / "result")).resolve()
READS_PER_FASTQ = int(os.environ.get("CODEX_OMICS_READS_PER_FASTQ", "20000"))


class InputPreparationError(RuntimeError):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


def fail(message: str, **details: Any) -> None:
    raise InputPreparationError(message, details)


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
    if not fasta:
        fail(
            "No genome FASTA found for nf-core acceptance data.",
            expected_root=str(genome_root),
            env_override="CODEX_OMICS_FASTA",
            patterns=["*.fa", "*.fasta"],
        )
    if not gtf:
        fail(
            "No genome GTF found for nf-core acceptance data.",
            expected_root=str(genome_root),
            env_override="CODEX_OMICS_GTF",
            patterns=["*.gtf"],
        )
    fasta_path = Path(fasta).resolve()
    gtf_path = Path(gtf).resolve()
    if not fasta_path.exists():
        fail("Genome FASTA path does not exist.", path=str(fasta_path), env_override="CODEX_OMICS_FASTA")
    if not gtf_path.exists():
        fail("Genome GTF path does not exist.", path=str(gtf_path), env_override="CODEX_OMICS_GTF")
    return {"fasta": str(fasta_path), "gtf": str(gtf_path)}


def first_existing(root: Path, patterns: list[str]) -> Path | None:
    for pattern in patterns:
        matches = sorted(root.rglob(pattern)) if root.exists() else []
        if matches:
            return matches[0]
    return None


def fastq_mate(path: Path) -> Path | None:
    name = path.name
    replacements = [
        (r"_R1(_\d+)?\.(fastq|fq)\.gz$", r"_R2\1.\2.gz"),
        (r"_1\.(fastq|fq)\.gz$", r"_2.\1.gz"),
    ]
    for pattern, replacement in replacements:
        if re.search(pattern, name):
            return path.with_name(re.sub(pattern, replacement, name))
    return None


def sample_name_from_r1(path: Path) -> str:
    name = path.name
    for pattern in [r"_R1(_\d+)?\.(fastq|fq)\.gz$", r"_1\.(fastq|fq)\.gz$"]:
        name = re.sub(pattern, "", name)
    return name


def find_fastq_pairs(root: Path) -> tuple[list[tuple[str, Path, Path]], list[Path]]:
    if not root.exists():
        fail("FASTQ input directory does not exist.", expected_root=str(root))
    pairs: list[tuple[str, Path, Path]] = []
    unpaired: list[Path] = []
    fastqs = sorted(
        item
        for item in root.rglob("*")
        if item.is_file() and "".join(item.suffixes).lower() in {".fastq.gz", ".fq.gz"}
    )
    for r1 in fastqs:
        mate = fastq_mate(r1)
        if not mate:
            continue
        if mate.exists():
            pairs.append((sample_name_from_r1(r1), r1, mate))
        else:
            unpaired.append(r1)
    return pairs, unpaired


def prepare_rna() -> dict[str, Any]:
    out = RESULT_DIR / "bulk_rna"
    subset_dir = out / "subset_fastq"
    rows = []
    pairs, unpaired = find_fastq_pairs(DATA_DIR / "nf-core/rna")
    if not pairs:
        fail(
            "No paired RNA FASTQ files were found.",
            expected_root=str(DATA_DIR / "nf-core/rna"),
            supported_patterns=["*_1.fq.gz", "*_1.fastq.gz", "*_R1.fq.gz", "*_R1.fastq.gz", "*_R1_001.fastq.gz"],
            unpaired=[str(path) for path in unpaired[:10]],
        )
    genome = genome_paths()
    for sample, r1, r2 in pairs:
        dst1 = subset_dir / r1.name
        dst2 = subset_dir / r2.name
        subset_fastq(r1, dst1)
        subset_fastq(r2, dst2)
        rows.append({"sample": sample, "fastq_1": str(dst1), "fastq_2": str(dst2), "strandedness": "auto"})
    sheet = out / "samplesheet.csv"
    write_csv(sheet, ["sample", "fastq_1", "fastq_2", "strandedness"], rows)
    return write_summary(out, {"project": "bulk_rna", "reads_per_fastq": READS_PER_FASTQ, "samples": len(rows), "samplesheet": str(sheet), **genome})


def prepare_atac() -> dict[str, Any]:
    out = RESULT_DIR / "atac"
    subset_dir = out / "subset_fastq"
    rows = []
    pairs, unpaired = find_fastq_pairs(DATA_DIR / "nf-core/atac")
    if not pairs:
        fail(
            "No paired ATAC FASTQ files were found.",
            expected_root=str(DATA_DIR / "nf-core/atac"),
            supported_patterns=["*_1.fq.gz", "*_1.fastq.gz", "*_R1.fq.gz", "*_R1.fastq.gz", "*_R1_001.fastq.gz"],
            unpaired=[str(path) for path in unpaired[:10]],
        )
    genome = genome_paths()
    for sample, r1, r2 in pairs:
        dst1 = subset_dir / r1.name
        dst2 = subset_dir / r2.name
        subset_fastq(r1, dst1)
        subset_fastq(r2, dst2)
        rows.append({"sample": sample, "fastq_1": str(dst1), "fastq_2": str(dst2), "replicate": "1"})
    sheet = out / "samplesheet.csv"
    write_csv(sheet, ["sample", "fastq_1", "fastq_2", "replicate"], rows)
    return write_summary(out, {"project": "atac", "reads_per_fastq": READS_PER_FASTQ, "samples": len(rows), "samplesheet": str(sheet), **genome})


def prepare_scvi() -> dict[str, Any]:
    import anndata as ad

    source = Path(os.environ.get("CODEX_OMICS_SCVI_H5AD", DATA_DIR / "scvi/lung_atlas_preprocessed.h5ad")).resolve()
    if not source.exists():
        fail("No scVI h5ad input found.", expected_path=str(source), env_override="CODEX_OMICS_SCVI_H5AD")
    out = RESULT_DIR / "scvi"
    out.mkdir(parents=True, exist_ok=True)
    subset = out / "scvi_subset.h5ad"
    n_obs = int(os.environ.get("CODEX_OMICS_SCVI_N_OBS", "3000"))
    if not subset.exists():
        adata = ad.read_h5ad(source)
        adata[: min(n_obs, adata.n_obs), :].copy().write_h5ad(subset)
    adata = ad.read_h5ad(subset, backed="r")
    try:
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
    finally:
        adata.file.close()


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
    try:
        if args.project in {"bulk_rna", "all"}:
            result["bulk_rna"] = prepare_rna()
        if args.project in {"atac", "all"}:
            result["atac"] = prepare_atac()
        if args.project in {"scvi", "all"}:
            result["scvi"] = prepare_scvi()
        print(json.dumps(result, indent=2, default=str))
    except InputPreparationError as exc:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "error_type": "InputPreparationFailed",
                    "message": str(exc),
                    "details": exc.details,
                },
                indent=2,
                default=str,
            ),
            file=sys.stderr,
        )
        raise SystemExit(2)


if __name__ == "__main__":
    main()
