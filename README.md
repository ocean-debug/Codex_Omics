# Codex Omics Skills

Codex Omics Skills is a repo-local Codex plugin plus Python CLI for reproducible omics analysis. It provides:

- universal nf-core / Nextflow planning and command generation;
- single-cell RNA-seq QC with Scanpy/scverse conventions;
- scvi-tools model discovery, validation, and adapter-based training;
- structured run specs, manifests, reports, and tests.

The project is implemented locally in this repository. Validation is intentionally performed on the remote cluster only.

## Remote validation

All verification should run under:

```bash
cd /path/to/codex_omics
source .venv/bin/activate
```

Requested resource shape, adjusted for the target cluster:

```text
node: <gpu-node>
cores: <core-count>
```

Default validation commands:

```bash
python --version
python -m pip install -e ".[dev,nfcore,scverse]"
python -m pytest tests/smoke -q
python -m pytest tests/unit -q
python -m pytest tests/integration -q
omics-codex --help
omics-codex inspect-data --input examples/scrna_qc/synthetic.h5ad
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

Heavy tests are not part of the default validation path.

The remote UV `.venv` is expected to provide `scvi-tools`; the `scvi` extra is
kept empty so editable installs do not rebuild the GPU stack.

Heavy checks are opt-in:

```bash
RUN_HEAVY_OMICS=1 python -m pytest tests/heavy -q
```
