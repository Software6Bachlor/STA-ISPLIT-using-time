import dataclasses
import pytest


def _load_model():
    from loader import loadData
    from parser import parseModel
    data = loadData("tests/testData/manufacturing-sta.jani")
    model = parseModel(data)
    consts_map = {"TIME_BOUND": 100.0, "PASS_W": 1, "FAIL_W": 1}
    new_consts = tuple(
        dataclasses.replace(c, value=consts_map[c.name]) for c in model.constants
    )
    return dataclasses.replace(model, constants=new_consts)


# ── Constructor ───────────────────────────────────────────────────────────────

def test_init_storesRareEventLocation():
    from models.simulation import MonteCarloSimulation

    sim = MonteCarloSimulation(_load_model(), numTrials=1, rareEventLocation="loc_0")

    assert sim.rareEventLocation == "loc_0"


# ── Location detection ────────────────────────────────────────────────────────

@pytest.mark.parametrize("locations,expected", [
    ({"Idle": "loc_0"},  True),   # at rare event location (failure sink)
    ({"Idle": "loc_1"},  False),  # at other location
    ({"Idle": "loc_17"}, False),  # at intermediate state, not rare
    ({"A": "loc_1", "B": "loc_0"}, True),   # multi-automaton: one matches
    ({"A": "loc_1", "B": "loc_2"},  False),  # multi-automaton: none match
], ids=[
    "at-rare-location",
    "at-other-location",
    "at-intermediate",
    "multi-automaton-match",
    "multi-automaton-no-match",
])
def test_locationDetection(locations, expected):
    from models.simulation import MonteCarloSimulation
    from models.state import State

    sim = MonteCarloSimulation(_load_model(), numTrials=1, rareEventLocation="loc_0")
    state = State(locations=locations, globalVars={}, autoVars={})

    assert (sim.rareEventLocation in state.locations.values()) == expected


# ── run() result shape ────────────────────────────────────────────────────────

def test_run_zeroTrials():
    from models.simulation import MonteCarloSimulation, MonteCarloResult

    result = MonteCarloSimulation(_load_model(), numTrials=0, rareEventLocation="loc_0").run()

    assert isinstance(result, MonteCarloResult)
    assert result.numTrials == 0
    assert result.numHits == 0
    assert result.ciContainsZero is True


def test_run_returnsMonteCarloResult():
    from models.simulation import MonteCarloSimulation, MonteCarloResult

    result = MonteCarloSimulation(_load_model(), numTrials=10, rareEventLocation="loc_0").run()

    assert isinstance(result, MonteCarloResult)


def test_run_numHitsWithinBounds():
    from models.simulation import MonteCarloSimulation

    result = MonteCarloSimulation(_load_model(), numTrials=10, rareEventLocation="loc_0").run()

    assert 0 <= result.numHits <= result.numTrials


def test_run_probabilityEstimateMatchesRatio():
    from models.simulation import MonteCarloSimulation

    result = MonteCarloSimulation(_load_model(), numTrials=10, rareEventLocation="loc_0").run()

    assert result.probabilityEstimate == result.numHits / result.numTrials


# ── Wilson CI correctness ─────────────────────────────────────────────────────

def test_run_zeroHits_ciContainsZeroTrue():
    from models.simulation import MonteCarloSimulation

    # loc_999 does not exist in the model — guaranteed 0 hits
    result = MonteCarloSimulation(_load_model(), numTrials=100, rareEventLocation="loc_999").run()

    assert result.numHits == 0
    assert result.ciContainsZero is True


def test_run_zeroHits_halfWidthPositive():
    from models.simulation import MonteCarloSimulation

    # loc_999 does not exist in the model — guaranteed 0 hits
    result = MonteCarloSimulation(_load_model(), numTrials=100, rareEventLocation="loc_999").run()

    assert result.halfWidth > 0


# ── Fixed-time mode ──────────────────────────────────────────────────────────

def test_run_fixedTime_stopsAfterWallClockLimit():
    from models.simulation import MonteCarloSimulation
    import time

    sim = MonteCarloSimulation(_load_model(), numTrials=None, rareEventLocation="loc_0", wallClockLimit=2.0)
    t0 = time.perf_counter()
    result = sim.run()
    elapsed = time.perf_counter() - t0

    assert elapsed < 5.0          # did not run forever
    assert result.numTrials > 0   # completed at least one trial


# ── writeResult() JSON output ─────────────────────────────────────────────────

def test_writeResult_createsJsonWithMcFields(tmp_path, monkeypatch):
    import json
    import containerMain
    from models.simulation import MonteCarloResult

    monkeypatch.setattr(containerMain, "RESULTS_DIR", str(tmp_path))

    model = _load_model()
    result = MonteCarloResult(
        probabilityEstimate=0.005,
        halfWidth=0.001,
        ciContainsZero=False,
        numTrials=1000,
        numHits=5,
    )

    containerMain.writeResult("some/path/manufacturing-sta.jani", model, 100.0, result)

    files = list(tmp_path.iterdir())
    assert len(files) == 1
    payload = json.loads(files[0].read_text(encoding="utf-8"))

    assert payload["modelName"] == "manufacturing-sta"
    assert payload["method"] == "CMC"
    assert payload["timeBound"] == 100.0
    assert payload["numTrials"] == 1000
    assert payload["numHits"] == 5
    assert payload["probabilityEstimate"] == 0.005
    assert payload["halfWidth"] == 0.001
    assert payload["ciContainsZero"] is False
    assert "generatedAtUtc" in payload
