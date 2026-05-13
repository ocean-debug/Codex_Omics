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

`envs/activate-nextflow.sh` exposes project-local Java/Nextflow and sets a
project-local Singularity cache. nf-core Singularity runs should use
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
omics-codex inspect-env --kind nfcore
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
force a fragile pip install of the GPU stack.

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
