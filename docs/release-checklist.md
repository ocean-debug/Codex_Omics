# Release Checklist

Use this checklist before tagging a public release.

## Repository Hygiene

- Confirm the working tree is clean:

  ```bash
  git status --short --branch
  ```

- Confirm only project files are tracked:

  ```bash
  git ls-tree -r --name-only HEAD
  ```

- Check that generated data, result folders, virtual environments, remote profiles, and app-local state are ignored.

## Sensitive Information

Run a repository scan before publishing:

```bash
git grep -n -I -E "<private-user>|<private-host>|<credential-pattern>" HEAD -- . ':!*.h5ad' ':!*.h5mu'
```

The scan should return no matches. If a match is intentional documentation, replace it with a placeholder before release.

## Default Validation

Run default validation in the remote project environment:

```bash
source .venv/bin/activate
source envs/activate-nextflow.sh
python -m pytest tests/smoke -q
python -m pytest tests/unit -q
python -m pytest tests/integration -q
omics-codex inspect-env --kind nfcore
omics-codex workflow plan --config examples/workflows/scrna_qc_scvi.yaml
```

Record the node, environment activation command, and pass/fail summary in the release notes.

## Heavy Validation

Heavy tests are optional and should be recorded separately:

```bash
source .venv/bin/activate
source envs/activate-nextflow.sh
RUN_HEAVY_OMICS=1 python -m pytest tests/heavy/test_scvi_family_training.py -q
RUN_HEAVY_OMICS=1 python -m pytest tests/heavy/test_nfcore_rnaseq_profile.py -q
```

Current v0.2 acceptance expectations:

- scVI family light training is the primary heavy GPU check.
- nf-core real execution depends on Java 17+, Nextflow, nf-core, and Singularity or Apptainer.
- nf-core Singularity runs use `envs/nextflow-singularity.config` and the project-local `NXF_SINGULARITY_CACHEDIR`.
- The default nf-core heavy test uses the rnaseq test profile with optional QC, alignment, pseudo-alignment, and quantification-merge steps skipped, keeping MultiQC, to avoid release gating on slow optional container downloads.
- If nf-core preflight passes, `test_nfcore_rnaseq_profile.py` must complete rather than return `blocked`.
- If nf-core times out or fails after preflight, record the command, log paths, and smallest environment or pipeline fix.

## GitHub Release

- Update `CHANGELOG.md`.
- Confirm `pyproject.toml` version matches the release tag.
- Push `main`.
- Create a GitHub release with validation results and known limitations.
