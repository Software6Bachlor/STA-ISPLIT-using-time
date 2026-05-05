"""Generate JANI benchmark models for the experiment matrix and write a manifest CSV.

By default this script runs the generator in dry-run mode (does not write .jani files).
Pass `--write` to actually write the files.

The execution of simulations and result collection is intentionally left as
placeholders; this script only generates models and writes the manifest that
downstream tools can consume.
"""
from __future__ import annotations

import csv
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "generateJaniBenchmarks.py"
DEFAULT_OUTPUT_DIR = ROOT / "models" / "benchmark" / "jani"
MANIFEST_DIR = ROOT / "benchmarks"
MANIFEST_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Job:
    config_id: str
    topologyFamily: str
    numStates: int
    numClocks: int
    branching_factor: float
    maxTimeBound: float
    rareEventProbability: float
    seed: int


def buildMatrix() -> List[Job]:
    jobs: List[Job] = []

    # Structural family: size x branching
    for ns in (12, 100, 400):
        for bf in (1.0, 2.5):
            for seed in range(10, 15):
                cid = f"S-n{ns}-b{str(bf).replace('.','p')}-s{seed}"
                jobs.append(Job(cid, "structural", ns, 4, bf, 30.0, 1e-3, seed))

    # Timing family: clocks x time bounds (use medium size)
    for ns in (1, 4, 16):
        for c in (10, 30, 100):
            for seed in range(15, 18):
                cid = f"S-n{ns}-b{str(c).replace('.','p')}-s{seed}"
                jobs.append(Job(cid, "structural", ns, c, 1.5, 30.0, 1e-3, seed))

    # Rarity family: vary rare event probability
    for rp in (1e-2, 1e-3, 1e-4, 1e-5):
        for seed in range(18, 21):
            cid = f"R-n100-r{str(rp).replace('e','e')}-s{seed}"
            jobs.append(Job(cid, "rarity", 100, 4, 1.5, 30.0, rp, seed))

    # Variability sampling: two representative configs with many seeds
    reps = [Job("V-chain", "variability", 100, 4, 1.0, 30.0, 1e-3, 20),
            Job("V-merge", "variability", 100, 4, 2.5, 30.0, 1e-3, 20)]
    for rep in reps:
        for seed in range(20, 30):
            cid = f"{rep.config_id}-s{seed}"
            jobs.append(Job(cid, rep.topologyFamily, rep.numStates, rep.numClocks, rep.branching_factor, rep.maxTimeBound, rep.rareEventProbability, seed))

    return jobs


MANIFEST_HEADER = [
    "config_id",
    "topology_family",
    "num_states",
    "num_clocks",
    "branching_factor",
    "max_time_bound",
    "rare_event_probability",
    "seed",
    "model_path",
    # Execution/results placeholders
    "method",
    "n_samples",
    "n_failure_hits",
    "est_probability",
    "std_error",
    "ci95_low",
    "ci95_high",
    "runtime_s",
    "notes",
]


def sanitizeToken(value: float) -> str:
    text = f"{value:.6g}"
    return text.replace("-", "m").replace(".", "p")


def callGenerator(job: Job, output_dir: Path, write_files: bool) -> List[Path]:
    cmd = [sys.executable, str(GENERATOR),
           "--num_states", str(job.numStates),
           "--num_clocks", str(job.numClocks),
           "--branching_factor", str(job.branching_factor),
           "--max_time_bound", str(job.maxTimeBound),
           "--rare_event_probability", str(job.rareEventProbability),
           "--seed", str(job.seed),
           "--output_dir", str(output_dir),
           "--model_prefix", "generated-sta"
           ]

    if not write_files:
        cmd.append("--dry_run")

    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("Generator failed for job:", job)
        print(result.stdout)
        print(result.stderr)
        raise SystemExit(result.returncode)

    # Parse stdout for written file names (formatSummaryRow prints the filename)
    paths: List[Path] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("[WROTE]") or line.startswith("[DRY-RUN]"):
            # Format: [WROTE] filename.jani | num_states=...
            try:
                name = line.split(" ")[1]
                candidate = output_dir / name
                paths.append(candidate)
            except Exception:
                continue

    return paths


def main(argv: List[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Generate JANI models for experiment matrix and write manifest CSV")
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_DIR / "manifest.csv")
    parser.add_argument("--write", action="store_true", help="Actually write .jani files (default: dry-run)")
    args = parser.parse_args(argv)

    jobs = buildMatrix()

    manifestPath: Path = args.manifest
    manifestPath.parent.mkdir(parents=True, exist_ok=True)

    with manifestPath.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=MANIFEST_HEADER)
        writer.writeheader()

        for job in jobs:
            try:
                paths = callGenerator(job, args.output_dir, args.write)
            except SystemExit as e:
                print(f"Skipping job due to generator error: {job.config_id}")
                continue

            # If generator produced multiple models (should be one per job), write one row per file
            if not paths:
                # No file detected; still write a manifest row with empty model_path to keep trace
                writer.writerow({
                    "config_id": job.config_id,
                    "topology_family": job.topologyFamily,
                    "num_states": job.numStates,
                    "num_clocks": job.numClocks,
                    "branching_factor": job.branching_factor,
                    "max_time_bound": job.maxTimeBound,
                    "rare_event_probability": job.rareEventProbability,
                    "seed": job.seed,
                    "model_path": "",
                    # placeholders left intentionally empty
                    "method": "",
                    "n_samples": "",
                    "n_failure_hits": "",
                    "est_probability": "",
                    "std_error": "",
                    "ci95_low": "",
                    "ci95_high": "",
                    "runtime_s": "",
                    "notes": "no-output-detected",
                })
            else:
                for p in paths:
                    writer.writerow({
                        "config_id": job.config_id,
                        "topology_family": job.topologyFamily,
                        "num_states": job.numStates,
                        "num_clocks": job.numClocks,
                        "branching_factor": job.branching_factor,
                        "max_time_bound": job.maxTimeBound,
                        "rare_event_probability": job.rareEventProbability,
                        "seed": job.seed,
                        "model_path": str(p),
                        # placeholders left intentionally empty for later execution/results
                        "method": "",
                        "n_samples": "",
                        "n_failure_hits": "",
                        "est_probability": "",
                        "std_error": "",
                        "ci95_low": "",
                        "ci95_high": "",
                        "runtime_s": "",
                        "notes": "",
                    })

    print(f"Wrote manifest to {manifestPath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
