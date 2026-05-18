from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


RIBOSEQ_SAMPLE_TYPES = {"riboseq", "rnaseq", "tiseq"}
RIBOSEQ_CORE_FIELDS = ["sample", "fastq_1", "fastq_2", "strandedness", "type"]
SCRNASEQ_CORE_FIELDS = ["sample", "fastq_1", "fastq_2"]
SPATIALVI_RAW_FIELDS = ["sample", "fastq_dir", "image", "cytaimage", "colorizedimage", "darkimage", "slide", "area", "manual_alignment", "slidefile"]
SPATIALVI_PROCESSED_FIELDS = ["sample", "spaceranger_dir"]
SPATIALVI_IMAGE_FIELDS = {"image", "cytaimage", "colorizedimage", "darkimage"}

PATTERNS = [
    re.compile(r"(?P<sample>.+?)[._-]R?1(?:[._-]\d+)?\.f(?:ast)?q\.gz$", re.IGNORECASE),
    re.compile(r"(?P<sample>.+?)_1\.f(?:ast)?q\.gz$", re.IGNORECASE),
]


def infer_sample(filename: str) -> str | None:
    for pattern in PATTERNS:
        match = pattern.match(filename)
        if match:
            return match.group("sample")
    return None


def discover_pairs(root: Path) -> list[dict[str, str]]:
    records = []
    for r1 in sorted(root.rglob("*")):
        if not r1.is_file() or not r1.name.lower().endswith((".fastq.gz", ".fq.gz")):
            continue
        sample = infer_sample(r1.name)
        if not sample:
            continue
        candidates = [
            Path(str(r1).replace("_R1", "_R2").replace("_1.", "_2.")),
            Path(str(r1).replace(".R1", ".R2")),
            Path(str(r1).replace("-R1", "-R2")),
        ]
        r2 = next((candidate for candidate in candidates if candidate != r1 and candidate.exists()), None)
        records.append({"sample": sample, "fastq_1": str(r1), "fastq_2": str(r2 or ""), "strandedness": "auto", "replicate": "1", "paired": bool(r2)})
    return records


def short_pipeline(pipeline: str) -> str:
    return pipeline.replace("nf-core/", "").lower()


def columns_for(pipeline: str, metadata_fields: list[str] | None = None, spatial_mode: str = "auto") -> list[str]:
    short = pipeline.replace("nf-core/", "").lower()
    if short == "rnaseq":
        return ["sample", "fastq_1", "fastq_2", "strandedness"]
    if short == "scrnaseq":
        fields = list(SCRNASEQ_CORE_FIELDS)
        for field in metadata_fields or []:
            if field not in fields:
                fields.append(field)
        return fields
    if short == "atacseq":
        return ["sample", "fastq_1", "fastq_2", "replicate"]
    if short == "sarek":
        return ["patient", "sex", "status", "sample", "lane", "fastq_1", "fastq_2"]
    if short == "riboseq":
        fields = list(RIBOSEQ_CORE_FIELDS)
        for field in metadata_fields or []:
            if field not in fields:
                fields.append(field)
        return fields
    if short == "spatialvi":
        fields = list(SPATIALVI_PROCESSED_FIELDS if spatial_mode == "processed" else SPATIALVI_RAW_FIELDS)
        for field in metadata_fields or []:
            if field not in fields:
                fields.append(field)
        return fields
    raise ValueError("Supported pipelines: rnaseq, scrnaseq, atacseq, sarek, riboseq, spatialvi")


def read_metadata(path: Path | None) -> tuple[dict[str, dict[str, str]], list[str]]:
    if path is None:
        return {}, []
    if not path.exists():
        raise ValueError(f"Metadata CSV does not exist: {path}")
    try:
        handle = path.open(newline="", encoding="utf-8-sig")
    except OSError as exc:
        raise ValueError(f"Metadata CSV could not be read: {path}") from exc
    with handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "sample" not in reader.fieldnames:
            raise ValueError("Metadata CSV must include a 'sample' column.")
        rows = {}
        for row in reader:
            sample = row.get("sample", "")
            if sample:
                rows[sample] = {key: value for key, value in row.items() if key is not None and value is not None}
        return rows, [field for field in reader.fieldnames if field != "sample"]


def resolve_spatial_mode(requested: str, metadata_fields: list[str]) -> str:
    if requested != "auto":
        return requested
    if "spaceranger_dir" in metadata_fields and not any(field in metadata_fields for field in ("fastq_dir", *SPATIALVI_IMAGE_FIELDS)):
        return "processed"
    return "raw"


def spatial_records(metadata: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    return [{"sample": sample, **row} for sample, row in metadata.items()]


def validate_spatialvi(metadata: dict[str, dict[str, str]], metadata_fields: list[str], spatial_mode: str) -> list[dict[str, str]]:
    errors = []
    if not metadata:
        return [{"error_type": "InvalidMetadata", "message": "spatialvi requires --metadata with at least one sample row."}]
    if spatial_mode == "processed":
        if "spaceranger_dir" not in metadata_fields:
            errors.append({"error_type": "InvalidMetadata", "message": "spatialvi processed mode requires a spaceranger_dir column."})
        return errors
    if "fastq_dir" not in metadata_fields:
        errors.append({"error_type": "InvalidMetadata", "message": "spatialvi raw mode requires a fastq_dir column."})
    for sample, row in metadata.items():
        if not any(row.get(field, "").strip() for field in SPATIALVI_IMAGE_FIELDS):
            errors.append({"error_type": "InvalidMetadata", "message": f"spatialvi raw sample {sample} must include at least one of image, cytaimage, colorizedimage, or darkimage."})
    return errors


def write_sheet(pipeline: str, records: list[dict[str, Any]], output: Path, sample_type: str = "riboseq", metadata: dict[str, dict[str, str]] | None = None, metadata_fields: list[str] | None = None, spatial_mode: str = "auto") -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = columns_for(pipeline, metadata_fields, spatial_mode)
    short = short_pipeline(pipeline)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            row = dict(record)
            if short in {"scrnaseq", "spatialvi"}:
                row.update((metadata or {}).get(record["sample"], {}))
                row["sample"] = record["sample"]
            if short == "scrnaseq":
                row["fastq_1"] = record["fastq_1"]
                row["fastq_2"] = record["fastq_2"]
            if short == "riboseq":
                row["type"] = sample_type
                row.update((metadata or {}).get(record["sample"], {}))
                row["sample"] = record["sample"]
                row["fastq_1"] = record["fastq_1"]
                row["fastq_2"] = record["fastq_2"]
                row.setdefault("strandedness", "auto")
                row.setdefault("type", sample_type)
            row.setdefault("patient", record["sample"])
            row.setdefault("sex", "NA")
            row.setdefault("status", "0")
            row.setdefault("lane", "1")
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an nf-core samplesheet from FASTQ files.")
    parser.add_argument("--pipeline", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--config")
    parser.add_argument("--sample-type", choices=sorted(RIBOSEQ_SAMPLE_TYPES), default="riboseq", help="Default nf-core/riboseq sample type when --pipeline riboseq.")
    parser.add_argument("--metadata", help="Optional CSV keyed by sample. Extra columns are merged into generated rows.")
    parser.add_argument("--spatial-mode", choices=["auto", "raw", "processed"], default="auto", help="nf-core/spatialvi samplesheet mode. Auto infers raw vs processed from metadata columns.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved", default="false")
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    records = discover_pairs(Path(args.input))
    errors = []
    metadata = {}
    metadata_fields: list[str] = []
    try:
        metadata, metadata_fields = read_metadata(Path(args.metadata) if args.metadata else None)
    except ValueError as exc:
        errors.append({"error_type": "InvalidMetadata", "message": str(exc)})
    if short_pipeline(args.pipeline) == "riboseq":
        invalid_types = sorted({row.get("type", "") for row in metadata.values() if row.get("type", "") and row.get("type", "") not in RIBOSEQ_SAMPLE_TYPES})
        if invalid_types:
            errors.append({"error_type": "InvalidSampleType", "message": f"Unsupported riboseq sample type(s): {', '.join(invalid_types)}"})
    spatial_mode = resolve_spatial_mode(args.spatial_mode, metadata_fields)
    if short_pipeline(args.pipeline) == "spatialvi":
        records = spatial_records(metadata)
        errors.extend(validate_spatialvi(metadata, metadata_fields, spatial_mode))
    if not Path(args.input).exists():
        errors.append({"error_type": "MissingInputDirectory", "message": f"Input path does not exist: {args.input}"})
    if short_pipeline(args.pipeline) != "spatialvi" and not records:
        errors.append({"error_type": "NoFastqPairs", "message": "No R1 FASTQ files were detected."})
    if short_pipeline(args.pipeline) not in {"riboseq", "spatialvi"} and any(not record.get("paired") for record in records):
        errors.append({"error_type": "MissingFastqMate", "message": "At least one R1 FASTQ did not have a detected R2 mate."})
    write_sheet(args.pipeline, records, Path(args.out), sample_type=args.sample_type, metadata=metadata, metadata_fields=metadata_fields, spatial_mode=spatial_mode)
    print(json.dumps({"pipeline": args.pipeline, "samplesheet": args.out, "records": len(records), "valid": bool(records) and not errors, "metadata": {"path": args.metadata, "fields": metadata_fields}, "spatial_mode": spatial_mode if short_pipeline(args.pipeline) == "spatialvi" else None, "errors": errors}, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
