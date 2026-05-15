from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


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
        r2 = next((candidate for candidate in candidates if candidate.exists()), None)
        records.append({"sample": sample, "fastq_1": str(r1), "fastq_2": str(r2 or ""), "strandedness": "auto", "replicate": "1", "paired": bool(r2)})
    return records


def columns_for(pipeline: str) -> list[str]:
    short = pipeline.replace("nf-core/", "").lower()
    if short == "rnaseq":
        return ["sample", "fastq_1", "fastq_2", "strandedness"]
    if short == "atacseq":
        return ["sample", "fastq_1", "fastq_2", "replicate"]
    if short == "sarek":
        return ["patient", "sex", "status", "sample", "lane", "fastq_1", "fastq_2"]
    raise ValueError("Supported pipelines: rnaseq, atacseq, sarek")


def write_sheet(pipeline: str, records: list[dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = columns_for(pipeline)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            row = dict(record)
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
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved", default="false")
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    records = discover_pairs(Path(args.input))
    errors = []
    if not Path(args.input).exists():
        errors.append({"error_type": "MissingInputDirectory", "message": f"Input path does not exist: {args.input}"})
    if not records:
        errors.append({"error_type": "NoFastqPairs", "message": "No R1 FASTQ files were detected."})
    if any(not record.get("paired") for record in records):
        errors.append({"error_type": "MissingFastqMate", "message": "At least one R1 FASTQ did not have a detected R2 mate."})
    write_sheet(args.pipeline, records, Path(args.out))
    print(json.dumps({"pipeline": args.pipeline, "samplesheet": args.out, "records": len(records), "valid": bool(records) and not errors, "errors": errors}, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
