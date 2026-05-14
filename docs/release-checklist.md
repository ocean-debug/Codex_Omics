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
git grep -n -I -E "192[.]168[.]|/[h]ome/[A-Za-z0-9._-]+|((pass(word|wd)|[s]ecret|[t]oken|api[_-]?[k]ey|private[_-]?[k]ey)[[:space:]_A-Za-z-]*[:=][[:space:]]*['\"][^'\"]+)" HEAD -- . ':!*.h5ad' ':!*.h5mu'
```

The scan should return no private paths, hosts, or credentials. Generic code terms such as `token` are acceptable only when they are not values or secrets.

## Default Validation

Run default validation in the remote project environment:

```bash
source .venv/bin/activate
source envs/activate-nextflow.sh
python -m pytest tests/smoke -q
python -m pytest tests/unit -q
python -m pytest tests/integration -q
omics-codex inspect-env --kind nfcore
omics-codex inspect-env --kind scvi
omics-codex doctor --json
omics-codex route --prompt "Create a bulk RNA workflow" --input examples --outdir results/route_demo --out results/route_demo.workflow.json
omics-codex template list
omics-codex template create --name scrna-qc-scvi --input examples --outdir results/template_scrna_scvi --out results/template_scrna_scvi.workflow.json
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

Current v0.3 acceptance expectations:

- scVI family light training is the primary heavy GPU check.
- `inspect-env --kind scvi` must report `scvi-tools`, PyTorch CUDA availability, visible GPU metadata, and actionable UV install hints when components are missing.
- nf-core real execution depends on Java 17+, Nextflow, nf-core, and Singularity or Apptainer.
- `inspect-env --kind nfcore` must report Java, Nextflow, nf-core, git, container backend, cache environment, blockers, warnings, and install hints.
- nf-core Singularity runs use `envs/nextflow-singularity.config` and the project-local `NXF_SINGULARITY_CACHEDIR`.
- The default nf-core heavy test uses the rnaseq test profile with optional QC, alignment, pseudo-alignment, and quantification-merge steps skipped, keeping MultiQC, to avoid release gating on slow optional container downloads.
- If nf-core preflight passes, `test_nfcore_rnaseq_profile.py` must complete rather than return `blocked`.
- If nf-core times out or fails after preflight, record the command, log paths, and smallest environment or pipeline fix.

## Real-data Acceptance

When site test data is available, run the non-committed acceptance templates:

```bash
export CODEX_OMICS_DATA_DIR=/path/to/data/test
export CODEX_OMICS_RESULT_DIR=/path/to/data/test/result
export CODEX_OMICS_NFCORE_PROFILE=singularity
export CODEX_OMICS_MAX_CPUS=12
export CODEX_OMICS_MAX_MEMORY=48.GB
bash scripts/acceptance/run_all.sh
```

Record statuses from `summary.json`. scVI and bulk RNA remain the active real-data gates. ATAC command/spec/report compatibility should remain intact, but ATAC true execution is not part of the routine v0.3 release gate unless explicitly requested.

## GitHub Release

- Update `CHANGELOG.md`.
- Confirm `pyproject.toml` version matches the release tag.
- Build and check the plugin package:

  ```bash
  python scripts/release/build_plugin_package.py
  python scripts/release/check_release.py --plugin-package dist/codex-omics-plugin-v0.4.0.zip
  ```

- Push `main`.
- Create a GitHub release with validation results and known limitations.
