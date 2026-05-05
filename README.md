## Benchmark Overview

This repository generates STA benchmark models and then evaluates them with simulation-based methods. The generated benchmark set is organized as a small matrix so the paper can compare how Restart and Monte Carlo behave under different structural and timing conditions.

### Input Matrix

The generator accepts these inputs:

| Parameter | Meaning | Typical values used in the matrix |
|---|---|---|
| `num_states` | Total locations in the automaton | `12`, `100`, `400` |
| `num_clocks` | Number of clocks in the model | `1`, `4`, `16` |
| `branching_factor` | Average outgoing branching | `1.0`, `1.5`, `2.5` |
| `max_time_bound` | Time horizon for the property | `10`, `30`, `100` |
| `rare_event_probability` | Failure probability at gateway transitions | `1e-2`, `1e-3`, `1e-4`, `1e-5` |
| `seed` | Random seed for topology variation | `10-29` depending on family |

The matrix is grouped into four families:

| Family | Varies | What it tells you |
|---|---|---|
| Structural | `num_states`, `branching_factor` | How the importance function behaves on small vs large and sparse vs highly branched topologies |
| Timing | `num_clocks`, `max_time_bound` | How sensitive the method is to clock pressure and short deadlines |
| Rarity | `rare_event_probability` | How the estimator behaves as the failure event becomes harder to observe |
| Variability | `seed` | How much results change across different random topologies with the same parameters |

### Output Data Structure

The helper script `scripts/generateAndManifest.py` writes a CSV manifest. Each row corresponds to one generated benchmark configuration.

| Column | Meaning |
|---|---|
| `config_id` | Short identifier for the configuration |
| `topology_family` | One of `structural`, `timing`, `rarity`, `variability` |
| `num_states` | Model size used for generation |
| `num_clocks` | Clock count used for generation |
| `branching_factor` | Branching value used for generation |
| `max_time_bound` | Time bound used for generation |
| `rare_event_probability` | Failure probability used for generation |
| `seed` | RNG seed used for generation |
| `model_path` | Path to the generated `.jani` model |
| `method` | Placeholder for `MonteCarlo` or `Restart` |
| `n_samples` | Placeholder for number of trajectories |
| `n_failure_hits` | Placeholder for number of failures observed |
| `est_probability` | Placeholder for estimated failure probability |
| `std_error` | Placeholder for estimated standard error |
| `ci95_low` | Placeholder for lower 95% confidence bound |
| `ci95_high` | Placeholder for upper 95% confidence bound |
| `runtime_s` | Placeholder for runtime in seconds |
| `notes` | Free-text notes, such as `no-output-detected` |

### Example Run

```powershell
python scripts/generateAndManifest.py --manifest benchmarks/manifest.csv
```

Use `--write` if you want the script to actually write `.jani` files instead of running the generator in dry-run mode.

To update the Docker image after dependency changes:

```powershell
docker build --no-cache -t simulation-image .
```
