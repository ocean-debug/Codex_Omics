# Remote Validation

Run all checks on the remote cluster, not on the local Windows checkout.

Remote folder:

```text
<remote-workdir>/codex_omics/
```

Environment:

```bash
source .venv/bin/activate
source envs/activate-nextflow.sh
```

`envs/activate-nextflow.sh` exposes project-local Java/Nextflow, sets
`NXF_SYNTAX_PARSER=v1` for compatibility with older nf-core pipeline config
syntax, and sets project-local Singularity/Apptainer caches. nf-core
Singularity/Apptainer runs should use
`envs/nextflow-singularity.config` so image pulls have a longer timeout and
report/timeline files can be overwritten during resumed validation.

Resource request:

```text
node=<gpu-node>
cores=<core-count>
```

Default commands:

```bash
python --version
python -m pip install -e ".[dev,nfcore,scverse]"
python -m pytest tests/smoke -q
python -m pytest tests/unit -q
python -m pytest tests/integration -q
omics-codex --help
omics-codex doctor --json
omics-codex inspect-env --kind all
omics-codex inspect-env --kind nfcore
omics-codex inspect-env --kind scvi
omics-codex route --prompt "Create a bulk RNA workflow" --input examples --outdir results/route_demo --out results/route_demo.workflow.json
omics-codex template list
omics-codex template create --name scrna-qc-scvi --input examples --outdir results/template_scrna_scvi --out results/template_scrna_scvi.workflow.json
omics-codex validate --config examples/scrna_qc/omics_run_spec.yaml
omics-codex nfcore build-command --config examples/nfcore_rnaseq/omics_run_spec.yaml
omics-codex scrna-qc run --config examples/scrna_qc/omics_run_spec.yaml
omics-codex scvi list-models
omics-codex scvi validate --config examples/scvi/omics_run_spec.yaml
omics-codex scvi train --config examples/scvi/omics_run_spec.yaml
omics-codex workflow plan --config examples/workflows/scrna_qc_scvi.yaml
omics-codex workflow run --config examples/workflows/scrna_qc_scvi.yaml
omics-codex workflow run --config examples/workflows/scrna_qc_scvi.approved.yaml
omics-codex workflow status --config examples/workflows/scrna_qc_scvi.approved.yaml
omics-codex report --manifest results/workflows/scrna_qc_scvi/workflow_manifest.json
```

`scvi-tools` is expected to be present in the project-local UV `.venv`. The
`pyproject.toml` `scvi` extra intentionally remains empty so validation does not
force a fragile pip install of the GPU stack. `inspect-env --kind scvi` reports
whether PyTorch sees CUDA, which GPU model is visible, and whether scVI/scverse
packages are importable.

Heavy checks are opt-in:

```bash
source .venv/bin/activate
source envs/activate-nextflow.sh
RUN_HEAVY_OMICS=1 python -m pytest tests/heavy -q
```

When Java, Nextflow, nf-core, and a container backend are available, the
nf-core heavy test is expected to complete instead of returning `blocked`. The
default heavy spec skips optional rnaseq QC, alignment, pseudo-alignment, and
quantification-merge modules while keeping MultiQC, so the check validates real
Nextflow/container execution without depending on slow site-specific downloads
for every optional image.

## Real-data acceptance templates

For site-provided test data, use the script templates without committing data or
results:

```bash
export CODEX_OMICS_DATA_DIR=/path/to/data/test
export CODEX_OMICS_RESULT_DIR=/path/to/data/test/result
export CODEX_OMICS_NFCORE_PROFILE=singularity
export CODEX_OMICS_MAX_CPUS=12
export CODEX_OMICS_MAX_MEMORY=48.GB
bash scripts/acceptance/run_all.sh
```

For ATAC, the script infers `read_length` from the first FASTQ by default. Set
`CODEX_OMICS_ATAC_READ_LENGTH` or `CODEX_OMICS_ATAC_MACS_GSIZE` to override the
auto-detected MACS2 genome-size input strategy. ATAC is no longer a default
blocker for v0.3 usability work; keep its command/spec/report path working, but
do not rerun ATAC as a routine validation unless explicitly requested.

The current reference run completed real scVI subset training and bulk RNA
`nf-core/rnaseq` subset execution. ATAC command/spec compatibility is assumed
for the current v0.3 path and should be revisited only when ATAC is back in
scope.
