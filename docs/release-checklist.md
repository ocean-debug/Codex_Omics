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
python -m pytest tests/smoke -q
python -m pytest tests/unit -q
python -m pytest tests/integration -q
omics-codex workflow plan --config examples/workflows/scrna_qc_scvi.yaml
```

Record the node, environment activation command, and pass/fail summary in the release notes.

## Heavy Validation

Heavy tests are optional and should be recorded separately:

```bash
RUN_HEAVY_OMICS=1 python -m pytest tests/heavy/test_scvi_family_training.py -q
RUN_HEAVY_OMICS=1 python -m pytest tests/heavy/test_nfcore_rnaseq_profile.py -q
```

Current v0.1.0 expectations:

- scVI family light training is the primary heavy GPU check.
- nf-core real execution depends on site-provided Java 17+, Nextflow, nf-core, and Singularity or Apptainer.
- If nf-core cannot run because the environment is incomplete, the expected outcome is a `blocked` manifest with a clear preflight error.

## GitHub Release

- Update `CHANGELOG.md`.
- Confirm `pyproject.toml` version matches the release tag.
- Push `main`.
- Create a GitHub release with validation results and known limitations.
