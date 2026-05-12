from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .common.errors import OmicsError
from .common.io import write_json, write_text


def create_omics_skill_template(name: str, outdir: str | Path) -> dict[str, Any]:
    slug = normalize_skill_name(name)
    root = Path(outdir) / slug
    if root.exists() and any(root.iterdir()):
        raise OmicsError("SkillTemplateExists", f"Skill template directory already exists: {root}", "Choose an empty output directory.", "create_skill_template")
    skill_dir = root
    tests_dir = root / "tests"
    examples_dir = root / "examples"
    schema_dir = root / "schemas"
    write_text(skill_dir / "SKILL.md", skill_markdown(slug))
    write_text(examples_dir / "omics_run_spec.yaml", example_spec(slug))
    write_json(schema_dir / f"{slug}.schema.json", schema_stub(slug))
    write_text(tests_dir / f"test_{slug.replace('-', '_')}.py", test_stub(slug))
    return {
        "status": "ok",
        "skill": slug,
        "root": str(root),
        "files": [
            str(skill_dir / "SKILL.md"),
            str(examples_dir / "omics_run_spec.yaml"),
            str(schema_dir / f"{slug}.schema.json"),
            str(tests_dir / f"test_{slug.replace('-', '_')}.py"),
        ],
    }


def normalize_skill_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not slug:
        raise OmicsError("InvalidSkillName", "Skill name must contain letters or digits.", "Use a concise lowercase skill name.", "normalize_skill_name")
    return slug[:63]


def skill_markdown(slug: str) -> str:
    return f"""---
name: {slug}
description: Run a reproducible omics workflow for {slug}, including input validation, execution planning, outputs, report, and run manifest. Use when users request {slug} analysis.
---

# {slug}

## Required workflow

1. Inspect inputs and confirm required metadata.
2. Validate `omics_run_spec.yaml`.
3. Plan commands and output paths before execution.
4. Run only when `execution.approved: true`.
5. Write `run_manifest.json`, `report.md`, and workflow-specific summaries.
"""


def example_spec(slug: str) -> str:
    return f"""run:
  name: {slug}_demo
  description: Example {slug} workflow.
  type: omics_report
  skill: omics-report
inputs:
  path: ./examples/{slug}/input
  type: unknown
execution:
  mode: command_only
  approved: false
outputs:
  outdir: ./results/{slug}
  report: ./results/{slug}/report.md
  manifest: ./results/{slug}/run_manifest.json
"""


def schema_stub(slug: str) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": f"{slug} run spec extension",
        "type": "object",
        "additionalProperties": True,
    }


def test_stub(slug: str) -> str:
    return f"""from __future__ import annotations


def test_{slug.replace('-', '_')}_template_exists() -> None:
    assert "{slug}"
"""
