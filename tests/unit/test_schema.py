from __future__ import annotations

from omics_codex.common.io import load_yaml_or_json
from omics_codex.common.schema import validate_payload


def test_example_run_spec_validates() -> None:
    payload = load_yaml_or_json("examples/nfcore_rnaseq/omics_run_spec.yaml")
    assert validate_payload(payload, "omics_run_spec") == []
