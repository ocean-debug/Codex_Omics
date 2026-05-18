# nf-core/spatialvi

Use this reference for spatial transcriptomics and Visium planning with
nf-core/spatialvi `dev`. The `dev` revision can change, so record the generated
command and manifest before execution.

## Samplesheets

Raw Visium mode uses Space Ranger inputs and image metadata:

```csv
sample,fastq_dir,image,cytaimage,colorizedimage,darkimage,slide,area,manual_alignment,slidefile
visium1,/abs/path/fastq,/abs/path/tissue.jpg,,,,V19A01,A1,false,
```

Processed mode starts from completed Space Ranger outputs:

```csv
sample,spaceranger_dir
visium1,/abs/path/spaceranger/outs
```

Generate from metadata:

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py --pipeline spatialvi --input spatial_dir --out samplesheet.csv --metadata metadata.csv --spatial-mode auto
```

Raw rows require `fastq_dir` and at least one of `image`, `cytaimage`,
`colorizedimage`, or `darkimage`. Processed rows require `spaceranger_dir`.

## Command Construction

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py --pipeline spatialvi --input samplesheet.csv --outdir results/spatialvi --profile singularity --spaceranger-reference /refs/spaceranger --dry-run --json
```

Default revision is `dev`. Use `--spaceranger-probeset` for probe-based runs,
`--hd-bin-size` for Visium HD, and `--skip-integration` or `--skip-downstream`
when only upstream outputs are needed. Additional official parameters can be
passed as repeatable `--extra-param KEY=VALUE`.

## Key Outputs

- Space Ranger outputs when raw FASTQs are processed.
- SpatialVI integration and downstream analysis outputs unless skipped.
- QC, MultiQC, and pipeline information files.

## Review Points

- Confirm raw vs processed mode before generating the samplesheet.
- Check image paths, slide, area, and manual alignment metadata before execution.
- Do not install Space Ranger or references automatically; generate the plan and
  ask for approval before any environment changes.
