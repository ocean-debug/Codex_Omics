from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from ..common.errors import OmicsError


FASTQ_PATTERNS = [
    re.compile(r"(?P<sample>.+?)[._-]R?1(?:[._-]\d+)?\.f(?:ast)?q\.gz$", re.IGNORECASE),
    re.compile(r"(?P<sample>.+?)_1\.f(?:ast)?q\.gz$", re.IGNORECASE),
]


def discover_fastq_pairs(fastq_dir: str | Path) -> list[dict[str, str]]:
    root = Path(fastq_dir)
    if not root.exists():
        raise OmicsError("InputNotFound", f"FASTQ directory does not exist: {root}", "Check inputs.path.", "discover_fastq_pairs")
    records: list[dict[str, str]] = []
    for r1 in sorted(root.rglob("*")):
        if not r1.is_file() or not str(r1).lower().endswith((".fastq.gz", ".fq.gz")):
            continue
        sample = infer_sample_from_r1(r1.name)
        if not sample:
            continue
        candidates = [
            Path(str(r1).replace("_R1", "_R2").replace("_1.", "_2.")),
            Path(str(r1).replace(".R1", ".R2")),
        ]
        r2 = next((candidate for candidate in candidates if candidate.exists()), None)
        records.append({"sample": sample, "fastq_1": str(r1), "fastq_2": str(r2 or ""), "strandedness": "auto"})
    return records


def infer_sample_from_r1(filename: str) -> str | None:
    for pattern in FASTQ_PATTERNS:
        match = pattern.match(filename)
        if match:
            return match.group("sample")
    return None


def write_rnaseq_samplesheet(records: list[dict[str, Any]], path: str | Path) -> Path:
    return write_samplesheet(records, path, ["sample", "fastq_1", "fastq_2", "strandedness"], {"strandedness": "auto"})


def write_atacseq_samplesheet(records: list[dict[str, Any]], path: str | Path) -> Path:
    rows: list[dict[str, Any]] = []
    for record in records:
        row = dict(record)
        row.setdefault("replicate", "1")
        rows.append(row)
    return write_samplesheet(rows, path, ["sample", "fastq_1", "fastq_2", "replicate"], {"replicate": "1"})


def write_sarek_samplesheet(records: list[dict[str, Any]], path: str | Path) -> Path:
    rows: list[dict[str, Any]] = []
    for record in records:
        row = dict(record)
        row.setdefault("patient", record.get("sample", "patient1"))
        row.setdefault("sex", "NA")
        row.setdefault("status", "0")
        row.setdefault("lane", "1")
        rows.append(row)
    return write_samplesheet(rows, path, ["patient", "sex", "status", "sample", "lane", "fastq_1", "fastq_2"], {})


def write_samplesheet(records: list[dict[str, Any]], path: str | Path, fieldnames: list[str], defaults: dict[str, str]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow({name: record.get(name, defaults.get(name, "")) for name in fieldnames})
    return target


PIPELINE_SAMPLE_COLUMNS = {
    "rnaseq": ["sample", "fastq_1", "fastq_2", "strandedness"],
    "atacseq": ["sample", "fastq_1", "fastq_2", "replicate"],
    "sarek": ["patient", "sex", "status", "sample", "lane", "fastq_1", "fastq_2"],
}


def make_samplesheet(pipeline: str, input_path: str | Path, output: str | Path) -> dict[str, Any]:
    short = pipeline.replace("nf-core/", "").lower()
    if short not in PIPELINE_SAMPLE_COLUMNS:
        raise OmicsError(
            "UnsupportedPipelineAdapter",
            f"No samplesheet adapter is available for nf-core/{short}.",
            "Use rnaseq, sarek, or atacseq, or provide an input samplesheet manually.",
            "make_samplesheet",
        )
    records = discover_fastq_pairs(input_path)
    if not records:
        raise OmicsError(
            "NoFastqPairsDiscovered",
            f"No FASTQ R1 files were discovered under: {input_path}",
            "Check inputs.path or provide an existing samplesheet.",
            "make_samplesheet",
        )
    if short == "rnaseq":
        path = write_rnaseq_samplesheet(records, output)
    elif short == "atacseq":
        path = write_atacseq_samplesheet(records, output)
    else:
        path = write_sarek_samplesheet(records, output)
    errors = validate_samplesheet(path, PIPELINE_SAMPLE_COLUMNS[short])
    return {"pipeline": f"nf-core/{short}", "samplesheet": str(path), "records": len(records), "valid": not errors, "errors": errors}


def validate_samplesheet(path: str | Path, required_columns: list[str]) -> list[str]:
    source = Path(path)
    if not source.exists():
        return [f"Samplesheet does not exist: {source}"]
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
    return [f"Missing required column: {column}" for column in required_columns if column not in columns]


def required_columns_for_pipeline(pipeline: str) -> list[str]:
    return PIPELINE_SAMPLE_COLUMNS.get(pipeline.replace("nf-core/", "").lower(), [])
