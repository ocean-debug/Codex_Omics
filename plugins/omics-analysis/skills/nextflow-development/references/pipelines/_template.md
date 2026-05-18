# nf-core/<pipeline>

Use this reference for planning nf-core/<pipeline> runs with revision
`<version-or-revision>`. Link the official usage and output pages here.

## Samplesheet

The required leading columns are:

```csv
<required,column,names>
<example,row,values>
```

Generate the samplesheet:

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py --pipeline <pipeline> --input <input_dir> --out samplesheet.csv
```

List any required metadata columns, optional metadata columns, and validation
rules. State whether single-end FASTQ, paired-end FASTQ, directories, or
preprocessed outputs are supported.

## Command Construction

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py --pipeline <pipeline> --revision <version-or-revision> --input samplesheet.csv --outdir results/<pipeline> --profile singularity --dry-run --json
```

Document common explicit flags and when contributors should use
`--extra-param KEY=VALUE` for lower-frequency official nf-core parameters.

## Key Outputs

- Primary result directory or report.
- QC and MultiQC outputs.
- Pipeline info, trace, timeline, command, manifest, and report files.

## Review Points

- Confirm samplesheet columns and metadata before execution.
- Confirm references and tool-specific indexes before approved execution.
- Confirm whether the workflow should be resumed with `-resume` after failure.

## Troubleshooting Notes

- Known parameter validation failures.
- Known annotation/reference caveats.
- Known container or cache considerations.
