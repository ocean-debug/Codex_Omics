# nf-core samplesheets

Use this reference when a workflow requires a CSV or TSV input table, when creating a samplesheet from FASTQ files, or when validating user-provided samplesheets.

## General rules

- Never invent columns when the pipeline schema or adapter does not define them.
- Prefer absolute paths for real data runs. Relative paths are acceptable in examples.
- Do not modify FASTQ, BAM, CRAM, or other input files.
- For paired-end FASTQ, preserve R1/R2 pairing and sample identity.
- Validate required columns before writing commands.

## Adapter levels

### Generic schema mode

Use for arbitrary nf-core pipelines:

1. Look for schema params such as `input`, `samplesheet`, or fields with CSV/TSV descriptions.
2. If the schema only says "input file" without columns, ask the user for the expected format or point them to the pipeline documentation.
3. Validate that the configured input path exists when running, or note that it is command-only if files are not present.

### Curated adapter mode

Use when the pipeline is one of the supported high-priority adapters:

- `rnaseq`
- `sarek`
- `atacseq`

Current minimal `rnaseq` columns:

```csv
sample,fastq_1,fastq_2,strandedness
SAMPLE1,/path/SAMPLE1_R1.fastq.gz,/path/SAMPLE1_R2.fastq.gz,auto
```

Recommended `sarek` columns:

```csv
patient,sample,lane,fastq_1,fastq_2,status
patient1,tumor,L001,/path/tumor_R1.fastq.gz,/path/tumor_R2.fastq.gz,1
patient1,normal,L001,/path/normal_R1.fastq.gz,/path/normal_R2.fastq.gz,0
```

Recommended `atacseq` columns:

```csv
sample,fastq_1,fastq_2,replicate
CONTROL,/path/ctrl_R1.fastq.gz,/path/ctrl_R2.fastq.gz,1
```

## FASTQ discovery

- Recognize `*_R1.fastq.gz`, `*_R2.fastq.gz`, `*_1.fq.gz`, and `*_2.fq.gz`.
- Keep lanes separate unless the selected pipeline explicitly expects merged samples.
- If a mate is missing, keep command generation blocked until the user confirms single-end mode.

## Validation checklist

- Required columns exist.
- File paths exist for execution mode.
- Paired-end rows have both mates.
- `strandedness` is explicit for RNA-seq or set to `auto`.
- Tumor/normal status is explicit for variant workflows.
