# STA-ISPLIT using time

## Generate JANI benchmarks

Use `generateJaniBenchmarks.py` to build stochastic timed automata benchmark models in JANI format.

Basic example:

```powershell
.\venv\Scripts\python.exe generateJaniBenchmarks.py \
  --num_states 1000 \
  --num_clocks 8 \
  --branching_factor 2.5 \
  --max_time_bound 1000 \
  --rare_event_probability 0.01 \
  --seed 67
```

Write models to disk without changing the benchmark set:

```powershell
.\venv\Scripts\python.exe generateJaniBenchmarks.py \
  --num_states 1000 \
  --num_clocks 8 \
  --branching_factor 2.5 \
  --max_time_bound 1000 \
  --rare_event_probability 0.01 \
  --seed 67 \
  --output_dir models/benchmark/jani
```

Validate model generation without writing files:

```powershell
.\venv\Scripts\python.exe generateJaniBenchmarks.py \
  --num_states 1000 \
  --num_clocks 8 \
  --branching_factor 2.5 \
  --max_time_bound 1000 \
  --rare_event_probability 0.01 \
  --seed 67 \
  --dry_run
```

Optional safety checks:

```powershell
.\venv\Scripts\python.exe generateJaniBenchmarks.py \
  --num_states 1000 \
  --num_clocks 8 \
  --branching_factor 2.5 \
  --max_time_bound 1000 \
  --rare_event_probability 0.01 \
  --seed 67 \
  --dry_run \
  --determinism_check \
  --min_transition_prob 1e-12 \
  --escape_prob 0
```

Notes:
- `loc_0` is the failure location.
- `loc_{numStates - 1}` is the absorbing safe sink.
- The generator requires at least 7 states.

## Rebuild the Docker image

If you change `requirements.txt`, rebuild the image with:

```powershell
docker build --no-cache -t simulation-image .
```
