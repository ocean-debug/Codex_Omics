from __future__ import annotations

import argparse
import json
from pathlib import Path


def detect(path: Path) -> dict[str, object]:
    fastqs = [p for p in path.rglob("*") if p.is_file() and p.name.lower().endswith((".fastq.gz", ".fq.gz"))] if path.exists() else []
    references = [p for p in path.rglob("*") if p.is_file() and p.name.lower().endswith((".fa", ".fasta", ".gtf", ".gff", ".gff3"))] if path.exists() else []
    return {
        "input": str(path),
        "exists": path.exists(),
        "fastq_count": len(fastqs),
        "reference_count": len(references),
        "candidate_data_type": "fastq" if fastqs else "unknown",
        "candidate_workflows": ["rnaseq", "atacseq", "sarek"] if fastqs else [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect omics input data type for Nextflow planning.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--config")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved", default="false")
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    print(json.dumps(detect(Path(args.input)), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
