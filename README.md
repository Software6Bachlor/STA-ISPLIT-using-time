# STA-ISPLIT using time

## Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running simulations

Simulations run inside Docker via `main.py`. The container mounts your project and a `results/` output directory automatically.

### Via Docker

```bash
python main.py \
  -m <memoryMb> \
  --method <mc|restart> \
  --model <path/to/model.jani> \
  --rareLocation <location_name> \
  --timeBound <float>             # required for --method mc
  --numTrials <int>               # default 1000, MC only
  --ifTimeLimit <float>           # optional: cap importance-function build time (seconds)
  --cpus <float>                  # optional: Docker CPU limit
```

Results are written as JSON to `results/`.

### Directly (no Docker, development only)

```bash
source .venv/bin/activate
python containerMain.py \
  --method <mc|restart> \
  --memoryMb <int> \
  --rareLocation <location_name> \
  --timeBound <float>             # required for --method mc
  --numTrials <int>               # default 1000, MC only
  <path/to/model.jani>
```

---

## Benchmark models

All benchmark models are in `models/benchmark/jani/`. Each has a `-test` variant with constants pre-filled for quick runs.

### manufacturing-sta

| Constant | Type | Example |
|----------|------|---------|
| `TIME_BOUND` | real | `550` |
| `PASS_W` | int | `9` |
| `FAIL_W` | int | `1` |

Rare event location: `loc_17`

```bash
# Monte Carlo (direct)
python containerMain.py \
  --method mc --memoryMb 512 \
  --numTrials 10000 --timeBound 550 \
  models/benchmark/jani/manufacturing-sta-test.jani

# Monte Carlo (via Docker)
python main.py -m 512 --method mc \
  --model models/benchmark/jani/manufacturing-sta-test.jani \
  --timeBound 550 --numTrials 10000

# RESTART (direct)
python containerMain.py \
  --method restart --memoryMb 512 \
  --rareLocation loc_17 \
  models/benchmark/jani/manufacturing-sta-test.jani

# RESTART (via Docker)
python main.py -m 512 --method restart \
  --model models/benchmark/jani/manufacturing-sta-test.jani \
  --rareLocation loc_17
```

### long-sta

| Constant | Type | Example |
|----------|------|---------|
| `TIME_BOUND` | real | `500` |
| `RARE_LO` | real | `15` |
| `Y_THRESHOLD` | real | `3` |

Rare event location: `loc_16`

```bash
# Monte Carlo (direct)
python containerMain.py \
  --method mc --memoryMb 512 \
  --numTrials 10000 --timeBound 500 \
  models/benchmark/jani/long-sta-test.jani

# Monte Carlo (via Docker)
python main.py -m 512 --method mc \
  --model models/benchmark/jani/long-sta-test.jani \
  --timeBound 500 --numTrials 10000

# RESTART (direct)
python containerMain.py \
  --method restart --memoryMb 512 \
  --rareLocation loc_16 \
  models/benchmark/jani/long-sta-test.jani

# RESTART (via Docker)
python main.py -m 512 --method restart \
  --model models/benchmark/jani/long-sta-test.jani \
  --rareLocation loc_16
```

### chain-sta

The chain model is a **template** — it must be expanded by `main.py` (which calls `ChainModelBuilder` to generate a concrete N-state chain). Running `containerMain.py` directly on the template is not supported.

| Constant | Type | Example |
|----------|------|---------|
| `N` | int | `5` |
| `TIME_BOUND` | real | `200` |
| `FAIL_W` | int | `1` |
| `PASS_W` | int | `9` |

Rare event location: `loc_0` (in the expanded model)

> Both methods require Docker — `main.py` expands the template via `ChainModelBuilder`
> before passing it to the container. Running `containerMain.py` directly on the template
> is not supported.
>
> Use `chain-sta-test.jani` (constants pre-filled, no prompts) or `chain-sta.jani`
> (undefined constants — `main.py` will prompt interactively for N, FAIL_W, PASS_W,
> TIME_BOUND before running).

```bash
# Monte Carlo (via Docker) — using pre-filled test variant
python main.py -m 512 --method mc \
  --model models/benchmark/jani/chain-sta-test.jani \
  --rareLocation loc_0 --timeBound 200 --numTrials 10000

# RESTART (via Docker) — using pre-filled test variant
python main.py -m 512 --method restart \
  --model models/benchmark/jani/chain-sta-test.jani \
  --rareLocation loc_0

# Monte Carlo with custom N — prompts for constants interactively
python main.py -m 512 --method mc \
  --model models/benchmark/jani/chain-sta.jani \
  --rareLocation loc_0 --timeBound 200 --numTrials 10000
```

---

## Generate JANI benchmarks

Use `generateJaniBenchmarks.py` to build new benchmark models in JANI format.

```bash
python generateJaniBenchmarks.py \
  --num_states 1000 \
  --num_clocks 8 \
  --branching_factor 2.5 \
  --max_time_bound 1000 \
  --rare_event_probability 0.01 \
  --seed 67
```

Write models to disk:

```bash
python generateJaniBenchmarks.py \
  --num_states 1000 \
  --num_clocks 8 \
  --branching_factor 2.5 \
  --max_time_bound 1000 \
  --rare_event_probability 0.01 \
  --seed 67 \
  --output_dir models/benchmark/jani
```

Validate without writing:

```bash
python generateJaniBenchmarks.py ... --dry_run
```

Optional safety checks:

```bash
python generateJaniBenchmarks.py ... --dry_run \
  --determinism_check \
  --min_transition_prob 1e-12 \
  --escape_prob 0
```

Notes:
- `loc_0` is the failure (rare event) location.
- `loc_{numStates - 1}` is the absorbing safe sink.
- At least 7 states required.

---

## Rebuild the Docker image

If you change `requirements.txt`, rebuild with:

```bash
docker build --no-cache -t simulation-image .
```

---

## Development

```bash
pytest                            # run all tests
pytest -v                         # verbose
pytest --cov                      # with coverage
ruff check .                      # lint
ruff check . --fix                # lint and auto-fix
```
