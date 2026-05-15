from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from common.io import ensure_outdir, write_text  # noqa: E402
from common.manifest import base_manifest, write_manifest  # noqa: E402
from common.report import write_report  # noqa: E402


def build_command(args: argparse.Namespace) -> str:
    pipeline = args.pipeline.replace("nf-core/", "")
    command = ["nextflow", "run", f"nf-core/{pipeline}", "-profile", args.profile]
    if args.revision:
        command.extend(["-r", args.revision])
    command.extend(["--input", args.input, "--outdir", args.outdir])
    if args.genome:
        command.extend(["--genome", args.genome])
    if args.max_cpus:
        command.extend(["--max_cpus", str(args.max_cpus)])
    if args.max_memory:
        command.extend(["--max_memory", args.max_memory])
    if args.resume:
        command.append("-resume")
    return " ".join(shlex.quote(part) for part in command)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a safe Nextflow command without executing it.")
    parser.add_argument("--pipeline", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--config")
    parser.add_argument("--profile", default="singularity")
    parser.add_argument("--genome")
    parser.add_argument("--revision")
    parser.add_argument("--max-cpus", type=int)
    parser.add_argument("--max-memory")
    parser.add_argument("--resume", action="store_true", default=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--approved", default="false")
    args = parser.parse_args()
    outdir = ensure_outdir(args.outdir)
    command = build_command(args)
    write_text(outdir / "command.sh", command + "\n")
    manifest = base_manifest(
        skill="nextflow-development",
        status="planned",
        inputs={"samplesheet": args.input},
        outputs={"outdir": str(outdir), "command": str(outdir / "command.sh"), "manifest": str(outdir / "run_manifest.json"), "report": str(outdir / "report.md")},
        parameters={"pipeline": args.pipeline, "profile": args.profile, "genome": args.genome, "revision": args.revision},
        commands=[command],
    )
    manifest["plan"] = {"approval_required": True, "will_execute": False}
    write_manifest(outdir / "run_manifest.json", manifest)
    write_report(outdir / "report.md", manifest, title="Nextflow Workflow Plan")
    print(json.dumps({"command": command, "manifest": str(outdir / "run_manifest.json"), "report": str(outdir / "report.md")}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
